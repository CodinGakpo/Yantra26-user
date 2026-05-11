# AWS → Neon DB + Firebase: Quick Start (5-10 minutes)

## Step 1: Neon DB Setup (2 minutes)

1. Go to https://console.neon.tech/
2. Create a new project
3. Copy your connection string from "Connection Details"
4. Extract these values and update `.env`:

```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=yantra_customer
DB_USER=neon_user
DB_PASSWORD=your_neon_password
DB_HOST=ep-xxxxx.neon.tech
DB_PORT=5432
```

## Step 2: Firebase Setup (2 minutes)

1. Go to https://firebase.google.com/
2. Create a new project or select existing
3. Create Storage bucket (Build → Storage → Create bucket)
4. Go to Project Settings → Service Accounts → "Generate new private key"
5. Save the JSON file in a **secure location**

Update `.env`:
```bash
FIREBASE_CREDENTIALS_PATH=/absolute/path/to/serviceAccountKey.json
FIREBASE_BUCKET_NAME=your-project-id.appspot.com
```

## Step 3: Install Dependencies (1 minute)

```bash
cd backend
pip install -r requirements.txt
```

## Step 4: Run Migrations (1 minute)

```bash
python manage.py migrate --settings=report_hub.settings.local
```

## Step 5: Test Connection (1 minute)

```bash
# Test Neon
python manage.py shell --settings=report_hub.settings.local
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("✓ Connected to Neon DB")
>>> exit()

# Test Firebase
python -c "from firebase_service import get_firebase_storage_service; get_firebase_storage_service(); print('✓ Firebase initialized')"
```

## Step 6: Start Backend

```bash
python manage.py runserver --settings=report_hub.settings.local
```

---

## For Frontend

```bash
cd frontend
npm install firebase

# Create .env.local with Firebase config
# See MIGRATION_GUIDE.md for Firebase config values
```

---

## Key Files Created

| File | Purpose |
|------|---------|
| `firebase_service.py` | Firebase Storage service module |
| `MIGRATION_GUIDE.md` | Comprehensive migration guide |
| `SETUP_CHECKLIST.md` | Detailed setup checklist |
| `FIREBASE_SERVICE_README.md` | Firebase service documentation |
| `.env.template` | Environment variables template |
| `migrate_s3_to_firebase.py` | Migration command for existing images |

---

## Common Issues

### "FIREBASE_CREDENTIALS_PATH not set"
→ Use absolute path: `/home/user/serviceAccountKey.json` (not relative paths)

### "Module firebase_admin not found"
→ Run: `pip install firebase-admin`

### "PostgreSQL connection refused"
→ Check Neon DB is online and credentials are correct

### "Firebase bucket not found"
→ Verify bucket name matches exactly: `project-id.appspot.com`

---

For detailed guidance, see **MIGRATION_GUIDE.md**
