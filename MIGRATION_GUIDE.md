# Migration Guide: AWS to Neon DB + Firebase

This guide will help you migrate your Yantra project from AWS (RDS + S3) to Neon DB + Firebase Storage.

## Overview of Changes

1. **Database**: AWS RDS (MySQL) → Neon DB (PostgreSQL)
2. **File Storage**: AWS S3 → Firebase Storage
3. **Code**: Updated Django settings and storage service implementation

## Prerequisites

- Active Neon DB account (https://neon.tech)
- Active Firebase project (https://firebase.google.com)
- Python 3.9+
- Git
- PostgreSQL client tools (optional, for direct DB management)

---

## Step 1: Set Up Neon DB

### 1.1 Create a Neon Database

1. Go to [Neon Console](https://console.neon.tech/)
2. Click "Create Project"
3. Name it "yantra26-customer" (or your preferred name)
4. Select your region (recommended: same as your application server)
5. Create the project

### 1.2 Get Connection Details

1. In Neon Console, navigate to your project
2. Go to "Connection Details"
3. Copy the connection string (it looks like the one you shared in the image)
4. Extract these credentials:
   - **Host**: `your-db-id.neon.tech`
   - **Database**: Your database name
   - **User**: Username (usually "neon_user" or similar)
   - **Password**: Your password (shown in connection string)
   - **Port**: 5432 (default)

### 1.3 Update Your .env File

```bash
# Replace with your Neon credentials
DB_ENGINE=django.db.backends.postgresql
DB_NAME=yantra_customer
DB_USER=neon_user
DB_PASSWORD=your_password_here
DB_HOST=ep-xxxxx.neon.tech
DB_PORT=5432
```

### 1.4 Install PostgreSQL Driver

The project now requires `psycopg2-binary` for PostgreSQL connection. This has been added to `requirements.txt`.

```bash
pip install -r requirements.txt
```

---

## Step 2: Set Up Firebase

### 2.1 Create a Firebase Project

1. Go to [Firebase Console](https://firebase.google.com/)
2. Click "Add project" or select existing project
3. Name it "nagrikmitra-customer" (or your preferred name)
4. Follow the setup wizard

### 2.2 Create a Firestore/Storage Bucket

1. In Firebase Console, go to "Build" → "Storage"
2. Click "Create bucket"
3. Choose your region (recommended: same as DB)
4. Accept the default security rules (we'll update them)
5. Click "Create"

**Note the bucket name** (format: `projectid.appspot.com`)

### 2.3 Create Service Account

1. Go to "Project Settings" (gear icon) → "Service Accounts"
2. Click "Generate new private key"
3. A JSON file will be downloaded: `serviceAccountKey.json`
4. **IMPORTANT**: Keep this file secure and never commit it to version control

### 2.4 Set Up Security Rules

Replace the default security rules with:

```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow authenticated users to read
    match /reports/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.resource.size < 50 * 1024 * 1024;
    }
    
    // Allow public read for non-sensitive files
    match /public/{allPaths=**} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

### 2.5 Update Your .env File

```bash
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/absolute/path/to/serviceAccountKey.json
FIREBASE_BUCKET_NAME=your-project-id.appspot.com
```

**Important**: 
- Use an **absolute path** for the credentials JSON file
- Never include the serviceAccountKey.json in your git repository
- Add it to `.gitignore`:
  ```
  serviceAccountKey.json
  firebase_credentials.json
  ```

---

## Step 3: Update Your Application

### 3.1 Update Requirements

```bash
# Install new dependencies
pip install firebase-admin psycopg2-binary

# Or reinstall all requirements
pip install -r requirements.txt --upgrade
```

### 3.2 Update Environment Configuration

1. Copy `.env.template` as reference:
   ```bash
   cp .env.template .env.example
   ```

2. Update your `.env` file with:
   - Neon DB credentials
   - Firebase configuration
   - Other existing settings (email, OAuth, blockchain, etc.)

### 3.3 Database Migration

Since we're switching from MySQL to PostgreSQL, you'll need to:

```bash
# Backup your current MySQL database (if needed)
mysqldump -u reportadmin -h reportmitra-mysql.cbsqk2s4swyr.ap-south-1.rds.amazonaws.com -p reportmitra_db > backup.sql

# Create fresh migrations for PostgreSQL
python manage.py makemigrations --settings=report_hub.settings.local

# Apply migrations to Neon DB
python manage.py migrate --settings=report_hub.settings.local
```

### 3.4 Test the Connection

```bash
# Test Neon DB connection
python manage.py shell --settings=report_hub.settings.local

# In the Python shell, run:
from django.db import connection
print(connection.connection)  # Should show PostgreSQL connection
exit()
```

### 3.5 Test Firebase Connection

```bash
# Create a test script
python -c "
from firebase_service import get_firebase_storage_service
firebase = get_firebase_storage_service()
print('✓ Firebase initialized successfully!')
"
```

---

## Step 4: Update Frontend (React)

Your frontend will need to be updated to use Firebase SDK instead of AWS S3.

### 4.1 Install Firebase SDK

```bash
cd frontend
npm install firebase
```

### 4.2 Initialize Firebase in Frontend

Create `src/config/firebase.js`:

```javascript
import { initializeApp } from 'firebase/app';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const storage = getStorage(app);
```

### 4.3 Update Image Upload Component

Replace S3 upload logic with Firebase:

```javascript
import { storage } from '@/config/firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';

// Example upload function
async function uploadReportImage(file) {
  const storageRef = ref(storage, `reports/${Date.now()}-${file.name}`);
  
  try {
    await uploadBytes(storageRef, file);
    const url = await getDownloadURL(storageRef);
    return {
      url: url,
      key: `reports/${Date.now()}-${file.name}`
    };
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
}
```

### 4.4 Update .env.local (Frontend)

Create `.env.local` in the frontend directory:

```
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

These values can be found in Firebase Console → Project Settings → General tab.

---

## Step 5: Running the Application

### 5.1 Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --settings=report_hub.settings.local

# Start the development server
python manage.py runserver --settings=report_hub.settings.local
```

### 5.2 Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

---

## Step 6: Data Migration (If You Have Existing Data)

If you have existing reports in your AWS database:

### Option A: Manual Export/Import

```bash
# Export from AWS MySQL
mysqldump -u reportadmin -h reportmitra-mysql.cbsqk2s4swyr.ap-south-1.rds.amazonaws.com -p reportmitra_db > data_export.sql

# Create tables in Neon
python manage.py migrate --settings=report_hub.settings.local

# Manually migrate image URLs and files
# (Requires custom script to transfer S3 URLs to Firebase)
```

### Option B: Fresh Start

For a cleaner migration, you can:
1. Keep the old database running in read-only mode
2. Start fresh with Neon DB
3. Migrate data gradually

---

## Step 7: Image Migration (S3 to Firebase)

To migrate existing images from S3 to Firebase:

```python
# Create a management command: backend/report/management/commands/migrate_images_s3_to_firebase.py

from django.core.management.base import BaseCommand
import boto3
from firebase_service import get_firebase_storage_service
from report.models import IssueReport

class Command(BaseCommand):
    help = 'Migrate images from S3 to Firebase Storage'
    
    def handle(self, *args, **options):
        s3_client = boto3.client('s3', 
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        firebase = get_firebase_storage_service()
        
        reports = IssueReport.objects.filter(image_url__isnull=False)
        
        for report in reports:
            try:
                # Download from S3
                obj = s3_client.get_object(
                    Bucket=settings.REPORT_IMAGES_BUCKET,
                    Key=report.image_url
                )
                content = obj['Body'].read()
                
                # Upload to Firebase
                file_name = report.image_url.split('/')[-1]
                result = firebase.upload_image(content, file_name)
                
                # Update the database record
                report.image_url = result['key']
                report.save()
                
                self.stdout.write(f"✓ Migrated {report.tracking_id}")
            except Exception as e:
                self.stderr.write(f"✗ Failed to migrate {report.tracking_id}: {e}")

# Run with:
# python manage.py migrate_images_s3_to_firebase --settings=report_hub.settings.local
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql postgresql://user:password@host:5432/dbname

# Or from Django:
python manage.py shell --settings=report_hub.settings.local
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("Connected!")
```

### Firebase Initialization Errors

- Ensure `serviceAccountKey.json` path is absolute
- Check file permissions: `chmod 600 /path/to/serviceAccountKey.json`
- Verify the JSON file is valid: `python -m json.tool serviceAccountKey.json`

### CORS Issues (Frontend/Backend)

Update `settings/local.py` or `settings/production.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "https://yourdomain.com",
]
```

### Image Upload Failures

Check that:
1. Firebase bucket name is correct in `.env`
2. Service account has Storage Editor role
3. Security rules allow uploads
4. Frontend is using correct Firebase config

---

## Admin Side Migration

For the admin repository, follow the same steps:

1. Create another Neon DB (or use a separate schema in the same Neon project)
2. Create a separate Firebase bucket (or use a separate folder in the same bucket)
3. Update admin backend with the same configuration changes
4. Update admin frontend with Firebase SDK

---

## Security Checklist

- [ ] `serviceAccountKey.json` added to `.gitignore`
- [ ] `.env` file added to `.gitignore` (use `.env.example` for template)
- [ ] Firebase security rules restrict access to authenticated users
- [ ] Neon DB password stored securely
- [ ] HTTPS enabled for production
- [ ] CORS origins restricted to trusted domains
- [ ] Firebase bucket versioning enabled for data protection

---

## Support Resources

- **Neon DB**: https://neon.tech/docs/
- **Firebase**: https://firebase.google.com/docs/storage
- **Django PostgreSQL**: https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
- **Firebase Admin SDK**: https://firebase.google.com/docs/admin/setup

---

## Next Steps

1. Set up Neon DB and Firebase as described
2. Install dependencies: `pip install -r requirements.txt`
3. Update `.env` with new credentials
4. Run migrations: `python manage.py migrate`
5. Test the connection
6. Update frontend with Firebase SDK
7. Deploy to production

Good luck with your migration! 🚀
