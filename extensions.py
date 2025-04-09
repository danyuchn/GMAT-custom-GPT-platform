from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from openai import OpenAI
import os

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Updated to blueprint name
login_manager.login_message = '請登入以訪問此頁面。'
login_manager.login_message_category = 'warning'

# OpenAI Client
# API Key will be loaded from config in create_app
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 