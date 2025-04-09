from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy.exc import IntegrityError
import traceback

from models import User
from extensions import db, login_manager

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        # Use current_app logger
        current_app.logger.error(f"Error loading user {user_id}: {str(e)}")
        return None

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            
            if not all([username, email, password]):
                flash("所有字段必須填寫", "warning") # Added category
                return redirect(url_for("auth.register"))
            
            if len(password) < 8 or not any(c.isdigit() for c in password):
                flash("密碼必須至少8位且包含數字", "warning") # Added category
                return redirect(url_for("auth.register"))
            
            # Check if user exists
            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash("用戶名或郵箱已被使用", "warning") # Added category
                return redirect(url_for("auth.register"))
            
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
            )
            
            db.session.add(new_user)
            db.session.commit()
            flash("✅ 註冊成功，請登錄", "success")
            return redirect(url_for("auth.login"))
            
        except IntegrityError:
            db.session.rollback()
            flash("⚠️ 用戶名或郵箱已被使用", "warning")
            # Redirect to prevent form resubmission issues
            return redirect(url_for("auth.register", username=request.form.get('username', ''), email=request.form.get('email', '')))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration failed: {traceback.format_exc()}")
            flash("🔥 系統錯誤，請聯繫管理員", "danger")
            # Redirect to prevent form resubmission issues
            return redirect(url_for("auth.register", username=request.form.get('username', ''), email=request.form.get('email', '')))

    return render_template("register.html",
                         username=request.args.get('username', ''), # Use args for GET redirect
                         email=request.args.get('email', '')) # Use args for GET redirect

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat.index')) # Redirect to a main page, assuming chat.index
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user) # `remember=True` can be added if needed
            next_page = request.args.get('next')
            # Use url_for with blueprint name
            return redirect(next_page or url_for('chat.index')) # Redirect to chat index after login
        else:
            flash('登入失敗，請檢查用戶名和密碼', 'danger')
    
    # Always render login template for GET or failed POST
    return render_template('login.html')

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("您已成功登出", "info") # Add feedback message
    return redirect(url_for("auth.login")) 