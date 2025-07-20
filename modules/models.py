"""
User models and authentication system for VisionLabel Pro
Simple in-memory user storage for demonstration purposes
"""

import bcrypt
from flask_login import UserMixin
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Optional, List

class User(UserMixin):
    """User model with Flask-Login integration"""
    
    def __init__(self, id: str, email: str, password_hash: str, created_at: str = None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.last_login = None
        self._is_active = True
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches user's password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary for storage"""
        return {
            'id': self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self._is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        user = cls(data['id'], data['email'], data['password_hash'], data['created_at'])
        user.last_login = data.get('last_login')
        user._is_active = data.get('is_active', True)
        return user
    
    def get_id(self) -> str:
        """Required by Flask-Login"""
        return self.id
    
    @property
    def is_active(self) -> bool:
        """Required by Flask-Login"""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        """Setter for is_active"""
        self._is_active = value

class UserManager:
    """Simple user management system with file-based storage"""
    
    def __init__(self, storage_file: str = 'users.json'):
        self.storage_file = storage_file
        self.users: Dict[str, User] = {}
        self.load_users()
        self.ensure_demo_user()
    
    def load_users(self):
        """Load users from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.users = {
                        user_id: User.from_dict(user_data) 
                        for user_id, user_data in data.items()
                    }
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading users: {e}")
                self.users = {}
    
    def save_users(self):
        """Save users to storage file"""
        try:
            data = {user_id: user.to_dict() for user_id, user in self.users.items()}
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def ensure_demo_user(self):
        """Ensure demo user exists for testing"""
        demo_email = "demo@visionlabel.pro"
        if not self.get_user_by_email(demo_email):
            self.create_user(demo_email, "demo123")
    
    def create_user(self, email: str, password: str) -> Optional[User]:
        """Create a new user"""
        if self.get_user_by_email(email):
            return None  # User already exists
        
        # Generate user ID
        user_id = f"user_{len(self.users) + 1:04d}"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = User(user_id, email, password_hash)
        self.users[user_id] = user
        self.save_users()
        
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if user and user.check_password(password) and user.is_active:
            # Update last login
            user.last_login = datetime.utcnow().isoformat()
            self.save_users()
            return user
        return None
    
    def update_user_login(self, user_id: str):
        """Update user's last login timestamp"""
        user = self.get_user(user_id)
        if user:
            user.last_login = datetime.utcnow().isoformat()
            self.save_users()
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        return list(self.users.values())
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user"""
        user = self.get_user(user_id)
        if user:
            user._is_active = False
            self.save_users()
            return True
        return False
    
    def activate_user(self, user_id: str) -> bool:
        """Activate a user"""
        user = self.get_user(user_id)
        if user:
            user._is_active = True
            self.save_users()
            return True
        return False

# Global user manager instance
user_manager = UserManager() 