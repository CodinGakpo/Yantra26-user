import logging
import os
import hashlib
import uuid
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


class LocalFileStorageService:
    def __init__(self):
        self.upload_dir = self._get_upload_directory()
        self._ensure_directory_exists()
    
    def _get_upload_directory(self) -> Path:
        if hasattr(settings, 'LOCAL_FILE_UPLOAD_DIR'):
            upload_dir = Path(settings.LOCAL_FILE_UPLOAD_DIR)
        else:
            media_root = getattr(settings, 'MEDIA_ROOT', Path(settings.BASE_DIR) / 'media')
            upload_dir = Path(media_root) / 'uploads'
        
        return upload_dir
    
    def _ensure_directory_exists(self):
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Upload directory ready: {self.upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory: {e}")
            raise
    
    def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        complaint_id: str = None
    ) -> Tuple[Optional[str], Optional[str]]:
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = uuid.uuid4().hex[:8]
            file_extension = os.path.splitext(file_name)[1]
            safe_name = f"{timestamp}_{unique_id}{file_extension}"
            
            if complaint_id:
                complaint_dir = self.upload_dir / complaint_id
                complaint_dir.mkdir(parents=True, exist_ok=True)
                file_full_path = complaint_dir / safe_name
                file_relative_path = f"uploads/{complaint_id}/{safe_name}"
            else:
                file_full_path = self.upload_dir / safe_name
                file_relative_path = f"uploads/{safe_name}"
            
            with open(file_full_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File saved locally: {file_full_path}")
            
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            file_url = f"{media_url}{file_relative_path}"
            
            return file_relative_path, file_url
            
        except Exception as e:
            logger.error(f"Local file upload error: {e}")
            return None, None
    
    def retrieve_file(self, file_path: str) -> Optional[bytes]:
        try:
            if file_path.startswith('uploads/'):
                relative_path = file_path[8:]
                full_path = self.upload_dir / relative_path
            else:
                full_path = self.upload_dir / file_path
            
            if not full_path.exists():
                logger.error(f"File not found: {full_path}")
                return None
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"File retrieved: {full_path}")
            return content
            
        except Exception as e:
            logger.error(f"File retrieval error: {e}")
            return None
    
    def get_file_url(self, file_path: str) -> str:
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        return f"{media_url}{file_path}"
    
    def verify_file_exists(self, file_path: str) -> bool:
        try:
            if file_path.startswith('uploads/'):
                relative_path = file_path[8:]
                full_path = self.upload_dir / relative_path
            else:
                full_path = self.upload_dir / file_path
            
            return full_path.exists()
            
        except Exception as e:
            logger.error(f"File existence check failed: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        try:
            if file_path.startswith('uploads/'):
                relative_path = file_path[8:]
                full_path = self.upload_dir / relative_path
            else:
                full_path = self.upload_dir / file_path
            
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted: {full_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {full_path}")
                return False
                
        except Exception as e:
            logger.error(f"File deletion error: {e}")
            return False
    
    def compute_file_hash(self, file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()


# Singleton instance
_local_storage_service = None


def get_local_storage_service() -> LocalFileStorageService:
    global _local_storage_service
    
    if _local_storage_service is None:
        _local_storage_service = LocalFileStorageService()
    
    return _local_storage_service


def get_file_storage_service() -> LocalFileStorageService:
    return get_local_storage_service()
