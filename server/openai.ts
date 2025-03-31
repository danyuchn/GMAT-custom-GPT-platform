import OpenAI from "openai";

// Define types for OpenAI API
type ChatCompletionSystemMessageParam = {
  role: "system";
  content: string;
};

type ChatCompletionUserMessageParam = {
  role: "user";
  content: string;
};

type ChatCompletionAssistantMessageParam = {
  role: "assistant";
  content: string;
};

type ChatCompletionToolMessageParam = {
  role: "tool";
  content: string;
  tool_call_id: string;
};

type ChatCompletionFunctionMessageParam = {
  role: "function";
  content: string;
  name: string;
};

// Combined type for message parameters
type ChatCompletionMessageParam = 
  | ChatCompletionSystemMessageParam 
  | ChatCompletionUserMessageParam 
  | ChatCompletionAssistantMessageParam
  | ChatCompletionToolMessageParam
  | ChatCompletionFunctionMessageParam;

// the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Generate welcome message based on system prompt
export async function generateSystemPrompt(prompt: string, promptTitle: string): Promise<string> {
  try {
    const messages = [
      { role: "system", content: prompt } as const,
      { role: "user", content: "Hello, I'd like to start practicing for the GMAT." } as const
    ];
    
    // Determine the appropriate model based on the prompt title
    const model = determineModel(promptTitle);
    console.log(`Using model: ${model} for welcome message with prompt: ${promptTitle}`);
    
    const response = await openai.chat.completions.create({
      model: model,
      messages: messages,
    });

    return response.choices[0].message.content || 
      "Welcome to GMAT practice! I'm your AI assistant ready to help you prepare for the exam. What topic would you like to focus on today?";
  } catch (error) {
    console.error("Error generating welcome message:", error);
    return "Welcome to GMAT practice! I'm your AI assistant ready to help you prepare for the exam. What topic would you like to focus on today?";
  }
}

// Determine which model to use based on prompt category
export function determineModel(promptTitle: string): string {
  // 對於數學題型使用o3-mini，其他類型使用gpt-4o
  if (!promptTitle) {
    console.log("No promptTitle provided, defaulting to gpt-4o");
    return "gpt-4o";
  }
  
  const mathRelatedKeywords = ['quant', 'math', '數學', 'Quant'];
  const graphRelatedKeywords = ['graph', 'chart', '圖表', 'Graph'];
  
  // 檢查是否為數學相關提示
  const isMathRelated = mathRelatedKeywords.some(keyword => 
    promptTitle.toLowerCase().includes(keyword.toLowerCase())
  );
  
  // 檢查是否為圖表相關提示（可能也包含數學內容）
  const isGraphRelated = graphRelatedKeywords.some(keyword => 
    promptTitle.toLowerCase().includes(keyword.toLowerCase())
  );
  
  if (isMathRelated || isGraphRelated) {
    console.log(`Using o3-mini for topic: ${promptTitle}`);
    return "o3-mini";
  } else {
    console.log(`Using gpt-4o for topic: ${promptTitle}`);
    return "gpt-4o";
  }
}

// Chat with the AI using conversation history
export async function chatWithAI(
  systemPrompt: string, 
  conversationHistory: any[],
  promptTitle: string,
  previousResponseId?: string
): Promise<{content: string, id: string}> {
  try {
    const systemMessage = { 
      role: "system", 
      content: systemPrompt 
    } as ChatCompletionSystemMessageParam;
    
    // Determine the appropriate model based on the prompt title
    const model = determineModel(promptTitle);
    console.log(`Using model: ${model} for prompt: ${promptTitle}`);
    
    // 將API轉換為OpenAI預期的格式
    const apiMessages = [
      systemMessage,
      ...conversationHistory.map(msg => {
        // 根據角色類型返回正確的消息格式
        if (msg.role === "user") {
          return { role: "user", content: msg.content } as const;
        } else if (msg.role === "assistant") {
          return { role: "assistant", content: msg.content } as const;
        } else if (msg.role === "system") {
          return { role: "system", content: msg.content } as const;
        } else if (msg.role === "function") {
          return { 
            role: "function", 
            content: msg.content, 
            name: (msg as ChatCompletionFunctionMessageParam).name 
          } as const;
        } else if (msg.role === "tool") {
          return { 
            role: "tool", 
            content: msg.content, 
            tool_call_id: (msg as ChatCompletionToolMessageParam).tool_call_id 
          } as const;
        }
        // 默認情況返回用戶消息
        return { role: "user", content: msg.content } as const;
      })
    ];

    // 注意：OpenAI最新的JS SDK不再使用previous_message_id，而是context參數
    const completionParams: any = {
      model: model,
      messages: apiMessages
    };
    
    // 只有在提供了之前的響應ID時，才添加context參數
    if (previousResponseId) {
      completionParams.context = { previous_messages: [{ id: previousResponseId }] };
    }
    
    const response = await openai.chat.completions.create(completionParams);

    return {
      content: response.choices[0].message.content || 
        "I'm sorry, I couldn't generate a response. Please try again.",
      id: response.id || ""
    };
  } catch (error) {
    console.error("Error chatting with AI:", error);
    return {
      content: "I'm sorry, there was an error processing your request. Please try again.",
      id: ""
    };
  }
}
