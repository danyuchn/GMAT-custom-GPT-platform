import { useEffect } from "react";
import { useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/navbar";
import Sidebar from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { BarChart4, FileDown, FileUp } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { type User, type Conversation } from "@shared/schema";

type ConversationDetails = Conversation & {
  user: User;
  promptTitle: string;
  messageCount: number;
  lastMessageDate: string;
};

type AnalyticsSummary = {
  totalUsers: number;
  totalConversations: number;
  totalMessages: number;
  activeUsers: number;
};

export default function Admin() {
  const [, navigate] = useLocation();
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();

  // Redirect to login if not authenticated or not admin
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    
    if (isAuthenticated && user && !user.isAdmin) {
      toast({
        title: "Access denied",
        description: "You don't have permission to view the admin dashboard",
        variant: "destructive",
      });
      navigate("/");
    }
  }, [isAuthenticated, user, navigate, toast]);

  // Fetch analytics summary
  const { data: analytics, isLoading: isLoadingAnalytics } = useQuery<AnalyticsSummary>({
    queryKey: ["/api/admin/analytics"],
    enabled: isAuthenticated && user?.isAdmin,
  });

  // Fetch recent conversations
  const { data: conversations, isLoading: isLoadingConversations } = useQuery<ConversationDetails[]>({
    queryKey: ["/api/admin/conversations"],
    enabled: isAuthenticated && user?.isAdmin,
  });

  if (!isAuthenticated || (user && !user.isAdmin)) {
    return null; // Don't render anything while redirecting
  }

  return (
    <div className="flex flex-col h-screen">
      <Navbar />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        
        <main className="flex-1 overflow-auto bg-white">
          <div className="h-full overflow-auto">
            <div className="py-6 px-4 sm:px-6 lg:px-8">
              <div className="md:flex md:items-center md:justify-between pb-5 border-b border-accent">
                <div className="min-w-0 flex-1">
                  <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                    Admin Dashboard
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">
                    Analytics and user conversation data
                  </p>
                </div>
                <div className="mt-4 flex md:mt-0 md:ml-4">
                  <Button variant="outline" className="flex items-center">
                    <FileDown className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                  <Button className="ml-3 flex items-center">
                    <BarChart4 className="h-4 w-4 mr-2" />
                    Generate Report
                  </Button>
                </div>
              </div>

              <div className="mt-8">
                <h3 className="text-lg font-medium leading-6 text-gray-900">Usage Overview</h3>
                <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                  <Card className="bg-white overflow-hidden shadow-sm rounded-lg border border-accent">
                    <CardContent className="px-4 py-5 sm:p-6">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 bg-primary/10 rounded-md p-3">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                          </svg>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Total Users
                            </dt>
                            <dd>
                              <div className="text-lg font-medium text-gray-900">
                                {isLoadingAnalytics ? "Loading..." : analytics?.totalUsers}
                              </div>
                            </dd>
                          </dl>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-white overflow-hidden shadow-sm rounded-lg border border-accent">
                    <CardContent className="px-4 py-5 sm:p-6">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 bg-primary/10 rounded-md p-3">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                          </svg>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Total Conversations
                            </dt>
                            <dd>
                              <div className="text-lg font-medium text-gray-900">
                                {isLoadingAnalytics ? "Loading..." : analytics?.totalConversations}
                              </div>
                            </dd>
                          </dl>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-white overflow-hidden shadow-sm rounded-lg border border-accent">
                    <CardContent className="px-4 py-5 sm:p-6">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 bg-primary/10 rounded-md p-3">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Total Messages
                            </dt>
                            <dd>
                              <div className="text-lg font-medium text-gray-900">
                                {isLoadingAnalytics ? "Loading..." : analytics?.totalMessages}
                              </div>
                            </dd>
                          </dl>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-white overflow-hidden shadow-sm rounded-lg border border-accent">
                    <CardContent className="px-4 py-5 sm:p-6">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 bg-primary/10 rounded-md p-3">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Active Users (Today)
                            </dt>
                            <dd>
                              <div className="text-lg font-medium text-gray-900">
                                {isLoadingAnalytics ? "Loading..." : analytics?.activeUsers}
                              </div>
                            </dd>
                          </dl>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              <div className="mt-8">
                <h3 className="text-lg font-medium leading-6 text-gray-900">Popular Topics</h3>
                <div className="mt-4 bg-white shadow-sm rounded-lg border border-accent">
                  <div className="p-6">
                    <div className="relative h-80">
                      <div className="absolute inset-0 flex justify-center items-center">
                        <div className="w-full h-full bg-gray-50 rounded flex flex-col items-center justify-center">
                          <div className="flex space-x-4 mb-4">
                            <div className="h-32 w-20 bg-primary opacity-80 rounded"></div>
                            <div className="h-64 w-20 bg-primary rounded"></div>
                            <div className="h-48 w-20 bg-primary opacity-90 rounded"></div>
                            <div className="h-24 w-20 bg-primary opacity-70 rounded"></div>
                            <div className="h-56 w-20 bg-primary opacity-95 rounded"></div>
                            <div className="h-40 w-20 bg-primary opacity-85 rounded"></div>
                            <div className="h-16 w-20 bg-primary opacity-60 rounded"></div>
                            <div className="h-36 w-20 bg-primary opacity-75 rounded"></div>
                          </div>
                          <div className="text-sm text-gray-500 mt-2">Chart: Topic popularity by usage</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8">
                <h3 className="text-lg font-medium leading-6 text-gray-900">Recent User Conversations</h3>
                <div className="mt-4 flex flex-col">
                  <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                    <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                      <div className="shadow-sm overflow-hidden border border-accent rounded-lg">
                        <Table>
                          <TableHeader className="bg-gray-50">
                            <TableRow>
                              <TableHead className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                User
                              </TableHead>
                              <TableHead className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Topic
                              </TableHead>
                              <TableHead className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Model
                              </TableHead>
                              <TableHead className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Messages
                              </TableHead>
                              <TableHead className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Date
                              </TableHead>
                              <TableHead className="relative px-6 py-3">
                                <span className="sr-only">View</span>
                              </TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody className="bg-white divide-y divide-gray-200">
                            {isLoadingConversations ? (
                              // Loading skeleton for table rows
                              Array(5).fill(0).map((_, index) => (
                                <TableRow key={index} className="animate-pulse">
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-300"></div>
                                      <div className="ml-4">
                                        <div className="h-4 bg-gray-300 rounded w-24 mb-2"></div>
                                        <div className="h-3 bg-gray-300 rounded w-32"></div>
                                      </div>
                                    </div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="h-4 bg-gray-300 rounded w-40"></div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="h-4 bg-gray-300 rounded w-16"></div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="h-4 bg-gray-300 rounded w-8"></div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="h-4 bg-gray-300 rounded w-32"></div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap text-right">
                                    <div className="h-4 bg-gray-300 rounded w-12 ml-auto"></div>
                                  </TableCell>
                                </TableRow>
                              ))
                            ) : (
                              conversations?.map((conversation) => (
                                <TableRow key={conversation.id}>
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-medium">
                                        {conversation.user.username.substring(0, 2).toUpperCase()}
                                      </div>
                                      <div className="ml-4">
                                        <div className="text-sm font-medium text-gray-900">
                                          {conversation.user.username}
                                        </div>
                                        <div className="text-sm text-gray-500">
                                          {conversation.user.email}
                                        </div>
                                      </div>
                                    </div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-900">{conversation.promptTitle}</div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-900">{conversation.model}</div>
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {conversation.messageCount}
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {conversation.lastMessageDate}
                                  </TableCell>
                                  <TableCell className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <a href="#" className="text-primary hover:text-primary/80">View</a>
                                  </TableCell>
                                </TableRow>
                              ))
                            )}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
