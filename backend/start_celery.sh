#!/bin/bash
# Start Celery Worker for Report Hub
# 
# Usage: ./start_celery.sh
#
# This script starts the Celery worker with the correct settings for macOS development

echo "🚀 Starting Celery Worker..."
echo "============================================"

# Activate virtual environment
venv\Scripts\activate
# Export Django settings
export DJANGO_SETTINGS_MODULE=report_hub.settings.local

# Start Celery worker with solo pool (required for macOS)
# --loglevel=info: Show INFO level logs
# --pool=solo: Use single process (avoids fork issues on macOS)
# -E: Enable task-sent events for monitoring
celery -A report_hub worker --loglevel=info --pool=solo -E

# Alternative for production (Linux):
# celery -A report_hub worker --loglevel=info --concurrency=4
