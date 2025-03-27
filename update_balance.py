from app import app, db
from token_manager import UserToken

# 在應用上下文中執行
with app.app_context():
    # 更新所有用戶的餘額
    tokens = UserToken.query.all()
    for token in tokens:
        token.balance = 5.0  # 設置為5元
    
    db.session.commit()
    print(f"已更新 {len(tokens)} 個用戶的餘額為 5.0 元")