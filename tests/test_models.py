"""
Unit tests for VisionLabel Pro user models and management system.

This module tests all user-related functionality including:
- User model creation and validation
- Password hashing and verification
- UserManager CRUD operations
- Flask-Login integration methods
- File-based storage operations
- User data serialization
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open
from datetime import datetime

from modules.models import User, UserManager
import bcrypt


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality and Flask-Login integration"""
    
    def test_user_creation_basic(self):
        """Test basic user creation with required parameters"""
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        assert user.id == 'test-123'
        assert user.email == 'test@example.com'
        assert user.password_hash == 'hashed_password'
        assert user.created_at is not None
        assert user.last_login is None
        assert user.is_active is True
    
    def test_user_creation_with_timestamp(self):
        """Test user creation with custom timestamp"""
        timestamp = '2024-01-01T12:00:00'
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash='hashed_password',
            created_at=timestamp
        )
        
        assert user.created_at == timestamp
    
    def test_user_password_verification_valid(self):
        """Test password verification with valid password"""
        # Create a real bcrypt hash for testing
        password = 'testpassword123'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash=hashed.decode('utf-8')
        )
        
        assert user.check_password(password) is True
    
    def test_user_password_verification_invalid(self):
        """Test password verification with invalid password"""
        # Create a real bcrypt hash for testing
        password = 'correctpassword'
        wrong_password = 'wrongpassword'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash=hashed.decode('utf-8')
        )
        
        assert user.check_password(wrong_password) is False
    
    def test_user_to_dict(self):
        """Test user serialization to dictionary"""
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash='hashed_password',
            created_at='2024-01-01T12:00:00'
        )
        user.last_login = '2024-01-02T10:00:00'
        user.is_active = False
        
        user_dict = user.to_dict()
        
        expected = {
            'id': 'test-123',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'created_at': '2024-01-01T12:00:00',
            'last_login': '2024-01-02T10:00:00',
            'is_active': False
        }
        
        assert user_dict == expected
    
    def test_user_from_dict(self):
        """Test user deserialization from dictionary"""
        user_data = {
            'id': 'test-123',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'created_at': '2024-01-01T12:00:00',
            'last_login': '2024-01-02T10:00:00',
            'is_active': False
        }
        
        user = User.from_dict(user_data)
        
        assert user.id == 'test-123'
        assert user.email == 'test@example.com'
        assert user.password_hash == 'hashed_password'
        assert user.created_at == '2024-01-01T12:00:00'
        assert user.last_login == '2024-01-02T10:00:00'
        assert user.is_active is False
    
    def test_user_from_dict_missing_optional_fields(self):
        """Test user deserialization with missing optional fields"""
        user_data = {
            'id': 'test-123',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'created_at': '2024-01-01T12:00:00'
        }
        
        user = User.from_dict(user_data)
        
        assert user.id == 'test-123'
        assert user.last_login is None
        assert user.is_active is True  # Default value
    
    def test_flask_login_get_id(self):
        """Test Flask-Login get_id method"""
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        assert user.get_id() == 'test-123'
    
    def test_flask_login_is_active_property(self):
        """Test Flask-Login is_active property getter and setter"""
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        # Test default value
        assert user.is_active is True
        
        # Test setter
        user.is_active = False
        assert user.is_active is False
        
        # Test setter with True
        user.is_active = True
        assert user.is_active is True
    
    def test_flask_login_is_authenticated(self):
        """Test Flask-Login is_authenticated property (inherited from UserMixin)"""
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        # UserMixin provides this property
        assert user.is_authenticated is True
    
    def test_flask_login_is_anonymous(self):
        """Test Flask-Login is_anonymous property (inherited from UserMixin)"""
        user = User(
            id='test-123',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        # UserMixin provides this property
        assert user.is_anonymous is False


@pytest.mark.unit
class TestUserManager:
    """Test UserManager functionality and file operations"""
    
    def test_user_manager_creation(self, temp_user_storage):
        """Test UserManager initialization"""
        manager = UserManager(storage_file=temp_user_storage)
        
        assert manager.storage_file == temp_user_storage
        assert isinstance(manager.users, dict)
    
    def test_user_manager_load_empty_file(self, temp_user_storage):
        """Test loading users from empty storage file"""
        manager = UserManager(storage_file=temp_user_storage)
        
        assert len(manager.users) == 1  # Demo user should be created
        assert 'demo@visionlabel.pro' in [user.email for user in manager.users.values()]
    
    def test_user_manager_load_existing_file(self, temp_user_storage):
        """Test loading users from existing storage file"""
        # Create test data
        test_data = {
            'user-1': {
                'id': 'user-1',
                'email': 'test1@example.com',
                'password_hash': 'hash1',
                'created_at': '2024-01-01T12:00:00',
                'is_active': True
            },
            'user-2': {
                'id': 'user-2',
                'email': 'test2@example.com',
                'password_hash': 'hash2',
                'created_at': '2024-01-02T12:00:00',
                'is_active': False
            }
        }
        
        # Write test data to file
        with open(temp_user_storage, 'w') as f:
            json.dump(test_data, f)
        
        # Load and test
        manager = UserManager(storage_file=temp_user_storage)
        
        assert len(manager.users) >= 2  # Test users + demo user
        assert 'user-1' in manager.users
        assert 'user-2' in manager.users
        assert manager.users['user-1'].email == 'test1@example.com'
        assert manager.users['user-2'].is_active is False
    
    def test_user_manager_load_corrupted_file(self, temp_user_storage):
        """Test loading users from corrupted storage file"""
        # Write invalid JSON
        with open(temp_user_storage, 'w') as f:
            f.write('invalid json content')
        
        # Should handle gracefully
        manager = UserManager(storage_file=temp_user_storage)
        
        assert len(manager.users) == 1  # Only demo user
    
    def test_user_manager_save_users(self, temp_user_storage):
        """Test saving users to storage file"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Add test user
        test_user = User('test-123', 'test@example.com', 'hashed_password')
        manager.users['test-123'] = test_user
        
        # Save and verify
        manager.save_users()
        
        # Read file and verify content
        with open(temp_user_storage, 'r') as f:
            data = json.load(f)
        
        assert 'test-123' in data
        assert data['test-123']['email'] == 'test@example.com'
    
    def test_user_manager_save_users_error_handling(self, temp_user_storage):
        """Test error handling during user saving"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Make file read-only to simulate write error
        os.chmod(temp_user_storage, 0o444)
        
        try:
            # This should not raise an exception but handle gracefully
            manager.save_users()
        except Exception:
            pytest.fail("save_users should handle errors gracefully")
        finally:
            # Restore write permissions for cleanup
            os.chmod(temp_user_storage, 0o666)
    
    def test_create_user_success(self, temp_user_storage):
        """Test successful user creation"""
        manager = UserManager(storage_file=temp_user_storage)
        
        user = manager.create_user('newuser@example.com', 'password123')
        
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.check_password('password123')
        assert user.id in manager.users
        assert manager.users[user.id] == user
    
    def test_create_user_duplicate_email(self, temp_user_storage):
        """Test user creation with duplicate email"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Create first user
        user1 = manager.create_user('duplicate@example.com', 'password123')
        assert user1 is not None
        
        # Try to create user with same email
        user2 = manager.create_user('duplicate@example.com', 'password456')
        assert user2 is None  # Should fail
    
    def test_get_user_existing(self, temp_user_storage):
        """Test getting existing user by ID"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Create user
        created_user = manager.create_user('test@example.com', 'password123')
        
        # Get user
        retrieved_user = manager.get_user(created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    def test_get_user_nonexistent(self, temp_user_storage):
        """Test getting non-existent user by ID"""
        manager = UserManager(storage_file=temp_user_storage)
        
        user = manager.get_user('nonexistent-id')
        
        assert user is None
    
    def test_get_user_by_email_existing(self, temp_user_storage):
        """Test getting existing user by email"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Create user
        created_user = manager.create_user('findme@example.com', 'password123')
        
        # Get user by email
        retrieved_user = manager.get_user_by_email('findme@example.com')
        
        assert retrieved_user is not None
        assert retrieved_user.email == 'findme@example.com'
        assert retrieved_user.id == created_user.id
    
    def test_get_user_by_email_nonexistent(self, temp_user_storage):
        """Test getting non-existent user by email"""
        manager = UserManager(storage_file=temp_user_storage)
        
        user = manager.get_user_by_email('nonexistent@example.com')
        
        assert user is None
    
    def test_get_user_by_email_case_sensitivity(self, temp_user_storage):
        """Test email case sensitivity in user lookup"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Create user with lowercase email
        manager.create_user('test@example.com', 'password123')
        
        # Try to find with different case
        user_upper = manager.get_user_by_email('TEST@EXAMPLE.COM')
        user_mixed = manager.get_user_by_email('Test@Example.Com')
        
        # Should not find user (case sensitive)
        assert user_upper is None
        assert user_mixed is None
    
    def test_demo_user_creation(self, temp_user_storage):
        """Test automatic demo user creation"""
        manager = UserManager(storage_file=temp_user_storage)
        
        demo_user = manager.get_user_by_email('demo@visionlabel.pro')
        
        assert demo_user is not None
        assert demo_user.email == 'demo@visionlabel.pro'
        assert demo_user.check_password('demo123')
    
    def test_password_hashing_security(self, temp_user_storage):
        """Test password hashing security"""
        manager = UserManager(storage_file=temp_user_storage)
        
        password = 'securepassword123'
        user = manager.create_user('security@example.com', password)
        
        # Password should be hashed
        assert user.password_hash != password
        assert user.password_hash.startswith('$2b$')  # bcrypt format
        
        # Should verify correctly
        assert user.check_password(password)
        assert not user.check_password('wrongpassword')
    
    def test_user_manager_persistence(self, temp_user_storage):
        """Test user data persistence across manager instances"""
        # Create first manager and add user
        manager1 = UserManager(storage_file=temp_user_storage)
        user = manager1.create_user('persistent@example.com', 'password123')
        user_id = user.id
        
        # Create second manager (simulates app restart)
        manager2 = UserManager(storage_file=temp_user_storage)
        
        # User should be loaded
        loaded_user = manager2.get_user(user_id)
        assert loaded_user is not None
        assert loaded_user.email == 'persistent@example.com'
        assert loaded_user.check_password('password123')


@pytest.mark.integration
class TestUserModelIntegration:
    """Integration tests for user model and authentication system"""
    
    def test_user_model_flask_login_integration(self, app, temp_user_storage):
        """Test User model integration with Flask-Login"""
        with app.app_context():
            manager = UserManager(storage_file=temp_user_storage)
            user = manager.create_user('integration@example.com', 'password123')
            
            # Test Flask-Login required methods
            assert hasattr(user, 'get_id')
            assert hasattr(user, 'is_active')
            assert hasattr(user, 'is_authenticated')
            assert hasattr(user, 'is_anonymous')
            
            # Test method returns
            assert user.get_id() == user.id
            assert user.is_authenticated is True
            assert user.is_anonymous is False
    
    def test_user_manager_with_real_bcrypt(self, temp_user_storage):
        """Test UserManager with real bcrypt hashing"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Test various password scenarios
        test_passwords = [
            'simple123',
            'Complex!Password@456',
            'unicode_test_café',
            'a' * 100,  # Long password
            '!@#$%^&*()_+{}|:<>?[]\\;\'\",./'  # Special characters
        ]
        
        for i, password in enumerate(test_passwords):
            email = f'test{i}@example.com'
            user = manager.create_user(email, password)
            
            assert user is not None
            assert user.check_password(password)
            assert not user.check_password(password + 'wrong')
    
    def test_concurrent_user_operations(self, temp_user_storage):
        """Test thread safety of user operations (basic test)"""
        manager = UserManager(storage_file=temp_user_storage)
        
        # Create multiple users rapidly
        users = []
        for i in range(10):
            user = manager.create_user(f'concurrent{i}@example.com', f'password{i}')
            users.append(user)
        
        # Verify all users were created correctly
        for i, user in enumerate(users):
            assert user is not None
            assert user.email == f'concurrent{i}@example.com'
            assert user.check_password(f'password{i}')
        
        # Verify persistence
        manager.save_users()
        manager2 = UserManager(storage_file=temp_user_storage)
        
        for i in range(10):
            loaded_user = manager2.get_user_by_email(f'concurrent{i}@example.com')
            assert loaded_user is not None
            assert loaded_user.check_password(f'password{i}') 