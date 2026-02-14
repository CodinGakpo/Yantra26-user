"""
Authentication error codes and messages for consistent error handling
"""

class AuthErrorCodes:
    """Error codes for authentication failures"""
    
    # User-related errors
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_INACTIVE = "USER_INACTIVE"
    
    # Password-related errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    PASSWORD_NOT_SET = "PASSWORD_NOT_SET"
    PASSWORDS_DONT_MATCH = "PASSWORDS_DONT_MATCH"
    PASSWORD_TOO_WEAK = "PASSWORD_TOO_WEAK"
    
    # OTP-related errors
    OTP_INVALID = "OTP_INVALID"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_SEND_FAILED = "OTP_SEND_FAILED"
    
    # OAuth-related errors
    OAUTH_TOKEN_INVALID = "OAUTH_TOKEN_INVALID"
    
    # General errors
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class AuthErrorMessages:
    """Default error messages for authentication failures"""
    
    USER_NOT_FOUND = "No account found with this email address."
    USER_ALREADY_EXISTS = "An account with this email already exists."
    USER_INACTIVE = "This account has been deactivated."
    
    INVALID_CREDENTIALS = "Invalid email or password."
    PASSWORD_NOT_SET = "Password login is not available for this account. Please use Google login or request an OTP."
    PASSWORDS_DONT_MATCH = "Passwords do not match."
    PASSWORD_TOO_WEAK = "Password does not meet security requirements."
    
    OTP_INVALID = "The code you entered is invalid. Please check and try again."
    OTP_EXPIRED = "This code has expired. Please request a new one."
    OTP_SEND_FAILED = "Failed to send verification code. Please try again."
    
    OAUTH_TOKEN_INVALID = "Invalid authentication token."
    
    MISSING_REQUIRED_FIELD = "Required field is missing."
    VALIDATION_ERROR = "Validation failed."


def create_error_response(code, message=None, field=None):
    """
    Create a standardized error response
    
    Args:
        code: Error code from AuthErrorCodes
        message: Custom message (optional, uses default if not provided)
        field: Specific field the error applies to (optional)
    
    Returns:
        dict: Standardized error response
    """
    if message is None:
        message = getattr(AuthErrorMessages, code, AuthErrorMessages.VALIDATION_ERROR)
    
    response = {
        "code": code,
        "message": message
    }
    
    if field:
        response["field"] = field
    
    return response
