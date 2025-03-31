import OpenAI from "openai";

// Define ChatCompletionMessageParam type locally to avoid import errors
type ChatCompletionMessageParam = {
  role: "system" | "user" | "assistant" | "function" | "tool";
  content: string;
  name?: string;
};

// Define ChatCompletionUserMessageParam for OpenAI API
type ChatCompletionUserMessageParam = {
  role: "user";
  content: string;
};

// Define ChatCompletionSystemMessageParam for OpenAI API
type ChatCompletionSystemMessageParam = {
  role: "system";
  content: string;
};

// Define ChatCompletionAssistantMessageParam for OpenAI API
type ChatCompletionAssistantMessageParam = {
  role: "assistant";
  content: string;
};

// the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Generate welcome message based on system prompt
export async function generateSystemPrompt(prompt: string, promptTitle: string): Promise<string> {
  try {
    const messages = [
      { role: "system", content: prompt } as ChatCompletionSystemMessageParam,
      { role: "user", content: "Hello, I'd like to start practicing for the GMAT." } as ChatCompletionUserMessageParam
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
  // 如果是數學相關題型，使用o3-mini
  const mathRelatedKeywords = ['quant', 'problem solving', 'data sufficiency', 'math', '數學'];
  const isMathRelated = mathRelatedKeywords.some(keyword => 
    promptTitle.toLowerCase().includes(keyword.toLowerCase())
  );
  
  return isMathRelated ? "o3-mini" : "gpt-4o";
}

// Chat with the AI using conversation history
export async function chatWithAI(
  systemPrompt: string, 
  conversationHistory: ChatCompletionMessageParam[],
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
    
    const response = await openai.chat.completions.create({
      model: model,
      messages: [
        systemMessage,
        ...conversationHistory
      ],
      previous_message_id: previousResponseId
    });

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
