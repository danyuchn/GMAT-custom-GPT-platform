from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import traceback

# 必須先加載環境變量
load_dotenv()

# 檢查API密鑰是否加載成功
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY未正確配置，請檢查.env文件")

print(f"API key loaded successfully: {OPENAI_API_KEY[:10]}...")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化資料庫和登入管理器
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=OPENAI_API_KEY)

# 定義價格（每 1M tokens）
INPUT_PRICE = 1.10
CACHED_INPUT_PRICE = 0.55
OUTPUT_PRICE = 4.40

# 資料庫模型定義
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # quant, verbal, graph
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0.0)

# 計算成本函數
def calculate_cost(prompt_tokens, completion_tokens, cached_input_tokens=0):
    non_cached_input_tokens = prompt_tokens - cached_input_tokens
    cached_input_cost = (cached_input_tokens / 1_000_000) * CACHED_INPUT_PRICE
    non_cached_input_cost = (non_cached_input_tokens / 1_000_000) * INPUT_PRICE
    input_cost = cached_input_cost + non_cached_input_cost
    output_cost = (completion_tokens / 1_000_000) * OUTPUT_PRICE
    total_cost = input_cost + output_cost
    return input_cost, output_cost, total_cost

# 導入token管理模組並初始化
import token_manager
token_manager.init_app(db, app)

def init_conversation(instruction="simple_explain"):
    system_prompts = {
        "simple_explain": "請用繁體中文解釋解題步驟，並以高中生能理解的方式回答。",
        "quick_solve": "請用繁體中文提供一個能在N分鐘內用紙筆和視覺估算解決數學問題的快捷方法。原則是：計算越少、數字越簡單、公式越少且越簡單越好。如果代入數字或使用視覺猜測更簡單，請採用這種方法。",
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

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        app.logger.error(f"用戶加載失敗: {str(e)}")
        return None

# 基本路由
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            
            if not all([username, email, password]):
                flash("所有字段必須填寫")
                return redirect(url_for("register"))
            
            if len(password) < 8 or not any(c.isdigit() for c in password):
                flash("密碼必須至少8位且包含數字")
                return redirect(url_for("register"))
            
            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash("用戶名或郵箱已被使用")
                return redirect(url_for("register"))
            
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
            )
            
            db.session.add(new_user)
            db.session.commit()
            flash("✅ 註冊成功，請登錄", "success")
            return redirect(url_for("login"))
            
        except IntegrityError:
            db.session.rollback()
            flash("⚠️ 用戶名或郵箱已被使用", "warning")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"註冊失敗: {traceback.format_exc()}")
            flash("🔥 系統錯誤，請聯繫管理員", "danger")

    return render_template("register.html",
                         username=request.form.get('username', ''),
                         email=request.form.get('email', ''))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('登入失敗，請檢查用戶名和密碼', 'danger')
    
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/new_chat/<category>")
@login_required
def new_chat(category):
    new_chat = Chat(user_id=current_user.id, category=category)
    db.session.add(new_chat)
    db.session.commit()
    session['active_chat_id'] = new_chat.id
    
    if category == 'quant':
        return redirect(url_for('quant'))
    elif category == 'verbal':
        return redirect(url_for('verbal_chat'))
    elif category == 'graph':
        return redirect(url_for('graph_chat'))
    else:
        return redirect(url_for('index'))

@app.route("/history")
@login_required
def history():
    all_chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.timestamp.desc()).all()
    
    user_chats = []
    for chat in all_chats:
        has_user_message = Message.query.filter_by(chat_id=chat.id, role="user").first() is not None
        if has_user_message:
            user_chats.append(chat)
    
    return render_template("history.html", chats=user_chats)

@app.route("/load_chat/<int:chat_id>")
@login_required
def load_chat(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    session['active_chat_id'] = chat.id
    
    if chat.category == 'quant':
        return redirect(url_for('quant'))
    elif chat.category == 'verbal':
        return redirect(url_for('verbal_chat'))
    elif chat.category == 'graph':
        return redirect(url_for('graph_chat'))
    else:
        return redirect(url_for('index'))

# 管理員路由
@app.route("/admin/chats")
@login_required
def admin_chats():
    if current_user.username != 'admin':
        flash("無權訪問管理頁面", "danger")
        return redirect(url_for('index'))
    
    users = User.query.all()
    user_id = request.args.get('user_id')
    chats = []
    
    if user_id:
        chats_with_user_messages = []
        all_chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.timestamp.desc()).all()
        
        for chat in all_chats:
            has_user_message = Message.query.filter_by(chat_id=chat.id, role="user").first() is not None
            if has_user_message:
                chats_with_user_messages.append(chat)
        
        chats = chats_with_user_messages
    
    return render_template("admin_chats.html", users=users, chats=chats, selected_user_id=user_id)

