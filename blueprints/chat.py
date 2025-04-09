from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_required, current_user
from datetime import datetime

from models import Chat, Message
from extensions import db, client
from utils import calculate_cost, init_conversation
import token_manager # Import token manager functions

chat_bp = Blueprint('chat', __name__, template_folder='../templates')

@chat_bp.route("/")
def index():
    """Main index page."""
    return render_template("index.html")

def handle_chat(category, template_name):
    """Generic chat handling function."""
    active_chat_id = session.get('active_chat_id')
    
    if not active_chat_id:
        # Create a new chat if no active chat exists
        new_chat = Chat(user_id=current_user.id, category=category)
        db.session.add(new_chat)
        db.session.commit()
        session['active_chat_id'] = new_chat.id
        active_chat_id = new_chat.id # Update active_chat_id for the current request
        session['current_instruction'] = 'simple_explain' # Set default instruction for new chat
    
    # Get current balance for display
    current_balance = token_manager.get_balance(current_user.id)
    # Get instruction from session, default to simple_explain
    current_session_instruction = session.get('current_instruction', 'simple_explain')
    
    if request.method == "POST":
        user_input = request.form.get('user_input', '').strip()
        # Get the instruction submitted with this request
        submitted_instruction = request.form.get('instruction', 'simple_explain')
        
        # Remove the block handling empty POST requests for mode switch
        # if not user_input and instruction != current_instruction: ... (REMOVED)
                
        # Handle user input
        if user_input:
            # Set instruction_to_use based on the current submission first.
            instruction_to_use = submitted_instruction 
            notification_message = None # Initialize notification message

            # Check if instruction changed compared to the session
            if submitted_instruction != current_session_instruction:
                # Instruction has changed, update session and prepare notification
                session['current_instruction'] = submitted_instruction
                current_session_instruction = submitted_instruction # Update local var for this request
                # instruction_to_use is already set correctly above
                
                # Prepare system message notification for mode change
                notification_message = Message(
                    chat_id=active_chat_id,
                    role="system",
                    content=f'<i class="fas fa-info-circle me-2"></i>已切換到 {instruction_to_use} 模式' 
                )
                # Add to session, commit later with user message
                db.session.add(notification_message) 

            # Check balance before proceeding
            has_balance, balance = token_manager.check_balance(current_user.id)
            if not has_balance:
                flash(f"您的API餘額不足 ({balance:.4f} 元)，請等待下週日重置。", "warning")
            else:
                # Save user message (and notification if it exists)
                user_message = Message(
                    chat_id=active_chat_id,
                    role="user",
                    content=user_input
                )
                db.session.add(user_message)
                
                try:
                    db.session.commit() # Commit user message and potential notification together
                except Exception as e:
                    db.session.rollback()
                    flash(f"保存消息時出錯: {str(e)}", "danger")
                    # Re-fetch messages and render template with error
                    messages = Message.query.filter_by(chat_id=active_chat_id).order_by(Message.timestamp).all()
                    next_reset = token_manager.get_next_reset_time()
                    days_until_reset = (next_reset - datetime.utcnow()).days
                    return render_template(template_name, messages=messages, api_balance=balance, days_until_reset=days_until_reset, default_instruction=current_session_instruction)
                
                # --- API Call Section --- 
                try:
                    # Prepare messages for OpenAI API using instruction_to_use
                    current_system_prompt = init_conversation(instruction_to_use)[0] 
                    messages_for_api = [current_system_prompt]
                    
                    # Fetch history (excluding system messages)
                    history = Message.query.filter(
                        Message.chat_id == active_chat_id, 
                        Message.role != 'system'
                    ).order_by(Message.timestamp).all()
                    
                    # Make sure user_message (committed above) is included in history for API
                    messages_for_api.extend([{"role": msg.role, "content": msg.content} for msg in history])

                    # Get previous response ID
                    previous_response_id = None
                    # Fetch the latest assistant message BEFORE the current user message was added
                    # Note: This logic might need adjustment if commits happen differently
                    last_ai_message = Message.query.filter(
                        Message.chat_id == active_chat_id, 
                        Message.role == 'assistant'
                    ).order_by(Message.timestamp.desc()).first()
                    if last_ai_message and last_ai_message.response_id:
                        previous_response_id = last_ai_message.response_id

                    # Call OpenAI API
                    request_params = {
                        "model": "o3-mini",
                        "messages": messages_for_api,
                        "stream": False
                    }
                    # Remove previous_response_id if it causes issues
                    # if previous_response_id:
                    #    request_params["response_id"] = previous_response_id
                    
                    response = client.chat.completions.create(**request_params)
                    model_reply = response.choices[0].message.content
                    response_id = getattr(response, 'id', None)

                    # --- Start Debug Prints ---
                    print(f"DEBUG: API call successful. Response ID: {response_id}")
                    print(f"DEBUG: AI Reply content (first 100 chars): {model_reply[:100] if model_reply else 'None'}")
                    # --- End Debug Prints ---
                    
                    # Calculate cost and deduct balance
                    prompt_tokens = completion_tokens = 0
                    turn_cost = 0.0
                    if hasattr(response, 'usage'):
                        prompt_tokens = response.usage.prompt_tokens
                        completion_tokens = response.usage.completion_tokens
                        cached_tokens = 0
                        if hasattr(response.usage, 'prompt_tokens_details') and response.usage.prompt_tokens_details and hasattr(response.usage.prompt_tokens_details, 'cached_tokens'):
                            cached_tokens = response.usage.prompt_tokens_details.cached_tokens
                        _, _, turn_cost = calculate_cost(prompt_tokens, completion_tokens, cached_tokens)
                        new_balance = token_manager.deduct_balance(current_user.id, turn_cost)
                        current_balance = new_balance # Update balance for display
                        if new_balance <= 0:
                            flash("您的API餘額已用完。", "warning")
                    
                    # Save AI message
                    ai_message = Message(
                        chat_id=active_chat_id,
                        role="assistant",
                        content=model_reply,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost=turn_cost,
                        response_id=response_id
                    )
                    db.session.add(ai_message)
                    # --- Start Debug Prints ---
                    print(f"DEBUG: AI Message object created and added to session.")
                    # --- End Debug Prints ---
                    db.session.commit() # Commit the AI message
                    # --- Start Debug Prints ---
                    print(f"DEBUG: AI Message committed successfully. ID: {ai_message.id}") 
                    # --- End Debug Prints ---
                
                except Exception as e:
                    flash(f"與 AI 服務溝通或處理回應時發生錯誤: {str(e)}", "danger")
                    # --- Start Debug Prints ---
                    print(f"ERROR in API/Commit block: {str(e)}") 
                    # --- End Debug Prints ---
                    db.session.rollback() # Rollback potential AI message commit

    # Fetch messages for rendering
    messages = []
    if active_chat_id:
        messages = Message.query.filter_by(chat_id=active_chat_id).order_by(Message.timestamp).all()
    
    # Get reset time for display
    next_reset = token_manager.get_next_reset_time()
    days_until_reset = (next_reset - datetime.utcnow()).days
    
    return render_template(template_name, 
                          messages=messages, 
                          api_balance=current_balance,
                          days_until_reset=days_until_reset,
                          # Pass current instruction from session for default selection
                          default_instruction=current_session_instruction)

