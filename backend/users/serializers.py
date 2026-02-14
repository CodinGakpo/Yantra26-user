from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import is_password_usable
from .models import CustomUser
from user_profile.models import UserProfile
from .auth_errors import AuthErrorCodes, AuthErrorMessages, create_error_response
from .services import raise_if_user_deactivated

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    is_temporarily_deactivated = serializers.BooleanField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_email_verified",
            "auth_method",
            "google_id",
            "profile_picture",
            "trust_score",
            "deactivated_until",
            "is_temporarily_deactivated",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "auth_method",
            "trust_score",
            "deactivated_until",
            "is_temporarily_deactivated",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with email/password
    Supports setting password for existing OAuth users (unified identity)
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password2']

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password2']:
            error = create_error_response(
                AuthErrorCodes.PASSWORDS_DONT_MATCH,
                AuthErrorMessages.PASSWORDS_DONT_MATCH
            )
            raise serializers.ValidationError(error)
        return attrs

    def validate_email(self, value):
        """Validate email - allow existing OAuth users without passwords"""
        email = value.lower()
        
        try:
            existing_user = CustomUser.objects.get(email=email)
            # If user exists and already has a password, reject
            if existing_user.has_usable_password():
                error = create_error_response(
                    AuthErrorCodes.USER_ALREADY_EXISTS,
                    AuthErrorMessages.USER_ALREADY_EXISTS
                )
                raise serializers.ValidationError(error)
            # If user exists but no password, allow setting password (unified identity)
            # Store the user in context for create method
            self.context['existing_user'] = existing_user
        except CustomUser.DoesNotExist:
            pass  # New user, proceed normally
        
        return email

    def create(self, validated_data):
        """Create new user or set password for existing OAuth user"""
        validated_data.pop('password2')
        email = validated_data['email']
        password = validated_data['password']
        
        # Check if this is an existing OAuth user
        existing_user = self.context.get('existing_user')
        
        if existing_user:
            # Set password for existing OAuth user (unified identity)
            existing_user.set_password(password)
            existing_user.save()
            return existing_user
        else:
            # Create new user
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                auth_method='email',
                is_email_verified=False
            )
            
            UserProfile.objects.create(user=user)
            return user

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with email/password
    Handles unified identity - checks if password is set
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate user credentials with proper error codes"""
        email = attrs.get('email', '').lower()
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )

        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )

        attrs['user'] = user
        return attrs
    
class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """Validate passwords match"""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "New password fields didn't match."
            })
        return attrs

    def validate_old_password(self, value):
        """Validate old password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class SetPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting password (for OAuth users who don't have a password yet)
    Different from ChangePasswordSerializer which requires old password
    """
    password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """Validate passwords match"""
        if attrs['password'] != attrs['password2']:
            error = create_error_response(
                AuthErrorCodes.PASSWORDS_DONT_MATCH,
                AuthErrorMessages.PASSWORDS_DONT_MATCH
            )
            raise serializers.ValidationError(error)
        
        # Check if user already has a usable password
        user = self.context['request'].user
        if user.has_usable_password():
            error = create_error_response(
                AuthErrorCodes.VALIDATION_ERROR,
                "Password is already set. Use change-password endpoint to change it."
            )
            raise serializers.ValidationError(error)
        
        return attrs


class RequestOTPSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP
    Works for all users - existing and new (unified identity)
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate and normalize email - allow all emails"""
        return value.lower()


class VerifyOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying OTP and logging in
    Creates user if doesn't exist, or authenticates existing user (unified identity)
    """
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate(self, attrs):
        """Validate OTP and get or create user"""
        from .models import EmailOTP
        
        email = attrs.get('email', '').lower()
        otp = attrs.get('otp')

        # Verify OTP
        try:
            otp_obj = EmailOTP.objects.filter(
                email=email,
                otp=otp,
                is_used=False
            ).latest('created_at')
            
            if not otp_obj.is_valid():
                raise serializers.ValidationError({
                    "otp": "This code has expired. Please request a new one."
                })
            
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({
                    "email": "No account found with this email."
                })
            
            otp_obj.is_used = True
            otp_obj.save()
            
            attrs['user'] = user
            return attrs
            
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError({
                "otp": "Invalid code. Please check and try again."
            })


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        """Validate Google OAuth token from web or iOS app"""
        from google.oauth2 import id_token
        from google.auth.transport import requests
        from django.conf import settings
        
        # Try validating with web client ID first
        client_ids = [settings.GOOGLE_CLIENT_ID]
        
        # Add iOS app client ID if configured
        if hasattr(settings, 'GOOGLE_CLIENT_ID_APP') and settings.GOOGLE_CLIENT_ID_APP:
            client_ids.append(settings.GOOGLE_CLIENT_ID_APP)
        
        last_error = None
        for client_id in client_ids:
            try:
                idinfo = id_token.verify_oauth2_token(
                    value,
                    requests.Request(),
                    client_id
                )
                # Token validated successfully with this client ID
                return idinfo
                
            except ValueError as e:
                last_error = e
                continue
        
        # If we get here, token validation failed for all client IDs
        error = create_error_response(
            AuthErrorCodes.OAUTH_TOKEN_INVALID,
            f"Invalid token: {str(last_error)}"
        )
        raise serializers.ValidationError(error)
    
    def create_or_get_user(self, validated_data):
        """
        Create or get user from Google data (unified identity)
        Always looks up by email first to maintain one user per email
        """
        google_data = validated_data['token']
        
        email = google_data.get('email')
        google_id = google_data.get('sub')
        first_name = google_data.get('given_name', '')
        last_name = google_data.get('family_name', '')
        profile_picture = google_data.get('picture', '')
        
        # Unified identity: Check if user exists by email
        try:
            user = CustomUser.objects.get(email=email)
            
            # Update Google-specific fields if not already set
            updated = False
            if not user.google_id:
                user.google_id = google_id
                updated = True
            
            if not user.profile_picture:
                user.profile_picture = profile_picture
                updated = True
            
            # Mark email as verified (Google emails are verified)
            if not user.is_email_verified:
                user.is_email_verified = True
                updated = True
            
            # Update first/last name if empty
            if not user.first_name and first_name:
                user.first_name = first_name
                updated = True
            
            if not user.last_name and last_name:
                user.last_name = last_name
                updated = True
            
            if updated:
                user.save()
                
        except CustomUser.DoesNotExist:
            # Create new user
            user = CustomUser.objects.create(
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
                auth_method='google',
                is_email_verified=True,
            )
            
            UserProfile.objects.create(user=user)
        
        return user
