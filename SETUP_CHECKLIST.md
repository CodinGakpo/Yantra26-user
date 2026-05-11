# Quick Setup Checklist - AWS to Neon + Firebase Migration

## Phase 1: Preparation (30 mins)

- [ ] Create Neon account at https://neon.tech
- [ ] Create Firebase project at https://firebase.google.com
- [ ] Backup your current AWS MySQL database
- [ ] Install PostgreSQL client tools (optional): `brew install postgresql` (Mac) or `apt-get install postgresql-client` (Linux)

## Phase 2: Neon DB Setup (15 mins)

- [ ] Create a new Neon project
- [ ] Create a new database (e.g., `yantra_customer`)
- [ ] Get connection credentials:
  - [ ] Host
  - [ ] Database name
  - [ ] Username
  - [ ] Password
  - [ ] Port (should be 5432)
- [ ] Test connection (optional):
  ```bash
  psql postgresql://user:password@host:5432/dbname -c "SELECT 1"
  ```

## Phase 3: Firebase Setup (20 mins)

- [ ] Create a new Firestore/Storage bucket
- [ ] Create a service account:
  - [ ] Go to Project Settings → Service Accounts
  - [ ] Click "Generate new private key"
  - [ ] Save JSON file to secure location
- [ ] Copy the bucket name (format: `project-id.appspot.com`)
- [ ] Update security rules (copy from MIGRATION_GUIDE.md)

## Phase 4: Update Backend Code (10 mins)

- [ ] Update `.env` file with new database credentials:
  ```
  DB_ENGINE=django.db.backends.postgresql
  DB_NAME=<neon_db_name>
  DB_USER=<neon_user>
  DB_PASSWORD=<neon_password>
  DB_HOST=<neon_host>
  DB_PORT=5432
  ```

- [ ] Add Firebase configuration to `.env`:
  ```
  FIREBASE_CREDENTIALS_PATH=/absolute/path/to/serviceAccountKey.json
  FIREBASE_BUCKET_NAME=<bucket-name>.appspot.com
  ```

- [ ] Add `serviceAccountKey.json` to `.gitignore`

- [ ] Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Phase 5: Database Migration (15 mins)

- [ ] Run migrations:
  ```bash
  python manage.py makemigrations --settings=report_hub.settings.local
  python manage.py migrate --settings=report_hub.settings.local
  ```

- [ ] Create superuser (if needed):
  ```bash
  python manage.py createsuperuser --settings=report_hub.settings.local
  ```

## Phase 6: Test Backend (10 mins)

- [ ] Test database connection:
  ```bash
  python manage.py shell --settings=report_hub.settings.local
  >>> from django.db import connection
  >>> connection.ensure_connection()
  >>> print("✓ PostgreSQL connected!")
  >>> exit()
  ```

- [ ] Test Firebase initialization:
  ```bash
  python -c "from firebase_service import get_firebase_storage_service; get_firebase_storage_service(); print('✓ Firebase initialized!')"
  ```

- [ ] Start backend server:
  ```bash
  python manage.py runserver --settings=report_hub.settings.local
  ```

## Phase 7: Update Frontend (20 mins)

- [ ] Install Firebase SDK:
  ```bash
  cd frontend
  npm install firebase
  ```

- [ ] Create `.env.local` in frontend directory:
  ```
  VITE_FIREBASE_API_KEY=<your_api_key>
  VITE_FIREBASE_AUTH_DOMAIN=<your_project>.firebaseapp.com
  VITE_FIREBASE_PROJECT_ID=<your_project_id>
  VITE_FIREBASE_STORAGE_BUCKET=<your_bucket>.appspot.com
  VITE_FIREBASE_MESSAGING_SENDER_ID=<your_sender_id>
  VITE_FIREBASE_APP_ID=<your_app_id>
  ```

- [ ] Create Firebase config file at `src/config/firebase.js` (see MIGRATION_GUIDE.md for template)
- [ ] Update image upload components to use Firebase SDK
- [ ] Test upload functionality

## Phase 8: Integration Testing (20 mins)

- [ ] Test user authentication
- [ ] Test report creation with image upload
- [ ] Test image viewing/download
- [ ] Test report listing
- [ ] Test blockchain integration (if applicable)

## Phase 9: Data Migration (Optional)

If you have existing data:

- [ ] Export data from AWS MySQL (see MIGRATION_GUIDE.md)
- [ ] Import data into Neon
- [ ] Run image migration script (see MIGRATION_GUIDE.md)
- [ ] Verify all data integrity

## Phase 10: Deployment Preparation (15 mins)

- [ ] Update production settings (settings/production.py)
- [ ] Set environment variables on your deployment platform
- [ ] Enable SSL/TLS for Neon connection
- [ ] Review security rules one more time
- [ ] Create deployment checklist

## Phase 11: Security Check

- [ ] [ ] Verify `serviceAccountKey.json` is in `.gitignore`
- [ ] [ ] Verify `.env` is in `.gitignore`
- [ ] [ ] Check Firebase security rules are restrictive
- [ ] [ ] Verify CORS settings are correct
- [ ] [ ] Confirm credentials are not logged anywhere
- [ ] [ ] Test HTTPS enforcement in production

## Phase 12: Monitoring & Cleanup

- [ ] [ ] Set up monitoring for Neon DB (optional)
- [ ] [ ] Set up monitoring for Firebase Storage usage
- [ ] [ ] Keep AWS resources running for backup (optional)
- [ ] [ ] Document access credentials securely
- [ ] [ ] Schedule AWS resource cleanup

---

## Estimated Total Time: 2-3 hours

### Breakdown:
- Preparation: 30 mins
- Neon setup: 15 mins
- Firebase setup: 20 mins
- Code updates: 10 mins
- Database: 15 mins
- Backend testing: 10 mins
- Frontend updates: 20 mins
- Integration testing: 20 mins
- Deployment prep: 15 mins
- Security check: 10 mins

---

## Emergency Rollback Plan

If something goes wrong:

1. Keep AWS resources running initially
2. Point application back to AWS MySQL
3. Restore S3 bucket access temporarily
4. Debug and fix issues
5. Try migration again

---

## Files Created/Modified

**New Files:**
- `firebase_service.py` - Firebase storage service module
- `FIREBASE_SERVICE_README.md` - Firebase service documentation
- `MIGRATION_GUIDE.md` - Comprehensive migration guide
- `.env.template` - Environment variables template
- `SETUP_CHECKLIST.md` - This file

**Modified Files:**
- `requirements.txt` - Added firebase-admin, psycopg2-binary
- `report_hub/settings/base.py` - Updated Firebase configuration
- `report_hub/settings/local.py` - PostgreSQL configuration
- `report_hub/settings/production.py` - PostgreSQL + SSL configuration
- `report/views.py` - Updated S3 to Firebase

---

## Support & Troubleshooting

Refer to the "Troubleshooting" section in MIGRATION_GUIDE.md for common issues.

Key contacts:
- Neon Support: https://neon.tech/docs/
- Firebase Support: https://firebase.google.com/support
- Django PostgreSQL: https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes

---

**Last Updated**: 2026-05-11
**Migration Version**: 1.0
