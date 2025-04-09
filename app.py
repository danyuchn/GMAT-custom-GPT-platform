import os
from flask import Flask

from config import Config
from extensions import db, migrate, login_manager, client
import token_manager

def create_app(config_class=Config):
    """Application Factory Function"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists
        
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # Client is already initialized in extensions.py with env var
    # client.api_key = app.config['OPENAI_API_KEY'] # Update API key if needed

    # Initialize token manager
    token_manager.init_app(app)
    
    # Import and register blueprints
    from blueprints.auth import auth_bp
    from blueprints.chat import chat_bp
    from blueprints.admin import admin_bp
    from blueprints.tools import tools_bp
    from blueprints.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp, url_prefix='/') # Set chat as default
    app.register_blueprint(admin_bp) # url_prefix defined in blueprint
    app.register_blueprint(tools_bp) # url_prefix defined in blueprint
    app.register_blueprint(api_bp)   # url_prefix defined in blueprint
    
    # Configure logging if needed
    # import logging
    # logging.basicConfig(level=logging.INFO)
    
    # Create database tables if they don't exist
    # This is usually handled by migrations, but can be useful for initial setup
    with app.app_context():
        # Reflect existing tables before creating
        # db.reflect()
        db.create_all()
        print(f"Database tables checked/created for URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        # You might want to check specific tables:
        # print(f"Tables found: {db.Model.metadata.tables.keys()}")
        
    # Optional: Add a simple root route if chat blueprint doesn't cover it
    # @app.route('/')
    # def hello():
    #    return "Hello, World!"

    return app

# Entry point for running the application
if __name__ == "__main__":
    app = create_app()
    # Configure session cookie settings (moved from old app.py)
    app.config.update(
        SESSION_COOKIE_SECURE=app.config.get('SESSION_COOKIE_SECURE', False),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax'
    )
    # Run the app (debug=True for development)
    # Use host='0.0.0.0' to be accessible externally
    app.run(host='0.0.0.0', port=5001, debug=True)