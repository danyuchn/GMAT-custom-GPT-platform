import type { Express, Request, Response, NextFunction } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import OpenAI from "openai";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { insertUserSchema, insertMessageSchema, insertConversationSchema, type User } from "../shared/schema";
import { generateSystemPrompt } from "./openai";
import { SessionData } from "express-session";

// Importing OpenAI types
type ChatCompletionMessageParam = {
  role: "system" | "user" | "assistant" | "function" | "tool";
  content: string;
  name?: string;
};

// Extend express-session
declare module "express-session" {
  interface SessionData {
    user?: User;
  }
}

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || "sk-default", // Will be replaced with actual key
});

export async function registerRoutes(app: Express): Promise<Server> {
  // Authentication routes
  app.post("/api/auth/register", async (req, res) => {
    try {
      const userData = insertUserSchema.parse(req.body);
      
      // Check if user already exists
      const existingUser = await storage.getUserByUsername(userData.username);
      if (existingUser) {
        return res.status(400).json({ message: "Username already exists" });
      }
      
      // Hash password
      const salt = await bcrypt.genSalt(10);
      const hashedPassword = await bcrypt.hash(userData.password, salt);
      
      // Create user
      const user = await storage.createUser({
        ...userData,
        password: hashedPassword,
      });
      
      // Remove password from response
      const { password, ...userWithoutPassword } = user;
      
      res.status(201).json(userWithoutPassword);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: error.errors });
      }
      res.status(500).json({ message: "Server error" });
    }
  });

  app.post("/api/auth/login", async (req, res) => {
    try {
      const { email, password } = req.body;
      
      // Validate input
      if (!email || !password) {
        return res.status(400).json({ message: "Please provide email and password" });
      }
      
      // Get user by email
      const user = await storage.getUserByEmail(email);
      if (!user) {
        return res.status(401).json({ message: "Invalid credentials" });
      }
      
      // Compare password
      const isMatch = await bcrypt.compare(password, user.password);
      if (!isMatch) {
        return res.status(401).json({ message: "Invalid credentials" });
      }
      
      // Remove password from response
      const { password: _, ...userWithoutPassword } = user;
      
      // Set user in session
      req.session.user = userWithoutPassword;
      
      res.json(userWithoutPassword);
    } catch (error) {
      console.error("Login error:", error);
      res.status(500).json({ message: "Server error" });
    }
  });

  app.post("/api/auth/logout", (req, res) => {
    req.session.destroy((err) => {
      if (err) {
        return res.status(500).json({ message: "Logout failed" });
      }
      // 清除自定義名稱的 cookie
      res.clearCookie("gmat.sid");
      res.json({ message: "Logged out successfully" });
    });
  });

  app.get("/api/auth/me", (req, res) => {
    if (req.session.user) {
      res.json(req.session.user);
    } else {
      res.status(401).json({ message: "Not authenticated" });
    }
  });

  // Auth middleware
  const isAuthenticated = (req: Request, res: Response, next: NextFunction) => {
    if (req.session.user) {
      next();
    } else {
      res.status(401).json({ message: "Not authenticated" });
    }
  };

  const isAdmin = (req: Request, res: Response, next: NextFunction) => {
    if (req.session.user && req.session.user.isAdmin) {
      next();
    } else {
      res.status(403).json({ message: "Not authorized" });
    }
  };

  // System Prompts routes
  app.get("/api/prompts", isAuthenticated, async (req, res) => {
    try {
      const prompts = await storage.getAllSystemPrompts();
      res.json(prompts);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  app.get("/api/prompts/:id", isAuthenticated, async (req, res) => {
    try {
      const prompt = await storage.getSystemPrompt(parseInt(req.params.id));
      if (!prompt) {
        return res.status(404).json({ message: "Prompt not found" });
      }
      res.json(prompt);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  // Conversations routes
  app.post("/api/conversations", isAuthenticated, async (req, res) => {
    try {
      const { systemPromptId, model } = req.body;
      const userId = req.session.user.id;
      
      // Validate input
      if (!systemPromptId || !model) {
        return res.status(400).json({ message: "Missing required fields" });
      }
      
      // Get system prompt
      const systemPrompt = await storage.getSystemPrompt(systemPromptId);
      if (!systemPrompt) {
        return res.status(404).json({ message: "System prompt not found" });
      }
      
      // Create conversation
      const conversationData = insertConversationSchema.parse({
        userId,
        systemPromptId,
        model,
      });
      
      const conversation = await storage.createConversation(conversationData);
      
      // Create welcome message from AI
      const welcomeMessage = await generateSystemPrompt(systemPrompt.prompt, model);
      
      await storage.createMessage({
        conversationId: conversation.id,
        content: welcomeMessage,
        isUserMessage: false,
      });
      
      res.status(201).json(conversation);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: error.errors });
      }
      res.status(500).json({ message: "Server error" });
    }
  });

  app.get("/api/conversations", isAuthenticated, async (req, res) => {
    try {
      const userId = req.session.user.id;
      const conversations = await storage.getConversationsByUserId(userId);
      res.json(conversations);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  app.get("/api/conversations/active/:systemPromptId", isAuthenticated, async (req, res) => {
    try {
      const userId = req.session.user.id;
      const systemPromptId = parseInt(req.params.systemPromptId);
      
      // Get active conversation or create new one
      let conversation = await storage.getActiveConversation(userId, systemPromptId);
      
      if (!conversation) {
        // Get system prompt
        const systemPrompt = await storage.getSystemPrompt(systemPromptId);
        if (!systemPrompt) {
          return res.status(404).json({ message: "System prompt not found" });
        }
        
        // Create new conversation
        conversation = await storage.createConversation({
          userId,
          systemPromptId,
          model: "o3-mini", // Default model
        });
        
        // Create welcome message from AI
        const welcomeMessage = await generateSystemPrompt(systemPrompt.prompt, "o3-mini");
        
        await storage.createMessage({
          conversationId: conversation.id,
          content: welcomeMessage,
          isUserMessage: false,
        });
      }
      
      res.json(conversation);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  app.get("/api/conversations/:id", isAuthenticated, async (req, res) => {
    try {
      const conversationId = parseInt(req.params.id);
      const userId = req.session.user.id;
      
      const conversation = await storage.getConversation(conversationId);
      
      if (!conversation) {
        return res.status(404).json({ message: "Conversation not found" });
      }
      
      // Check if user owns the conversation
      if (conversation.userId !== userId && !req.session.user.isAdmin) {
        return res.status(403).json({ message: "Not authorized" });
      }
      
      res.json(conversation);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  app.get("/api/conversations/:id/messages", isAuthenticated, async (req, res) => {
    try {
      const conversationId = parseInt(req.params.id);
      const userId = req.session.user.id;
      
      // Check if user owns the conversation
      const conversation = await storage.getConversation(conversationId);
      
      if (!conversation) {
        return res.status(404).json({ message: "Conversation not found" });
      }
      
      if (conversation.userId !== userId && !req.session.user.isAdmin) {
        return res.status(403).json({ message: "Not authorized" });
      }
      
      const messages = await storage.getMessagesByConversationId(conversationId);
      res.json(messages);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  app.post("/api/conversations/:id/messages", isAuthenticated, async (req, res) => {
    try {
      const conversationId = parseInt(req.params.id);
      const userId = req.session.user.id;
      
      // Check if user owns the conversation
      const conversation = await storage.getConversation(conversationId);
      
      if (!conversation) {
        return res.status(404).json({ message: "Conversation not found" });
      }
      
      if (conversation.userId !== userId) {
        return res.status(403).json({ message: "Not authorized" });
      }
      
      // Get system prompt for the conversation
      const systemPrompt = await storage.getSystemPrompt(conversation.systemPromptId);
      
      if (!systemPrompt) {
        return res.status(404).json({ message: "System prompt not found" });
      }
      
      // Create user message
      const messageData = insertMessageSchema.parse({
        conversationId,
        content: req.body.content,
        isUserMessage: true,
      });
      
      await storage.createMessage(messageData);
      
      // Get all messages for the conversation
      const messages = await storage.getMessagesByConversationId(conversationId);
      
      // Generate AI response
      const prompt = systemPrompt.prompt;
      const userMessages: ChatCompletionMessageParam[] = messages.map(msg => ({
        role: msg.isUserMessage ? "user" : "assistant",
        content: msg.content
      } as ChatCompletionMessageParam));
      
      const systemMessage: ChatCompletionMessageParam = { 
        role: "system", 
        content: prompt 
      };
      
      const response = await openai.chat.completions.create({
        model: conversation.model,
        messages: [
          systemMessage,
          ...userMessages
        ],
      });
      
      const aiContent = response.choices[0].message.content || "I'm not sure how to respond to that.";
      
      // Save AI response
      const aiMessageData = insertMessageSchema.parse({
        conversationId,
        content: aiContent,
        isUserMessage: false,
      });
      
      const aiMessage = await storage.createMessage(aiMessageData);
      
      res.status(201).json(aiMessage);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: error.errors });
      }
      console.error("Error sending message:", error);
      res.status(500).json({ message: "Server error" });
    }
  });

  // Admin routes
  app.get("/api/admin/analytics", isAuthenticated, isAdmin, async (req, res) => {
    try {
      const analytics = await storage.getAdminAnalytics();
      res.json(analytics);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  app.get("/api/admin/conversations", isAuthenticated, isAdmin, async (req, res) => {
    try {
      const conversations = await storage.getRecentConversations();
      res.json(conversations);
    } catch (error) {
      res.status(500).json({ message: "Server error" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
