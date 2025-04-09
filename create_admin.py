from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()

# Run within the application context
with app.app_context():
    # Check if the admin user already exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("Admin account already exists.")
    else:
        # Create the admin user
        admin_password = 'admin123'
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash(admin_password, method='pbkdf2:sha256', salt_length=16)
        )
        
        # Add to the database and commit
        db.session.add(admin_user)
        try:
            db.session.commit()
            print(f"Admin account 'admin' created successfully with default password!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin account: {str(e)}")