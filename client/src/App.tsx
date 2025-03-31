import { Switch, Route, useLocation, useRoute, Redirect } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import NotFound from "@/pages/not-found";
import Login from "@/pages/login";
import Home from "@/pages/home";
import Chat from "@/pages/chat";
import Admin from "@/pages/admin";
import { AuthProvider, useAuth } from "./lib/auth";

// Protected route component
function ProtectedRoute({ 
  component: Component, 
  adminOnly = false, 
  ...rest 
}: { 
  component: React.ComponentType<any>; 
  adminOnly?: boolean; 
  [key: string]: any 
}) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    // Show loading state
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Redirect to="/login" />;
  }

  if (adminOnly && (!user || !(user as any).isAdmin)) {
    // Redirect non-admin users trying to access admin pages
    return <Redirect to="/" />;
  }

  // Render the protected component
  return <Component {...rest} />;
}

// Public only route (accessible only when NOT authenticated)
function PublicOnlyRoute({ 
  component: Component, 
  ...rest 
}: { 
  component: React.ComponentType<any>; 
  [key: string]: any 
}) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }
  
  if (isAuthenticated) {
    return <Redirect to="/" />;
  }
  
  return <Component {...rest} />;
}

function Router() {
  return (
    <Switch>
      <Route path="/login" component={(props) => <PublicOnlyRoute component={Login} {...props} />} />
      <Route path="/" component={(props) => <ProtectedRoute component={Home} {...props} />} />
      <Route path="/chat/:promptId" component={(props) => <ProtectedRoute component={Chat} {...props} />} />
      <Route path="/admin" component={(props) => <ProtectedRoute component={Admin} adminOnly={true} {...props} />} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router />
        <Toaster />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
