import { 
  type User, 
  type InsertUser, 
  type SystemPrompt, 
  type InsertSystemPrompt,
  type Conversation,
  type InsertConversation,
  type Message,
  type InsertMessage 
} from "@shared/schema";

// modify the interface with any CRUD methods
// you might need

export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  getUserByEmail(email: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  getAllUsers(): Promise<User[]>;
  
  // System Prompt methods
  getSystemPrompt(id: number): Promise<SystemPrompt | undefined>;
  getAllSystemPrompts(): Promise<SystemPrompt[]>;
  createSystemPrompt(prompt: InsertSystemPrompt): Promise<SystemPrompt>;
  
  // Conversation methods
  getConversation(id: number): Promise<Conversation | undefined>;
  getConversationsByUserId(userId: number): Promise<Conversation[]>;
  getActiveConversation(userId: number, systemPromptId: number): Promise<Conversation | undefined>;
  createConversation(conversation: InsertConversation): Promise<Conversation>;
  
  // Message methods
  getMessage(id: number): Promise<Message | undefined>;
  getMessagesByConversationId(conversationId: number): Promise<Message[]>;
  createMessage(message: InsertMessage): Promise<Message>;
  
  // Admin methods
  getAdminAnalytics(): Promise<any>;
  getRecentConversations(): Promise<any[]>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private systemPrompts: Map<number, SystemPrompt>;
  private conversations: Map<number, Conversation>;
  private messages: Map<number, Message>;
  
  private userIdCounter: number;
  private systemPromptIdCounter: number;
  private conversationIdCounter: number;
  private messageIdCounter: number;

  constructor() {
    this.users = new Map();
    this.systemPrompts = new Map();
    this.conversations = new Map();
    this.messages = new Map();
    
    this.userIdCounter = 1;
    this.systemPromptIdCounter = 1;
    this.conversationIdCounter = 1;
    this.messageIdCounter = 1;
    
    // Initialize with default data
    this.initializeDefaultData();
  }

  private initializeDefaultData() {
    // Create default admin user synchronously
    const adminId = this.userIdCounter++;
    const adminNow = new Date();
    const adminUser: User = {
      id: adminId,
      username: "admin",
      password: "$2b$10$6hX3W8164gN2ubwaFuLLmemSGEBghGUPzsyIAUrl0FlD1Vll4Up2e", // "password"
      email: "admin@gmat.ai",
      isAdmin: true,
      createdAt: adminNow
    };
    this.users.set(adminId, adminUser);
    
    // Create default regular user synchronously
    const userId = this.userIdCounter++;
    const userNow = new Date();
    const regularUser: User = {
      id: userId,
      username: "user",
      password: "$2b$10$6hX3W8164gN2ubwaFuLLmemSGEBghGUPzsyIAUrl0FlD1Vll4Up2e", // "password"
      email: "user@gmat.ai",
      isAdmin: false,
      createdAt: userNow
    };
    this.users.set(userId, regularUser);
    
    // Create system prompts for GMAT topics
    this.createSystemPrompt({
      title: "Quant - Problem Solving",
      prompt: "You are a GMAT Quantitative Problem Solving expert. Help students understand and solve GMAT problem solving questions involving arithmetic, algebra, geometry, word problems, and number properties. Provide step-by-step explanations and test-taking strategies. Always start by welcoming the student and offering examples of topics you can help with.",
      description: "Practice arithmetic, algebra, geometry, and word problem strategies.",
      icon: "calculator",
      badge: "Popular",
      badgeColor: "green",
      practiceCount: "150+ practice problems",
    });
    
    this.createSystemPrompt({
      title: "Quant - Data Sufficiency",
      prompt: "You are a GMAT Data Sufficiency expert. Help students analyze what information is needed to solve quantitative problems following the GMAT data sufficiency format. Explain the methodology for evaluating statements, identifying when data is sufficient or insufficient, and avoiding common traps. Always start by welcoming the student and offering to explain the data sufficiency question format.",
      description: "Learn to analyze what information is needed to solve problems.",
      icon: "bar-chart-3",
      badge: "Challenging",
      badgeColor: "yellow",
      practiceCount: "100+ practice questions",
    });
    
    this.createSystemPrompt({
      title: "Verbal - Critical Reasoning",
      prompt: "You are a GMAT Critical Reasoning expert. Help students identify arguments, analyze reasoning, strengthen or weaken arguments, find assumptions, and evaluate conclusions. Teach students to carefully read arguments and answer questions by precisely evaluating the logic. Always start by welcoming the student and explaining the different types of critical reasoning questions you can help with.",
      description: "Strengthen arguments and identify reasoning flaws.",
      icon: "code",
      badge: "Popular",
      badgeColor: "green",
      practiceCount: "120+ practice passages",
    });
    
    this.createSystemPrompt({
      title: "Verbal - Sentence Correction",
      prompt: "You are a GMAT Sentence Correction expert. Help students identify and fix grammatical errors, improve clarity, and ensure concise expression in sentences. Focus on common GMAT grammar topics like subject-verb agreement, pronouns, modifiers, parallelism, idioms, and verb tense. Always start by welcoming the student and explaining the main concepts you can help with.",
      description: "Improve grammar, clarity, and concision in writing.",
      icon: "languages",
      badge: "Essential",
      badgeColor: "blue",
      practiceCount: "200+ practice sentences",
    });
    
    this.createSystemPrompt({
      title: "Verbal - Reading Comprehension",
      prompt: "You are a GMAT Reading Comprehension expert. Help students analyze complex passages and answer questions about main ideas, details, inferences, and author's tone. Teach strategies for efficient reading, note-taking, and question answering techniques specific to GMAT. Always start by welcoming the student and offering to provide practice passages or explain reading strategies.",
      description: "Build skills for analyzing complex passages and answering questions.",
      icon: "book-text",
      badge: "Time-intensive",
      badgeColor: "purple",
      practiceCount: "80+ practice passages",
    });
    
    this.createSystemPrompt({
      title: "Integrated Reasoning",
      prompt: "You are a GMAT Integrated Reasoning expert. Help students interpret graphs, tables, and multi-source reasoning problems. Guide them through analyzing data presented in various formats and drawing correct conclusions. Cover all four IR question types: graphics interpretation, table analysis, multi-source reasoning, and two-part analysis. Always start by welcoming the student and explaining the IR section format.",
      description: "Practice interpreting graphics, tables, and multi-source reasoning.",
      icon: "database",
      badge: "Challenging",
      badgeColor: "yellow",
      practiceCount: "90+ practice questions",
    });
    
    this.createSystemPrompt({
      title: "Analytical Writing Assessment",
      prompt: "You are a GMAT Analytical Writing Assessment expert. Help students analyze arguments, identify flaws in reasoning, and structure coherent essays. Guide them in developing strong introductions, body paragraphs with examples, and conclusions. Provide feedback on essay organization, clarity, and effective critique of arguments. Always start by welcoming the student and explaining the AWA section format.",
      description: "Develop argument analysis and essay writing skills.",
      icon: "edit",
      badge: "Essential",
      badgeColor: "blue",
      practiceCount: "50+ practice prompts",
    });
    
    this.createSystemPrompt({
      title: "Test Strategy & Timing",
      prompt: "You are a GMAT Test Strategy and Timing expert. Help students develop effective approaches for each section, manage time efficiently, and build test-taking stamina. Provide guidance on question pacing, when to guess, and how to maintain focus during the long exam. Share strategies for the adaptive nature of the test and dealing with test anxiety. Always start by welcoming the student and asking which aspects of test strategy they want to focus on.",
      description: "Learn time management and strategic approaches to test taking.",
      icon: "zap",
      badge: "Popular",
      badgeColor: "green",
      practiceCount: "Practice & advice",
    });
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username.toLowerCase() === username.toLowerCase(),
    );
  }
  
  async getUserByEmail(email: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.email.toLowerCase() === email.toLowerCase(),
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.userIdCounter++;
    const now = new Date();
    const user: User = { 
      ...insertUser, 
      id,
      isAdmin: insertUser.isAdmin ?? false, // 確保 isAdmin 有值
      createdAt: now
    };
    this.users.set(id, user);
    return user;
  }
  
  async getAllUsers(): Promise<User[]> {
    return Array.from(this.users.values());
  }
  
  // System Prompt methods
  async getSystemPrompt(id: number): Promise<SystemPrompt | undefined> {
    return this.systemPrompts.get(id);
  }
  
  async getAllSystemPrompts(): Promise<SystemPrompt[]> {
    return Array.from(this.systemPrompts.values());
  }
  
  async createSystemPrompt(insertPrompt: InsertSystemPrompt): Promise<SystemPrompt> {
    const id = this.systemPromptIdCounter++;
    const prompt: SystemPrompt = { 
      ...insertPrompt, 
      id,
      badge: insertPrompt.badge ?? null,
      badgeColor: insertPrompt.badgeColor ?? null,
      practiceCount: insertPrompt.practiceCount ?? null
    };
    this.systemPrompts.set(id, prompt);
    return prompt;
  }
  
  // Conversation methods
  async getConversation(id: number): Promise<Conversation | undefined> {
    return this.conversations.get(id);
  }
  
  async getConversationsByUserId(userId: number): Promise<Conversation[]> {
    return Array.from(this.conversations.values()).filter(
      (conversation) => conversation.userId === userId,
    );
  }
  
  async getActiveConversation(userId: number, systemPromptId: number): Promise<Conversation | undefined> {
    // Get most recent conversation for this user and system prompt
    const userConversations = await this.getConversationsByUserId(userId);
    return userConversations
      .filter(c => c.systemPromptId === systemPromptId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0];
  }
  
  async createConversation(insertConversation: InsertConversation): Promise<Conversation> {
    const id = this.conversationIdCounter++;
    const now = new Date();
    const conversation: Conversation = {
      ...insertConversation,
      id,
      createdAt: now,
    };
    this.conversations.set(id, conversation);
    return conversation;
  }
  
  // Message methods
  async getMessage(id: number): Promise<Message | undefined> {
    return this.messages.get(id);
  }
  
  async getMessagesByConversationId(conversationId: number): Promise<Message[]> {
    return Array.from(this.messages.values())
      .filter((message) => message.conversationId === conversationId)
      .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
  }
  
  async createMessage(insertMessage: InsertMessage): Promise<Message> {
    const id = this.messageIdCounter++;
    const now = new Date();
    const message: Message = {
      ...insertMessage,
      id,
      createdAt: now,
    };
    this.messages.set(id, message);
    return message;
  }
  
  // Admin methods
  async getAdminAnalytics(): Promise<any> {
    const totalUsers = this.users.size;
    const totalConversations = this.conversations.size;
    const totalMessages = this.messages.size;
    
    // Count users with activity in the last 24 hours
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const recentMessages = Array.from(this.messages.values())
      .filter(message => new Date(message.createdAt) >= oneDayAgo);
    
    const activeUserIds = new Set(
      Array.from(this.conversations.values())
        .filter(conv => recentMessages.some(msg => msg.conversationId === conv.id))
        .map(conv => conv.userId)
    );
    
    const activeUsers = activeUserIds.size;
    
    return {
      totalUsers,
      totalConversations,
      totalMessages,
      activeUsers,
    };
  }
  
  async getRecentConversations(): Promise<any[]> {
    // Get all conversations with additional data
    const conversations = Array.from(this.conversations.values());
    
    // Sort by creation date, most recent first
    const sortedConversations = conversations.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
    
    // Take only the 10 most recent conversations
    const recentConversations = sortedConversations.slice(0, 10);
    
    // Add additional data for each conversation
    const result = await Promise.all(
      recentConversations.map(async conversation => {
        const user = await this.getUser(conversation.userId);
        const systemPrompt = await this.getSystemPrompt(conversation.systemPromptId);
        const messages = await this.getMessagesByConversationId(conversation.id);
        
        // Format date for display
        const date = new Date(conversation.createdAt);
        const now = new Date();
        
        let formattedDate;
        if (date.toDateString() === now.toDateString()) {
          formattedDate = `Today, ${date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
        } else if (date.toDateString() === new Date(now.setDate(now.getDate() - 1)).toDateString()) {
          formattedDate = `Yesterday, ${date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
        } else {
          formattedDate = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        }
        
        return {
          ...conversation,
          user: user,
          promptTitle: systemPrompt?.title || "Unknown",
          messageCount: messages.length,
          lastMessageDate: formattedDate,
        };
      })
    );
    
    return result;
  }
}

export const storage = new MemStorage();
