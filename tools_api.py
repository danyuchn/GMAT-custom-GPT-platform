from openai import OpenAI
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def handle_math_classification(user_input):
    """
    處理數學分類工具的 API 請求
    
    Args:
        user_input (str): 用戶輸入的數學題目
        
    Returns:
        dict: API 回應結果
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "GMAT的數學核心觀念有：\nValue, Order, Factors, Algebra, Equalities, Inequalities, Rates, Ratios, Percents, Statistics, Sets, Counting, Probability, Estimation, and Series\n這幾類。\n\n用戶將會給你一或多道數學題目，請分析用戶所提供的每一道題目在設計時，是希望測驗考生的上面哪一個數學核心觀念（請不要給出上面未列出的分類）。\n\nMust do Double check on each question: 每道題目請做兩次獨立的核心觀念判斷，並且檢查你的兩次判斷是否一致。如果不一致，請做第三次最終判斷。\n\n並且最後將每個核心觀念出現的題目數量統計成表格。\n\n"
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1
        )
        
        # 從標準的 chat.completions API 獲取文本內容
        content = response.choices[0].message.content
        
        # 返回 API 回應的內容
        return {
            "status": "success",
            "content": content
        }
    except Exception as e:
        # 處理錯誤情況
        return {
            "status": "error",
            "message": str(e)
        }

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