import { useState } from "react";
import { useLocation } from "wouter";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/hooks/use-toast";

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";

const formSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().default(false),
});

type FormValues = z.infer<typeof formSchema>;

export default function Login() {
  const [, navigate] = useLocation();
  const { login } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  });

  const onSubmit = async (data: FormValues) => {
    setIsLoading(true);
    try {
      // Using direct fetch instead of apiRequest to handle error response
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Cache-Control": "no-cache",
          "Pragma": "no-cache"
        },
        body: JSON.stringify({
          email: data.email,
          password: data.password,
        }),
        credentials: "include",
      });
      
      const responseData = await response.json();
      
      if (response.ok) {
        // Show success message
        toast({
          title: "Login successful",
          description: "Welcome back to GMAT AI Assistant",
        });
        
        // Set user data in context - this will trigger the auth context update
        // and the protected routes will automatically handle redirect
        login(responseData);
      } else {
        // Handle error from server
        toast({
          title: "Login failed",
          description: responseData.message || "Please check your credentials and try again",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Login failed",
        description: error instanceof Error ? error.message : "Please check your credentials and try again",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12 sm:px-6 lg:px-8">
      <Card className="max-w-md w-full space-y-8 p-10 rounded-xl shadow-md">
        <div>
          <h1 className="text-center text-3xl font-bold text-primary">GMAT AI Assistant</h1>
          <p className="mt-2 text-center text-sm text-gray-600">Your intelligent study partner</p>
        </div>
        
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="mt-8 space-y-6">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="sr-only">Email address</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="Email address" 
                      type="email" 
                      {...field} 
                      className="appearance-none rounded-md relative block w-full px-3 py-2 border border-accent placeholder-gray-500 text-foreground focus:outline-none focus:ring-primary focus:border-primary focus:z-10 sm:text-sm"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="sr-only">Password</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="Password" 
                      type="password" 
                      {...field} 
                      className="appearance-none rounded-md relative block w-full px-3 py-2 border border-accent placeholder-gray-500 text-foreground focus:outline-none focus:ring-primary focus:border-primary focus:z-10 sm:text-sm"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex items-center justify-between">
              <FormField
                control={form.control}
                name="rememberMe"
                render={({ field }) => (
                  <FormItem className="flex items-center">
                    <FormControl>
                      <Checkbox 
                        checked={field.value} 
                        onCheckedChange={field.onChange}
                        className="h-4 w-4 text-primary focus:ring-primary border-accent rounded"
                      />
                    </FormControl>
                    <FormLabel className="ml-2 block text-sm text-gray-600">
                      Remember me
                    </FormLabel>
                  </FormItem>
                )}
              />

              <div className="text-sm">
                <a href="#" className="font-medium text-primary hover:text-primary/80">
                  Forgot your password?
                </a>
              </div>
            </div>

            <Button 
              type="submit" 
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </Button>
            
            <div className="text-center text-sm">
              <span className="text-gray-600">Don't have an account?</span>
              <a href="#" className="font-medium text-primary hover:text-primary/80 ml-1">Sign up</a>
            </div>
          </form>
        </Form>
      </Card>
    </div>
  );
}
