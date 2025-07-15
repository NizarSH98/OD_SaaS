from flask import Flask
from config import Config
from modules.routes import main_bp
import os

def create_app():
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['FRAMES_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATASETS_FOLDER'], exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 