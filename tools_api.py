import os
from datetime import datetime # Needed if update_user_quota is kept

# Import client from extensions and config for prices
from extensions import client, db # Import db if update_user_quota is kept
from config import Config
import token_manager # Use token_manager for balance deductions
# from models import UserQuota # Import UserQuota if update_user_quota is kept

# Use prices from Config
def calculate_cost(input_tokens, cached_tokens, output_tokens, model="gpt-4o"):
    """
    Calculate API request cost based on tokens and model pricing from config.
    Args:
        input_tokens (int): Input token count.
        cached_tokens (int): Cached input token count.
        output_tokens (int): Output token count.
        model (str): Model name (currently only gpt-4o supported).
    Returns:
        float: Calculated cost in USD.
    """
    if model == "gpt-4o":
        non_cached_input = input_tokens - cached_tokens
        input_cost = non_cached_input * Config.GPT4O_INPUT_PRICE_PER_TOKEN
        cached_cost = cached_tokens * Config.GPT4O_CACHED_INPUT_PRICE_PER_TOKEN
        output_cost = output_tokens * Config.GPT4O_OUTPUT_PRICE_PER_TOKEN
        return input_cost + cached_cost + output_cost
    else:
        # Extend for other models if needed
        return 0.0

# Function to handle common API call logic
def _make_api_call(request_data, user_id):
    """Internal function to make OpenAI API call, calculate cost, and deduct balance."""
    try:
        response = client.chat.completions.create(**request_data) # Adjusted call
        
        # Extract content and response ID (handle potential variations in response structure)
        content = "Error: Could not parse response content."
        if response.choices and response.choices[0].message and response.choices[0].message.content:
             content = response.choices[0].message.content
        # Handle LaTeX formatting if necessary (moved inside call)
        content = content.replace('\\\\(', '\\(').replace('\\\\)', '\\)')
        content = content.replace('\\\\[', '\\[').replace('\\\\]', '\\]')
             
        response_id = getattr(response, 'id', None)
        
        # Get token usage and calculate cost
        input_tokens = cached_tokens = output_tokens = 0
        cost = 0.0
        if hasattr(response, 'usage'):
            input_tokens = response.usage.prompt_tokens
            # Safely access cached tokens
            cached_tokens = response.usage.prompt_tokens_details.cached_tokens if hasattr(response.usage, 'prompt_tokens_details') and response.usage.prompt_tokens_details else 0
            output_tokens = response.usage.completion_tokens
            cost = calculate_cost(input_tokens, cached_tokens, output_tokens)
            
            # Deduct balance using token_manager
            token_manager.deduct_balance(user_id, cost)
            # update_user_quota(user_id, input_tokens + output_tokens, cost) # Alternative/Additional tracking
        
        return {
            "status": "success",
            "content": content,
            "tokens": {
                "input": input_tokens,
                "cached": cached_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens # Total is sum of input & output
            },
            "cost": cost,
            "response_id": response_id
        }
    except Exception as e:
        # Log error properly
        print(f"API call failed: {str(e)}") # Replace with logger
        return {
            "status": "error",
            "message": str(e)
        }

