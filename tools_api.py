from openai import OpenAI
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 初始化 OpenAI 客戶端
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY未正確配置，請檢查.env文件")

client = OpenAI(api_key=OPENAI_API_KEY)

# 定義 GPT-4o 模型的價格（每百萬 token）
GPT4O_PRICES = {
    "input": 2.50 / 1000000,  # $2.50 / 1M tokens
    "cached_input": 1.25 / 1000000,  # $1.25 / 1M tokens
    "output": 10.00 / 1000000  # $10.00 / 1M tokens
}

def calculate_cost(input_tokens, cached_tokens, output_tokens, model="gpt-4o"):
    """
    計算 API 請求的成本
    
    Args:
        input_tokens (int): 輸入 token 數量
        cached_tokens (int): 緩存的輸入 token 數量
        output_tokens (int): 輸出 token 數量
        model (str): 使用的模型名稱
        
    Returns:
        float: 請求成本（美元）
    """
    if model == "gpt-4o":
        # 計算非緩存輸入 token 的數量
        non_cached_input = input_tokens - cached_tokens
        
        # 計算成本
        input_cost = non_cached_input * GPT4O_PRICES["input"]
        cached_cost = cached_tokens * GPT4O_PRICES["cached_input"]
        output_cost = output_tokens * GPT4O_PRICES["output"]
        
        return input_cost + cached_cost + output_cost
    else:
        # 如果添加其他模型，可以在這裡擴展
        return 0.0

