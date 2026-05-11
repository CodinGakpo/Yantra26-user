# Connection Troubleshooting Guide

## Neon DB Connection Issues

### Issue 1: "connect() got an unexpected keyword argument 'init_command'"

**Cause**: MySQL-specific option used with PostgreSQL

**Solution**: Already fixed in settings files. Verify `settings/local.py` has:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # No "init_command" - that's MySQL only
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",
        },
    }
}
```

### Issue 2: "could not connect to server"

**Causes & Solutions**:

```bash
# 1. Check if database is online
psql postgresql://user:password@host:5432/dbname -c "SELECT 1"

# 2. Verify credentials in .env
echo $DB_HOST
echo $DB_USER
echo $DB_NAME

# 3. Check for typos in hostname
# Neon format: ep-xxxxx.neon.tech (NOT neon.tech)

# 4. Verify port (should be 5432, not 3306)
echo $DB_PORT

# 5. Test from Django
python manage.py shell --settings=report_hub.settings.local
>>> from django.db import connection
>>> connection.ensure_connection()
# If no error, connection works
```

### Issue 3: "SSL connection error"

**Cause**: Neon DB requires SSL in production

**Solution**: Add to `settings/production.py`:
```python
"OPTIONS": {
    "sslmode": "require",
}
```

For development (local.py), SSL is optional:
```python
"OPTIONS": {
    "sslmode": "prefer",  # or "disable" for local dev
}
```

### Issue 4: "too many connections"

**Cause**: Connection pool exhausted

**Solution**: Add connection pooling to settings:
```python
"CONN_MAX_AGE": 600,  # Reuse connections for 600 seconds
```

### Issue 5: "password authentication failed"

**Cause**: Wrong password or user doesn't have permission

**Solution**:
```bash
# Copy password exactly (no extra spaces)
# Check for special characters that need escaping

# Example in .env:
DB_PASSWORD=myP@ssw0rd!

# If password has special chars, it might need URL encoding
# Test directly with psql:
psql -U user -h host -d dbname -c "SELECT 1"
```

---

## Firebase Connection Issues

### Issue 1: "FIREBASE_CREDENTIALS_PATH is not set"

**Cause**: Missing environment variable

**Solution**:
```bash
# Add to .env file (ABSOLUTE PATH REQUIRED):
FIREBASE_CREDENTIALS_PATH=/home/user/serviceAccountKey.json

# NOT relative:
# FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json  ❌

# Verify file exists:
ls -la /home/user/serviceAccountKey.json
```

### Issue 2: "No module named 'firebase_admin'"

**Cause**: Firebase SDK not installed

**Solution**:
```bash
pip install firebase-admin==6.4.0

# Or install all requirements:
pip install -r requirements.txt
```

### Issue 3: "Error: Application already initialized"

**Cause**: Firebase initialized multiple times

**Solution**: The `firebase_service.py` handles this with singleton pattern. If you see this error:
```python
# Don't do this:
firebase_admin.initialize_app(creds)  # ❌

# Instead, use the service:
from firebase_service import get_firebase_storage_service
firebase = get_firebase_storage_service()  # ✅
```

### Issue 4: "Permission denied (403)"

**Cause**: Service account lacks permissions

**Solution**:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Look for the service account email (e.g., `firebase-adminsdk-xxxxx@project.iam.gserviceaccount.com`)
3. Go to Google Cloud Console → IAM
4. Find the service account
5. Grant these roles:
   - `Firebase Storage Admin`
   - `Storage Admin` (in Cloud Storage section)
6. Wait 5-10 minutes for permissions to propagate

### Issue 5: "Bucket not found"

**Cause**: Wrong bucket name or bucket doesn't exist

**Solution**:
```bash
# Correct format:
FIREBASE_BUCKET_NAME=my-project-id.appspot.com  # ✅

# Wrong formats:
FIREBASE_BUCKET_NAME=my-project-id               # ❌ Missing .appspot.com
FIREBASE_BUCKET_NAME=gs://my-project-id          # ❌ gs:// prefix
FIREBASE_BUCKET_NAME=my-bucket-name              # ❌ Wrong bucket

# Find correct bucket name:
# Firebase Console → Build → Storage → Bucket name shown on right side
```

### Issue 6: "Invalid service account format"

**Cause**: JSON file is corrupted or incomplete

**Solution**:
```bash
# Validate JSON format:
python -m json.tool /path/to/serviceAccountKey.json

# File should contain:
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "...",
  "token_uri": "...",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}

