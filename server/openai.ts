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

const openai = new OpenAI({ 
  apiKey: process.env.OPENAI_API_KEY,
  timeout: 60000, // 60 seconds timeout
  maxRetries: 2 // limit retries to 2 times
  // Note: maxConcurrency不是有效的ClientOptions參數，已移除
});

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
    
    // 創建不同參數配置，取決於使用的模型
    const completionParams: any = {
      model: model,
      messages: messages,
    };

    // o3-mini 模型使用不同的參數
    if (model === "o3-mini") {
      // o3-mini只支持max_completion_tokens和messages參數
      completionParams.max_completion_tokens = 1000;
      // 不添加temperature, max_tokens等參數
    } else {
      // 其他模型使用標準參數
      completionParams.max_tokens = 1000;
      completionParams.temperature = 0.7;
      completionParams.presence_penalty = 0;
      completionParams.frequency_penalty = 0;
    }
    
    console.log(`Generating welcome message with params:`, JSON.stringify({
      model: completionParams.model,
      paramKeys: Object.keys(completionParams)
    }));
    
    const response = await openai.chat.completions.create(completionParams);

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
  
  const promptLower = promptTitle.toLowerCase();
  
  // 確保不會將模型名稱當作提示詞內容
  if (promptLower === "o3-mini" || promptLower === "gpt-4o") {
    console.log(`Detected model name as prompt title, using gpt-4o`);
    return "gpt-4o";
  }
  
  const isMathRelated = mathRelatedKeywords.some(keyword => 
    promptLower.includes(keyword.toLowerCase())
  );
  const isGraphRelated = graphRelatedKeywords.some(keyword => 
    promptLower.includes(keyword.toLowerCase())
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
    // 根據模型類型使用不同的參數設置
    const completionParams: any = {
      model: model,
      messages: apiMessages
    };
    
    // o3-mini 模型使用不同的參數
    if (model === "o3-mini") {
      // o3-mini只支持max_completion_tokens和messages參數
      completionParams.max_completion_tokens = 1000;
      // 不添加temperature, max_tokens等參數
    } else {
      // 其他模型使用標準參數
      completionParams.max_tokens = 1000;
      completionParams.temperature = 0.7;
      completionParams.presence_penalty = 0;
      completionParams.frequency_penalty = 0;
    }
    
    // 只有在提供了之前的響應ID時，才添加context參數
    if (previousResponseId) {
      completionParams.context = { previous_messages: [{ id: previousResponseId }] };
    }
    
    console.log(`Sending request with params:`, JSON.stringify({
      model: completionParams.model,
      paramKeys: Object.keys(completionParams)
    }));
    
    const response = await openai.chat.completions.create(completionParams);

    return {
      content: response.choices[0].message.content || 
        "I'm sorry, I couldn't generate a response. Please try again.",
      id: response.id || ""
    };
  } catch (error) {
    // Log detailed error information
    console.error("Error chatting with AI:", {
      error: error instanceof Error ? error.message : error,
      model: model,
      params: completionParams
    });

    // Check for specific error types
    if (error instanceof OpenAI.APIError) {
      console.error("OpenAI API Error:", {
        status: error.status,
        message: error.message,
        code: error.code,
        type: error.type
      });
      
      // Handle rate limits
      if (error.status === 429) {
        return {
          content: "The service is currently busy. Please try again in a moment.",
          id: ""
        };
      }
    }

    return {
      content: "I apologize, but I encountered an error. Please try your question again.",
      id: ""
    };
  }
}