def handle_math_classification(user_input):
    """
    處理數學分類工具的 API 請求
    
    Args:
        user_input (str): 用戶輸入的數學題目
        
    Returns:
        dict: API 回應結果
    """
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "GMAT的數學核心觀念有：\nValue, Order, Factors, Algebra, Equalities, Inequalities, Rates, Ratios, Percents, Statistics, Sets, Counting, Probability, Estimation, and Series\n這幾類。\n\n用戶將會給你一或多道數學題目，請分析用戶所提供的每一道題目在設計時，是希望測驗考生的上面哪一個數學核心觀念（請不要給出上面未列出的分類）。\n\nMust do Double check on each question: 每道題目請做兩次獨立的核心觀念判斷，並且檢查你的兩次判斷是否一致。如果不一致，請做第三次最終判斷。\n\n並且最後將每個核心觀念出現的題目數量統計成表格。\n\n"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_input
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            temperature=0.2,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # 正確提取文本內容
        content = response.output[0].content[0].text
        
        # 處理 LaTeX 格式，確保正確渲染
        # 不需要替換 \( 和 \)，因為 MathJax 已經支持這種格式
        # 只需要處理可能的轉義問題
        content = content.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
        content = content.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
        
        # 獲取 token 使用情況
        input_tokens = response.usage.input_tokens
        cached_tokens = response.usage.input_tokens_details.cached_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = response.usage.total_tokens
        
        # 計算成本
        cost = calculate_cost(input_tokens, cached_tokens, output_tokens)
        
        # 更新用戶的 API 配額（需要實現這個函數）
        update_user_quota(input_tokens, output_tokens, cost)
        
        # 返回 API 回應的內容，包括 token 使用情況和成本
        return {
            "status": "success",
            "content": content,
            "tokens": {
                "input": input_tokens,
                "cached": cached_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            "cost": cost
        }
    except Exception as e:
        # 處理錯誤情況
        return {
            "status": "error",
            "message": str(e)
        }

def handle_word_problem_converter(user_input):
    """
    處理應用題轉換工具的 API 請求
    
    Args:
        user_input (str): 用戶輸入的數學題目
        
    Returns:
        dict: API 回應結果
    """
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Role: You are an expert in transforming GMAT quantitative questions into engaging, real-world scenarios.\n\nTask: Follow these steps to assist the user:\n1. The user will provide a GMAT math multiple-choice question in the form of text or an image.\n2. Convert the question into a word problem with a real-world scenario and story (30-50 words), written in English. Do not change any numerical values in the question.\n3. If the question provided is already a word problem (has a real-world scenario and story), simply translate it to English without altering anything else."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_input
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            temperature=1.0,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # 正確提取文本內容
        content = response.output[0].content[0].text
        
        # 處理 LaTeX 格式，確保正確渲染
        # 不需要替換 \( 和 \)，因為 MathJax 已經支持這種格式
        # 只需要處理可能的轉義問題
        content = content.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
        content = content.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
        
        # 獲取 token 使用情況
        input_tokens = response.usage.input_tokens
        cached_tokens = response.usage.input_tokens_details.cached_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = response.usage.total_tokens
        
        # 計算成本
        cost = calculate_cost(input_tokens, cached_tokens, output_tokens)
        
        # 更新用戶的 API 配額（需要實現這個函數）
        update_user_quota(input_tokens, output_tokens, cost)
        
        # 返回 API 回應的內容，包括 token 使用情況和成本
        return {
            "status": "success",
            "content": content,
            "tokens": {
                "input": input_tokens,
                "cached": cached_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            "cost": cost
        }
    except Exception as e:
        # 處理錯誤情況
        return {
            "status": "error",
            "message": str(e)
        }

def handle_cr_classification(user_input):
    """
    處理 CR 分類工具的 API 請求
    
    Args:
        user_input (str): 用戶輸入的 CR 題目
        
    Returns:
        dict: API 回應結果
    """
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": """Role: You are an expert in GMAT Critical Reasoning problem-solving and question design.

Task: The user will provide you with CR questions, and you must identify which of the following four sub-types these questions belong to (see Sub-Type Definitions).

For each question, make two independent judgments on the sub-type and check if they are consistent. If inconsistent, make a third final judgment.
Create a table for the user that organizes the number of occurrences for each sub-type.

Sub-type Definitions:

The four subtypes of Critical Reasoning questions are Analysis, Construction, Critique, and Plan.

Analysis:
- Questions about logical structure and roles of statements
- Common phrases: "roles in boldface", "argument proceeds by", "technique used", "responds to"
- Focus on logical/rhetorical roles, argumentative methods, unstated points

Construction:
- Questions about completing partial arguments/explanations
- Common phrases: "logically completes", "most strongly support", "best explains", "depends on assumption"
- Focus on conclusions, missing premises, explanations for observations

Critique:
- Questions about judging reasoning, finding strengths/weaknesses
- Common phrases: "vulnerable to criticism", "logically flawed", "weakens", "strengthens", "useful to evaluate"
- Focus on logical flaws, evidence assessment, hypothesis evaluation

Plan:
- Questions about reasoning for proposed actions
- Focus on plans, strategies, actions
- Common themes: plan success conditions, strategy evaluation, policy assessment"""
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_input
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            temperature=0.2,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # 正確提取文本內容
        content = response.output[0].content[0].text
        
        # 處理 LaTeX 格式，確保正確渲染
        content = content.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
        content = content.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
        
        # 獲取 token 使用情況
        input_tokens = response.usage.input_tokens
        cached_tokens = response.usage.input_tokens_details.cached_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = response.usage.total_tokens
        
        # 計算成本
        cost = calculate_cost(input_tokens, cached_tokens, output_tokens)
        
        # 更新用戶的 API 配額
        update_user_quota(input_tokens, output_tokens, cost)
        
        return {
            "status": "success",
            "content": content,
            "tokens": {
                "input": input_tokens,
                "cached": cached_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            "cost": cost
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def handle_distractor_mocker(user_input):
    """
    處理混淆選項檢討工具的 API 請求
    
    Args:
        user_input (str): 用戶輸入的題目和兩個選項
        
    Returns:
        dict: API 回應結果
    """
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Role: You are a GMAT expert for study abroad exams, specializing in helping users understand GMAT questions.\n\nTask: Communicate with the user in Traditional Chinese, using a tone and style as if speaking to a 10-year-old, ensuring simplicity and clarity. Follow these steps:\n\nThe user will provide a GMAT question along with exactly two options (one correct and one incorrect).\nExplain in detail:\nWhy the correct option meets the question's requirements.\nWhy the incorrect option does not meet the question's requirements.\nProvide two distinct analogy scenarios (new stories) for both the correct option and the incorrect option, helping the user understand why the correct option is correct and the incorrect option is incorrect.\n\nThen, based on the English question and two options provided by the user, change the story's domain and content while preserving the logic of the passage and options.\n\nCreate a variant question and two options in English, with the grammatical structure as similar as possible to the original question."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_input
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            temperature=1.0,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # 正確提取文本內容
        content = response.output[0].content[0].text
        
        # 處理 LaTeX 格式，確保正確渲染
        content = content.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
        content = content.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
        
        # 獲取 token 使用情況
        input_tokens = response.usage.input_tokens
        cached_tokens = response.usage.input_tokens_details.cached_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = response.usage.total_tokens
        
        # 計算成本
        cost = calculate_cost(input_tokens, cached_tokens, output_tokens)
        
        # 更新用戶的 API 配額
        update_user_quota(input_tokens, output_tokens, cost)
        
        return {
            "status": "success",
            "content": content,
            "tokens": {
                "input": input_tokens,
                "cached": cached_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            "cost": cost
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# 更新用戶 API 配額的函數
def update_user_quota(input_tokens, output_tokens, cost, user_id=None):
    """
    更新用戶的 API 使用配額
    
    Args:
        input_tokens (int): 輸入 token 數量
        output_tokens (int): 輸出 token 數量
        cost (float): API 請求成本
        user_id (int, optional): 用戶 ID，如果為 None，則使用當前登錄用戶
        
    Returns:
        bool: 更新是否成功
    """
    try:
        from flask import current_app, session
        from flask_login import current_user
        from datetime import datetime
        
        # 獲取數據庫連接
        db = current_app.extensions['sqlalchemy'].db
        
        # 如果沒有指定用戶 ID，則使用當前登錄用戶的 ID
        if user_id is None and current_user.is_authenticated:
            user_id = current_user.id
        elif user_id is None and 'user_id' in session:
            user_id = session['user_id']
        else:
            # 如果無法確定用戶，則返回失敗
            return False
        
        # 獲取用戶的 API 配額記錄
        quota = db.session.execute(db.select("UserQuota").filter_by(user_id=user_id)).scalar_one_or_none()
        
        if quota:
            # 更新現有配額
            quota.total_tokens += input_tokens + output_tokens
            quota.total_cost += cost
            quota.last_updated = datetime.now()
        else:
            # 創建新的配額記錄
            from models import UserQuota
            quota = UserQuota(
                user_id=user_id,
                total_tokens=input_tokens + output_tokens,
                total_cost=cost,
                last_updated=datetime.now()
            )
            db.session.add(quota)
        
        # 提交更改
        db.session.commit()
        return True
    except Exception as e:
        # 記錄錯誤但不中斷用戶體驗
        print(f"更新用戶配額時出錯: {str(e)}")
        return False

# 其他工具函數可以在這裡添加
def handle_verbal_tool(tool_type, user_input):
    """語文工具處理函數"""
    pass

def handle_core_tool(tool_type, user_input):
    """核心能力工具處理函數"""
    pass

# 工具路由映射
TOOL_HANDLERS = {
    "math_classification": handle_math_classification,
    "word_problem_converter": handle_word_problem_converter,
    "cr_classification": handle_cr_classification,
    "distractor_mocker": handle_distractor_mocker,
    # 可以添加更多工具的處理函數
}

def process_tool_request(tool_type, user_input):
    """
    處理工具請求的主函數
    
    Args:
        tool_type (str): 工具類型
        user_input (str): 用戶輸入
        
    Returns:
        dict: 處理結果
    """
    if tool_type in TOOL_HANDLERS:
        return TOOL_HANDLERS[tool_type](user_input)
    else:
        return {
            "status": "error",
            "message": f"未知的工具類型: {tool_type}"
        }