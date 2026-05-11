# Firebase Service Module Documentation

## Overview

The `firebase_service.py` module provides a singleton service to interact with Firebase Storage, handling image uploads, presigned URLs, and file management for the Yantra application.

## Installation

1. Install firebase-admin:
```bash
pip install firebase-admin
```

2. Obtain Firebase Service Account credentials:
   - Go to Firebase Console → Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file to a secure location

## Configuration

Add these environment variables to your `.env` file:

```bash
FIREBASE_CREDENTIALS_PATH=/absolute/path/to/serviceAccountKey.json
FIREBASE_BUCKET_NAME=your-project-id.appspot.com
```

## Usage Examples

### Initialize the Service

```python
from firebase_service import get_firebase_storage_service

firebase = get_firebase_storage_service()
```

### Upload an Image

```python
from firebase_service import get_firebase_storage_service

firebase = get_firebase_storage_service()

# Upload image from bytes
image_bytes = open('report.jpg', 'rb').read()
result = firebase.upload_image(
    file_content=image_bytes,
    file_name='report.jpg',
    content_type='image/jpeg'
)

# Returns:
# {
#     'url': 'https://storage.googleapis.com/...',
#     'key': 'reports/abc123-report.jpg',
#     'name': 'report.jpg'
# }
```

### Get Presigned Download URL

```python
firebase = get_firebase_storage_service()

# Get a time-limited download URL (valid for 24 hours)
url = firebase.get_presigned_url(
    blob_path='reports/abc123-report.jpg',
    expiration_hours=24
)
```

### Get Public URL

```python
firebase = get_firebase_storage_service()

# Get the permanent public URL
url = firebase.get_public_url('reports/abc123-report.jpg')
```

### Delete an Image

```python
firebase = get_firebase_storage_service()

success = firebase.delete_image('reports/abc123-report.jpg')
if success:
    print("Image deleted")
```

## Integration with Django Views

The service is already integrated into `report/views.py`:

### Upload Endpoint

```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def presign_s3(request):
    """
    Returns Firebase upload information for the frontend.
    
    Frontend should use this to upload to Firebase directly.
    """
    # Implementation returns firebase bucket and path
```

### Download Endpoint

```python
@api_view(["GET"])
@permission_classes([AllowAny])
def presign_get_for_track(request, id):
    """
    Returns presigned URLs for viewing report images.
    """
    # Implementation generates download URLs
```

## Frontend Integration

### Install Firebase SDK

```bash
npm install firebase
```

### Initialize Firebase (React)

Create `src/config/firebase.js`:

```javascript
import { initializeApp } from 'firebase/app';
import { getStorage } from 'firebase/storage';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const storage = getStorage(app);
export const auth = getAuth(app);
```

### Upload Image Component Example

```javascript
import { storage } from '@/config/firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';

async function handleImageUpload(file) {
  try {
    // First, get upload info from backend
    const uploadInfo = await fetch('/api/report/s3/presign/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        fileName: file.name,
        contentType: file.type,
      }),
    }).then(r => r.json());

    // Create a reference using the key from backend
    const storageRef = ref(storage, uploadInfo.key);

    // Upload to Firebase
    await uploadBytes(storageRef, file, {
      customMetadata: {
        uploadedAt: new Date().toISOString(),
      },
    });

    // Get the download URL
    const downloadURL = await getDownloadURL(storageRef);

    // Send the image_url (key) to your backend
    // Backend will store the key in the database
    return {
      url: downloadURL,
      key: uploadInfo.key,
    };
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
}
```

## Security Considerations

### Service Account Protection

- **Never** commit `serviceAccountKey.json` to version control
- Add to `.gitignore`:
  ```
  serviceAccountKey.json
  firebase_credentials.json
  *.json  # if needed
  ```

- Use environment variables for the file path
- Restrict file permissions: `chmod 600 serviceAccountKey.json`

### Firebase Security Rules

Set restrictive rules in Firebase Console → Storage → Rules:

```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /reports/{allPaths=**} {
      // Only authenticated users can read/write their own reports
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
                      request.resource.size < 50 * 1024 * 1024;
    }
    
    match /public/{allPaths=**} {
      allow read: if true;
      allow write: if false;  // No direct writes to public folder
    }
  }
}
```

## Error Handling

```python
from firebase_service import get_firebase_storage_service
from django.http import JsonResponse

firebase = get_firebase_storage_service()

try:
    result = firebase.upload_image(file_content, file_name)
except Exception as e:
    return JsonResponse(
        {'error': 'Upload failed', 'details': str(e)},
        status=500
    )
```

## Troubleshooting

### Firebase Not Initialized

```
RuntimeError: FIREBASE_CREDENTIALS_PATH environment variable is not set
```

**Solution**: 
1. Set the environment variable: `export FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json`
2. Use an absolute path (not relative)

### Permission Denied

```
google.cloud.exceptions.PermissionDenied: 403 Forbidden
```

**Solution**:
1. Check service account has "Editor" or "Storage Admin" role
2. Verify Firebase security rules allow the operation
3. Ensure bucket name is correct

### Bucket Not Found

```
google.cloud.exceptions.NotFound: 404 Not Found
```

**Solution**:
1. Verify `FIREBASE_BUCKET_NAME` matches exactly (format: `project-id.appspot.com`)
2. Check bucket exists in Firebase Console → Storage
3. Ensure service account has access to the bucket

## Performance Tips

1. **Compression**: Compress images before upload
2. **Batching**: Group multiple uploads
3. **Caching**: Cache URLs to avoid repeated generation
4. **CDN**: Firebase Storage serves through Google's CDN automatically
5. **Pagination**: For large file lists, use pagination

## Testing

```python
# test_firebase_service.py
from django.test import TestCase
from firebase_service import get_firebase_storage_service
import io

class FirebaseServiceTest(TestCase):
    def setUp(self):
        self.firebase = get_firebase_storage_service()
    
    def test_upload_image(self):
        # Create a test image
        image_content = b'fake_image_data'
        result = self.firebase.upload_image(
            image_content,
            'test.jpg',
            'image/jpeg'
        )
        
        self.assertIn('url', result)
        self.assertIn('key', result)
        self.assertTrue(result['url'].startswith('https://'))
        
        # Clean up
        self.firebase.delete_image(result['key'])
    
    def test_get_presigned_url(self):
        # Upload first
        image_content = b'fake_image_data'
        result = self.firebase.upload_image(
            image_content,
            'test.jpg'
        )
        
        # Get presigned URL
        url = self.firebase.get_presigned_url(result['key'])
        self.assertTrue(url.startswith('https://'))
        
        # Clean up
        self.firebase.delete_image(result['key'])

# Run tests
# python manage.py test report.tests.FirebaseServiceTest --settings=report_hub.settings.local
```

## Migration from S3

See [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) for detailed S3 to Firebase migration instructions.

## References

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Firebase Storage Documentation](https://firebase.google.com/docs/storage)
- [Firebase Storage Best Practices](https://firebase.google.com/docs/storage/usage/best-practices)
