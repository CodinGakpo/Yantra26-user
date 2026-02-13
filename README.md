# NagrikMitra - Citizen Civic Issue Reporting Platform

**NagrikMitra** (नागरिक मित्र - "Citizen's Friend") is a comprehensive civic issue reporting and tracking platform that empowers citizens to report infrastructure problems, track resolution progress, and promote government accountability through transparent, blockchain-verified complaint management.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2-green.svg)
![React Native](https://img.shields.io/badge/React%20Native-0.76-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

NagrikMitra enables citizens to report civic issues (potholes, broken streetlights, waste management problems, etc.) through multiple platforms while ensuring transparency and accountability via blockchain technology. The platform automatically classifies issues using machine learning and maintains tamper-proof records of complaint lifecycle events.

### Key Highlights

- 🔐 **Aadhaar-based verification** prevents spam and ensures authentic reporting
- 🤖 **ML-powered department classification** automatically routes complaints to the correct department
- ⛓️ **Blockchain transparency** ensures tamper-proof tracking of complaint status changes
- 📱 **Multi-platform support** with web, Android, and iOS applications
- 🔍 **Real-time tracking** allows citizens to monitor resolution progress
- 📊 **Analytics dashboard** provides insights into civic issue patterns

---

## ✨ Core Features

### 1. **Citizen Report Submission**

Citizens can submit civic issue reports with the following details:

```json
{
  "issue_title": "Pothole on Main Street",
  "location": "123 Main St, Sector 15",
  "issue_description": "Large pothole causing traffic hazard",
  "image_url": "https://s3.amazonaws.com/...",
  "status": "pending"
}
```

- **Image Upload**: Pre-signed S3 URLs for direct, secure image uploads
- **Location Tracking**: GPS-based location capture with map integration
- **Unique Tracking ID**: Each report receives a unique 8-character tracking ID

### 2. **ML-Based Department Classification**

The platform uses a TensorFlow/Keras image classification model to automatically route reports to the appropriate department:

```python
# Department categories
- Traffic & Transportation
- Water & Sanitation
- Electricity & Street Lighting
- Waste Management
- Roads & Infrastructure
- Parks & Recreation
```

Model provides confidence scores to ensure accurate routing.

### 3. **Blockchain Verification**

Every complaint lifecycle event is recorded on the blockchain:

```solidity
Events Tracked:
- CREATED: Initial complaint submission
- ASSIGNED: Complaint assigned to department
- STATUS_UPDATED: Status changes (pending → in_progress → resolved)
- ESCALATED: Complaint escalation
- RESOLVED: Final resolution
- EVIDENCE_ADDED: Additional evidence submission
```

**Hash Anchoring**: Evidence files are stored locally with SHA-256 hashes recorded on-chain for integrity verification.

### 4. **Aadhaar Verification**

Citizens must verify their Aadhaar identity before submitting reports:

```python
# Verification flow
1. User enters 12-digit Aadhaar number
2. System validates against Aadhaar database
3. Links verified Aadhaar to user profile
4. Enables report submission
```

This prevents duplicate/spam reports while maintaining citizen accountability.

### 5. **Multi-Platform Access**

- **Web Application** (Vite + React): Full-featured dashboard with analytics
- **Android App** (React Native): Native mobile experience for on-the-go reporting
- **iOS App** (Swift): Native iOS application

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATIONS                       │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │  Web (React) │  │ Android (RN)  │  │  iOS (Swift)    │  │
│  └──────┬───────┘  └───────┬───────┘  └────────┬────────┘  │
└─────────┼──────────────────┼───────────────────┼───────────┘
          │                  │                   │
          └──────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │   API Gateway   │
                    │  (Django REST)  │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
   ┌──────▼──────┐   ┌───────▼────────┐  ┌─────▼──────┐
   │   Report    │   │   Blockchain   │  │   ML       │
   │   Service   │   │   Service      │  │  Service   │
   └──────┬──────┘   └───────┬────────┘  └─────┬──────┘
          │                  │                  │
   ┌──────▼──────┐   ┌───────▼────────┐  ┌─────▼──────┐
   │  PostgreSQL │   │ Amazon Managed │  │ TensorFlow │
   │  Database   │   │  Blockchain    │  │   Model    │
   └─────────────┘   └────────────────┘  └────────────┘
          │
   ┌──────▼──────┐
   │   AWS S3    │
   │ (Images)    │
   └─────────────┘
```

### Core Components

#### 1. **Backend (Django REST Framework)**

**Role**: Central API server managing all business logic, authentication, and data persistence.

**Key Modules**:

- **Report Module** (`backend/report/`)
  - Handles CRUD operations for civic issue reports
  - Manages report lifecycle (pending → in_progress → resolved → closed)
  - Generates unique tracking IDs
  - Integrates with S3 for image storage

- **Blockchain Module** (`backend/blockchain/`)
  - Abstracts Web3.py interactions
  - Records complaint events on smart contract
  - Maintains local cache of blockchain transactions
  - Provides hash anchoring for evidence files
  - Handles Ethereum transaction signing and gas management

- **ML Module** (`backend/ml/`)
  - Loads pre-trained TensorFlow/Keras model
  - Provides FastAPI endpoint for image classification
  - Returns department predictions with confidence scores
  - Preprocesses images (resize, normalize)

- **Aadhaar Module** (`backend/aadhaar/`)
  - Verifies Aadhaar numbers against database
  - Links verified Aadhaar to user profiles
  - Enforces verification requirement before report submission

- **User Profile Module** (`backend/user_profile/`)
  - Manages user authentication (JWT)
  - Stores user metadata and Aadhaar verification status
  - Tracks user report history

**Design Decisions**:

- **Async Task Processing**: Uses Celery for blockchain transactions to avoid blocking HTTP requests
- **Separation of Concerns**: Each module is independent with clear interfaces
- **Blockchain as Service**: All blockchain logic isolated in `blockchain/services.py`
- **Local Storage + Hash Anchoring**: Evidence files stored locally (not on IPFS) with hashes on-chain for cost efficiency

#### 2. **Smart Contract (Solidity)**

**Role**: Provides immutable, transparent record of complaint lifecycle events.

**File**: `backend/blockchain/contracts/ComplaintRegistry.sol`

**Key Functions**:

```solidity
// Log a new complaint event
function logEvent(
    string memory complaintId,
    string memory eventType,
    bytes32 eventHash,
    string memory eventData
) public returns (bytes32 transactionHash)

// Anchor evidence hash on-chain
function anchorEvidence(
    string memory complaintId,
    bytes32 fileHash,
    uint256 timestamp
) public returns (bytes32 transactionHash)
```

**Why Blockchain?**

- **Immutability**: Once recorded, events cannot be altered
- **Transparency**: Citizens can verify status changes independently
- **Accountability**: Government departments cannot hide or manipulate records
- **Audit Trail**: Complete history of all actions taken

#### 3. **ML Classification Service**

**Role**: Automatically determines which government department should handle a report.

**Model Architecture**:

- Pre-trained CNN (Convolutional Neural Network)
- Input: 224x224px RGB images
- Output: Department classification + confidence score

**Training Data**: Images of various civic issues labeled by department

**Integration Flow**:

```
1. User uploads image via mobile/web app
2. Image stored in S3, URL returned
3. Backend calls ML service with image data
4. ML service returns predicted department + confidence
5. Report created with auto-assigned department
```

#### 4. **Frontend Applications**

**Web App** (`frontend/`):
- Built with React 19 + Vite + Tailwind CSS
- Features:
  - Interactive map view of all reports (Leaflet)
  - Submit report form with image upload
  - Track report by ID
  - User profile and history
  - Google OAuth integration

**Android App** (`android-app/`):
- React Native 0.76 with TypeScript
- Features:
  - Native navigation (React Navigation)
  - Camera integration for on-the-fly reporting
  - AsyncStorage for offline support
  - Push notifications (future)

**iOS Apps** (`NagrikMitra/`, `NagrikMitra2/`):
- Native Swift applications
- Features:
  - iOS-native UI/UX
  - CoreLocation for GPS tracking
  - PhotoKit integration

### Data Flow: Report Submission

```
1. User Opens App
         ↓
2. Aadhaar Verification Check
         ↓
   [Not Verified] → Redirect to Verification
         ↓
   [Verified] → Proceed
         ↓
3. User Fills Report Form
   - Title, Description, Location
   - Captures/Uploads Image
         ↓
4. Request Pre-signed S3 URL
         ↓
5. Upload Image Directly to S3
         ↓
6. Submit Report to Backend
   POST /api/reports/
         ↓
7. Backend Creates Report Record
   - Generates Tracking ID
   - Calls ML Service for Classification
         ↓
8. ML Service Returns Department
         ↓
9. Backend Saves Report with Department
         ↓
10. Celery Task: Log to Blockchain
   - Create event hash
   - Sign transaction
   - Submit to smart contract
         ↓
11. Return Success to User
   - Display Tracking ID
   - Show on Community Feed
```

### Security Architecture

- **Authentication**: JWT tokens with refresh mechanism
- **Authorization**: Role-based access control (citizen, department admin, super admin)
- **Data Privacy**: Aadhaar numbers hashed, not stored in plaintext
- **Image Security**: Pre-signed S3 URLs with expiration
- **Blockchain Security**: Private keys stored in environment variables (production: AWS Secrets Manager)
- **CORS**: Configured to allow only trusted origins

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.2 + Django REST Framework 3.15
- **Database**: PostgreSQL (implied) / SQLite (development)
- **Blockchain**: Web3.py, eth-account, Amazon Managed Blockchain
- **ML**: TensorFlow 2.x, FastAPI for ML endpoints
- **Task Queue**: Celery 5.3 + RabbitMQ/Redis
- **Authentication**: djangorestframework-simplejwt
- **Storage**: AWS S3 (boto3)

### Frontend (Web)
- **Framework**: React 19
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4
- **Routing**: React Router DOM 7
- **Maps**: Leaflet + react-leaflet
- **3D Graphics**: Three.js
- **ML**: TensorFlow.js (client-side classification)

### Mobile (Android)
- **Framework**: React Native 0.76
- **Navigation**: React Navigation 7
- **State Management**: React Context API
- **Storage**: AsyncStorage
- **Maps**: react-native-maps
- **Image Picker**: react-native-image-picker

### iOS
- **Language**: Swift
- **UI Framework**: SwiftUI
- **Networking**: URLSession
- **Storage**: CoreData

### DevOps & Deployment
- **Containerization**: Docker (implied)
- **Cloud**: AWS (S3, Managed Blockchain)
- **Version Control**: Git

---

## 📦 Installation

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 14+ (or SQLite for development)
- **Docker**: Latest (optional, for containerization)
- **Blockchain Node**: Access to Ethereum-compatible blockchain

For mobile development:
- **Android Studio**: Latest version (for Android)
- **Xcode**: Latest version (for iOS, macOS only)
- **React Native CLI**: `npm install -g react-native-cli`

### Backend Setup

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/nagrikmitra.git
cd nagrikmitra
```

2. **Set up Python virtual environment**:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:

Create a `.env` file in the `backend/` directory:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/nagrikmitra

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=nagrikmitra-images
AWS_S3_REGION_NAME=us-east-1

# Blockchain
BLOCKCHAIN_NODE_URL=https://your-blockchain-node.amazonaws.com
BLOCKCHAIN_CONTRACT_ADDRESS=0xYourContractAddress
BLOCKCHAIN_PRIVATE_KEY=your-private-key
BLOCKCHAIN_USE_POA=true

# JWT
JWT_SECRET_KEY=your-jwt-secret

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ML Model
ML_MODEL_PATH=ml/model/civic_issue_imgmodel.keras
```

5. **Run database migrations**:

```bash
python manage.py migrate
```

6. **Create superuser** (admin account):

```bash
python manage.py createsuperuser
```

7. **Collect static files**:

```bash
python manage.py collectstatic
```

8. **Start development server**:

```bash
python manage.py runserver 0.0.0.0:8000
```

9. **Start Celery worker** (in separate terminal):

```bash
celery -A report_hub worker -l info
```

### Frontend (Web) Setup

1. **Navigate to frontend directory**:

```bash
cd frontend
```

2. **Install dependencies**:

```bash
npm install
```

3. **Configure environment**:

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id
```

4. **Start development server**:

```bash
npm run dev
```

Visit `http://localhost:5173` in your browser.

### Android App Setup

1. **Navigate to Android app directory**:

```bash
cd android-app
```

2. **Install dependencies**:

```bash
npm install
```

3. **Set up Android environment**:

Ensure `ANDROID_HOME` is set:

```bash
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

4. **Configure API endpoint**:

Edit `src/config/environment.ts`:

```typescript
export const API_BASE_URL = 'http://10.0.2.2:8000/api'; // Android emulator
// For physical device: use your machine's local IP
```

5. **Start Metro bundler**:

```bash
npm start
```

6. **Run on Android** (in separate terminal):

```bash
npm run android
```

### iOS App Setup

1. **Navigate to iOS app directory**:

```bash
cd NagrikMitra
```

2. **Install CocoaPods dependencies** (if applicable):

```bash
pod install
```

3. **Open in Xcode**:

```bash
open NagrikMitra.xcodeproj
```

4. **Configure API endpoint** in the project settings.

5. **Build and run** from Xcode (⌘+R).

---

## 🚀 Usage

### For Citizens

#### 1. **Register and Verify Aadhaar**

```bash
# Via Web App
1. Visit http://localhost:5173
2. Click "Register"
3. Fill registration form
4. Navigate to Profile
5. Enter 12-digit Aadhaar number
6. Click "Verify"
```

#### 2. **Submit a Report**

```bash
# Via Mobile App
1. Open app and login
2. Tap "Report Issue"
3. Take/upload photo
4. Fill in:
   - Issue Title
   - Description
   - Location (auto-captured or manual)
5. Submit
6. Note your Tracking ID (e.g., "RT123456")
```

#### 3. **Track Your Report**

```bash
# Via Web/Mobile
1. Navigate to "Track Report"
2. Enter Tracking ID
3. View:
   - Current Status
   - Assigned Department
   - Timeline of Events
   - Blockchain Transaction Hash (for verification)
```

#### 4. **View Community Reports**

Browse all reports on the community feed, filterable by:
- Status (pending, in_progress, resolved)
- Department
- Location
- Date range

### For Developers

#### API Examples

**1. User Registration**

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "citizen123",
    "email": "citizen@example.com",
    "password": "securepassword",
    "phone_number": "+919876543210"
  }'
```

**2. Login (Get JWT Token)**

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "citizen123",
    "password": "securepassword"
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**3. Verify Aadhaar**

```bash
curl -X POST http://localhost:8000/api/aadhaar/verify/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "aadhaar_number": "123456789012"
  }'
```

**4. Get Pre-signed S3 URL**

```bash
curl -X POST http://localhost:8000/api/reports/presign-s3/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "pothole-image.jpg",
    "contentType": "image/jpeg"
  }'

# Response:
{
  "url": "https://nagrikmitra-images.s3.amazonaws.com/...",
  "key": "uploads/abc123.jpg"
}
```

**5. Create Report**

```bash
curl -X POST http://localhost:8000/api/reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_title": "Large Pothole",
    "location": "123 Main St",
    "issue_description": "Deep pothole causing accidents",
    "image_url": "https://nagrikmitra-images.s3.amazonaws.com/..."
  }'

# Response:
{
  "id": 42,
  "tracking_id": "RT123456",
  "issue_title": "Large Pothole",
  "status": "pending",
  "department": "Roads & Infrastructure",
  "confidence_score": 0.94,
  "issue_date": "2026-02-10T10:30:00Z"
}
```

**6. Get All Reports**

```bash
curl -X GET http://localhost:8000/api/reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**7. Track Specific Report**

```bash
curl -X GET http://localhost:8000/api/reports/track/RT123456/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Running Tests

**Backend Tests**:

```bash
cd backend
python manage.py test
```

**Frontend Tests**:

```bash
cd frontend
npm run test
```

**Android Tests**:

```bash
cd android-app
npm test
```

---

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/register/` | Register new user |
| POST | `/api/users/login/` | Login and get JWT |
| POST | `/api/users/token/refresh/` | Refresh JWT token |
| GET | `/api/users/profile/` | Get user profile |

### Aadhaar Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/aadhaar/verify/` | Verify Aadhaar number |

### Report Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/` | List all reports |
| POST | `/api/reports/` | Create new report |
| GET | `/api/reports/{id}/` | Get specific report |
| PUT | `/api/reports/{id}/` | Update report |
| DELETE | `/api/reports/{id}/` | Delete report (admin only) |
| GET | `/api/reports/track/{tracking_id}/` | Track by tracking ID |
| POST | `/api/reports/presign-s3/` | Get pre-signed S3 URL |

### Blockchain Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/blockchain/transactions/{complaint_id}/` | Get blockchain events for complaint |
| POST | `/api/blockchain/verify-evidence/` | Verify evidence integrity |

### ML Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ml/predict/` | Classify image and predict department |

---

## 📁 Project Structure

```
nagrikmitra/
├── backend/                     # Django backend
│   ├── manage.py               # Django management script
│   ├── requirements.txt        # Python dependencies
│   ├── report_hub/             # Main Django project
│   │   ├── settings/          # Settings modules
│   │   ├── urls.py            # Root URL configuration
│   │   └── celery.py          # Celery configuration
│   ├── report/                 # Report management app
│   │   ├── models.py          # IssueReport model
│   │   ├── views.py           # Report API views
│   │   ├── serializers.py     # DRF serializers
│   │   └── urls.py            # Report URLs
│   ├── blockchain/             # Blockchain integration
│   │   ├── models.py          # BlockchainTransaction, EvidenceHash
│   │   ├── services.py        # Web3 service layer
│   │   ├── contracts/         # Solidity smart contracts
│   │   └── listeners.py       # Event listeners
│   ├── ml/                     # Machine learning
│   │   ├── predict.py         # Prediction API
│   │   ├── model/             # Trained models
│   │   └── views.py           # ML endpoints
│   ├── aadhaar/                # Aadhaar verification
│   │   ├── models.py          # AadhaarDatabase model
│   │   └── views.py           # Verification logic
│   ├── user_profile/           # User profiles
│   │   ├── models.py          # UserProfile model
│   │   └── serializers.py     # Profile serializers
│   └── users/                  # Authentication
│       └── views.py           # Login, registration
│
├── frontend/                   # Web application (React)
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client services
│   │   ├── context/           # React Context providers
│   │   └── App.tsx            # Root component
│   ├── package.json
│   └── vite.config.js
│
├── android-app/                # React Native Android
│   ├── src/
│   │   ├── screens/           # Screen components
│   │   ├── navigation/        # Navigation config
│   │   ├── shared/
│   │   │   ├── api/          # API services
│   │   │   ├── context/      # Auth context
│   │   │   └── utils/        # Utility functions
│   │   └── App.tsx
│   ├── android/               # Native Android
│   └── package.json
│
├── NagrikMitra/                # Native iOS app (Swift)
│   ├── NagrikMitra/           # iOS source code
│   └── NagrikMitra.xcodeproj
│
├── NagrikMitra2/               # iOS app variant
└── README.md                   # This file
```

---

## 🔮 Future Improvements

### Short-term (Next 6 months)

- [ ] **Push Notifications**: Real-time alerts on status changes
- [ ] **Offline Mode**: Queue reports when network unavailable
- [ ] **Photo Compression**: Reduce image sizes before upload
- [ ] **Multi-language Support**: Hindi, regional languages
- [ ] **Geofencing**: Auto-detect relevant government jurisdiction
- [ ] **Report Clustering**: Group nearby similar issues

### Medium-term (6-12 months)

- [ ] **Admin Dashboard**: Government department portal for report management
- [ ] **SLA Tracking**: Monitor resolution time commitments
- [ ] **Escalation System**: Auto-escalate overdue complaints
- [ ] **Citizen Rewards**: Gamification for active reporters
- [ ] **Social Features**: Comment threads, upvoting urgent issues
- [ ] **Accessibility**: Screen reader support, high contrast mode

### Long-term (12+ months)

- [ ] **AI Chatbot**: Help citizens describe issues
- [ ] **Predictive Analytics**: Forecast infrastructure maintenance needs
- [ ] **Integration with Government Systems**: Direct ERP integration
- [ ] **Public API**: Allow third-party integrations
- [ ] **Data Visualization**: Heatmaps, trends, analytics
- [ ] **Cross-platform Desktop App**: Electron-based desktop client

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Write tests** for new functionality
5. **Run tests**: `python manage.py test` (backend) or `npm test` (frontend)
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**

### Code Style Guidelines

**Python (Backend)**:
- Follow PEP 8
- Use type hints where possible
- Write docstrings for all functions/classes
- Maximum line length: 100 characters

**JavaScript/TypeScript (Frontend)**:
- Use ESLint configuration provided
- Prefer functional components with hooks
- Use TypeScript for type safety
- Format with Prettier

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add description of changes in PR
4. Wait for code review approval
5. Squash commits before merge

### Reporting Bugs

Use GitHub Issues with the following template:

```
**Bug Description**: Clear description of the bug

**Steps to Reproduce**:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Environment**:
- OS: [e.g. macOS 13]
- Browser/App Version: [e.g. Chrome 110, Android App 1.0]
- Backend Version: [e.g. Django 5.2]

**Screenshots**: If applicable
```

### Feature Requests

We're open to new ideas! Submit via GitHub Issues with:

- **Problem Statement**: What problem does this solve?
- **Proposed Solution**: How would you implement it?
- **Alternatives Considered**: Other approaches you thought about
- **Additional Context**: Mockups, examples, etc.

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 NagrikMitra Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/nagrikmitra/issues)
- **Email**: support@nagrikmitra.in
- **Documentation**: [Wiki](https://github.com/yourusername/nagrikmitra/wiki)

---

## 🙏 Acknowledgments

- TensorFlow team for ML framework
- Web3.py maintainers for blockchain integration
- React Native community for mobile framework
- OpenStreetMap contributors for mapping data
- All contributors and testers

---

<div align="center">
  <p>Made with ❤️ for citizens everywhere</p>
  <p>⭐ Star this repo if you find it useful!</p>
</div>
