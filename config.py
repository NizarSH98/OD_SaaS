import os
from datetime import timedelta

class Config:
    """Configuration class for the Flask application"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    FRAMES_FOLDER = 'frames'
    DATASETS_FOLDER = 'datasets'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    
    # Allowed file extensions
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'}
    
    # Frame extraction settings
    DEFAULT_FRAME_INTERVAL = 1.0  # seconds
    MAX_FRAME_INTERVAL = 10.0     # seconds
    MIN_FRAME_INTERVAL = 0.1      # seconds
    
    # Session timeout
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Dataset export formats
    EXPORT_FORMATS = ['yolo', 'coco', 'pascal_voc']
    
    @staticmethod
    def allowed_file(filename, allowed_extensions):
        """Check if file has an allowed extension"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions 