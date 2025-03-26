# 文件开头部分调整环境变量加载顺序
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.exc import IntegrityError  # 添加这一行导入IntegrityError
import traceback  # 添加这一行导入traceback模块，因为你在代码中使用了traceback.format_exc()

# 必须先加载环境变量
load_dotenv('/Users/danyuchn/Documents/GitHub/GMAT-custom-GPT-platform/.env')  # 指定绝对路径

# 检查API密钥是否加载成功
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY未正确配置，请检查.env文件")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # 使用环境变量或随机生成
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/danyuchn/Documents/GitHub/GMAT-custom-GPT-platform/users.db'  # 修改为绝对路径
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化資料庫
db = SQLAlchemy(app)

# 初始化登入管理器
# 确保login_manager配置正确
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 必须指向登录路由名称
login_manager.login_message_category = 'warning'  # 添加消息分类

# 讀取 API 金鑰
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# 定義價格（每 1M tokens）
INPUT_PRICE = 1.10
CACHED_INPUT_PRICE = 0.55
OUTPUT_PRICE = 4.40

# 用戶模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

# 聊天記錄模型
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # quant, verbal, graph
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True)

# 訊息模型
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

@login_manager.user_loader
def load_user(user_id):
    try:
        print(f"正在加载用户ID: {user_id}")  # 添加调试日志
        return User.query.get(int(user_id))
    except Exception as e:
        app.logger.error(f"用户加载失败: {str(e)}")
        return None

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
            
            # 添加空值校验
            if not all([username, email, password]):
                flash("所有字段必须填写")
                return redirect(url_for("register"))
            
            # 增强密码策略
            if len(password) < 8 or not any(c.isdigit() for c in password):
                flash("密码必须至少8位且包含数字")
                return redirect(url_for("register"))
            
            # 检查用户是否已存在
            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash("用户名或邮箱已被使用")
                return redirect(url_for("register"))
            
            # 修正密码哈希方法 - 移除不支持的 iterations 参数
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(
                    password, 
                    method='pbkdf2:sha256', 
                    salt_length=16
                )
            )
            
            # 添加事务提交验证
            db.session.add(new_user)
            db.session.commit()
            app.logger.info(f"用户注册成功: {username}")  # 添加成功日志
            flash("✅ 注册成功，请登录", "success")  # 添加消息分类
            return redirect(url_for("login"))
            
        except IntegrityError as e:
            db.session.rollback()
            flash("⚠️ 用户名或邮箱已被使用", "warning")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"注册失败: {traceback.format_exc()}")  # 记录完整堆栈
            flash("🔥 系统错误，请联系管理员", "danger")

    # 保持已填写内容
    return render_template("register.html",
                         username=request.form.get('username', ''),
                         email=request.form.get('email', ''))

