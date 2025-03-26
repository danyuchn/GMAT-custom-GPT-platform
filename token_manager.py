from datetime import datetime, timedelta
import calendar

# 定義用戶Token餘額模型
class UserToken(object):
    """這個類將在init_app被調用時正確初始化"""
    pass

# 存儲db引用
_db = None

def init_app(db, app):
    """使用Flask應用和SQLAlchemy實例初始化token管理器"""
    global _db, UserToken
    _db = db
    
    # 現在使用db實例定義UserToken模型
    class UserTokenModel(db.Model):
        __tablename__ = 'user_token'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        balance = db.Column(db.Float, default=10.0, nullable=False)  # 初始餘額10元
        last_reset = db.Column(db.DateTime, default=datetime.utcnow)
        user = db.relationship('User', backref=db.backref('token_balance', lazy=True, uselist=False))
    
    # 替換佔位符為實際模型
    UserToken = UserTokenModel
    
    # 如果表不存在則創建
    with app.app_context():
        db.create_all()
    
    return UserToken

# 檢查用戶餘額是否足夠
def check_balance(user_id, cost=0):
    """
    檢查用戶餘額是否足夠支付成本
    
    Args:
        user_id: 用戶ID
        cost: 本次操作的成本
        
    Returns:
        (bool, float): (餘額是否足夠, 當前餘額)
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    # 如果用戶沒有餘額記錄，創建一個
    if not token:
        token = UserToken(user_id=user_id)
        _db.session.add(token)
        _db.session.commit()
    
    # 檢查是否需要重置餘額（每週日）
    check_weekly_reset(token)
    
    # 檢查餘額是否足夠
    if token.balance < cost:
        return False, token.balance
    
    return True, token.balance

# 扣除用戶餘額
def deduct_balance(user_id, cost):
    """
    從用戶餘額中扣除成本
    
    Args:
        user_id: 用戶ID
        cost: 需要扣除的成本
        
    Returns:
        float: 扣除後的餘額
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    if not token:
        token = UserToken(user_id=user_id)
        _db.session.add(token)
    
    # 檢查是否需要重置餘額
    check_weekly_reset(token)
    
    # 扣除成本
    token.balance -= cost
    if token.balance < 0:
        token.balance = 0
    
    _db.session.commit()
    return token.balance

# 檢查是否需要每週重置
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
        token.balance = 10.0  # 重置為10元
        token.last_reset = now
        _db.session.commit()

# 獲取用戶當前餘額
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
        token = UserToken(user_id=user_id)
        _db.session.add(token)
        _db.session.commit()
    
    # 檢查是否需要重置餘額
    check_weekly_reset(token)
    
    return token.balance

# 獲取下次重置時間
def get_next_reset_time():
    """
    獲取下一次餘額重置的時間
    
    Returns:
        datetime: 下次重置時間
    """
    now = datetime.utcnow()
    days_until_sunday = 6 - now.weekday() if now.weekday() != 6 else 7
    next_reset = now + timedelta(days=days_until_sunday)
    next_reset = next_reset.replace(hour=0, minute=0, second=0, microsecond=0)
    return next_reset