"""
Comprehensive test suite for unified identity authentication system
Tests Google OAuth, password, and OTP login with unified identity model
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import EmailOTP
from users.auth_errors import AuthErrorCodes
import json

User = get_user_model()


class UnifiedIdentityAuthTestCase(TestCase):
    """Test unified identity across Google OAuth, password, and OTP login"""
    
    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        self.test_email = "test@example.com"
        self.test_password = "SecurePass123!"
        self.oauth_email = "oauth@example.com"
    
    def tearDown(self):
        """Clean up after tests"""
        User.objects.all().delete()
        EmailOTP.objects.all().delete()
    
    # ========== Test 1: OAuth User Creation ==========
    def test_oauth_user_has_no_password(self):
        """Test that OAuth-created users have no usable password"""
        # Create OAuth user (simulating what GoogleAuthSerializer does)
        user = User.objects.create(
            email=self.oauth_email,
            google_id="google123",
            auth_method='google',
            is_email_verified=True
        )
        
        # Verify user has no usable password
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.is_email_verified)
        self.assertEqual(user.google_id, "google123")
    
    # ========== Test 2: Password Login for OAuth User (Should Fail) ==========
    def test_password_login_fails_for_oauth_user(self):
        """Test that password login fails with proper error for OAuth users"""
        # Create OAuth user
        user = User.objects.create(
            email=self.oauth_email,
            google_id="google123",
            auth_method='google',
            is_email_verified=True
        )
        
        # Try to login with password
        response = self.client.post('/api/users/login/', {
            'email': self.oauth_email,
            'password': self.test_password
        })
        
        # Should fail with PASSWORD_NOT_SET error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check for structured error response
        data = response.json()
        self.assertIn('code', data)
        self.assertEqual(data['code'], AuthErrorCodes.PASSWORD_NOT_SET)
        self.assertIn('message', data)
    
    # ========== Test 3: OAuth User Sets Password ==========
    def test_oauth_user_can_set_password_via_register(self):
        """Test OAuth user can set password via register endpoint (unified identity)"""
        # Create OAuth user
        user = User.objects.create(
            email=self.oauth_email,
            google_id="google123",
            auth_method='google',
            is_email_verified=True
        )
        initial_id = user.id
        
        # OAuth user sets password via register endpoint
        response = self.client.post('/api/users/register/', {
            'email': self.oauth_email,
            'password': self.test_password,
            'password2': self.test_password
        })
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify same user now has password
        user.refresh_from_db()
        self.assertEqual(user.id, initial_id)  # Same user
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password(self.test_password))
        
        # Google ID should still be there
        self.assertEqual(user.google_id, "google123")
    
    # ========== Test 4: OAuth User Login with Password After Setting ==========
    def test_oauth_user_can_login_with_password_after_setting(self):
        """Test OAuth user can login with password after setting it"""
        # Create OAuth user and set password
        user = User.objects.create(
            email=self.oauth_email,
            google_id="google123",
            auth_method='google',
            is_email_verified=True
        )
        user.set_password(self.test_password)
        user.save()
        
        # Login with password should now work
        response = self.client.post('/api/users/login/', {
            'email': self.oauth_email,
            'password': self.test_password
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('tokens', data)
        self.assertIn('access', data['tokens'])
        self.assertIn('refresh', data['tokens'])
        self.assertEqual(data['user']['email'], self.oauth_email)
    
    # ========== Test 5: Regular Email/Password Registration ==========
    def test_regular_email_password_registration(self):
        """Test normal email/password registration"""
        response = self.client.post('/api/users/register/', {
            'email': self.test_email,
            'password': self.test_password,
            'password2': self.test_password
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user created with password
        user = User.objects.get(email=self.test_email)
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password(self.test_password))
        self.assertEqual(user.auth_method, 'email')
    
    # ========== Test 6: Duplicate Registration with Password ==========
    def test_duplicate_registration_with_password_fails(self):
        """Test that registering with existing email that has password fails"""
        # Create user with password
        User.objects.create_user(
            email=self.test_email,
            password=self.test_password,
            auth_method='email'
        )
        
        # Try to register again with same email
        response = self.client.post('/api/users/register/', {
            'email': self.test_email,
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        })
        
        # Should fail with USER_ALREADY_EXISTS
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('code', data)
        self.assertEqual(data['code'], AuthErrorCodes.USER_ALREADY_EXISTS)
    
    # ========== Test 7: OTP Login for Existing User ==========
    def test_otp_login_for_existing_user(self):
        """Test OTP login works for existing users"""
        # Create user
        user = User.objects.create_user(
            email=self.test_email,
            password=self.test_password,
            auth_method='email'
        )
        
        # Request OTP
        response = self.client.post('/api/users/request-otp/', {
            'email': self.test_email
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get OTP from database
        otp_obj = EmailOTP.objects.filter(email=self.test_email).latest('created_at')
        
        # Verify OTP
        response = self.client.post('/api/users/verify-otp/', {
            'email': self.test_email,
            'otp': otp_obj.otp
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('tokens', data)
        self.assertEqual(data['user']['email'], self.test_email)
        
        # Verify it's the same user
        self.assertEqual(data['user']['id'], user.id)
    
    # ========== Test 8: OTP Login Creates New User ==========
    def test_otp_login_creates_new_user(self):
        """Test OTP login creates new user if doesn't exist (unified identity)"""
        new_email = "newuser@example.com"
        
        # Request OTP for non-existent user
        response = self.client.post('/api/users/request-otp/', {
            'email': new_email
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get OTP from database
        otp_obj = EmailOTP.objects.filter(email=new_email).latest('created_at')
        
        # Verify user doesn't exist yet
        self.assertFalse(User.objects.filter(email=new_email).exists())
        
        # Verify OTP (should create user)
        response = self.client.post('/api/users/verify-otp/', {
            'email': new_email,
            'otp': otp_obj.otp
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user was created
        user = User.objects.get(email=new_email)
        self.assertTrue(user.is_email_verified)  # OTP verifies email
        self.assertFalse(user.has_usable_password())  # No password set
    
    # ========== Test 9: OTP Login for OAuth User ==========
    def test_otp_login_works_for_oauth_user(self):
        """Test OTP login works for OAuth-created users (unified identity)"""
        # Create OAuth user
        user = User.objects.create(
            email=self.oauth_email,
            google_id="google123",
            auth_method='google',
            is_email_verified=True
        )
        initial_id = user.id
        
        # Request OTP
        response = self.client.post('/api/users/request-otp/', {
            'email': self.oauth_email
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get OTP
        otp_obj = EmailOTP.objects.filter(email=self.oauth_email).latest('created_at')
        
        # Verify OTP
        response = self.client.post('/api/users/verify-otp/', {
            'email': self.oauth_email,
            'otp': otp_obj.otp
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should authenticate same user
        self.assertEqual(data['user']['id'], initial_id)
        self.assertEqual(data['user']['email'], self.oauth_email)
        
        # Google ID should still be there
        user.refresh_from_db()
        self.assertEqual(user.google_id, "google123")
    
    # ========== Test 10: Invalid OTP ==========
    def test_invalid_otp_returns_proper_error(self):
        """Test invalid OTP returns structured error"""
        response = self.client.post('/api/users/verify-otp/', {
            'email': self.test_email,
            'otp': '999999'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('code', data)
        self.assertEqual(data['code'], AuthErrorCodes.OTP_INVALID)
    
    # ========== Test 11: Get Available Auth Methods ==========
    def test_get_available_auth_methods(self):
        """Test user can query available authentication methods"""
        # OAuth user with no password
        oauth_user = User.objects.create(
            email=self.oauth_email,
            google_id="google123",
            auth_method='google'
        )
        methods = oauth_user.get_available_auth_methods()
        self.assertIn('otp', methods)
        self.assertIn('google', methods)
        self.assertNotIn('password', methods)
        
        # OAuth user after setting password
        oauth_user.set_password(self.test_password)
        oauth_user.save()
        methods = oauth_user.get_available_auth_methods()
        self.assertIn('otp', methods)
        self.assertIn('google', methods)
        self.assertIn('password', methods)
        
        # Regular user with password
        regular_user = User.objects.create_user(
            email=self.test_email,
            password=self.test_password
        )
        methods = regular_user.get_available_auth_methods()
        self.assertIn('otp', methods)
        self.assertIn('password', methods)
        self.assertNotIn('google', methods)
    
    # ========== Test 12: Invalid Credentials Error ==========
    def test_invalid_credentials_returns_proper_error(self):
        """Test invalid credentials return structured error"""
        # Create user
        User.objects.create_user(
            email=self.test_email,
            password=self.test_password
        )
        
        # Try wrong password
        response = self.client.post('/api/users/login/', {
            'email': self.test_email,
            'password': 'WrongPassword123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('code', data)
        self.assertEqual(data['code'], AuthErrorCodes.INVALID_CREDENTIALS)


class SetPasswordEndpointTestCase(TestCase):
    """Test the set-password endpoint for OAuth users"""
    
    def setUp(self):
        self.client = APIClient()
        self.oauth_email = "oauth@example.com"
        self.test_password = "SecurePass123!"
    
    def test_oauth_user_can_set_password(self):
        """Test OAuth user can set password via authenticated endpoint"""
        # Create OAuth user
        user = User.objects.create(
            email=self.oauth_email,
            google_id="google123",
            auth_method='google',
            is_email_verified=True
        )
        
        # Authenticate client
        self.client.force_authenticate(user=user)
        
        # Set password
        response = self.client.post('/api/users/set-password/', {
            'password': self.test_password,
            'password2': self.test_password
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was set
        user.refresh_from_db()
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password(self.test_password))
    
    def test_set_password_fails_if_password_already_set(self):
        """Test set-password fails if user already has a password"""
        # Create user with password
        user = User.objects.create_user(
            email=self.oauth_email,
            password='ExistingPass123!'
        )
        
        # Authenticate client
        self.client.force_authenticate(user=user)
        
        # Try to set password
        response = self.client.post('/api/users/set-password/', {
            'password': self.test_password,
            'password2': self.test_password
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('code', data)


def run_all_tests():
    """Helper function to run all tests"""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(UnifiedIdentityAuthTestCase))
    suite.addTests(loader.loadTestsFromTestCase(SetPasswordEndpointTestCase))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    run_all_tests()