@app.route("/admin/delete_chats", methods=["POST"])
@login_required
def delete_chats():
    if current_user.username != 'admin':
        flash("無權訪問管理頁面", "danger")
        return redirect(url_for('index'))
    
    chat_ids = request.form.getlist('chat_ids')
    user_id = request.form.get('user_id')
    
    if not chat_ids:
        flash("未選擇任何聊天記錄", "warning")
    else:
        try:
            for chat_id in chat_ids:
                Message.query.filter_by(chat_id=chat_id).delete()
                Chat.query.filter_by(id=chat_id).delete()
            
            db.session.commit()
            flash(f"成功刪除 {len(chat_ids)} 條聊天記錄", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"刪除失敗: {str(e)}", "danger")
    
    return redirect(url_for('admin_chats', user_id=user_id))

@app.route("/admin/chat/<int:chat_id>")
@login_required
def admin_chat_detail(chat_id):
    if current_user.username != 'admin':
        flash("無權訪問管理頁面", "danger")
        return redirect(url_for('index'))
    
    chat = Chat.query.get_or_404(chat_id)
    user = User.query.get(chat.user_id)
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    
    return render_template("admin_chat_detail.html", chat=chat, user=user, messages=messages)

@app.route("/admin/analyze_user/<int:user_id>", methods=["GET"])
@login_required
def analyze_user_questions(user_id):
    if current_user.username != 'admin':
        flash("無權訪問管理頁面", "danger")
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    chats = Chat.query.filter_by(user_id=user_id).all()
    
    all_questions = []
    for chat in chats:
        user_messages = Message.query.filter_by(chat_id=chat.id, role="user").order_by(Message.timestamp).all()
        for msg in user_messages:
            all_questions.append({
                "category": chat.category,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "content": msg.content
            })
    
    if not all_questions:
        flash("該用戶沒有提問記錄", "warning")
        return redirect(url_for('admin_chats', user_id=user_id))
    
    questions_text = f"學生: {user.username}\n\n"
    for i, q in enumerate(all_questions, 1):
        questions_text += f"問題 {i} ({q['category']} - {q['timestamp']}):\n{q['content']}\n\n"
    
    try:
        response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": "你是一位老師，請分析這位同學詢問的問題集，告訴我他的弱項概念有哪些"},
                {"role": "user", "content": questions_text}
            ],
            stream=False
        )
        
        analysis_result = response.choices[0].message.content
        
        session['analysis_result'] = analysis_result
        session['analyzed_user_id'] = user_id
        session['analyzed_user_name'] = user.username
        session['questions_count'] = len(all_questions)
        
        return redirect(url_for('show_analysis_result'))
        
    except Exception as e:
        flash(f"分析過程中出現錯誤: {str(e)}", "danger")
        return redirect(url_for('admin_chats', user_id=user_id))

@app.route("/admin/analysis_result")
@login_required
def show_analysis_result():
    if current_user.username != 'admin':
        flash("無權訪問管理頁面", "danger")
        return redirect(url_for('index'))
    
    analysis_result = session.get('analysis_result')
    user_id = session.get('analyzed_user_id')
    user_name = session.get('analyzed_user_name')
    questions_count = session.get('questions_count')
    
    if not analysis_result or not user_id:
        flash("沒有可用的分析結果", "warning")
        return redirect(url_for('admin_chats'))
    
    return render_template("analysis_result.html", 
                          analysis_result=analysis_result, 
                          user_id=user_id,
                          user_name=user_name,
                          questions_count=questions_count)

