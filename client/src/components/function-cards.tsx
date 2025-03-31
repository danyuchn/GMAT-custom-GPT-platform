import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChatFunction, chatFunctions } from "./chat-function-selector";
import { Sparkles, Lightbulb, Copy, BookOpen, Search, ExternalLink, MapPin, FileBarChart2, HelpCircle, Undo2 } from "lucide-react";

// Icon mapping for each function type
const iconMap: Record<string, any> = {
  simple_explain: Sparkles,
  quick_solve: Lightbulb,
  variant_question: Copy,
  concept_explanation: BookOpen,
  pattern_recognition: Search,
  quick_solve_cr_tpa: ExternalLink,
  quick_solve_rc: ExternalLink,
  mind_map: MapPin,
  approach_diagnosis: FileBarChart2,
  logical_term_explanation: HelpCircle,
};

interface FunctionCardsProps {
  onSelect: (prompt: string) => void;
  selectedFunction: string | null;
}

export default function FunctionCards({ onSelect, selectedFunction }: FunctionCardsProps) {
  // Group by categories
  const quantFunctions = chatFunctions.filter(f => 
    ["simple_explain", "quick_solve", "variant_question", "concept_explanation", "pattern_recognition"].includes(f.key)
  );
  
  const verbalFunctions = chatFunctions.filter(f => 
    ["quick_solve_cr_tpa", "quick_solve_rc", "mind_map", "approach_diagnosis", "logical_term_explanation"].includes(f.key)
  );
  
  const handleSelect = (func: ChatFunction) => {
    onSelect(func.prompt);
  };
  
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-3">量化題型功能</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {quantFunctions.map((func) => (
            <Card 
              key={func.key} 
              className={`cursor-pointer transition-all ${selectedFunction === func.key ? 'ring-2 ring-primary' : 'hover:shadow-md'}`}
              onClick={() => handleSelect(func)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{func.title}</CardTitle>
                  {(() => {
                    const Icon = iconMap[func.key] || Undo2;
                    return <Icon className="h-5 w-5 text-primary" />;
                  })()}
                </div>
                <CardDescription className="text-xs line-clamp-2">
                  {func.description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium mb-3">語言題型功能</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {verbalFunctions.map((func) => (
            <Card 
              key={func.key} 
              className={`cursor-pointer transition-all ${selectedFunction === func.key ? 'ring-2 ring-primary' : 'hover:shadow-md'}`}
              onClick={() => handleSelect(func)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{func.title}</CardTitle>
                  {(() => {
                    const Icon = iconMap[func.key] || Undo2;
                    return <Icon className="h-5 w-5 text-primary" />;
                  })()}
                </div>
                <CardDescription className="text-xs line-clamp-2">
                  {func.description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
      
      {selectedFunction && (
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
          <p className="font-medium mb-1">已選擇：{chatFunctions.find(f => f.key === selectedFunction)?.title}</p>
          <p className="text-sm text-slate-700 mb-2">{chatFunctions.find(f => f.key === selectedFunction)?.description}</p>
          <div className="text-xs text-slate-500 bg-white p-2 rounded border border-slate-200">
            提示：{chatFunctions.find(f => f.key === selectedFunction)?.prompt}
          </div>
        </div>
      )}
    </div>
  );
}