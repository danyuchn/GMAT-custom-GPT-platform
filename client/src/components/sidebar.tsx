import { Link, useLocation } from "wouter";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import {
  HomeIcon,
  MessageSquare,
  BarChart2,
  Settings,
  LogOut,
} from "lucide-react";

export default function Sidebar() {
  const [location] = useLocation();
  const { logout } = useAuth();
  const { user } = useAuth();

  const handleLogout = () => {
    logout();
    window.location.href = "/login";
  };

  const navItems = [
    {
      label: "Home",
      icon: HomeIcon,
      href: "/",
      active: location === "/",
    },
    {
      label: "Conversations",
      icon: MessageSquare,
      href: "/",
      active: location.startsWith("/chat"),
    },
    {
      label: "Analytics",
      icon: BarChart2,
      href: "/admin",
      active: location === "/admin",
      admin: true,
    },
    {
      label: "Settings",
      icon: Settings,
      href: "/settings",
      active: location === "/settings",
    },
  ];

  return (
    <aside id="sidebar" className="hidden md:flex flex-col w-64 border-r border-accent bg-white">
      <div className="overflow-y-auto flex-1">
        <nav className="px-2 py-4 space-y-2">
          {navItems.map((item) => {
            // Skip admin-only items for non-admin users
            if (item.admin && !user?.isAdmin) return null;
            
            return (
              <Link key={item.label} href={item.href}>
                <a
                  className={cn(
                    "flex items-center px-4 py-2 text-sm font-medium rounded-md group",
                    item.active
                      ? "bg-primary text-white"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  <item.icon
                    className={cn(
                      "mr-3 h-5 w-5",
                      item.active ? "text-white" : "text-gray-500"
                    )}
                  />
                  {item.label}
                </a>
              </Link>
            );
          })}
        </nav>
      </div>
      
      <div className="p-4 border-t border-accent">
        <button
          onClick={handleLogout}
          className="flex items-center px-4 py-2 text-sm font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900 w-full"
        >
          <LogOut className="mr-3 h-5 w-5 text-gray-500" />
          Logout
        </button>
      </div>
    </aside>
  );
}
