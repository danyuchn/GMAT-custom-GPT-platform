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
      title: "Quant-related",
      prompt: "You are a GMAT Quantitative expert. Help students understand and solve GMAT quantitative questions involving arithmetic, algebra, geometry, word problems, number properties, and data sufficiency. Provide step-by-step explanations and test-taking strategies. Always start by welcoming the student and offer to help with their quantitative questions. Always respond in Traditional Chinese (繁體中文). For mathematical expressions, ALWAYS use LaTeX notation with dollar signs: inline formulas with single dollars like $x^2$ and display formulas with double dollars like $$\\frac{a}{b}$$. Never use plain text for mathematical expressions - always format them properly with LaTeX.",
      description: "數學題型：練習算術、代數、幾何、數據充分性和解題技巧",
      icon: "calculator",
      badge: "熱門",
      badgeColor: "green",
      practiceCount: "250+ 練習題",
    });
    
    this.createSystemPrompt({
      title: "Verbal-Related",
      prompt: "You are a GMAT Verbal expert. Help students with critical reasoning, reading comprehension, and sentence correction questions. Guide them in identifying arguments, analyzing passages, strengthening/weakening arguments, finding assumptions, evaluating conclusions, and fixing grammar issues. Always start by welcoming the student and asking which verbal area they want to focus on. Always respond in Traditional Chinese (繁體中文).",
      description: "語言題型：加強批判性思維、閱讀理解和句子改錯能力",
      icon: "book-text",
      badge: "必學",
      badgeColor: "blue",
      practiceCount: "400+ 練習題",
    });
    
    this.createSystemPrompt({
      title: "Graph-Related",
      prompt: "You are a GMAT Integrated Reasoning expert. Help students interpret graphs, tables, and multi-source reasoning problems. Guide them through analyzing data presented in various formats and drawing correct conclusions. Cover all four IR question types: graphics interpretation, table analysis, multi-source reasoning, and two-part analysis. Always start by welcoming the student and offering to help with graph interpretation and analysis. Always respond in Traditional Chinese (繁體中文). For mathematical expressions, ALWAYS use LaTeX notation with dollar signs: inline formulas with single dollars like $x^2$ and display formulas with double dollars like $$\\frac{a}{b}$$. Never use plain text for mathematical expressions - always format them properly with LaTeX.",
      description: "圖表題型：練習解讀圖表、表格和多源推理問題",
      icon: "bar-chart-3",
      badge: "挑戰",
      badgeColor: "yellow",
      practiceCount: "90+ 練習題",
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
      responseId: insertMessage.responseId || null,
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
