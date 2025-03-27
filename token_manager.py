from datetime import datetime, timedelta
import calendar

# 定義用戶Token餘額模型
class UserToken(object):
    """這個類將在init_app被調用時正確初始化"""
    pass

_db = None
_app = None

def init_app(db, app):
    """
    初始化token管理模組
    
    Args:
        db: SQLAlchemy實例
        app: Flask應用實例
    """
    global _db, _app, UserToken
    _db = db
    _app = app
    
    # 定義用戶Token餘額模型
    class UserTokenModel(db.Model):
        __tablename__ = 'user_token'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        balance = db.Column(db.Float, default=5.0, nullable=False)  # 初始餘額5元
        last_reset = db.Column(db.DateTime, default=datetime.utcnow)
        user = db.relationship('User', backref=db.backref('token_balance', lazy=True, uselist=False))
    
    # 將UserToken指向UserTokenModel
    UserToken = UserTokenModel
    
    # 確保數據表存在
    with app.app_context():
        db.create_all()

def check_balance(user_id, cost=0):
    """
    檢查用戶餘額是否足夠支付成本
    
    Args:
        user_id: 用戶ID
        cost: 本次操作的成本
        
    Returns:
        tuple: (是否有足夠餘額, 當前餘額)
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    if not token:
        token = UserToken(user_id=user_id, balance=5.0)  # 初始餘額5元
        _db.session.add(token)
        _db.session.commit()
    
    # 檢查是否需要重置餘額
    check_weekly_reset(token)
    
    # 檢查餘額是否足夠
    if token.balance - cost < 0:
        return False, token.balance
    
    return True, token.balance

def deduct_balance(user_id, cost):
    """
    從用戶餘額中扣除成本
    
    Args:
        user_id: 用戶ID
        cost: 本次操作的成本
        
    Returns:
        float: 扣除後的餘額
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    if not token:
        token = UserToken(user_id=user_id, balance=5.0)  # 初始餘額5元
        _db.session.add(token)
    
    # 檢查是否需要重置餘額
    check_weekly_reset(token)
    
    # 確保成本是正數
    if cost < 0:
        cost = 0
    
    # 扣除成本
    token.balance -= cost
    
    # 確保餘額不會變成負數
    if token.balance < 0:
        token.balance = 0
    
    _db.session.commit()
    
    print(f"用戶 {user_id} 扣除成本 {cost:.6f} 元，當前餘額: {token.balance:.6f} 元")
    
    return token.balance

def check_weekly_reset(token):
    """
    檢查是否需要重置用戶餘額（每週日）
    
    Args:
        token: UserToken對象
    """
    now = datetime.utcnow()
    
    # 如果上次重置時間是在不同的週，且現在是週日，則重置
    if (token.last_reset.isocalendar()[1] != now.isocalendar()[1] or 
        token.last_reset.year != now.year) and now.weekday() == 6:
        token.balance = 5.0  # 重置為5元
        token.last_reset = now
        _db.session.commit()

def get_balance(user_id):
    """
    獲取用戶當前餘額
    
    Args:
        user_id: 用戶ID
        
    Returns:
        float: 當前餘額
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    if not token:
        token = UserToken(user_id=user_id, balance=5.0)  # 初始餘額5元
        _db.session.add(token)
        _db.session.commit()
    
    # 檢查是否需要重置餘額
    check_weekly_reset(token)
    
    return token.balance

def get_next_reset_time():
    """
    獲取下一次餘額重置的時間
    
    Returns:
        datetime: 下次重置時間
    """
    now = datetime.utcnow()
    days_until_sunday = (6 - now.weekday()) % 7  # 計算距離下一個週日的天數
    
    # 如果今天是週日但已經過了重置時間，則設為下週日
    if days_until_sunday == 0 and now.hour >= 0:
        days_until_sunday = 7
        
    next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_until_sunday)
    return next_reset