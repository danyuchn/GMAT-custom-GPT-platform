from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user

from models import User, Chat, Message
from extensions import db, client

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates')

# Decorator to check for admin privileges
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.username != 'admin':
            flash("您沒有權限訪問此頁面", "danger")
            return redirect(url_for('chat.index')) # Redirect to main index
        return f(*args, **kwargs)
    # Preserve original function name for Flask
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route("/chats")
@admin_required
def admin_chats():
    """Display chats for selected user or list all users."""
    users = User.query.order_by(User.username).all()
    user_id_str = request.args.get('user_id')
    selected_user_id = None
    chats = []
    
    if user_id_str:
        try:
            selected_user_id = int(user_id_str)
            # Fetch chats with at least one user message for the selected user
            chats = Chat.query.filter(
                Chat.user_id == selected_user_id,
                Chat.messages.any(Message.role == 'user') # Efficient check
            ).order_by(Chat.timestamp.desc()).all()
        except ValueError:
            flash("無效的用戶 ID", "warning")
    
    return render_template("admin_chats.html", users=users, chats=chats, selected_user_id=selected_user_id)

@admin_bp.route("/delete_chats", methods=["POST"])
@admin_required
def delete_chats():
    """Delete selected chat records for a user."""
    chat_ids = request.form.getlist('chat_ids')
    user_id = request.form.get('user_id') # Keep user_id to redirect back
    
    if not chat_ids:
        flash("未選擇任何聊天記錄", "warning")
    else:
        try:
            # Efficiently delete messages and chats using IN clause
            Message.query.filter(Message.chat_id.in_(chat_ids)).delete(synchronize_session=False)
            Chat.query.filter(Chat.id.in_(chat_ids)).delete(synchronize_session=False)
            
            db.session.commit()
            flash(f"成功刪除 {len(chat_ids)} 條聊天記錄", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"刪除聊天記錄時發生錯誤: {str(e)}", "danger")
            current_app.logger.error(f"Error deleting chats: {str(e)}")
    
    # Redirect back to the user's chat list
    redirect_url = url_for('.admin_chats')
    if user_id:
        redirect_url = url_for('.admin_chats', user_id=user_id)
    return redirect(redirect_url)

@admin_bp.route("/chat/<int:chat_id>")
@admin_required
def admin_chat_detail(chat_id):
    """Display details of a specific chat."""
    chat = Chat.query.get_or_404(chat_id)
    # Ensure admin can view any user's chat detail
    user = User.query.get_or_404(chat.user_id)
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    
    return render_template("admin_chat_detail.html", chat=chat, user=user, messages=messages)

@admin_bp.route("/analyze_user/<int:user_id>", methods=["GET"])
@admin_required
def analyze_user_questions(user_id):
    """Analyze a user's questions using OpenAI API."""
    user = User.query.get_or_404(user_id)
    
    # Get all user messages across all their chats
    all_user_messages = Message.query.join(Chat).filter(
        Chat.user_id == user_id, 
        Message.role == 'user'
    ).order_by(Message.timestamp).all()
    
    if not all_user_messages:
        flash("該用戶沒有提問記錄", "warning")
        return redirect(url_for('.admin_chats', user_id=user_id))
    
    # Format questions for the API
    questions_text = f"學生: {user.username}\n\n"
    for i, msg in enumerate(all_user_messages, 1):
        chat_category = msg.chat.category # Get category from related chat
        timestamp_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        questions_text += f"問題 {i} ({chat_category} - {timestamp_str}):\n{msg.content}\n\n"
    
    try:
        # Call OpenAI API for analysis
        response = client.chat.completions.create(
            model="o3-mini", # Consider making this configurable
            messages=[
                {"role": "system", "content": "你是一位經驗豐富的GMAT老師，請詳細分析這位同學詢問的問題集，指出他在GMAT各個考點上的具體弱項概念，並提供針對性的學習建議。"},
                {"role": "user", "content": questions_text}
            ],
            stream=False
        )
        
        analysis_result = response.choices[0].message.content
        
        # Store results in session for display on another page
        session['analysis_result'] = analysis_result
        session['analyzed_user_id'] = user_id
        session['analyzed_user_name'] = user.username
        session['questions_count'] = len(all_user_messages)
        
        return redirect(url_for('.show_analysis_result'))
        
    except Exception as e:
        flash(f"使用 AI 分析時出現錯誤: {str(e)}", "danger")
        current_app.logger.error(f"Error analyzing user questions for {user_id}: {str(e)}")
        return redirect(url_for('.admin_chats', user_id=user_id))

@admin_bp.route("/analysis_result")
@admin_required
def show_analysis_result():
    """Display the analysis result stored in session."""
    analysis_result = session.get('analysis_result')
    user_id = session.get('analyzed_user_id')
    user_name = session.get('analyzed_user_name')
    questions_count = session.get('questions_count')
    
    if not analysis_result or user_id is None: # Check if user_id exists
        flash("沒有可用的分析結果或用戶信息", "warning")
        return redirect(url_for('.admin_chats'))
    
    # Optionally clear session data after displaying
    # session.pop('analysis_result', None)
    # session.pop('analyzed_user_id', None)
    # session.pop('analyzed_user_name', None)
    # session.pop('questions_count', None)
    
    return render_template("analysis_result.html", 
                          analysis_result=analysis_result, 
                          user_id=user_id,
                          user_name=user_name,
                          questions_count=questions_count) 