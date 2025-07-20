from flask import Flask
from flask_login import LoginManager
from config import Config
from modules.routes import main_bp
from modules.auth import auth_bp
from modules.models import user_manager
import os

def create_app():
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return user_manager.get_user(user_id)
    
    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['FRAMES_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATASETS_FOLDER'], exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 