@app.route("/login", methods=["GET", "POST"])
def login():
    # 检查用户是否已登录
    if current_user.is_authenticated:
        return redirect(url_for("index"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        next_url = request.form.get("next", "")
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # 登录用户并设置"记住我"选项
            login_user(user, remember=True)
            
            # 添加会话初始化逻辑
            session.pop('active_chat_id', None)  # 清除旧会话
            session.permanent = True  # 设置会话为永久
            
            # 处理重定向
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for("new_chat", category="quant"))
        else:
            flash("登入失敗，請檢查用戶名和密碼", "danger")
            app.logger.warning(f"登录失败尝试: {username}")
    
    return render_template("login.html")

@app.route("/new_chat/<category>")
@login_required
def new_chat(category):
    # 創建新聊天記錄
    new_chat = Chat(user_id=current_user.id, category=category)
    db.session.add(new_chat)
    db.session.commit()
    session['active_chat_id'] = new_chat.id
    
    # 修正重定向目標
    if category == 'quant':
        return redirect(url_for('quant'))  # 修改为'quant'而不是'quant_chat'
    elif category == 'verbal':
        return redirect(url_for('verbal_chat'))
    elif category == 'graph':
        return redirect(url_for('graph_chat'))
    else:
        return redirect(url_for('index'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# 添加history路由，之前被注释掉了
@app.route("/history")
@login_required
def history():
    # 获取用户的所有聊天记录
    all_chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.timestamp.desc()).all()
    
    # 过滤掉没有用户消息的聊天记录
    user_chats = []
    for chat in all_chats:
        # 检查是否有用户消息
        has_user_message = Message.query.filter_by(chat_id=chat.id, role="user").first() is not None
        if has_user_message:
            user_chats.append(chat)
    
    return render_template("history.html", chats=user_chats)

@app.route("/load_chat/<int:chat_id>")
@login_required
def load_chat(chat_id):
    # 檢查聊天記錄是否屬於當前用戶
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    session['active_chat_id'] = chat.id
    
    # 修正重定向目標
    if chat.category == 'quant':
        return redirect(url_for('quant'))  # 修改为'quant'而不是'quant_chat'
    elif chat.category == 'verbal':
        return redirect(url_for('verbal_chat'))
    elif chat.category == 'graph':
        return redirect(url_for('graph_chat'))
    else:
        return redirect(url_for('index'))

# 創建資料庫表格
# 修改文件末尾的初始化块
# 添加管理员后台路由
@app.route("/admin/chats")
@login_required
def admin_chats():
    # 简单的管理员权限检查
    if current_user.username != 'admin':
        flash("无权访问管理页面", "danger")
        return redirect(url_for('index'))
    
    # 获取所有用户
    users = User.query.all()
    
    # 获取指定用户的聊天记录
    user_id = request.args.get('user_id')
    chats = []
    
    if user_id:
        # 修改：只获取有用户消息的聊天记录
        chats_with_user_messages = []
        all_chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.timestamp.desc()).all()
        
        for chat in all_chats:
            # 检查是否有用户消息
            has_user_message = Message.query.filter_by(chat_id=chat.id, role="user").first() is not None
            if has_user_message:
                chats_with_user_messages.append(chat)
        
        chats = chats_with_user_messages
    
    return render_template("admin_chats.html", users=users, chats=chats, selected_user_id=user_id)

# 添加删除聊天记录的路由
@app.route("/admin/delete_chats", methods=["POST"])
@login_required
def delete_chats():
    # 管理员权限检查
    if current_user.username != 'admin':
        flash("无权访问管理页面", "danger")
        return redirect(url_for('index'))
    
    chat_ids = request.form.getlist('chat_ids')
    user_id = request.form.get('user_id')
    
    if not chat_ids:
        flash("未选择任何聊天记录", "warning")
    else:
        try:
            # 首先删除关联的消息
            for chat_id in chat_ids:
                Message.query.filter_by(chat_id=chat_id).delete()
            
            # 然后删除聊天记录
            for chat_id in chat_ids:
                Chat.query.filter_by(id=chat_id).delete()
            
            db.session.commit()
            flash(f"成功删除 {len(chat_ids)} 条聊天记录", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"删除失败: {str(e)}", "danger")
    
    # 重定向回聊天列表页面
    return redirect(url_for('admin_chats', user_id=user_id))

# 添加查看特定聊天内容的路由
@app.route("/admin/chat/<int:chat_id>")
@login_required
def admin_chat_detail(chat_id):
    # 简单的管理员权限检查
    if current_user.username != 'admin':
        flash("无权访问管理页面", "danger")
        return redirect(url_for('index'))
    
    # 获取聊天记录
    chat = Chat.query.get_or_404(chat_id)
    user = User.query.get(chat.user_id)
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    
    return render_template("admin_chat_detail.html", chat=chat, user=user, messages=messages)

# 添加新的路由用于分析学生问题
@app.route("/admin/analyze_user/<int:user_id>", methods=["GET"])
@login_required
def analyze_user_questions(user_id):
    # 管理员权限检查
    if current_user.username != 'admin':
        flash("无权访问管理页面", "danger")
        return redirect(url_for('index'))
    
    # 获取用户信息
    user = User.query.get_or_404(user_id)
    
    # 获取该用户的所有聊天记录
    chats = Chat.query.filter_by(user_id=user_id).all()
    
    # 提取所有用户问题
    all_questions = []
    for chat in chats:
        # 只获取用户的消息
        user_messages = Message.query.filter_by(chat_id=chat.id, role="user").order_by(Message.timestamp).all()
        for msg in user_messages:
            # 添加问题和分类信息
            all_questions.append({
                "category": chat.category,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "content": msg.content
            })
    
    # 如果没有问题，返回提示
    if not all_questions:
        flash("该用户没有提问记录", "warning")
        return redirect(url_for('admin_chats', user_id=user_id))
    
    # 构建问题文本
    questions_text = f"学生: {user.username}\n\n"
    for i, q in enumerate(all_questions, 1):
        questions_text += f"问题 {i} ({q['category']} - {q['timestamp']}):\n{q['content']}\n\n"
    
    # 调用OpenAI API进行分析
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
        
        # 保存分析结果到会话，以便在模板中显示
        session['analysis_result'] = analysis_result
        session['analyzed_user_id'] = user_id
        session['analyzed_user_name'] = user.username
        session['questions_count'] = len(all_questions)
        
        # 重定向到结果页面
        return redirect(url_for('show_analysis_result'))
        
    except Exception as e:
        flash(f"分析过程中出现错误: {str(e)}", "danger")
        return redirect(url_for('admin_chats', user_id=user_id))

# 添加显示分析结果的路由
@app.route("/admin/analysis_result")
@login_required
def show_analysis_result():
    # 管理员权限检查
    if current_user.username != 'admin':
        flash("无权访问管理页面", "danger")
        return redirect(url_for('index'))
    
    # 从会话中获取分析结果
    analysis_result = session.get('analysis_result')
    user_id = session.get('analyzed_user_id')
    user_name = session.get('analyzed_user_name')
    questions_count = session.get('questions_count')
    
    if not analysis_result or not user_id:
        flash("没有可用的分析结果", "warning")
        return redirect(url_for('admin_chats'))
    
    return render_template("analysis_result.html", 
                          analysis_result=analysis_result, 
                          user_id=user_id,
                          user_name=user_name,
                          questions_count=questions_count)

# 删除这里重复的路由定义
# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for("index"))

# 删除这里重复的quant_chat路由定义 - 整个函数都需要删除
# @app.route("/quant", methods=["GET", "POST"])
# @login_required
# def quant_chat():
#     ...  # 删除整个重复的函数定义直到下一个路由

# 添加正确的quant路由
@app.route("/quant", methods=["GET", "POST"])
@login_required
def quant():  # 函数名改为quant，与路由匹配
    active_chat_id = session.get('active_chat_id')
    
    if not active_chat_id:
        # 创建新的聊天记录
        new_chat = Chat(user_id=current_user.id, category="quant")
        db.session.add(new_chat)
        db.session.commit()
        session['active_chat_id'] = new_chat.id
        
        # 添加系统提示但不立即保存到数据库，等用户发送消息后再保存
        instruction = request.form.get("instruction", "simple_explain")
        session['pending_system_message'] = init_conversation(instruction)[0]
    
    if request.method == "POST":
        user_input = request.form.get("user_input")
        instruction = request.form.get("instruction", "simple_explain")  # 确保获取参数
        
        if user_input:
            # 获取当前聊天
            chat_id = session['active_chat_id']
            
            # 如果是第一条用户消息，先添加系统消息
            if not Message.query.filter_by(chat_id=chat_id).first():
                system_message = session.get('pending_system_message') or init_conversation(instruction)[0]
                new_system_message = Message(
                    chat_id=chat_id,
                    role=system_message["role"],
                    content=system_message["content"]
                )
                db.session.add(new_system_message)
            else:
                # 删除旧的系统消息
                Message.query.filter_by(chat_id=active_chat_id, role="system").delete()
                
                # 生成新的系统提示
                system_message = init_conversation(instruction)[0]
                new_system_message = Message(
                    chat_id=active_chat_id,
                    role=system_message["role"],
                    content=system_message["content"]
                )
                db.session.add(new_system_message)
            
            # 添加用户消息到数据库
            user_message = Message(
                chat_id=chat_id,
                role="user",
                content=user_input
            )
            db.session.add(user_message)
            db.session.commit()
            
            # 获取聊天历史
            messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            conversation_history = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            # 调用 OpenAI API
            response = client.chat.completions.create(
                model="o3-mini",
                messages=conversation_history,
                stream=False
            )
            model_reply = response.choices[0].message.content
            
            # 获取 token 使用数据
            prompt_tokens = completion_tokens = 0
            turn_cost = 0.0
            
            if hasattr(response, 'usage'):
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                _, _, turn_cost = calculate_cost(prompt_tokens, completion_tokens)
            
            # 添加 AI 回复到数据库
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
    
    # 获取当前聊天的所有消息
    chat_id = session.get('active_chat_id')
    if chat_id:
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    else:
        messages = []
    
    return render_template("quant_chat.html", messages=messages)

# 同样需要添加verbal_chat和graph_chat路由
@app.route("/verbal", methods=["GET", "POST"])
@login_required
def verbal_chat():
    # 实现类似quant的逻辑
    # ... 代码略 ...
    return render_template("verbal_chat.html", messages=[])

@app.route("/graph", methods=["GET", "POST"])
@login_required
def graph_chat():
    # 实现类似quant的逻辑
    # ... 代码略 ...
    return render_template("graph_chat.html", messages=[])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print(f"已创建数据表: {db.Model.metadata.tables.keys()}")
        
        # 测试代码放在这里
        app.config.update(
            SESSION_COOKIE_SECURE=False,  # 开发环境设为False
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax'
        )
        user = User.query.filter_by(username='test').first()
        if user:
            print("密码验证结果:", check_password_hash(user.password, '您注册时使用的密码'))
            
    app.run(host='0.0.0.0', port=5001, debug=True)