# 聊天處理通用函數
# 導入token管理模組
def handle_chat(category, template_name):
    active_chat_id = session.get('active_chat_id')
    
    if not active_chat_id:
        new_chat = Chat(user_id=current_user.id, category=category)
        db.session.add(new_chat)
        db.session.commit()
        session['active_chat_id'] = new_chat.id
        
        instruction = request.form.get("instruction", "simple_explain")
        session['pending_system_message'] = init_conversation(instruction)[0]
    
    # 獲取用戶當前餘額
    current_balance = token_manager.get_balance(current_user.id)
    
    if request.method == "POST":
        user_input = request.form.get("user_input")
        instruction = request.form.get("instruction", "simple_explain")
        
        if user_input:
            # 檢查用戶餘額是否足夠
            has_balance, balance = token_manager.check_balance(current_user.id)
            if not has_balance:
                flash(f"您的API餘額不足，請等待下週日重置。當前餘額: {balance:.4f} 元", "warning")
                chat_id = session.get('active_chat_id')
                if chat_id:
                    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
                else:
                    messages = []
                return render_template(template_name, messages=messages, api_balance=balance)
            
            chat_id = session['active_chat_id']
            
            if not Message.query.filter_by(chat_id=chat_id).first():
                system_message = session.get('pending_system_message') or init_conversation(instruction)[0]
                new_system_message = Message(
                    chat_id=chat_id,
                    role=system_message["role"],
                    content=system_message["content"]
                )
                db.session.add(new_system_message)
            else:
                Message.query.filter_by(chat_id=active_chat_id, role="system").delete()
                
                system_message = init_conversation(instruction)[0]
                new_system_message = Message(
                    chat_id=active_chat_id,
                    role=system_message["role"],
                    content=system_message["content"]
                )
                db.session.add(new_system_message)
            
            user_message = Message(
                chat_id=chat_id,
                role="user",
                content=user_input
            )
            db.session.add(user_message)
            db.session.commit()
            
            messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            conversation_history = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            response = client.chat.completions.create(
                model="o3-mini",
                messages=conversation_history,
                stream=False
            )
            model_reply = response.choices[0].message.content
            
            # 獲取API回應後，扣除成本
            prompt_tokens = completion_tokens = 0
            turn_cost = 0.0
            
            if hasattr(response, 'usage'):
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                _, _, turn_cost = calculate_cost(prompt_tokens, completion_tokens)
                
                # 扣除用戶餘額
                new_balance = token_manager.deduct_balance(current_user.id, turn_cost)
                
                # 如果餘額不足，提示用戶
                if new_balance <= 0:
                    flash(f"您的API餘額已用完，請等待下週日重置。", "warning")
            
            ai_message = Message(
                chat_id=chat_id,
                role="assistant",
                content=model_reply,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=turn_cost
            )
            db.session.add(ai_message)
            db.session.commit()
    
    chat_id = session.get('active_chat_id')
    if chat_id:
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    else:
        messages = []
    
    # 獲取下次重置時間
    next_reset = token_manager.get_next_reset_time()
    days_until_reset = (next_reset - datetime.utcnow()).days
    
    return render_template(template_name, 
                          messages=messages, 
                          api_balance=current_balance,
                          days_until_reset=days_until_reset)

# 聊天路由
@app.route("/quant", methods=["GET", "POST"])
@login_required
def quant():
    return handle_chat("quant", "quant_chat.html")

@app.route("/verbal", methods=["GET", "POST"])
@login_required
def verbal_chat():
    return handle_chat("verbal", "verbal_chat.html")

@app.route("/graph", methods=["GET", "POST"])
@login_required
def graph_chat():
    return handle_chat("graph", "graph_chat.html")

# 添加工具頁面路由
# 在 quant_tool 函數中添加成本計算和餘額扣除
@app.route('/quant_tool', methods=['GET', 'POST'])
@login_required
def quant_tool():
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        instruction = request.form.get('instruction')
        
        # 檢查用戶餘額是否足夠
        has_balance, balance = token_manager.check_balance(current_user.id)
        if not has_balance:
            flash(f"您的API餘額不足，請等待下週日重置。當前餘額: {balance:.4f} 元", "warning")
            chat_id = session.get('chat_id')
            if chat_id:
                messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            else:
                messages = []
            return render_template('quant_tool.html', messages=messages, api_balance=balance)
        
        # 使用工具 API 處理請求
        from tools_api import process_tool_request
        result = process_tool_request(instruction, user_input)
        
        # 創建新的消息
        timestamp = datetime.now()
        
        # 用戶消息
        user_message = Message(
            role='user',
            content=user_input,
            timestamp=timestamp,
            chat_id=session.get('chat_id')
        )
        
        # AI 回應
        if result['status'] == 'success':
            ai_content = result['content']
        else:
            ai_content = f"處理請求時發生錯誤: {result['message']}"
            
        # 估算 token 使用量和成本
        # 這裡使用簡單估算，實際應該從 API 回應中獲取
        prompt_tokens = len(user_input) // 4  # 粗略估計，4個字符約等於1個token
        completion_tokens = len(ai_content) // 4
        _, _, turn_cost = calculate_cost(prompt_tokens, completion_tokens)
        
        # 扣除用戶餘額
        new_balance = token_manager.deduct_balance(current_user.id, turn_cost)
        
        # 如果餘額不足，提示用戶
        if new_balance <= 0:
            flash(f"您的API餘額已用完，請等待下週日重置。", "warning")
            
        ai_message = Message(
            role='assistant',
            content=ai_content,
            timestamp=timestamp,
            chat_id=session.get('chat_id'),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=turn_cost
        )
        
        # 保存消息
        db.session.add(user_message)
        db.session.add(ai_message)
        db.session.commit()
        
        # 獲取更新後的消息列表
        messages = Message.query.filter_by(chat_id=session.get('chat_id')).order_by(Message.timestamp).all()
        
        # 獲取當前餘額和重置天數
        current_balance = token_manager.get_balance(current_user.id)
        next_reset = token_manager.get_next_reset_time()
        days_until_reset = (next_reset - datetime.utcnow()).days
        
        return render_template('quant_tool.html', 
                              messages=messages, 
                              api_balance=current_balance,
                              days_until_reset=days_until_reset)
    
    # GET 請求處理
    chat_id = request.args.get('chat_id')
    if chat_id:
        session['chat_id'] = chat_id
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    else:
        # 創建新的聊天
        # 使用正確的字段，不使用 title 或 name
        new_chat = Chat(
            user_id=current_user.id,
            category="quant_tool"
        )
        db.session.add(new_chat)
        db.session.commit()
        
        session['chat_id'] = new_chat.id
        messages = []
    
    return render_template('quant_tool.html', messages=messages)

