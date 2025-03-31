import { type User, type SystemPrompt, type Conversation, type Message } from "@shared/schema";

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  user: User;
  token?: string;
}

export interface ChatMessage extends Message {
  isLoading?: boolean;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
  systemPrompt: SystemPrompt;
}

export interface AdminAnalytics {
  totalUsers: number;
  totalConversations: number;
  totalMessages: number;
  activeUsers: number;
}

export interface AdminConversation extends Conversation {
  user: User;
  promptTitle: string;
  messageCount: number;
  lastMessageDate: string;
}
