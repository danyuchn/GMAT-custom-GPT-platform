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
  try {
    // 如果內容為空，直接返回
    if (!content) return '';
    
    // 為了處理多行LaTeX公式，需要使用([\s\S]*?)來匹配包括換行在內的所有字符
    // 使用非貪婪模式確保匹配的結束是最近的一個結束符
    const blockRegex = /\$\$([\s\S]*?)\$\$/g;
    const inlineRegex = /\$([^$\n]+?)\$/g;
    
    // 保存處理過的內容塊以防止重複處理
    const processedBlocks: { [key: string]: string } = {};
    let blockCount = 0;
    
    // 第一步：將換行符轉換成<br>，但保護數學公式內的換行
    let processedContent = content.replace(/\n/g, '<br>');
    
    // 第二步：處理block公式 ($$...$$)，使用占位符替換它們
    processedContent = processedContent.replace(blockRegex, (match, latex) => {
      try {
        // 將$$公式中的<br>換回\n以確保LaTeX正確解析
        const fixedLatex = latex.replace(/<br>/g, '\n').trim();
        
        // 生成一個唯一的占位符
        const placeholder = `__KATEX_BLOCK_${blockCount++}__`;
        
        // 渲染LaTeX並存儲結果
        processedBlocks[placeholder] = `<div class="katex-block flex justify-center py-2">${
          katex.renderToString(fixedLatex, { 
            displayMode: true,
            throwOnError: false,
            strict: false,
            output: 'html',
            trust: true // 允許某些特殊命令
          })
        }</div>`;
        
        return placeholder;
      } catch (error) {
        console.error('KaTeX渲染錯誤 (block):', error, 'LaTeX:', latex);
        return match; // 如果渲染失敗，保留原始文本
      }
    });
    
    // 第三步：處理inline公式 ($...$)
    processedContent = processedContent.replace(inlineRegex, (match, latex) => {
      try {
        // 確保我們不處理已經作為占位符的部分
        if (match.includes('__KATEX_BLOCK_')) return match;
        
        // 清理LaTeX內容
        const cleanLatex = latex.trim();
        
        return katex.renderToString(cleanLatex, { 
          displayMode: false,
          throwOnError: false,
          strict: false,
          output: 'html',
          trust: true
        });
      } catch (error) {
        console.error('KaTeX渲染錯誤 (inline):', error, 'LaTeX:', latex);
        return match; // 如果渲染失敗，保留原始文本
      }
    });
    
    // 第四步：將占位符替換回渲染好的LaTeX
    Object.keys(processedBlocks).forEach(placeholder => {
      processedContent = processedContent.replace(placeholder, processedBlocks[placeholder]);
    });
    
    return processedContent;
  } catch (error) {
    console.error('LaTeX渲染總體錯誤:', error);
    return content; // 發生嚴重錯誤時，返回原始內容
  }
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