@chat_bp.route("/new_chat/<category>")
@login_required
def new_chat(category):
    """Start a new chat session."""
    valid_categories = ['quant', 'verbal', 'graph'] # Define valid categories
    if category not in valid_categories:
        flash("無效的聊天類型", "danger")
        return redirect(url_for('chat.index'))
        
    # Create new chat record
    new_chat_obj = Chat(user_id=current_user.id, category=category)
    db.session.add(new_chat_obj)
    db.session.commit()
    session['active_chat_id'] = new_chat_obj.id
    session.pop('pending_system_message', None) # Clear pending message for new chat
    session.pop('current_instruction', None) # Clear current instruction
    
    # Redirect to the specific chat view
    return redirect(url_for(f'chat.{category}_chat')) # Adjusted redirect

@chat_bp.route("/history")
@login_required
def history():
    """Display user's chat history."""
    # Fetch chats that have at least one user message
    user_chats = Chat.query.filter(
        Chat.user_id == current_user.id,
        Chat.messages.any(Message.role == 'user') # Efficiently check for user messages
    ).order_by(Chat.timestamp.desc()).all()
    
    return render_template("history.html", chats=user_chats)

@chat_bp.route("/load_chat/<int:chat_id>")
@login_required
def load_chat(chat_id):
    """Load a specific chat session."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    session['active_chat_id'] = chat.id
    session.pop('pending_system_message', None) # Clear pending message when loading
    session.pop('current_instruction', None) # Clear current instruction

    # Determine the redirect target based on chat category
    if chat.category == 'quant':
        return redirect(url_for('chat.quant_chat'))
    elif chat.category == 'verbal':
        return redirect(url_for('chat.verbal_chat'))
    elif chat.category == 'graph':
        return redirect(url_for('chat.graph_chat'))
    elif chat.category == 'quant_tool': # Handle tool chats if needed
        return redirect(url_for('tools.quant_tool', chat_id=chat_id))
    elif chat.category == 'verbal_tool':
         return redirect(url_for('tools.verbal_tool', chat_id=chat_id))
    elif chat.category == 'core_tool':
         return redirect(url_for('tools.core_tool', chat_id=chat_id))
    else:
        flash("無法識別的聊天類型", "warning")
        return redirect(url_for('chat.index'))

# Specific chat routes calling handle_chat
@chat_bp.route("/quant", methods=["GET", "POST"])
@login_required
def quant_chat():
    return handle_chat("quant", "quant_chat.html")

@chat_bp.route("/verbal", methods=["GET", "POST"])
@login_required
def verbal_chat():
    return handle_chat("verbal", "verbal_chat.html")

@chat_bp.route("/graph", methods=["GET", "POST"])
@login_required
def graph_chat():
    return handle_chat("graph", "graph_chat.html") 