def handle_math_classification(user_input, user_id, previous_response_id=None):
    """Handle math classification tool API request."""
    request_data = {
        "model": "o3-mini", # Use o3-mini as in the original app
        "messages": [
            {
                "role": "system",
                "content": "GMAT的數學核心觀念有：\nValue, Order, Factors, Algebra, Equalities, Inequalities, Rates, Ratios, Percents, Statistics, Sets, Counting, Probability, Estimation, and Series\n這幾類。\n\n用戶將會給你一或多道數學題目，請分析用戶所提供的每一道題目在設計時，是希望測驗考生的上面哪一個數學核心觀念（請不要給出上面未列出的分類）。\n\nMust do Double check on each question: 每道題目請做兩次獨立的核心觀念判斷，並且檢查你的兩次判斷是否一致。如果不一致，請做第三次最終判斷。\n\n並且最後將每個核心觀念出現的題目數量統計成表格。"
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2048, # Renamed from max_output_tokens for chat completions
        "top_p": 1,
        # "store": True # Not a standard chat completion parameter
    }
    if previous_response_id:
        request_data["response_id"] = previous_response_id # This might not be standard
        
    return _make_api_call(request_data, user_id)

def handle_word_problem_converter(user_input, user_id, previous_response_id=None):
    """Handle word problem converter tool API request."""
    request_data = {
        "model": "o3-mini",
        "messages": [
             {
                "role": "system",
                "content": "Role: You are an expert in transforming GMAT quantitative questions into engaging, real-world scenarios.\n\nTask: Follow these steps to assist the user:\n1. The user will provide a GMAT math multiple-choice question in the form of text or an image.\n2. Convert the question into a word problem with a real-world scenario and story (30-50 words), written in English. Do not change any numerical values in the question.\n3. If the question provided is already a word problem (has a real-world scenario and story), simply translate it to English without altering anything else."
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        "temperature": 1.0,
        "max_tokens": 2048,
        "top_p": 1,
    }
    if previous_response_id:
        request_data["response_id"] = previous_response_id
        
    return _make_api_call(request_data, user_id)

def handle_cr_classification(user_input, user_id, previous_response_id=None):
    """Handle CR classification tool API request."""
    request_data = {
        "model": "o3-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert GMAT Critical Reasoning (CR) tutor.\nYour task is to classify the type of GMAT CR question provided by the user.\n\nThe possible CR question types are:\n1.  **Assumption:** Identify an unstated premise the argument relies on.\n2.  **Strengthen:** Find a statement that makes the argument's conclusion more likely.\n3.  **Weaken:** Find a statement that makes the argument's conclusion less likely.\n4.  **Evaluate:** Identify a question whose answer would help determine the argument's validity.\n5.  **Inference:** Determine what must be true based on the given statements.\n6.  **Explain/Resolve Discrepancy:** Find a statement that reconciles seemingly contradictory information.\n7.  **Flaw:** Identify the logical error in the argument's reasoning.\n8.  **Boldface:** Analyze the role played by the bolded portions of the argument.\n9.  **Method of Reasoning:** Describe how the argument proceeds logically.\n10. **Main Point/Conclusion:** Identify the primary claim the argument tries to establish.\n\nPlease respond ONLY with the name of the question type from the list above."
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        "temperature": 0.2,
        "max_tokens": 50, # Shorter response needed
        "top_p": 1,
    }
    if previous_response_id:
         request_data["response_id"] = previous_response_id
         
    return _make_api_call(request_data, user_id)

def handle_distractor_mocker(user_input, user_id, previous_response_id=None):
    """Handle distractor mocker tool API request."""
    request_data = {
        "model": "o3-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a GMAT test creation expert specializing in crafting plausible incorrect answer choices (distractors) for Verbal questions (CR, RC, SC).\n\nTask: The user will provide a GMAT Verbal question (including the passage/stimulus if applicable) AND its correct answer.\n1. Analyze the question, passage (if any), and the correct answer.\n2. Identify common reasoning errors or traps relevant to the question type.\n3. Create ONE realistic and tempting incorrect answer choice (distractor) based on these potential errors.\n4. Provide a brief (1-2 sentence) explanation of WHY this distractor is incorrect and what specific trap it targets."
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        "temperature": 0.8, # Allow for more creative distractors
        "max_tokens": 500,
        "top_p": 1,
    }
    if previous_response_id:
        request_data["response_id"] = previous_response_id
        
    return _make_api_call(request_data, user_id)

# This function duplicates token_manager logic. 
# It might be useful for separate tracking but complicates balance management.
# Consider removing it or integrating it carefully with token_manager.
# def update_user_quota(user_id, tokens_used, cost_incurred):
#     """Update the UserQuota record for a user."""
#     if not user_id:
#         return # Cannot update without user ID
        
#     quota = UserQuota.query.filter_by(user_id=user_id).first()
#     now = datetime.utcnow()
    
#     if not quota:
#         quota = UserQuota(user_id=user_id, total_tokens=tokens_used, total_cost=cost_incurred, last_updated=now)
#         db.session.add(quota)
#     else:
#         quota.total_tokens += tokens_used
#         quota.total_cost += cost_incurred
#         quota.last_updated = now
        
#     try:
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         # Log error
#         print(f"Error updating UserQuota for {user_id}: {str(e)}")

# Simplified handlers just calling process_tool_request
# def handle_verbal_tool(tool_type, user_input):
#     return process_tool_request(tool_type, user_input)

# def handle_core_tool(tool_type, user_input):
#     return process_tool_request(tool_type, user_input)

# Unified function to process any tool request
def process_tool_request(tool_type, user_input, user_id, previous_response_id=None):
    """
    Processes a request for a specific tool.
    Args:
        tool_type (str): The identifier for the tool (e.g., 'math_classification').
        user_input (str): The input text from the user.
        user_id (int): The ID of the user making the request (for balance deduction).
        previous_response_id (str, optional): ID of the previous response for caching.
    Returns:
        dict: A dictionary containing the status and result of the API call.
    """
    handlers = {
        "math_classification": handle_math_classification,
        "word_problem_converter": handle_word_problem_converter,
        "cr_classification": handle_cr_classification,
        "distractor_mocker": handle_distractor_mocker,
        # Add other tool handlers here
    }
    
    handler = handlers.get(tool_type)
    
    if handler:
        # Pass user_id to the specific handler
        return handler(user_input, user_id, previous_response_id)
    else:
        return {
            "status": "error",
            "message": f"未知的工具類型: {tool_type}"
        }