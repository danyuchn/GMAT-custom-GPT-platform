import { useEffect } from "react";
import { useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth";
import Navbar from "@/components/navbar";
import Sidebar from "@/components/sidebar";
import PromptCard from "@/components/prompt-card";
import { type SystemPrompt } from "@shared/schema";

export default function Home() {
  const [, navigate] = useLocation();
  const { user, isAuthenticated } = useAuth();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
    }
  }, [isAuthenticated, navigate]);

  // Fetch system prompts
  const { data: systemPrompts, isLoading } = useQuery<SystemPrompt[]>({
    queryKey: ["/api/prompts"],
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) {
    return null; // Don't render anything while redirecting
  }

  return (
    <div className="flex flex-col h-screen">
      <Navbar />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        
        <main className="flex-1 overflow-auto bg-white">
          <div id="prompt-selection" className="h-full overflow-auto">
            <div className="py-6 px-4 sm:px-6 lg:px-8">
              <div className="md:flex md:items-center md:justify-between pb-5 border-b border-accent">
                <div className="min-w-0 flex-1">
                  <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                    GMAT 學習主題
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">
                    選擇一個主題開始與 AI 助手練習
                  </p>
                </div>
              </div>

              <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {isLoading ? (
                  // Loading skeleton
                  Array(8).fill(0).map((_, index) => (
                    <div key={index} className="bg-white rounded-lg shadow-sm border border-accent overflow-hidden animate-pulse">
                      <div className="px-4 py-5 sm:p-6">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 bg-gray-200 rounded-md p-3 h-12 w-12"></div>
                          <div className="ml-5 w-full">
                            <div className="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
                            <div className="h-4 bg-gray-200 rounded w-full"></div>
                          </div>
                        </div>
                      </div>
                      <div className="px-4 py-4 sm:px-6 bg-gray-50 flex justify-between items-center">
                        <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                      </div>
                    </div>
                  ))
                ) : (
                  systemPrompts?.map((prompt) => (
                    <PromptCard key={prompt.id} prompt={prompt} />
                  ))
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
