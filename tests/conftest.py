"""
Pytest configuration and shared fixtures for VisionLabel Pro test suite.

This module provides common test fixtures, mock objects, and configuration
used across all test modules for comprehensive testing of the SaaS platform.
"""

import pytest
import tempfile
import shutil
import os
import json
import cv2
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, patch

# Import application modules
from app import create_app
from modules.models import User, UserManager
from modules.video_processor import VideoProcessor
from modules.data_storage import LabelStorage
from config import Config


class TestConfig(Config):
    """Test-specific configuration with isolated storage"""
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    
    # Use temporary directories for testing
    UPLOAD_FOLDER = None  # Will be set in fixture
    FRAMES_FOLDER = None  # Will be set in fixture
    DATASETS_FOLDER = None  # Will be set in fixture


@pytest.fixture
def app():
    """
    Create and configure a Flask application instance for testing.
    
    Returns:
        Flask: Configured Flask app with test settings
    """
    app = create_app()
    app.config.from_object(TestConfig)
    
    # Create temporary directories for testing
    temp_dir = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = os.path.join(temp_dir, 'uploads')
    app.config['FRAMES_FOLDER'] = os.path.join(temp_dir, 'frames')
    app.config['DATASETS_FOLDER'] = os.path.join(temp_dir, 'datasets')
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['FRAMES_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATASETS_FOLDER'], exist_ok=True)
    
    yield app
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(app):
    """
    Create a test client for the Flask application.
    
    Args:
        app: Flask application fixture
        
    Returns:
        FlaskClient: Test client for making HTTP requests
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    Create a test CLI runner for the Flask application.
    
    Args:
        app: Flask application fixture
        
    Returns:
        FlaskCliRunner: Test CLI runner
    """
    return app.test_cli_runner()


@pytest.fixture
def temp_user_storage():
    """
    Create temporary user storage file for testing.
    
    Returns:
        str: Path to temporary user storage file
    """
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def user_manager(temp_user_storage):
    """
    Create a UserManager instance with temporary storage.
    
    Args:
        temp_user_storage: Temporary storage file fixture
        
    Returns:
        UserManager: User manager with isolated storage
    """
    return UserManager(storage_file=temp_user_storage)


@pytest.fixture
def test_user():
    """
    Create a test user instance.
    
    Returns:
        User: Test user object
    """
    return User(
        id='test-user-123',
        email='test@visionlabel.pro',
        password_hash='$2b$12$test.hash.for.testing.purposes.only'
    )


@pytest.fixture
def mock_video_file():
    """
    Create a mock video file for testing video processing.
    
    Returns:
        str: Path to mock video file
    """
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.mp4', delete=False)
    
    # Create a simple test video using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_file.name, fourcc, 30.0, (640, 480))
    
    # Generate 90 frames (3 seconds at 30fps)
    for i in range(90):
        # Create a simple colored frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :] = [i % 255, (i * 2) % 255, (i * 3) % 255]  # Changing colors
        
        # Add frame number text
        cv2.putText(frame, f'Frame {i}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out.write(frame)
    
    out.release()
    temp_file.close()
    
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def video_processor(app):
    """
    Create a VideoProcessor instance for testing.
    
    Args:
        app: Flask application fixture
        
    Returns:
        VideoProcessor: Video processor with test configuration
    """
    return VideoProcessor(app.config['FRAMES_FOLDER'])


@pytest.fixture
def label_storage(app):
    """
    Create a LabelStorage instance for testing.
    
    Args:
        app: Flask application fixture
        
    Returns:
        LabelStorage: Label storage with test configuration
    """
    return LabelStorage(app.config['DATASETS_FOLDER'])


@pytest.fixture
def sample_annotations():
    """
    Create sample annotation data for testing.
    
    Returns:
        list: Sample bounding box annotations
    """
    return [
        {
            'id': 'annotation-1',
            'class': 'person',
            'x': 100,
            'y': 150,
            'width': 200,
            'height': 300,
            'confidence': 0.95
        },
        {
            'id': 'annotation-2',
            'class': 'car',
            'x': 400,
            'y': 200,
            'width': 150,
            'height': 100,
            'confidence': 0.87
        }
    ]


@pytest.fixture
def sample_project_metadata():
    """
    Create sample project metadata for testing.
    
    Returns:
        dict: Sample project metadata
    """
    return {
        'project_id': 'test-project-123',
        'video_name': 'test_video.mp4',
        'video_path': '/path/to/test_video.mp4',
        'created_at': datetime.now().isoformat(),
        'fps': 30.0,
        'total_frames': 90,
        'duration': 3.0,
        'frame_interval': 1.0,
        'extracted_frames': 3,
        'frame_size': [640, 480]
    }


@pytest.fixture
def mock_cv2_capture():
    """
    Create a mock OpenCV VideoCapture object for testing.
    
    Returns:
        MagicMock: Mock VideoCapture object
    """
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.side_effect = lambda prop: {
        cv2.CAP_PROP_FPS: 30.0,
        cv2.CAP_PROP_FRAME_COUNT: 90
    }.get(prop, 0)
    
    # Mock frame reading
    def mock_read():
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        return True, frame
    
    mock_cap.read = mock_read
    mock_cap.release = MagicMock()
    
    return mock_cap


@pytest.fixture
def authenticated_client(client, user_manager, test_user):
    """
    Create an authenticated test client with logged-in user.
    
    Args:
        client: Flask test client
        user_manager: User manager fixture
        test_user: Test user fixture
        
    Returns:
        FlaskClient: Authenticated test client
    """
    # Add user to manager
    user_manager.users[test_user.id] = test_user
    
    # Login user
    with client.session_transaction() as sess:
        sess['_user_id'] = test_user.id
        sess['_fresh'] = True
    
    return client


# Pytest markers for different test categories
pytest.mark.unit = pytest.mark.filterwarnings("ignore::DeprecationWarning")
pytest.mark.integration = pytest.mark.filterwarnings("ignore::DeprecationWarning")
pytest.mark.slow = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for component interaction")
    config.addinivalue_line("markers", "slow: Slow tests that may take longer to run") 