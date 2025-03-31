import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChatFunction, chatFunctions } from "./chat-function-selector";
import { 
  Sparkles, Lightbulb, Copy, BookOpen, Search, ExternalLink, 
  MapPin, FileBarChart2, HelpCircle, Undo2, Calculator, 
  BrainCircuit, Compass, BarChart3, BookText, Asterisk,
  ListChecks, Footprints
} from "lucide-react";

// Enhanced icon mapping for each function type with specific colors
const iconMap: Record<string, any> = {
  // 數學題型功能
  simple_explain: { icon: Lightbulb, color: "text-amber-500" },
  quick_solve: { icon: Sparkles, color: "text-cyan-500" },
  variant_question: { icon: Asterisk, color: "text-indigo-500" },
  concept_explanation: { icon: BrainCircuit, color: "text-purple-500" },
  pattern_recognition: { icon: Compass, color: "text-fuchsia-500" },
  
  // 語言題型功能
  quick_solve_cr_tpa: { icon: Sparkles, color: "text-blue-500" },
  quick_solve_rc: { icon: BookText, color: "text-emerald-500" },
  mind_map: { icon: MapPin, color: "text-teal-500" },
  approach_diagnosis: { icon: ListChecks, color: "text-rose-500" },
  logical_term_explanation: { icon: HelpCircle, color: "text-violet-500" },
  
  // 圖表題型功能相關
  graph_default: { icon: BarChart3, color: "text-orange-500" }
};

interface FunctionCardsProps {
  onSelect: (prompt: string) => void;
  selectedFunction: string | null;
}

// 功能卡片組件
const FunctionCard = ({ func, isSelected, onSelect }: { 
  func: ChatFunction, 
  isSelected: boolean, 
  onSelect: () => void 
}) => {
  const iconData = iconMap[func.key] || iconMap.graph_default;
  const Icon = iconData.icon || Undo2;

  return (
    <Card 
      key={func.key} 
      className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-primary' : 'hover:shadow-md'}`}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{func.title}</CardTitle>
          <Icon className={`h-5 w-5 ${iconData.color}`} />
        </div>
        <CardDescription className="text-xs line-clamp-2">
          {func.description}
        </CardDescription>
      </CardHeader>
    </Card>
  );
};

export default function FunctionCards({ onSelect, selectedFunction }: FunctionCardsProps) {
  // Get the current prompt ID from URL
  const pathname = window.location.pathname;
  const promptId = pathname.split('/').pop();
  
  // Determine which function set to display based on the promptId
  const quantFunctions = chatFunctions.filter(f => 
    ["simple_explain", "quick_solve", "variant_question", "concept_explanation", "pattern_recognition"].includes(f.key)
  );
  
  const verbalFunctions = chatFunctions.filter(f => 
    ["quick_solve_cr_tpa", "quick_solve_rc", "mind_map", "approach_diagnosis", "logical_term_explanation"].includes(f.key)
  );
  
  const graphFunctions = chatFunctions.filter(f => 
    ["mind_map", "pattern_recognition", "approach_diagnosis"].includes(f.key)
  );
  
  // Determine which functions to show based on the prompt ID
  const isQuantPrompt = promptId === "1"; // Assuming Quant is ID 1
  const isVerbalPrompt = promptId === "2"; // Assuming Verbal is ID 2
  const isGraphPrompt = promptId === "3"; // Assuming Graph is ID 3
  
  const handleSelect = (func: ChatFunction) => {
    onSelect(func.prompt);
  };
  
  return (
    <div className="space-y-6">
      {isQuantPrompt && (
        <div>
          <h3 className="text-lg font-medium mb-3">量化題型功能</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {quantFunctions.map((func) => (
              <FunctionCard 
                key={func.key}
                func={func}
                isSelected={selectedFunction === func.key}
                onSelect={() => handleSelect(func)}
              />
            ))}
          </div>
        </div>
      )}
      
      {isVerbalPrompt && (
        <div>
          <h3 className="text-lg font-medium mb-3">語言題型功能</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {verbalFunctions.map((func) => (
              <FunctionCard 
                key={func.key}
                func={func}
                isSelected={selectedFunction === func.key}
                onSelect={() => handleSelect(func)}
              />
            ))}
          </div>
        </div>
      )}
      
      {isGraphPrompt && (
        <div>
          <h3 className="text-lg font-medium mb-3">圖表題型功能</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {graphFunctions.map((func) => (
              <FunctionCard 
                key={func.key}
                func={func}
                isSelected={selectedFunction === func.key}
                onSelect={() => handleSelect(func)}
              />
            ))}
          </div>
        </div>
      )}
      
      {selectedFunction && (
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
          <p className="font-medium mb-1">已選擇：{chatFunctions.find(f => f.key === selectedFunction)?.title}</p>
          <p className="text-sm text-slate-700 mb-2">{chatFunctions.find(f => f.key === selectedFunction)?.description}</p>
        </div>
      )}
    </div>
  );
}