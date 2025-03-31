import { useLocation } from "wouter";
import { type SystemPrompt } from "@shared/schema";
import {
  Calculator,
  BarChart3,
  Code,
  BookText,
  Languages,
  Database,
  Edit,
  Zap,
} from "lucide-react";

interface PromptCardProps {
  prompt: SystemPrompt;
}

const iconMap: Record<string, any> = {
  calculator: Calculator,
  "bar-chart-3": BarChart3,
  code: Code,
  "book-text": BookText,
  languages: Languages,
  database: Database,
  edit: Edit,
  zap: Zap,
};

// 映射標題為中文顯示
const titleMap: Record<string, string> = {
  "Quant-related": "數學題型",
  "Verbal-Related": "語言題型",
  "Graph-Related": "圖表題型"
};

export default function PromptCard({ prompt }: PromptCardProps) {
  const [, navigate] = useLocation();

  const handleClick = () => {
    navigate(`/chat/${prompt.id}`);
  };

  // Get the appropriate icon component or default to Calculator
  const IconComponent = prompt.icon ? iconMap[prompt.icon] || Calculator : Calculator;

  return (
    <div 
      className="bg-white rounded-lg shadow-sm border border-accent overflow-hidden hover:shadow-md transition-shadow duration-200 cursor-pointer"
      onClick={handleClick}
    >
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0 bg-primary rounded-md p-3">
            <IconComponent className="h-6 w-6 text-white" />
          </div>
          <div className="ml-5">
            <h3 className="text-lg font-medium leading-6 text-gray-900">{titleMap[prompt.title] || prompt.title}</h3>
            <div className="mt-2 text-sm text-gray-500">
              {prompt.description}
            </div>
          </div>
        </div>
      </div>
      <div className="px-4 py-4 sm:px-6 bg-gray-50 flex justify-between items-center">
        <div className="text-xs font-medium text-primary truncate">
          {prompt.practiceCount}
        </div>
        {prompt.badge && (
          <div>
            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-${prompt.badgeColor || 'green'}-100 text-${prompt.badgeColor || 'green'}-800`}>
              {prompt.badge}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
