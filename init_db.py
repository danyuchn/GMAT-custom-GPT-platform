from app import app, db

with app.app_context():
    db.create_all()
    print("資料庫表已成功創建！") 