# If validation fails, re-download from Firebase Console
```

---

## Testing Both Connections

### Test Neon DB

```bash
# Method 1: Using psql
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
# Should show connection prompt

# Method 2: Using Django
python manage.py shell --settings=report_hub.settings.local
>>> from django.db import connection
>>> with connection.cursor() as cursor:
...     cursor.execute("SELECT NOW()")
...     print(cursor.fetchone())
(datetime.datetime(...),)
>>> exit()

# Method 3: Run migrations
python manage.py migrate --settings=report_hub.settings.local
```

### Test Firebase

```bash
# Python test script
python << 'EOF'
from firebase_service import get_firebase_storage_service

try:
    firebase = get_firebase_storage_service()
    print("✓ Firebase initialized successfully")
    
    # Test upload
    test_data = b"test content"
    result = firebase.upload_image(test_data, "test.txt", "text/plain")
    print(f"✓ Upload successful: {result['key']}")
    
    # Clean up
    firebase.delete_image(result['key'])
    print("✓ Delete successful")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
EOF
```

### Test API Endpoints

```bash
# 1. Upload endpoint (requires authentication token)
curl -X POST http://localhost:8000/api/report/s3/presign/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "fileName": "test.jpg",
    "contentType": "image/jpeg"
  }'

# 2. Get report images endpoint
curl http://localhost:8000/api/report/123/track/images/
```

---

## Common Environment Variable Issues

### Issue: Typos in .env

```bash
# Check these exactly (case-sensitive on Linux):
DB_ENGINE                  # django.db.backends.postgresql
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST                    # Must be neon.tech domain
DB_PORT                    # 5432 (NOT 3306)

FIREBASE_CREDENTIALS_PATH  # Absolute path
FIREBASE_BUCKET_NAME       # project-id.appspot.com
```

### Issue: .env not being loaded

```bash
# Verify python-dotenv is installed:
pip show python-dotenv

# Verify .env is in correct location:
ls -la backend/.env

# Check if .env is being read:
python manage.py shell --settings=report_hub.settings.local
>>> import os
>>> print(os.getenv('DB_HOST'))
# Should print your Neon host
```

---

## Debugging Steps

### 1. Enable Django Debug Logging

Add to `settings/local.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### 2. Print Environment Variables

```python
# In views.py or management command:
import os
from django.conf import settings

print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"Firebase Path: {os.getenv('FIREBASE_CREDENTIALS_PATH')}")
print(f"Firebase Bucket: {getattr(settings, 'FIREBASE_BUCKET_NAME', 'NOT SET')}")
```

### 3. Test Each Component

```bash
# Step 1: Database only
python manage.py shell --settings=report_hub.settings.local
>>> IssueReport.objects.count()
# If this works, DB is fine

# Step 2: Firebase only
python -c "from firebase_service import get_firebase_storage_service; get_firebase_storage_service()"
# If no error, Firebase is fine

# Step 3: API endpoints
python manage.py runserver --settings=report_hub.settings.local
# Try upload endpoint

# Step 4: Frontend
npm run dev
# Try uploading from UI
```

---

## Quick Verification Checklist

- [ ] Neon DB credentials copied exactly
- [ ] Firebase service account JSON downloaded
- [ ] Firebase bucket name matches (with .appspot.com)
- [ ] Both added to .env (NOT in .env.local or other files)
- [ ] Absolute paths used for Firebase credentials
- [ ] requirements.txt installed
- [ ] No typos in variable names
- [ ] File permissions correct (chmod 600 for JSON)
- [ ] Both connections test successfully
- [ ] Django migrations run without errors

---

## Getting Help

If issues persist:

1. **Check the logs**:
   ```bash
   # Backend logs
   tail -f /var/log/nagrikmitra/backend.log
   
   # Browser console (frontend)
   F12 → Console tab
   ```

2. **Verify environment**:
   ```bash
   python --version  # 3.9+
   pip list | grep postgres  # psycopg2-binary should be there
   pip list | grep firebase  # firebase-admin should be there
   ```

3. **Test individual components**:
   - Database: `psql ...`
   - Firebase: `python -c "..."`
   - API: `curl ...`
   - Frontend: Browser DevTools

4. **Check documentation**:
   - MIGRATION_GUIDE.md - Full setup steps
   - FIREBASE_SERVICE_README.md - Firebase integration
   - This file - Troubleshooting

---

**Still stuck? Check the "Troubleshooting" section in MIGRATION_GUIDE.md for more detailed solutions.**
