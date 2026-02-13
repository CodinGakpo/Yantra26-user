"""
Django Settings for Blockchain Integration

Add these settings to your settings.py or create a new blockchain_settings.py
"""

import os
from pathlib import Path

# Get BASE_DIR if it exists, otherwise compute it
try:
    # BASE_DIR should be set by base.py before this import
    BASE_DIR
except NameError:
    # Fallback: compute BASE_DIR relative to this file
    BASE_DIR = Path(__file__).resolve().parent

# ============ Blockchain Configuration ============

# Enable/disable blockchain features
BLOCKCHAIN_ENABLED = os.getenv('BLOCKCHAIN_ENABLED', 'true').lower() == 'true'

# Amazon Managed Blockchain connection
BLOCKCHAIN_NODE_URL = os.getenv('BLOCKCHAIN_NODE_URL', '')
BLOCKCHAIN_WS_URL = os.getenv('BLOCKCHAIN_WS_URL', '')

# Smart Contract
BLOCKCHAIN_CONTRACT_ADDRESS = os.getenv('BLOCKCHAIN_CONTRACT_ADDRESS', '')
BLOCKCHAIN_CONTRACT_ABI_PATH = os.getenv(
    'BLOCKCHAIN_CONTRACT_ABI_PATH',
    str(Path(BASE_DIR) / 'blockchain/contracts/build/ComplaintRegistry_abi.json')
)

# Private Key (use AWS Secrets Manager in production)
BLOCKCHAIN_PRIVATE_KEY = os.getenv('BLOCKCHAIN_PRIVATE_KEY', '')

# Gas Configuration
BLOCKCHAIN_GAS_LIMIT = int(os.getenv('BLOCKCHAIN_GAS_LIMIT', '500000'))
BLOCKCHAIN_GAS_PRICE_MULTIPLIER = float(os.getenv('BLOCKCHAIN_GAS_PRICE_MULTIPLIER', '1.1'))
BLOCKCHAIN_TX_TIMEOUT = int(os.getenv('BLOCKCHAIN_TX_TIMEOUT', '120'))

# Proof of Authority
BLOCKCHAIN_USE_POA = os.getenv('BLOCKCHAIN_USE_POA', 'false').lower() == 'true'

# Explorer URL
BLOCKCHAIN_EXPLORER_URL = os.getenv('BLOCKCHAIN_EXPLORER_URL', 'https://etherscan.io')

# ============ Local File Storage Configuration ============

# Local file upload directory for evidence files (replaces IPFS)
LOCAL_FILE_UPLOAD_DIR = os.getenv('LOCAL_FILE_UPLOAD_DIR', str(Path(BASE_DIR) / 'media/uploads'))

# Media files configuration (for Django to serve uploaded files)
MEDIA_ROOT = os.getenv('MEDIA_ROOT', str(Path(BASE_DIR) / 'media'))
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')

# ============ Celery Configuration ============

import ssl

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# SSL Configuration for Upstash Redis (rediss://)
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'visibility_timeout': 3600,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            1: 1,  # TCP_KEEPIDLE
            2: 1,  # TCP_KEEPINTVL
            3: 5,  # TCP_KEEPCNT
        },
    }

if CELERY_RESULT_BACKEND.startswith('rediss://'):
    CELERY_REDIS_BACKEND_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }

# Task serialization and execution settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_ALWAYS_EAGER = False  # Set to True to run tasks synchronously in DEBUG mode
CELERY_TASK_EAGER_PROPAGATES = True

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Check SLA violations every 15 minutes
    'check-sla-violations': {
        'task': 'blockchain.tasks.check_sla_violations',
        'schedule': crontab(minute='*/15'),
    },
    # Sync blockchain events every 10 minutes
    'sync-blockchain-events': {
        'task': 'blockchain.tasks.sync_blockchain_events',
        'schedule': crontab(minute='*/10'),
    },
    # Retry failed transactions every hour
    'retry-failed-transactions': {
        'task': 'blockchain.tasks.retry_failed_transactions',
        'schedule': crontab(minute=0),
    },
}

CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# ============ SLA Configuration ============

COMPLAINT_SLA_HOURS = int(os.getenv('COMPLAINT_SLA_HOURS', '48'))

# ============ Logging Configuration ============

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # File handler disabled by default - uncomment and create logs/ directory if needed
        # 'blockchain_file': {
        #     'class': 'logging.FileHandler',
        #     'filename': str(Path(BASE_DIR) / 'logs/blockchain.log'),
        #     'formatter': 'verbose',
        # },
    },
    'loggers': {
        'blockchain': {
            'handlers': ['console'],  # Add 'blockchain_file' if file logging enabled
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============ AWS Secrets Manager (Production) ============

"""
For production, use AWS Secrets Manager instead of environment variables:

import boto3
import json

def get_blockchain_secrets():
    secret_name = os.getenv('AWS_SECRETS_MANAGER_SECRET_NAME')
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    secret_value = client.get_secret_value(SecretId=secret_name)
    return json.loads(secret_value['SecretString'])

if not DEBUG:
    secrets = get_blockchain_secrets()
    BLOCKCHAIN_PRIVATE_KEY = secrets['private_key']
"""