@app.route('/verbal_tool', methods=['GET', 'POST'])
@login_required
def verbal_tool():
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        instruction = request.form.get('instruction', 'cr_classification')
        
        # 檢查用戶餘額是否足夠
        has_balance, balance = token_manager.check_balance(current_user.id)
        if not has_balance:
            flash(f"您的API餘額不足，請等待下週日重置。當前餘額: {balance:.4f} 元", "warning")
            chat_id = session.get('chat_id')
            if chat_id:
                messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            else:
                messages = []
            return render_template('verbal_tool.html', messages=messages, api_balance=balance)
        
        # 使用工具 API 處理請求
        from tools_api import process_tool_request
        result = process_tool_request(instruction, user_input)
        
        # 創建新的消息
        timestamp = datetime.now()
        
        # 獲取或創建聊天ID
        chat_id = session.get('chat_id')
        if not chat_id:
            new_chat = Chat(user_id=current_user.id, category="verbal_tool")
            db.session.add(new_chat)
            db.session.commit()
            chat_id = new_chat.id
            session['chat_id'] = chat_id
        
        # 用戶消息
        user_message = Message(
            role='user',
            content=user_input,
            timestamp=timestamp,
            chat_id=chat_id
        )
        
        # AI 回應
        if result['status'] == 'success':
            ai_content = result['content']
        else:
            ai_content = f"處理請求時發生錯誤: {result['message']}"
            
        # 估算 token 使用量和成本
        prompt_tokens = len(user_input) // 4  # 粗略估計，4個字符約等於1個token
        completion_tokens = len(ai_content) // 4
        _, _, turn_cost = calculate_cost(prompt_tokens, completion_tokens)
        
        # 扣除用戶餘額
        new_balance = token_manager.deduct_balance(current_user.id, turn_cost)
        
        # 如果餘額不足，提示用戶
        if new_balance <= 0:
            flash(f"您的API餘額已用完，請等待下週日重置。", "warning")
            
        ai_message = Message(
            role='assistant',
            content=ai_content,
            timestamp=timestamp,
            chat_id=chat_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=turn_cost
        )
        
        # 保存消息
        db.session.add(user_message)
        db.session.add(ai_message)
        db.session.commit()
        
        # 獲取更新後的消息列表
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
        
        # 獲取當前餘額和重置天數
        current_balance = token_manager.get_balance(current_user.id)
        next_reset = token_manager.get_next_reset_time()
        days_until_reset = (next_reset - datetime.utcnow()).days
        
        return render_template('verbal_tool.html', 
                              messages=messages, 
                              api_balance=current_balance,
                              days_until_reset=days_until_reset)
    
    # GET 請求處理
    chat_id = request.args.get('chat_id')
    if chat_id:
        session['chat_id'] = chat_id
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    else:
        # 創建新的聊天
        new_chat = Chat(
            user_id=current_user.id,
            category="verbal_tool"
        )
        db.session.add(new_chat)
        db.session.commit()
        
        session['chat_id'] = new_chat.id
        messages = []
    
    # 獲取當前餘額和重置天數
    current_balance = token_manager.get_balance(current_user.id)
    next_reset = token_manager.get_next_reset_time()
    days_until_reset = (next_reset - datetime.utcnow()).days
    
    return render_template('verbal_tool.html', 
                          messages=messages, 
                          api_balance=current_balance,
                          days_until_reset=days_until_reset)

