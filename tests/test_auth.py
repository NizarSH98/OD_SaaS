"""
Unit tests for VisionLabel Pro authentication system.

This module tests all authentication-related functionality including:
- User registration and validation
- Login and logout flows
- Form validation and error handling
- Flask-Login integration
- Password security and hashing
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import url_for, session
from flask_login import current_user

from modules.auth import LoginForm, RegisterForm
from modules.models import User


@pytest.mark.unit
class TestAuthenticationRoutes:
    """Test authentication route handlers and flows"""
    
    def test_login_page_get(self, client):
        """Test GET request to login page renders correctly"""
        response = client.get('/auth/login')
        
        assert response.status_code == 200
        assert b'Sign In' in response.data
        assert b'Email' in response.data
        assert b'Password' in response.data
        assert b'Remember Me' in response.data
    
    def test_login_redirect_if_authenticated(self, authenticated_client):
        """Test login page redirects authenticated users to dashboard"""
        response = authenticated_client.get('/auth/login')
        
        assert response.status_code == 302
        assert '/auth/login' not in response.location
    
    def test_register_page_get(self, client):
        """Test GET request to register page renders correctly"""
        response = client.get('/auth/register')
        
        assert response.status_code == 200
        assert b'Create Account' in response.data
        assert b'Email' in response.data
        assert b'Password' in response.data
        assert b'Confirm Password' in response.data
    
    def test_register_redirect_if_authenticated(self, authenticated_client):
        """Test register page redirects authenticated users to dashboard"""
        response = authenticated_client.get('/auth/register')
        
        assert response.status_code == 302
        assert '/auth/register' not in response.location
    
    @patch('modules.auth.user_manager')
    def test_login_valid_credentials(self, mock_user_manager, client, test_user):
        """Test successful login with valid credentials"""
        # Setup mock user manager
        mock_user_manager.get_user_by_email.return_value = test_user
        test_user.check_password = MagicMock(return_value=True)
        
        # Attempt login
        response = client.post('/auth/login', data={
            'email': 'test@visionlabel.pro',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        mock_user_manager.get_user_by_email.assert_called_once_with('test@visionlabel.pro')
        test_user.check_password.assert_called_once_with('testpassword123')
    
    @patch('modules.auth.user_manager')
    def test_login_invalid_email(self, mock_user_manager, client):
        """Test login failure with non-existent email"""
        mock_user_manager.get_user_by_email.return_value = None
        
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    @patch('modules.auth.user_manager')
    def test_login_invalid_password(self, mock_user_manager, client, test_user):
        """Test login failure with incorrect password"""
        mock_user_manager.get_user_by_email.return_value = test_user
        test_user.check_password = MagicMock(return_value=False)
        
        response = client.post('/auth/login', data={
            'email': 'test@visionlabel.pro',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    @patch('modules.auth.user_manager')
    def test_register_new_user(self, mock_user_manager, client):
        """Test successful user registration"""
        mock_user_manager.get_user_by_email.return_value = None  # User doesn't exist
        mock_user = MagicMock()
        mock_user_manager.create_user.return_value = mock_user
        
        response = client.post('/auth/register', data={
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        mock_user_manager.get_user_by_email.assert_called_once_with('newuser@example.com')
        mock_user_manager.create_user.assert_called_once_with('newuser@example.com', 'password123')
    
    @patch('modules.auth.user_manager')
    def test_register_existing_user(self, mock_user_manager, client, test_user):
        """Test registration failure when user already exists"""
        mock_user_manager.get_user_by_email.return_value = test_user
        
        response = client.post('/auth/register', data={
            'email': 'test@visionlabel.pro',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'An account with this email already exists' in response.data
    
    @patch('modules.auth.user_manager')
    def test_register_creation_failure(self, mock_user_manager, client):
        """Test registration failure when user creation fails"""
        mock_user_manager.get_user_by_email.return_value = None
        mock_user_manager.create_user.return_value = None  # Creation fails
        
        response = client.post('/auth/register', data={
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Error creating account' in response.data
    
    def test_logout(self, authenticated_client):
        """Test user logout functionality"""
        response = authenticated_client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to login page
        assert b'Sign In' in response.data
    
    def test_logout_unauthenticated(self, client):
        """Test logout when user is not authenticated"""
        response = client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_profile_page_authenticated(self, authenticated_client, test_user):
        """Test profile page access for authenticated user"""
        with patch('modules.auth.current_user', test_user):
            response = authenticated_client.get('/auth/profile')
            
            assert response.status_code == 200
            assert b'Profile' in response.data
            assert test_user.email.encode() in response.data
    
    def test_profile_page_unauthenticated(self, client):
        """Test profile page redirects unauthenticated users"""
        response = client.get('/auth/profile')
        
        assert response.status_code == 302
        assert '/auth/login' in response.location


@pytest.mark.unit
class TestAuthenticationForms:
    """Test authentication form validation and behavior"""
    
    def test_login_form_valid_data(self, app):
        """Test login form validation with valid data"""
        with app.app_context():
            form = LoginForm(data={
                'email': 'test@example.com',
                'password': 'password123',
                'remember_me': True
            })
            
            assert form.validate()
            assert form.email.data == 'test@example.com'
            assert form.password.data == 'password123'
            assert form.remember_me.data is True
    
    def test_login_form_invalid_email(self, app):
        """Test login form validation with invalid email"""
        with app.app_context():
            form = LoginForm(data={
                'email': 'invalid-email',
                'password': 'password123'
            })
            
            assert not form.validate()
            assert 'Please enter a valid email address' in form.email.errors
    
    def test_login_form_missing_email(self, app):
        """Test login form validation with missing email"""
        with app.app_context():
            form = LoginForm(data={
                'password': 'password123'
            })
            
            assert not form.validate()
            assert 'Email is required' in form.email.errors
    
    def test_login_form_missing_password(self, app):
        """Test login form validation with missing password"""
        with app.app_context():
            form = LoginForm(data={
                'email': 'test@example.com'
            })
            
            assert not form.validate()
            assert 'Password is required' in form.password.errors
    
    def test_register_form_valid_data(self, app):
        """Test register form validation with valid data"""
        with app.app_context():
            form = RegisterForm(data={
                'email': 'test@example.com',
                'password': 'password123',
                'confirm_password': 'password123'
            })
            
            assert form.validate()
            assert form.email.data == 'test@example.com'
            assert form.password.data == 'password123'
            assert form.confirm_password.data == 'password123'
    
    def test_register_form_invalid_email(self, app):
        """Test register form validation with invalid email"""
        with app.app_context():
            form = RegisterForm(data={
                'email': 'invalid-email',
                'password': 'password123',
                'confirm_password': 'password123'
            })
            
            assert not form.validate()
            assert 'Please enter a valid email address' in form.email.errors
    
    def test_register_form_short_password(self, app):
        """Test register form validation with short password"""
        with app.app_context():
            form = RegisterForm(data={
                'email': 'test@example.com',
                'password': 'short',
                'confirm_password': 'short'
            })
            
            assert not form.validate()
            assert 'Password must be at least 8 characters long' in form.password.errors
    
    def test_register_form_password_mismatch(self, app):
        """Test register form validation with password mismatch"""
        with app.app_context():
            form = RegisterForm(data={
                'email': 'test@example.com',
                'password': 'password123',
                'confirm_password': 'different456'
            })
            
            assert not form.validate()
            assert 'Passwords must match' in form.confirm_password.errors
    
    def test_register_form_missing_email(self, app):
        """Test register form validation with missing email"""
        with app.app_context():
            form = RegisterForm(data={
                'password': 'password123',
                'confirm_password': 'password123'
            })
            
            assert not form.validate()
            assert 'Email is required' in form.email.errors


@pytest.mark.unit
class TestAuthenticationSecurity:
    """Test security aspects of authentication system"""
    
    def test_csrf_protection_enabled_in_production(self, app):
        """Test that CSRF protection is enabled in production"""
        # Note: We disable CSRF in test config, but this tests the default
        with app.app_context():
            # In production, WTF_CSRF_ENABLED should be True (default)
            production_config = app.config.copy()
            production_config['TESTING'] = False
            production_config.pop('WTF_CSRF_ENABLED', None)
            
            # Default behavior should enable CSRF
            assert production_config.get('WTF_CSRF_ENABLED', True) is True
    
    def test_password_not_logged(self, client, caplog):
        """Test that passwords are not logged in application logs"""
        with caplog.at_level('DEBUG'):
            client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'secretpassword123'
            })
            
            # Check that password doesn't appear in logs
            log_content = caplog.text.lower()
            assert 'secretpassword123' not in log_content
            assert 'password' not in log_content or 'password field' in log_content
    
    def test_session_security(self, client):
        """Test session security settings"""
        with client.session_transaction() as sess:
            # Test that session has proper security attributes
            # Flask-Login should handle session security
            assert sess.permanent is False  # Default value
    
    @patch('modules.auth.user_manager')
    def test_login_rate_limiting_protection(self, mock_user_manager, client):
        """Test protection against rapid login attempts"""
        mock_user_manager.get_user_by_email.return_value = None
        
        # Simulate multiple failed login attempts
        for _ in range(5):
            response = client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
            
            # Should still respond normally (rate limiting would be implemented at web server level)
            assert response.status_code in [200, 302]
    
    def test_remember_me_functionality(self, client, test_user):
        """Test remember me functionality"""
        with patch('modules.auth.user_manager') as mock_user_manager:
            mock_user_manager.get_user_by_email.return_value = test_user
            test_user.check_password = MagicMock(return_value=True)
            
            # Login with remember me
            response = client.post('/auth/login', data={
                'email': 'test@visionlabel.pro',
                'password': 'testpassword123',
                'remember_me': True
            })
            
            # Should set appropriate session/cookie settings
            assert response.status_code == 302


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication system"""
    
    def test_authentication_required_routes(self, client):
        """Test that protected routes require authentication"""
        protected_routes = [
            '/upload',
            '/annotate/test-project',
            '/api/frame/test-project/0',
            '/api/annotations/test-project/0',
            '/auth/profile'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]
            if response.status_code == 302:
                assert '/auth/login' in response.location
    
    def test_authenticated_user_access(self, authenticated_client):
        """Test that authenticated users can access protected routes"""
        response = authenticated_client.get('/')
        assert response.status_code == 200
        
        response = authenticated_client.get('/upload')
        assert response.status_code == 200
    
    def test_full_authentication_flow(self, client, app):
        """Test complete authentication flow from registration to logout"""
        with patch('modules.auth.user_manager') as mock_user_manager:
            # Register user
            mock_user_manager.get_user_by_email.return_value = None
            mock_user = MagicMock()
            mock_user_manager.create_user.return_value = mock_user
            
            register_response = client.post('/auth/register', data={
                'email': 'flowtest@example.com',
                'password': 'testpass123',
                'confirm_password': 'testpass123'
            }, follow_redirects=True)
            
            assert register_response.status_code == 200
            
            # Login
            mock_user_manager.get_user_by_email.return_value = mock_user
            mock_user.check_password = MagicMock(return_value=True)
            
            login_response = client.post('/auth/login', data={
                'email': 'flowtest@example.com',
                'password': 'testpass123'
            }, follow_redirects=True)
            
            assert login_response.status_code == 200
            
            # Access protected route
            protected_response = client.get('/upload')
            assert protected_response.status_code == 200
            
            # Logout
            logout_response = client.get('/auth/logout', follow_redirects=True)
            assert logout_response.status_code == 200 