import { useMemo } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/lib/auth";
import { type Message } from "@shared/schema";
import { LightbulbIcon } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  isLast: boolean;
}

export default function MessageBubble({ message, isLast }: MessageBubbleProps) {
  const { user } = useAuth();
  
  const initials = useMemo(() => {
    return user?.username ? user.username.substring(0, 2).toUpperCase() : "U";
  }, [user]);

  if (message.isUserMessage) {
    return (
      <div className="mb-4 max-w-3xl mx-auto">
        <div className="flex items-start justify-end">
          <div className="bg-primary text-white rounded-lg shadow-sm px-4 py-5 max-w-[80%]">
            <div className="text-sm">
              <p>{message.content}</p>
            </div>
          </div>
          <div className="flex-shrink-0 ml-4">
            <Avatar className="h-10 w-10 rounded-full bg-gray-200">
              <AvatarFallback className="text-gray-600 font-medium">
                {initials}
              </AvatarFallback>
            </Avatar>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="mb-4 max-w-3xl mx-auto">
      <div className="flex items-start">
        <div className="flex-shrink-0 mr-4">
          <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-white">
            <LightbulbIcon className="h-6 w-6" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm px-4 py-5 border border-accent max-w-[80%]">
          <div className="text-sm text-gray-700 prose prose-sm" dangerouslySetInnerHTML={{ __html: message.content.replace(/\n/g, '<br>') }} />
        </div>
      </div>
    </div>
  );
}
