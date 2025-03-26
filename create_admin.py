from app import app, db, User
from werkzeug.security import generate_password_hash

# 在应用上下文中执行
with app.app_context():
    # 检查管理员是否已存在
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("管理员账户已存在")
    else:
        # 创建管理员用户
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123', method='pbkdf2:sha256', salt_length=16)
        )
        
        # 添加到数据库并提交
        db.session.add(admin_user)
        db.session.commit()
        print("管理员账户创建成功！")