# 修改 core_tool 路由函數
@app.route('/core_tool', methods=['GET', 'POST'])
@login_required
def core_tool():
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        instruction = request.form.get('instruction', 'time_management')
        
        # 檢查用戶餘額是否足夠
        has_balance, balance = token_manager.check_balance(current_user.id)
        if not has_balance:
            flash(f"您的API餘額不足，請等待下週日重置。當前餘額: {balance:.4f} 元", "warning")
            chat_id = session.get('chat_id')
            if chat_id:
                messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            else:
                messages = []
            return render_template('core_tool.html', messages=messages, api_balance=balance)
        
        # 使用工具 API 處理請求
        from tools_api import process_tool_request
        result = process_tool_request(instruction, user_input)
        
        # 創建新的消息
        timestamp = datetime.now()
        
        # 獲取或創建聊天ID
        chat_id = session.get('chat_id')
        if not chat_id:
            new_chat = Chat(user_id=current_user.id, category="core_tool")
            db.session.add(new_chat)
            db.session.commit()
            chat_id = new_chat.id
            session['chat_id'] = chat_id
        
        # 用戶消息
        user_message = Message(
            role='user',
            content=user_input,
            timestamp=timestamp,
            chat_id=chat_id
        )
        
        # AI 回應
        if result['status'] == 'success':
            ai_content = result['content']
        else:
            ai_content = f"處理請求時發生錯誤: {result['message']}"
            
        # 估算 token 使用量和成本
        prompt_tokens = len(user_input) // 4  # 粗略估計，4個字符約等於1個token
        completion_tokens = len(ai_content) // 4
        _, _, turn_cost = calculate_cost(prompt_tokens, completion_tokens)
        
        # 扣除用戶餘額
        new_balance = token_manager.deduct_balance(current_user.id, turn_cost)
        
        # 如果餘額不足，提示用戶
        if new_balance <= 0:
            flash(f"您的API餘額已用完，請等待下週日重置。", "warning")
            
        ai_message = Message(
            role='assistant',
            content=ai_content,
            timestamp=timestamp,
            chat_id=chat_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=turn_cost
        )
        
        # 保存消息
        db.session.add(user_message)
        db.session.add(ai_message)
        db.session.commit()
        
        # 獲取更新後的消息列表
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
        
        # 獲取當前餘額和重置天數
        current_balance = token_manager.get_balance(current_user.id)
        next_reset = token_manager.get_next_reset_time()
        days_until_reset = (next_reset - datetime.utcnow()).days
        
        return render_template('core_tool.html', 
                              messages=messages, 
                              api_balance=current_balance,
                              days_until_reset=days_until_reset)
    
    # GET 請求處理
    chat_id = request.args.get('chat_id')
    if chat_id:
        session['chat_id'] = chat_id
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    else:
        # 創建新的聊天
        new_chat = Chat(
            user_id=current_user.id,
            category="core_tool"
        )
        db.session.add(new_chat)
        db.session.commit()
        
        session['chat_id'] = new_chat.id
        messages = []
    
    # 獲取當前餘額和重置天數
    current_balance = token_manager.get_balance(current_user.id)
    next_reset = token_manager.get_next_reset_time()
    days_until_reset = (next_reset - datetime.utcnow()).days
    
    return render_template('core_tool.html', 
                          messages=messages, 
                          api_balance=current_balance,
                          days_until_reset=days_until_reset)

@app.route('/api/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """獲取當前用戶的 API 使用統計"""
    try:
        # 獲取用戶餘額
        balance = token_manager.get_balance(current_user.id)
        
        # 獲取下次重置時間
        next_reset = token_manager.get_next_reset_time()
        days_until_reset = (next_reset - datetime.utcnow()).days
        
        # 計算用戶的總 token 使用量和成本
        messages = Message.query.join(Chat).filter(Chat.user_id == current_user.id).all()
        total_tokens = sum(msg.prompt_tokens + msg.completion_tokens for msg in messages)
        total_cost = sum(msg.cost for msg in messages)
        
        return jsonify({
            'status': 'success',
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'balance': balance,
            'days_until_reset': days_until_reset
        })
    except Exception as e:
        app.logger.error(f"獲取用戶統計失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print(f"已創建數據表: {db.Model.metadata.tables.keys()}")
        
        app.config.update(
            SESSION_COOKIE_SECURE=False,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax'
        )
            
    app.run(host='0.0.0.0', port=5001, debug=True)