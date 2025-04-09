from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_required, current_user
from datetime import datetime

from models import Chat, Message
from extensions import db
import token_manager # Import token manager functions
from tools_api import process_tool_request # Import the unified tool processor

tools_bp = Blueprint('tools', __name__, url_prefix='/tools', template_folder='../templates')

# Common function to handle tool requests
def handle_tool_request(tool_category, template_name, supported_tools=None):
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        # Get tool_type from form (quant uses 'instruction', verbal/core use 'tool_type')
        tool_type = request.form.get('instruction') or request.form.get('tool_type')
        chat_id = session.get('tool_chat_id') # Use specific session key for tool chats

        if not chat_id:
            flash("沒有活動的工具聊天會話", "warning")
            return redirect(url_for('.' + tool_category + '_tool')) # Redirect to the tool's GET route

        if not user_input:
             flash("請輸入內容", "warning")
             return redirect(url_for('.' + tool_category + '_tool', chat_id=chat_id))

        if not tool_type:
            flash("請選擇一個工具或指令", "warning")
            return redirect(url_for('.' + tool_category + '_tool', chat_id=chat_id))

        # Check balance
        has_balance, balance = token_manager.check_balance(current_user.id)
        if not has_balance:
            flash(f"您的API餘額不足 ({balance:.4f} 元)，請等待下週日重置。", "warning")
        else:
            # Get previous response ID
            previous_response_id = None
            last_ai_message = Message.query.filter_by(
                chat_id=chat_id, 
                role='assistant'
            ).order_by(Message.timestamp.desc()).first()
            if last_ai_message and last_ai_message.response_id:
                previous_response_id = last_ai_message.response_id
            
            # Save user message first
            user_message = Message(
                role='user',
                content=user_input,
                timestamp=datetime.utcnow(),
                chat_id=chat_id
            )
            db.session.add(user_message)
            db.session.commit() # Commit user message before API call

            # Process tool request via tools_api
            # Pass user_id for balance deduction in tools_api
            result = process_tool_request(tool_type, user_input, current_user.id, previous_response_id)
            
            ai_content = ""
            response_id = None
            prompt_tokens = 0
            completion_tokens = 0
            cost = 0.0

            if result['status'] == 'success':
                ai_content = result['content']
                response_id = result.get('response_id')
                prompt_tokens = result.get('tokens', {}).get('input', 0)
                completion_tokens = result.get('tokens', {}).get('output', 0)
                cost = result.get('cost', 0.0)
                # Balance is already deducted in process_tool_request
                if token_manager.get_balance(current_user.id) <= 0:
                     flash("您的API餘額已用完。", "warning")
            else:
                ai_content = f"處理請求時發生錯誤: {result['message']}"
                flash(ai_content, "danger")
            
            # Save AI message (even if error occurred, to show feedback)
            ai_message = Message(
                role='assistant',
                content=ai_content,
                timestamp=datetime.utcnow(),
                chat_id=chat_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                response_id=response_id
            )
            db.session.add(ai_message)
            db.session.commit()
        
        # Redirect to GET to show results and prevent resubmission
        # Pass the selected tool type back to the template via args
        return redirect(url_for('.' + tool_category + '_tool', chat_id=chat_id, tool_type=tool_type))

    # GET Request Handling
    chat_id = request.args.get('chat_id')
    tool_type = request.args.get('tool_type') # Get tool type from args for GET
    messages = []
    
    if chat_id:
        # Verify chat belongs to user and category matches
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id, category=tool_category+"_tool").first()
        if chat:
            session['tool_chat_id'] = chat.id
            messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()
        else:
            flash("無效或不匹配的聊天 ID", "warning")
            session.pop('tool_chat_id', None)
            chat_id = None # Reset chat_id if invalid
    
    if not chat_id: # Create new chat if no valid chat_id
        new_chat = Chat(
            user_id=current_user.id,
            category=tool_category + "_tool"
        )
        db.session.add(new_chat)
        db.session.commit()
        session['tool_chat_id'] = new_chat.id
        messages = [] # Start with empty messages for new chat

    # Get balance and reset time
    current_balance = token_manager.get_balance(current_user.id)
    next_reset = token_manager.get_next_reset_time()
    days_until_reset = (next_reset - datetime.utcnow()).days
    
    # Pass supported_tools and selected_tool (tool_type) to template
    return render_template(template_name, 
                          messages=messages, 
                          api_balance=current_balance,
                          days_until_reset=days_until_reset,
                          supported_tools=supported_tools,
                          selected_tool=tool_type)


@tools_bp.route('/quant_tool', methods=['GET', 'POST'])
@login_required
def quant_tool():
    supported_quant_tools = [
        {"id": "math_classification", "name": "核心概念分類"},
        {"id": "word_problem_converter", "name": "轉換為應用題"}
    ]
    return handle_tool_request('quant', 'quant_tool.html', supported_tools=supported_quant_tools)

@tools_bp.route('/verbal_tool', methods=['GET', 'POST'])
@login_required
def verbal_tool():
    supported_verbal_tools = [
        {"id": "cr_classification", "name": "CR題型分類"},
        {"id": "distractor_mocker", "name": "干擾項生成"}
        # Add other verbal tools here if needed
    ]
    # Get default tool type for GET request
    default_tool = 'cr_classification' if request.method == 'GET' else None
    return handle_tool_request('verbal', 'verbal_tool.html', supported_tools=supported_verbal_tools)

@tools_bp.route('/core_tool', methods=['GET', 'POST'])
@login_required
def core_tool():
    # Define supported core tools if any, or pass None
    supported_core_tools = None 
    return handle_tool_request('core', 'core_tool.html', supported_tools=supported_core_tools) 