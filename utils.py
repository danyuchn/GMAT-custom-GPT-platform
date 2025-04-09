from config import Config

def calculate_cost(prompt_tokens, completion_tokens, cached_input_tokens=0):
    """Calculate cost based on tokens and pricing from config."""
    non_cached_input_tokens = prompt_tokens - cached_input_tokens
    cached_input_cost = (cached_input_tokens / 1_000_000) * Config.CACHED_INPUT_PRICE
    non_cached_input_cost = (non_cached_input_tokens / 1_000_000) * Config.INPUT_PRICE
    input_cost = cached_input_cost + non_cached_input_cost
    output_cost = (completion_tokens / 1_000_000) * Config.OUTPUT_PRICE
    total_cost = input_cost + output_cost
    return input_cost, output_cost, total_cost

def init_conversation(instruction="simple_explain"):
    """Initialize conversation with system prompts."""
    system_prompts = {
        "simple_explain": "請用繁體中文解釋解題步驟，並以高中生能理解的方式回答。",
        "quick_solve": "請用繁體中文提供一個能在2分鐘內用紙筆和視覺估算解決數學問題的快捷方法。原則是：計算越少、數字越簡單、公式越少且越簡單越好。如果代入數字或使用視覺猜測更簡單，請採用這種方法。",
        "variant_question": "請用繁體中文設計一個變體題目，讓我可以練習使用相同的解題方法。",
        "concept_explanation": "如果你是題目出題者，你希望在這個問題中測試哪些特定的數學概念？請用繁體中文回答。",
        "pattern_recognition": "在未來的題目中，應該具備哪些特徵才能應用這種特定的解題方法？請用繁體中文回答。",
        "quick_solve_cr_tpa": "請用繁體中文提供一個能在2分鐘內解決問題的快捷方法。原則如下：\n1. 首先，閱讀問題並識別解鎖問題的關鍵要素。\n2. 接著，告訴我文章中哪些部分是相關信息，哪些不是。\n3. 然後，指出是使用預寫（預先草擬答案）策略還是排除策略來回答問題。\n每個步驟必須包含引導到下一步的明確提示，並遵循線性、單向的人類思維過程。",
        "quick_solve_rc": "請用繁體中文提供一個能在6-8分鐘內快速解決問題的方法。該方法應遵循以下步驟：\n1. 首先，識別文章中需要注意的關鍵信息（注意：即使不清楚問題可能測試什麼，也應該這樣做）。\n2. 接著，為每個問題指定關鍵詞和要點。\n3. 然後，根據這些關鍵詞和要點，指出文章中哪些相關段落是相關的。\n4. 之後，建議是使用預寫策略還是排除策略來回答問題。\n5. 如果選擇預寫，請詳細說明逐步推理過程。\n每個步驟必須提供引導到下一步的明確線索，並且必須遵循線性、單向的思維過程。此外，請為每個選項的判斷提供詳細解釋。",
        "mind_map": "請用繁體中文創建文章本身的思維導圖。",
        "approach_diagnosis": "這是我對問題解決過程的語言解釋。請用繁體中文識別我的方法中的任何錯誤，並提出改進建議。",
        "logical_term_explanation": "請用繁體中文解釋文章中提供的五個答案選項中每個邏輯術語的含義。"
    }
    
    system_prompt = system_prompts.get(instruction, system_prompts["simple_explain"])
    return [{"role": "system", "content": system_prompt}] 