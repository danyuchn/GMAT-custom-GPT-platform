import { useState } from "react";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// 定義對話功能類型
export interface ChatFunction {
  key: string;
  title: string;
  description: string;
  prompt: string;
}

// 對話功能列表
export const chatFunctions: ChatFunction[] = [
  {
    key: "simple_explain",
    title: "簡單解釋",
    description: "以高中生能理解的方式解釋解題步驟",
    prompt: "請用繁體中文解釋解題步驟，並以高中生能理解的方式回答。"
  },
  {
    key: "quick_solve",
    title: "快速解法",
    description: "提供在2分鐘內用紙筆解決問題的方法",
    prompt: "請用繁體中文提供一個能在2分鐘內用紙筆和視覺估算解決數學問題的快捷方法。原則是：計算越少、數字越簡單、公式越少且越簡單越好。如果代入數字或使用視覺猜測更簡單，請採用這種方法。"
  },
  {
    key: "variant_question",
    title: "變體題目",
    description: "設計一個變體題目來練習相同的解題方法",
    prompt: "請用繁體中文設計一個變體題目，讓我可以練習使用相同的解題方法。"
  },
  {
    key: "concept_explanation",
    title: "概念說明",
    description: "解釋題目測試的數學概念",
    prompt: "如果你是題目出題者，你希望在這個問題中測試哪些特定的數學概念？請用繁體中文回答。"
  },
  {
    key: "pattern_recognition",
    title: "模式識別",
    description: "幫助識別適用此解法的題目特徵",
    prompt: "在未來的題目中，應該具備哪些特徵才能應用這種特定的解題方法？請用繁體中文回答。"
  },
  {
    key: "quick_solve_cr_tpa",
    title: "批判性閱讀 - 快速解法",
    description: "2分鐘內解決批判性閱讀問題的方法",
    prompt: "請用繁體中文提供一個能在2分鐘內解決問題的快捷方法。原則如下：\n1. 首先，閱讀問題並識別解鎖問題的關鍵要素。\n2. 接著，告訴我文章中哪些部分是相關信息，哪些不是。\n3. 然後，指出是使用預寫（預先草擬答案）策略還是排除策略來回答問題。\n每個步驟必須包含引導到下一步的明確提示，並遵循線性、單向的人類思維過程。"
  },
  {
    key: "quick_solve_rc",
    title: "閱讀理解 - 快速解法",
    description: "6-8分鐘內解決閱讀理解問題的方法",
    prompt: "請用繁體中文提供一個能在6-8分鐘內快速解決問題的方法。該方法應遵循以下步驟：\n1. 首先，識別文章中需要注意的關鍵信息（注意：即使不清楚問題可能測試什麼，也應該這樣做）。\n2. 接著，為每個問題指定關鍵詞和要點。\n3. 然後，根據這些關鍵詞和要點，指出文章中哪些相關段落是相關的。\n4. 之後，建議是使用預寫策略還是排除策略來回答問題。\n5. 如果選擇預寫，請詳細說明逐步推理過程。\n每個步驟必須提供引導到下一步的明確線索，並且必須遵循線性、單向的思維過程。此外，請為每個選項的判斷提供詳細解釋。"
  },
  {
    key: "mind_map",
    title: "思維導圖",
    description: "創建文章的思維導圖",
    prompt: "請用繁體中文創建文章本身的思維導圖。"
  },
  {
    key: "approach_diagnosis",
    title: "解題方法診斷",
    description: "分析解題方法中的錯誤並提供改進建議",
    prompt: "這是我對問題解決過程的語言解釋。請用繁體中文識別我的方法中的任何錯誤，並提出改進建議。"
  },
  {
    key: "logical_term_explanation",
    title: "邏輯術語解釋",
    description: "解釋文章中的邏輯術語",
    prompt: "請用繁體中文解釋文章中提供的五個答案選項中每個邏輯術語的含義。"
  }
];

interface ChatFunctionSelectorProps {
  onSelect: (prompt: string) => void;
}

export default function ChatFunctionSelector({ onSelect }: ChatFunctionSelectorProps) {
  const [activeFunction, setActiveFunction] = useState<string | null>(null);
  
  const handleSelect = (key: string) => {
    const selectedFunction = chatFunctions.find(func => func.key === key);
    if (selectedFunction) {
      setActiveFunction(key);
      onSelect(selectedFunction.prompt);
    }
  };
  
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2">
        <Select onValueChange={handleSelect}>
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="選擇對話功能" />
          </SelectTrigger>
          <SelectContent>
            {chatFunctions.map((func) => (
              <SelectItem key={func.key} value={func.key}>
                {func.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        {activeFunction && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant="outline" className="cursor-help">
                  <span className="flex items-center gap-1">
                    {chatFunctions.find(f => f.key === activeFunction)?.title}
                    <HelpCircle className="h-3.5 w-3.5" />
                  </span>
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs">{chatFunctions.find(f => f.key === activeFunction)?.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      
      {activeFunction && (
        <div className="mt-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm">
          <p className="text-slate-700">
            {chatFunctions.find(f => f.key === activeFunction)?.description}
          </p>
        </div>
      )}
    </div>
  );
}