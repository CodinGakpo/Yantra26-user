# Nagrikmitra: AWS to Neon DB + Firebase Migration

> A blockchain-enabled AI-powered civic issue reporting platform migration from AWS (RDS + S3) to Neon DB + Firebase Storage

## 📋 Quick Links

- **First time?** → Start with [QUICK_START.md](QUICK_START.md) (5-10 mins)
- **Need details?** → See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) (comprehensive)
- **Setup checklist?** → Use [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)
- **Troubleshooting?** → Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Backend only?** → Read [backend/FIREBASE_SERVICE_README.md](backend/FIREBASE_SERVICE_README.md)

---

## 🎯 What's Being Done

This migration replaces AWS services with modern alternatives:

| Component | Before | After |
|-----------|--------|-------|
| **Database** | AWS RDS (MySQL) | Neon DB (PostgreSQL) |
| **File Storage** | AWS S3 | Firebase Storage |
| **Configuration** | AWS credentials | Firebase + Neon credentials |

---

## ✅ What's Already Done

### Code Changes
- ✅ Firebase Storage service module (`firebase_service.py`)
- ✅ Django settings updated for PostgreSQL
- ✅ API endpoints updated from S3 to Firebase
- ✅ Dependencies added to `requirements.txt`
- ✅ Management command for image migration

### Documentation
- ✅ Comprehensive migration guide
- ✅ Setup checklist (12 phases)
- ✅ Firebase service documentation
- ✅ Troubleshooting guide
- ✅ Quick start guide
- ✅ Configuration template

---

## 🚀 Getting Started (3 Steps)

### 1. **Create Accounts**
   - Neon DB: https://neon.tech (create new project)
   - Firebase: https://firebase.google.com (create storage bucket)

### 2. **Update Configuration**
   ```bash
   # Copy template
   cp .env.template .env.example
   
   # Edit .env with your credentials:
   # - Neon DB details
   # - Firebase service account path
   # - Firebase bucket name
   ```

### 3. **Install & Test**
   ```bash
   pip install -r requirements.txt
   python manage.py migrate --settings=report_hub.settings.local
   ```

See [QUICK_START.md](QUICK_START.md) for detailed commands.

---

## 📁 New Files Created

```
yantra26-user/
├── QUICK_START.md                    # ⭐ Start here (5-10 mins)
├── MIGRATION_GUIDE.md                # 📖 Complete guide
├── SETUP_CHECKLIST.md                # ✅ Detailed checklist
├── TROUBLESHOOTING.md                # 🔧 Common issues & fixes
├── IMPLEMENTATION_SUMMARY.md         # 📊 What was changed
├── .env.template                     # 📝 Environment template
└── backend/
    ├── firebase_service.py           # 🔥 Firebase service module
    ├── FIREBASE_SERVICE_README.md    # 📚 Service documentation
    └── report/
        ├── views.py (MODIFIED)
        └── management/
            └── commands/
                └── migrate_s3_to_firebase.py  # 🔄 Migration utility
```

---

## 🏗️ Architecture

### Backend Structure
```
Django Application
├── Firebase Service (firebase_service.py)
│   ├── Upload images
│   ├── Generate signed URLs
│   └── Delete images
├── Report API (report/views.py)
│   ├── presign_s3() → Firebase upload info
│   └── presign_get_for_track() → Signed download URLs
└── Database
    └── Neon DB (PostgreSQL)
```

### Frontend Workflow
```
1. User selects image
2. Frontend requests upload info from backend
3. Backend returns Firebase bucket & path
4. Frontend uploads directly to Firebase
5. Frontend stores path in report
6. Backend stores path in database
7. Later, user views report
8. Frontend requests signed URL from backend
9. Backend returns time-limited download URL
10. Frontend displays image
```

---

## 🔐 Security Features

✅ **Neon DB**
- PostgreSQL with automatic backups
- SSL connections (enforced in production)
- Connection pooling
- Query timeouts

✅ **Firebase Storage**
- Service account authentication
- Security rules restricting access
- Signed URLs with expiration
- Automatic CDN distribution
- Data encryption at rest

✅ **Configuration**
- Credentials in environment variables
- No hardcoded secrets
- Service account JSON excluded from version control

---

## 📊 Migration Phases

1. **Setup & Config** (1-2 hours)
   - Create Neon DB & Firebase projects
   - Obtain credentials
   - Update `.env`
   - Install dependencies

2. **Database Migration** (30 mins - 2 hours)
   - Run Django migrations
   - Test database connection
   - Optionally migrate existing data

3. **Frontend Updates** (1-2 hours)
   - Install Firebase SDK
   - Update upload components
   - Update .env with Firebase config

4. **Testing** (1-2 hours)
   - Test all API endpoints
   - Test image uploads
   - Test image downloads
   - Verify blockchain integration

5. **Deployment** (1-2 hours)
   - Update production environment
   - Deploy to servers
   - Monitor for issues

**Total Estimated Time: 4-9 hours**

---

## 🛠️ Management Commands

### Migrate Images from S3 to Firebase

```bash
# Dry run (see what would be migrated)
python manage.py migrate_s3_to_firebase \
  --dry-run \
  --settings=report_hub.settings.local

# Actually migrate
python manage.py migrate_s3_to_firebase \
  --settings=report_hub.settings.local

# With error tolerance
python manage.py migrate_s3_to_firebase \
  --skip-errors \
  --settings=report_hub.settings.local
```

---

## 📚 Documentation Structure

