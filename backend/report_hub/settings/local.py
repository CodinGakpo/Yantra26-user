from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Use SQLite for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Use MySQL for production (uncomment below and comment SQLite above)
# DATABASES = {
#     "default": {
#         "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.mysql"),
#         "NAME": os.getenv("DB_NAME"),
#         "USER": os.getenv("DB_USER"),
#         "PASSWORD": os.getenv("DB_PASSWORD"),
#         "HOST": os.getenv("DB_HOST"),
#         "PORT": os.getenv("DB_PORT", "3306"),
#         "OPTIONS": {
#             "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
#             "charset": "utf8mb4",
#         },
#     }
# }
# ============ Import Blockchain Settings ============
# Import blockchain settings from backend root
import sys
from pathlib import Path
backend_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))

try:
    from blockchain_settings import *
    
    # Override Celery settings for local development
    # Run tasks synchronously without Redis for hackathon demo reliability
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
    print("✅ Celery configured in EAGER mode (synchronous) for local development")
    print("   Tasks will execute immediately without Redis")
    
except ImportError:
    # If blockchain_settings doesn't exist, define minimal required settings
    BLOCKCHAIN_ENABLED = False
    BLOCKCHAIN_NODE_URL = ''
    BLOCKCHAIN_CONTRACT_ADDRESS = ''
    BLOCKCHAIN_CONTRACT_ABI_PATH = str(BASE_DIR / 'blockchain/contracts/build/ComplaintRegistry_abi.json')
    BLOCKCHAIN_PRIVATE_KEY = ''
    BLOCKCHAIN_GAS_LIMIT = 500000
    BLOCKCHAIN_GAS_PRICE_MULTIPLIER = 1.1
    BLOCKCHAIN_TX_TIMEOUT = 120
    BLOCKCHAIN_USE_POA = False
    BLOCKCHAIN_EXPLORER_URL = 'https://etherscan.io'
    
    # Local file storage
    LOCAL_FILE_UPLOAD_DIR = str(BASE_DIR / 'media/uploads')
    
    # Celery (optional)
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
    # SLA config
    COMPLAINT_SLA_HOURS = 48
