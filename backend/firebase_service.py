"""
Firebase Storage Service Module
Handles image uploads and URLs for the application
"""
import os
import uuid
import firebase_admin
from firebase_admin import credentials, storage
from datetime import timedelta
import json
from pathlib import Path


class FirebaseStorageService:
    """Service to handle Firebase Storage operations"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseStorageService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase Admin SDK if not already initialized"""
        if not self._initialized:
            self._initialize_firebase()
            FirebaseStorageService._initialized = True
    
    @staticmethod
    def _initialize_firebase():
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
        except ValueError:
            # Firebase not initialized, initialize it
            firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            firebase_bucket = os.getenv('FIREBASE_BUCKET_NAME')
            
            if not firebase_creds_path:
                raise RuntimeError(
                    "FIREBASE_CREDENTIALS_PATH environment variable is not set. "
                    "Please provide the path to your Firebase service account JSON file."
                )
            
            if not firebase_bucket:
                raise RuntimeError(
                    "FIREBASE_BUCKET_NAME environment variable is not set. "
                    "Please provide your Firebase Storage bucket name."
                )
            
            # Load credentials from the specified path
            creds = credentials.Certificate(firebase_creds_path)
            
            # Initialize Firebase Admin SDK
            firebase_admin.initialize_app(creds, {
                'storageBucket': firebase_bucket,
            })
    
    def upload_image(self, file_content, file_name, content_type='image/jpeg'):
        """
        Upload an image to Firebase Storage and return a public URL.
        
        Args:
            file_content: Binary content of the file
            file_name: Original file name
            content_type: MIME type of the file (default: image/jpeg)
        
        Returns:
            dict: {
                'url': 'https://...',  # Public URL
                'key': 'reports/...',  # Storage path
                'name': 'file_name'
            }
        
        Raises:
            Exception: If upload fails
        """
        try:
            bucket = storage.bucket()
            
            # Create a unique key
            unique_id = uuid.uuid4().hex
            storage_path = f"reports/{unique_id}-{file_name}"
            
            # Upload file to Firebase Storage
            blob = bucket.blob(storage_path)
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            # Make blob publicly readable by setting a custom claim
            blob.make_public()
            
            # Get the public URL
            public_url = blob.public_url
            
            return {
                'url': public_url,
                'key': storage_path,
                'name': file_name
            }
        
        except Exception as e:
            raise Exception(f"Firebase upload failed: {str(e)}")
    
    def get_presigned_url(self, blob_path, expiration_hours=1):
        """
        Generate a presigned URL for an existing blob.
        
        Args:
            blob_path: Path to the blob in Firebase Storage
            expiration_hours: Number of hours the URL is valid
        
        Returns:
            str: Presigned download URL
        """
        try:
            bucket = storage.bucket()
            blob = bucket.blob(blob_path)
            
            # Generate download URL valid for the specified duration
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
            
            return url
        
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def get_upload_signed_url(self, blob_path, content_type, expiration_hours=1):
        """
        Generate a signed URL for direct browser upload (HTTP PUT).

        Args:
            blob_path: Path to the blob in Firebase Storage
            content_type: MIME type expected for upload
            expiration_hours: Number of hours the URL is valid

        Returns:
            str: Signed upload URL (HTTPS)
        """
        try:
            bucket = storage.bucket()
            blob = bucket.blob(blob_path)

            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="PUT",
                content_type=content_type,
            )
        except Exception as e:
            raise Exception(f"Failed to generate upload signed URL: {str(e)}")
    
    def delete_image(self, blob_path):
        """
        Delete an image from Firebase Storage.
        
        Args:
            blob_path: Path to the blob in Firebase Storage
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            bucket = storage.bucket()
            blob = bucket.blob(blob_path)
            blob.delete()
            return True
        
        except Exception as e:
            print(f"Failed to delete image from Firebase: {str(e)}")
            return False
    
    def get_public_url(self, blob_path):
        """
        Get the public URL for a blob in Firebase Storage.
        
        Args:
            blob_path: Path to the blob in Firebase Storage
        
        Returns:
            str: Public URL
        """
        bucket = storage.bucket()
        return f"https://storage.googleapis.com/{bucket.name}/{blob_path}"


# Singleton instance
_firebase_service = None


def get_firebase_storage_service():
    """
    Get or create the Firebase Storage Service instance.
    
    Returns:
        FirebaseStorageService: Singleton instance
    """
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseStorageService()
    return _firebase_service