```
Quick References (5-15 mins)
├── QUICK_START.md
└── This README.md

Setup Instructions (1-2 hours)
├── MIGRATION_GUIDE.md
├── SETUP_CHECKLIST.md
└── IMPLEMENTATION_SUMMARY.md

Code Integration (30 mins - 2 hours)
├── backend/FIREBASE_SERVICE_README.md
└── Code examples in MIGRATION_GUIDE.md

Troubleshooting (As needed)
├── TROUBLESHOOTING.md
└── "Troubleshooting" sections in other docs
```

---

## 🆘 Troubleshooting Quick Links

**Database Issues**
- "connect() got unexpected keyword" → [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-1-connect-got-an-unexpected-keyword-argument-init_command)
- "could not connect to server" → [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-2-could-not-connect-to-server)
- "too many connections" → [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-4-too-many-connections)

**Firebase Issues**
- "FIREBASE_CREDENTIALS_PATH is not set" → [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-1-firebase_credentials_path-is-not-set)
- "Permission denied (403)" → [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-4-permission-denied-403)
- "Bucket not found" → [TROUBLESHOOTING.md](TROUBLESHOOTING.md#issue-5-bucket-not-found)

---

## 🔄 Next Steps

### Immediate (Today)
1. [ ] Read [QUICK_START.md](QUICK_START.md)
2. [ ] Create Neon DB project
3. [ ] Create Firebase project
4. [ ] Download Firebase service account JSON

### Short Term (This Week)
5. [ ] Update `.env` file
6. [ ] Install dependencies
7. [ ] Run migrations
8. [ ] Test database connection
9. [ ] Test Firebase connection

### Medium Term (Next Week)
10. [ ] Update frontend with Firebase SDK
11. [ ] Update image upload components
12. [ ] Test complete flow
13. [ ] Migrate existing data (if applicable)

### Long Term
14. [ ] Deploy to production
15. [ ] Monitor both services
16. [ ] Update admin repo (follow same process)
17. [ ] Plan AWS resource cleanup

---

## 📞 Support Resources

- **Neon DB**: [neon.tech/docs](https://neon.tech/docs/)
- **Firebase**: [firebase.google.com/docs](https://firebase.google.com/docs)
- **Django PostgreSQL**: [docs.djangoproject.com](https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes)

---

## 📝 Project Information

- **Project**: Nagrikmitra
- **Type**: Blockchain-enabled civic issue reporting platform
- **Backend**: Django REST Framework 5.2.7
- **Frontend**: React 18 + Vite
- **Database**: PostgreSQL (via Neon)
- **Storage**: Firebase Storage
- **Special Features**: Smart contract integration, ML classification, Aadhaar verification

---

## 🎓 Key Concepts

### Neon DB
- PostgreSQL-compatible serverless database
- Automatic backups and scaling
- Perfect for serverless applications
- Requires psycopg2 Python driver

### Firebase Storage
- Google Cloud storage integration
- Automatic CDN distribution
- Built-in security rules
- Signed URLs for secure temporary access
- Requires firebase-admin Python SDK

### Service Accounts
- Used for server-to-server communication
- Credentials downloaded as JSON file
- Should be kept secure (never commit to git)
- Used in `firebase_service.py` for authentication

---

## ✨ Key Features of This Migration

✅ **Zero Downtime** - Can run both old and new systems in parallel
✅ **Data Migration** - Included utility to migrate existing S3 images
✅ **Comprehensive Docs** - Multiple guides for different needs
✅ **Testing Tools** - Management commands for validation
✅ **Security First** - Follows best practices
✅ **Rollback Plan** - Can revert to AWS if needed
✅ **Scalable** - Prepared for production deployment

---

## 📋 Dependencies

**New Python Packages**
```
firebase-admin==6.4.0      # Firebase integration
psycopg2-binary==2.9.9    # PostgreSQL driver
```

**Frontend Package**
```bash
npm install firebase       # Firebase SDK for React
```

**Existing Dependencies** (unchanged)
- Django 5.2.7
- Django REST Framework 3.15.2
- web3.py (for blockchain)
- tensorflow (for ML)

---

## 🎯 Success Criteria

Migration is complete when:

- [ ] Neon DB is connected and migrations run successfully
- [ ] Firebase Storage bucket is created and accessible
- [ ] Image upload works via Firebase
- [ ] Image download generates signed URLs correctly
- [ ] All existing data is migrated (if applicable)
- [ ] Admin repo is updated with same changes
- [ ] Production environment is tested
- [ ] Performance is acceptable
- [ ] No CORS errors
- [ ] Blockchain integration still works

---

## 🚫 Common Mistakes

❌ Using relative paths for Firebase credentials
❌ Committing serviceAccountKey.json to git
❌ Wrong bucket name format (missing .appspot.com)
❌ Not updating CORS origins
❌ Mixing MySQL and PostgreSQL connection options
❌ Forgetting to install new dependencies
❌ Not updating admin repo with same changes

---

## 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | May 11, 2026 | Initial implementation |

---

## 💡 Tips

- **Start Small**: Test with local development first
- **Document Everything**: Keep notes of your setup
- **Test Thoroughly**: Try upload, download, delete
- **Monitor Logs**: Enable debug logging while testing
- **Keep Backups**: AWS data stays until fully migrated
- **Ask Questions**: All docs have links to external resources

---

## 🎉 Ready?

**Let's get started!** Follow this path:

1. **Quick Preview** → [QUICK_START.md](QUICK_START.md)
2. **Detailed Guide** → [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
3. **Step by Step** → [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)
4. **Stuck?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Happy migrating! 🚀**

*For questions or issues, refer to the comprehensive documentation provided.*
