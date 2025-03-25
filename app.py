from flask import Flask, render_template, request, redirect, url_for, session
from openai import OpenAI
import os
from dotenv import load_dotenv  # 新增

load_dotenv()  # 新增

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 用於 session 保護

# 讀取 API 金鑰（建議存放在環境變數中）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# 定義價格（每 1M tokens）
INPUT_PRICE = 1.10  # $1.10 per 1M input tokens
CACHED_INPUT_PRICE = 0.55  # $0.55 per 1M cached input tokens
OUTPUT_PRICE = 4.40  # $4.40 per 1M output tokens

# 計算成本函數
def calculate_cost(prompt_tokens, completion_tokens, cached_input_tokens=0):
    non_cached_input_tokens = prompt_tokens - cached_input_tokens
    cached_input_cost = (cached_input_tokens / 1_000_000) * CACHED_INPUT_PRICE
    non_cached_input_cost = (non_cached_input_tokens / 1_000_000) * INPUT_PRICE
    input_cost = cached_input_cost + non_cached_input_cost
    output_cost = (completion_tokens / 1_000_000) * OUTPUT_PRICE
    total_cost = input_cost + output_cost
    return input_cost, output_cost, total_cost

# 初始化對話歷史
def init_conversation(instruction="simple_explain"):
    if instruction == "simple_explain":
        system_prompt = "請用繁體中文解釋解題步驟，並以高中生能理解的方式回答。"
    elif instruction == "quick_solve":
        system_prompt = "請用繁體中文提供一個能在N分鐘內用紙筆和視覺估算解決數學問題的快捷方法。原則是：計算越少、數字越簡單、公式越少且越簡單越好。如果代入數字或使用視覺猜測更簡單，請採用這種方法。"
    elif instruction == "variant_question":
        system_prompt = "請用繁體中文設計一個變體題目，讓我可以練習使用相同的解題方法。"
    
    return [
        {"role": "system", "content": system_prompt}
    ]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/quant")
def quant_chat():
    # 將原來的chat函數重命名為quant_chat
    if request.method == "POST":
        user_input = request.form.get("user_input")
        instruction = request.form.get("instruction", "simple_explain")
        
        # 每次提交時都重新初始化對話歷史
        session["conversation_history"] = init_conversation(instruction)
        session["total_input_tokens"] = 0
        session["total_completion_tokens"] = 0
        session["total_cost"] = 0.0
        
        if user_input:
            conversation_history = session["conversation_history"]
            # 根据选择指令修改用户输入
            if instruction == "solve":
                user_input = f"請解決以下問題：\n{user_input}"
            elif instruction == "summarize":
                user_input = f"請總結以下內容：\n{user_input}"
            elif instruction == "translate":
                user_input = f"請將以下內容翻譯成英文：\n{user_input}"
            # 將使用者訊息加入對話歷史
            conversation_history.append({"role": "user", "content": user_input})
            
            # 呼叫 OpenAI API
            response = client.chat.completions.create(
                model="o3-mini",
                messages=conversation_history,
                stream=False
            )
            model_reply = response.choices[0].message.content

            # 取得 token 使用數據
            if hasattr(response, 'usage'):
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                session["total_input_tokens"] += prompt_tokens
                session["total_completion_tokens"] += completion_tokens
                input_cost, output_cost, turn_cost = calculate_cost(prompt_tokens, completion_tokens)
                session["total_cost"] += turn_cost
            else:
                prompt_tokens = completion_tokens = 0
                input_cost = output_cost = turn_cost = 0

            # 將模型回覆加入對話歷史
            model_reply = model_reply.replace('\n', '<br>')  # 新增：將換行符轉換為HTML標籤
            conversation_history.append({"role": "assistant", "content": model_reply})
            session["conversation_history"] = conversation_history

            # 將結果傳遞給前端顯示
            return render_template(
                "chat.html",
                user_input=user_input,
                model_reply=model_reply,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                turn_cost=turn_cost,
                total_input_tokens=session["total_input_tokens"],
                total_completion_tokens=session["total_completion_tokens"],
                total_cost=session["total_cost"]
            )
        else:
            return redirect(url_for("chat"))
    
    return render_template("chat.html")

# 添加其他分類的路由
@app.route("/verbal")
def verbal_chat():
    # 可以根據需要實現不同的邏輯
    return "Verbal-related 頁面（待實現）"

@app.route("/graph")
def graph_chat():
    # 可以根據需要實現不同的邏輯
    return "Graph-related 頁面（待實現）"

if __name__ == "__main__":
    app.run(debug=True)
