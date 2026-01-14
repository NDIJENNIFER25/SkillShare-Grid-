"""
Chunked Upload Handler for Distributed Cloud Storage
Handles large file uploads by splitting them into chunks
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
import threading
import time

class ChunkedUploadHandler:
    CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks

    def __init__(self, storage_path: str = "storage_system/uploads"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Track active uploads
        self.active_uploads: Dict[str, Dict] = {}
        self.upload_lock = threading.Lock()

        # Metadata storage
        self.metadata_path = self.storage_path / "upload_metadata.json"
        self._load_metadata()

    def _load_metadata(self):
        """Load upload metadata from disk"""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r') as f:
                self.active_uploads = json.load(f)
        else:
            self.active_uploads = {}

    def _save_metadata(self):
        """Save upload metadata to disk"""
        with open(self.metadata_path, 'w') as f:
            json.dump(self.active_uploads, f, indent=2)

    def initiate_upload(self, filename: str, total_size: int, file_hash: str,
                       user_id: str, category: str = "general") -> Dict:
        """Initiate a chunked upload session"""
        upload_id = hashlib.md5(f"{filename}{user_id}{time.time()}".encode()).hexdigest()
        total_chunks = (total_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE

        upload_info = {
            "upload_id": upload_id,
            "filename": filename,
            "total_size": total_size,
            "total_chunks": total_chunks,
            "chunk_size": self.CHUNK_SIZE,
            "file_hash": file_hash,
            "user_id": user_id,
            "category": category,
            "uploaded_chunks": [],
            "status": "in_progress",
            "created_at": time.time(),
            "nodes_replicated": []
        }

        with self.upload_lock:
            self.active_uploads[upload_id] = upload_info
            self._save_metadata()

        upload_dir = self.storage_path / upload_id
        upload_dir.mkdir(exist_ok=True)

        return upload_info

    def get_upload_status(self, upload_id: str) -> Optional[Dict]:
        """Get status of an upload session"""
        return self.active_uploads.get(upload_id)

    def get_all_uploads(self, user_id: Optional[str] = None,
                       category: Optional[str] = None) -> List[Dict]:
        """Get all uploads, optionally filtered by user or category"""
        uploads = list(self.active_uploads.values())

        if user_id:
            uploads = [u for u in uploads if u.get("user_id") == user_id]

        if category:
            uploads = [u for u in uploads if u.get("category") == category]

        return uploads