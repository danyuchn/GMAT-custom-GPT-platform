import { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "wouter";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth";
import { apiRequest, queryClient } from "@/lib/queryClient";
import Navbar from "@/components/navbar";
import Sidebar from "@/components/sidebar";
import MessageBubble from "@/components/message-bubble";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { type Message, type SystemPrompt, type Conversation } from "@shared/schema";
import { RefreshCw, Send, ArrowLeft, Save } from "lucide-react";

export default function Chat() {
  const { promptId } = useParams();
  const [, navigate] = useLocation();
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const messageEndRef = useRef<HTMLDivElement>(null);
  const [model, setModel] = useState<string>("o3-mini");
  const [message, setMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
    }
  }, [isAuthenticated, navigate]);

  // Fetch system prompt
  const { data: systemPrompt, isLoading: isLoadingPrompt } = useQuery<SystemPrompt>({
    queryKey: [`/api/prompts/${promptId}`],
    enabled: isAuthenticated,
  });

  // Fetch or create conversation
  const { data: conversation, isLoading: isLoadingConversation } = useQuery<Conversation>({
    queryKey: [`/api/conversations/active/${promptId}`],
    enabled: isAuthenticated && !!promptId,
  });

  // Fetch messages for the conversation
  const { data: messages, isLoading: isLoadingMessages } = useQuery<Message[]>({
    queryKey: [`/api/conversations/${conversation?.id}/messages`],
    enabled: isAuthenticated && !!conversation?.id,
  });

  // Create new conversation mutation
  const createConversationMutation = useMutation({
    mutationFn: async () => {
      return apiRequest("POST", "/api/conversations", {
        systemPromptId: Number(promptId),
        model
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [`/api/conversations/active/${promptId}`] });
      toast({
        title: "New conversation started",
        description: "You can now start chatting with your AI assistant",
      });
    },
    onError: (error) => {
      toast({
        title: "Failed to start new conversation",
        description: error instanceof Error ? error.message : "Please try again later",
        variant: "destructive",
      });
    }
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!conversation?.id) return;
      setIsProcessing(true);
      
      return apiRequest("POST", `/api/conversations/${conversation.id}/messages`, {
        content,
        isUserMessage: true
      });
    },
    onSuccess: () => {
      setMessage("");
      queryClient.invalidateQueries({ queryKey: [`/api/conversations/${conversation?.id}/messages`] });
    },
    onError: (error) => {
      toast({
        title: "Failed to send message",
        description: error instanceof Error ? error.message : "Please try again later",
        variant: "destructive",
      });
      setIsProcessing(false);
    }
  });

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!message.trim() || isProcessing) return;
    
    await sendMessageMutation.mutateAsync(message);
  };

  // Handle creating a new conversation
  const handleNewConversation = () => {
    createConversationMutation.mutate();
  };

  // Scroll to bottom of messages when they update
  useEffect(() => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Update model selection
  const handleModelChange = (value: string) => {
    setModel(value);
  };

  if (!isAuthenticated) {
    return null; // Don't render anything while redirecting
  }

  return (
    <div className="flex flex-col h-screen">
      <Navbar />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        
        <main className="flex-1 overflow-auto bg-white">
          <div className="h-full flex flex-col">
            <div className="border-b border-accent bg-white">
              <div className="flex justify-between items-center px-4 py-3 sm:px-6">
                <div className="flex items-center">
                  <button 
                    className="md:hidden mr-3 text-gray-500"
                    onClick={() => navigate("/")}
                  >
                    <ArrowLeft className="h-6 w-6" />
                  </button>
                  <div>
                    <h2 className="text-lg font-medium text-gray-900">
                      {isLoadingPrompt ? "Loading..." : systemPrompt?.title}
                    </h2>
                    <div className="text-sm text-gray-500">Start your practice conversation</div>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <div className="relative inline-block text-left">
                    <Select 
                      value={model} 
                      onValueChange={handleModelChange}
                    >
                      <SelectTrigger className="w-[180px] border-accent">
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="o3-mini">o3-mini (faster)</SelectItem>
                        <SelectItem value="gpt-4o">gpt-4o (smarter)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <Button 
                    variant="outline" 
                    className="ml-3 text-primary"
                  >
                    <Save className="h-5 w-5 mr-1" />
                    Save
                  </Button>
                  
                  <Button 
                    className="ml-3"
                    onClick={handleNewConversation}
                    disabled={createConversationMutation.isPending}
                  >
                    <RefreshCw className={`h-5 w-5 mr-1 ${createConversationMutation.isPending ? 'animate-spin' : ''}`} />
                    New
                  </Button>
                </div>
              </div>
            </div>
            
            <div className="flex-1 overflow-auto p-4 bg-background" id="chat-messages">
              {isLoadingMessages ? (
                // Loading skeleton for messages
                <>
                  <div className="mb-4 max-w-3xl mx-auto animate-pulse">
                    <div className="flex items-start">
                      <div className="flex-shrink-0 mr-4">
                        <div className="h-10 w-10 rounded-full bg-gray-300"></div>
                      </div>
                      <div className="bg-white rounded-lg shadow-sm px-4 py-5 w-2/3">
                        <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                        <div className="h-4 bg-gray-300 rounded w-full mb-2"></div>
                        <div className="h-4 bg-gray-300 rounded w-5/6"></div>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                messages?.map((msg, index) => (
                  <MessageBubble 
                    key={index} 
                    message={msg} 
                    isLast={index === messages.length - 1}
                  />
                ))
              )}
              <div ref={messageEndRef} />
            </div>
            
            <div className="border-t border-accent bg-white p-4">
              <div className="max-w-3xl mx-auto">
                <form 
                  className="relative"
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                >
                  <Textarea
                    id="message-input"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    rows={3}
                    placeholder="Type your message here..."
                    className="block w-full rounded-md border border-accent shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-3 pr-20"
                    disabled={isProcessing}
                  />
                  <div className="absolute bottom-2 right-2 flex">
                    <Button 
                      type="submit"
                      disabled={!message.trim() || isProcessing}
                      className="inline-flex items-center px-4 py-2 shadow-sm"
                    >
                      <Send className="h-5 w-5 mr-1" />
                      Send
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
