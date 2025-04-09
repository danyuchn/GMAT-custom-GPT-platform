from extensions import db
from flask_login import UserMixin
from datetime import datetime

# User model from original app.py
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)
    # Relationship for UserToken added from token_manager
    token_balance = db.relationship('UserToken', backref='user', lazy=True, uselist=False)
    # Relationship for UserQuota from original models.py
    quota = db.relationship('UserQuota', backref='user', lazy=True)

# Chat model from original app.py
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Increased length for tool categories
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade="all, delete-orphan") # Added cascade delete

# Message model from original app.py
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0.0)
    response_id = db.Column(db.String(100), nullable=True)

# UserToken model from token_manager.py
class UserToken(db.Model):
    __tablename__ = 'user_token'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True) # Ensure one token record per user
    balance = db.Column(db.Float, default=5.0, nullable=False)  # Initial balance 5
    last_reset = db.Column(db.DateTime, default=datetime.utcnow)

# UserQuota model from original models.py
class UserQuota(db.Model):
    __tablename__ = 'user_quota'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True) # Ensure one quota record per user
    total_tokens = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)