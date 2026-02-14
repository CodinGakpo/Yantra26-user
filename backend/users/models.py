from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string

class CustomUserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        
        if 'username' not in extra_fields or not extra_fields.get('username'):
            extra_fields['username'] = email.split('@')[0]
            base_username = extra_fields['username']
            counter = 1
            while self.model.objects.filter(username=extra_fields['username']).exists():
                extra_fields['username'] = f"{base_username}{counter}"
                counter += 1
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):

    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(max_length=500, null=True, blank=True)
    
    AUTH_METHOD_CHOICES = [
        ('email', 'Email/JWT'),
        ('google', 'Google OAuth'),
    ]
    auth_method = models.CharField(
        max_length=10, 
        choices=AUTH_METHOD_CHOICES, 
        default='email',
        help_text='Primary authentication method used for account creation'
    )
    
    # Trust score system
    trust_score = models.IntegerField(default=100, help_text='User trust score (0-110)')
    deactivated_until = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text='User is temporarily deactivated until this time'
    )
    
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    def has_usable_password(self):
        """Check if user has set a usable password"""
        from django.contrib.auth.hashers import is_password_usable
        return is_password_usable(self.password)
    
    @property
    def is_temporarily_deactivated(self):
        """Check if user is currently deactivated"""
        if not self.deactivated_until:
            return False
        return timezone.now() < self.deactivated_until
    
    def get_available_auth_methods(self):
        """Get list of available authentication methods for this user"""
        methods = ['otp']  # OTP is always available
        
        if self.has_usable_password():
            methods.append('password')
        
        if self.google_id:
            methods.append('google')
        
        return methods

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='user',
    )

    def __str__(self):
        return self.email


class EmailOTP(models.Model):
    """Model to store email OTP for authentication"""
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @classmethod
    def generate_otp(cls, email):
        """Generate a new 6-digit OTP"""
        otp = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)
        
        cls.objects.filter(email=email, is_used=False).update(is_used=True)
        
        otp_obj = cls.objects.create(
            email=email,
            otp=otp,
            expires_at=expires_at
        )
        return otp_obj


class TrustScoreLog(models.Model):
    """Immutable audit log for trust score changes"""
    
    APPEAL_NOT_APPEALED = 'not_appealed'
    APPEAL_PENDING = 'pending'
    APPEAL_APPROVED = 'approved'
    APPEAL_REJECTED = 'rejected'
    
    APPEAL_STATUS_CHOICES = [
        (APPEAL_NOT_APPEALED, 'Not Appealed'),
        (APPEAL_PENDING, 'Appeal Pending'),
        (APPEAL_APPROVED, 'Appeal Approved'),
        (APPEAL_REJECTED, 'Appeal Rejected'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='trust_score_logs'
    )
    delta = models.IntegerField(help_text='Change in trust score (can be negative)')
    reason = models.TextField(help_text='Reason for trust score change')
    report = models.ForeignKey(
        'report.IssueReport',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Associated report if applicable'
    )
    appeal_status = models.CharField(
        max_length=20,
        choices=APPEAL_STATUS_CHOICES,
        default=APPEAL_NOT_APPEALED
    )
    admin_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='Admin user ID who made the change'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Trust Score Log'
        verbose_name_plural = 'Trust Score Logs'
    
    def __str__(self):
        return f"{self.user.email} - {self.delta:+d} ({self.reason[:50]})"
