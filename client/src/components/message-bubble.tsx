import { useMemo, useEffect, useRef } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/lib/auth";
import { type Message } from "@shared/schema";
import { LightbulbIcon } from "lucide-react";
import katex from "katex";
import "katex/dist/katex.min.css";

interface MessageBubbleProps {
  message: Message;
  isLast: boolean;
}

// 用於處理並渲染LaTeX數學公式
const renderLatex = (content: string): string => {
  // 使用正則表達式找出所有的LaTeX公式
  // 匹配 $...$ 用於行內公式
  // 匹配 $$...$$ 用於獨立公式 - 使用非貪婪模式 .*? 並允許多行
  const inlineRegex = /\$([^$]+?)\$/g;
  const blockRegex = /\$\$([\s\S]*?)\$\$/g;
  
  // 先將換行符轉換成<br>標籤
  let processedContent = content.replace(/\n/g, '<br>');
  
  // 首先處理獨立公式 (block)
  processedContent = processedContent.replace(blockRegex, (match, latex) => {
    try {
      // 添加具有樣式的div容器，使公式居中顯示
      return `<div class="katex-block flex justify-center py-2">${katex.renderToString(latex.trim(), { 
        displayMode: true,
        throwOnError: false, // 防止渲染錯誤導致整個組件崩潰
        output: 'html'
      })}</div>`;
    } catch (error) {
      console.error('KaTeX渲染錯誤 (block):', error, 'LaTeX:', latex);
      return match; // 如果渲染失敗，保留原始文本
    }
  });
  
  // 然後處理行內公式 (inline)
  processedContent = processedContent.replace(inlineRegex, (match, latex) => {
    try {
      // 確保我們不處理已經處理過的部分 (防止嵌套處理)
      if (match.includes('class="katex"')) return match;
      
      return katex.renderToString(latex.trim(), { 
        displayMode: false,
        throwOnError: false,
        output: 'html'
      });
    } catch (error) {
      console.error('KaTeX渲染錯誤 (inline):', error, 'LaTeX:', latex);
      return match; // 如果渲染失敗，保留原始文本
    }
  });
  
  return processedContent;
};

export default function MessageBubble({ message, isLast }: MessageBubbleProps) {
  const { user } = useAuth();
  const contentRef = useRef<HTMLDivElement>(null);
  
  const initials = useMemo(() => {
    // Type assertion to help TypeScript understand the structure
    const typedUser = user as { username?: string } | null;
    if (typedUser && typedUser.username) {
      return typedUser.username.substring(0, 2).toUpperCase();
    }
    return "U";
  }, [user]);

  if (message.isUserMessage) {
    return (
      <div className="mb-4 max-w-3xl mx-auto">
        <div className="flex items-start justify-end">
          <div className="bg-primary text-white rounded-lg shadow-sm px-4 py-5 max-w-[80%]">
            <div 
              className="text-sm prose prose-sm prose-invert" 
              dangerouslySetInnerHTML={{ __html: renderLatex(message.content) }}
            />
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
          <div 
            ref={contentRef}
            className="text-sm text-gray-700 prose prose-sm" 
            dangerouslySetInnerHTML={{ __html: renderLatex(message.content) }} 
          />
        </div>
      </div>
    </div>
  );
}
