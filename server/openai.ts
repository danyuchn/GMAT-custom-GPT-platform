import OpenAI from "openai";

// the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Generate welcome message based on system prompt
export async function generateSystemPrompt(prompt: string, model: string): Promise<string> {
  try {
    const response = await openai.chat.completions.create({
      model: model === "gpt-4o" ? "gpt-4o" : "o3-mini",
      messages: [
        { role: "system", content: prompt },
        { role: "user", content: "Hello, I'd like to start practicing for the GMAT." }
      ],
    });

    return response.choices[0].message.content || 
      "Welcome to GMAT practice! I'm your AI assistant ready to help you prepare for the exam. What topic would you like to focus on today?";
  } catch (error) {
    console.error("Error generating welcome message:", error);
    return "Welcome to GMAT practice! I'm your AI assistant ready to help you prepare for the exam. What topic would you like to focus on today?";
  }
}

// Chat with the AI using conversation history
export async function chatWithAI(
  systemPrompt: string, 
  conversationHistory: Array<{ role: string; content: string }>,
  model: string
): Promise<string> {
  try {
    const response = await openai.chat.completions.create({
      model: model === "gpt-4o" ? "gpt-4o" : "o3-mini",
      messages: [
        { role: "system", content: systemPrompt },
        ...conversationHistory
      ],
    });

    return response.choices[0].message.content || 
      "I'm sorry, I couldn't generate a response. Please try again.";
  } catch (error) {
    console.error("Error chatting with AI:", error);
    return "I'm sorry, there was an error processing your request. Please try again.";
  }
}
