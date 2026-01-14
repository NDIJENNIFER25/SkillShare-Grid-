import os
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, List
import hashlib
from datetime import datetime

class VHDManager:
    """Manages Virtual Hard Disks (VHD) - folder-based storage for users"""

    def __init__(self, base_path: str = "vhd_storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.base_path / "vhd_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load VHD metadata from disk"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save VHD metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def create_vhd(self, user_id: str, size_gb: int = 1) -> Dict:
        """
        Create a new VHD (folder) for a user

        Args:
            user_id: Unique user identifier
            size_gb: Storage size in GB (default 1GB)

        Returns:
            Dict with VHD information
        """
        vhd_path = self.base_path / user_id

        # Check if VHD already exists
        if vhd_path.exists():
            return {
                "status": "error",
                "message": f"VHD already exists for user {user_id}"
            }

        # Create VHD directory structure
        vhd_path.mkdir(parents=True)
        (vhd_path / "files").mkdir()
        (vhd_path / ".metadata").mkdir()

        # Create VHD metadata
        vhd_info = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "size_bytes": size_gb * 1024 * 1024 * 1024,
            "used_bytes": 0,
            "file_count": 0,
            "path": str(vhd_path)
        }

        self.metadata[user_id] = vhd_info
        self._save_metadata()

        return {
            "status": "success",
            "message": f"VHD created for user {user_id}",
            "vhd_info": vhd_info
        }

    def get_vhd_info(self, user_id: str) -> Optional[Dict]:
        """Get VHD information for a user"""
        return self.metadata.get(user_id)

    def delete_vhd(self, user_id: str) -> Dict:
        """Delete a user's VHD"""
        vhd_path = self.base_path / user_id

        if not vhd_path.exists():
            return {
                "status": "error",
                "message": f"VHD not found for user {user_id}"
            }

        # Delete the VHD directory
        shutil.rmtree(vhd_path)

        # Remove from metadata
        if user_id in self.metadata:
            del self.metadata[user_id]
            self._save_metadata()

        return {
            "status": "success",
            "message": f"VHD deleted for user {user_id}"
        }

    def store_file(self, user_id: str, file_name: str, file_data: bytes) -> Dict:
        """
        Store a file in user's VHD

        Args:
            user_id: User identifier
            file_name: Name of the file
            file_data: Binary file data

        Returns:
            Dict with operation status
        """
        vhd_info = self.get_vhd_info(user_id)

        if not vhd_info:
            return {
                "status": "error",
                "message": f"VHD not found for user {user_id}"
            }

        vhd_path = Path(vhd_info["path"])
        file_size = len(file_data)

        # Check storage quota
        if vhd_info["used_bytes"] + file_size > vhd_info["size_bytes"]:
            return {
                "status": "error",
                "message": "Storage quota exceeded",
                "used_bytes": vhd_info["used_bytes"],
                "total_bytes": vhd_info["size_bytes"]
            }

        # Generate file ID and paths
        file_id = hashlib.md5(f"{user_id}-{file_name}-{datetime.now()}".encode()).hexdigest()
        file_path = vhd_path / "files" / file_id
        metadata_path = vhd_path / ".metadata" / f"{file_id}.json"

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)

        # Save file metadata
        file_metadata = {
            "file_id": file_id,
            "original_name": file_name,
            "size_bytes": file_size,
            "uploaded_at": datetime.now().isoformat(),
            "checksum": hashlib.sha256(file_data).hexdigest()
        }

        with open(metadata_path, 'w') as f:
            json.dump(file_metadata, f, indent=2)

        # Update VHD metadata
        vhd_info["used_bytes"] += file_size
        vhd_info["file_count"] += 1
        self.metadata[user_id] = vhd_info
        self._save_metadata()

        return {
            "status": "success",
            "message": "File stored successfully",
            "file_id": file_id,
            "file_metadata": file_metadata
        }

    def retrieve_file(self, user_id: str, file_id: str) -> Optional[Dict]:
        """
        Retrieve a file from user's VHD

        Returns:
            Dict with file_data (bytes) and metadata, or None if not found
        """
        vhd_info = self.get_vhd_info(user_id)

        if not vhd_info:
            return None

        vhd_path = Path(vhd_info["path"])
        file_path = vhd_path / "files" / file_id
        metadata_path = vhd_path / ".metadata" / f"{file_id}.json"

        if not file_path.exists() or not metadata_path.exists():
            return None

        # Load file data
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return {
            "file_data": file_data,
            "metadata": metadata
        }

    def list_files(self, user_id: str) -> List[Dict]:
        """List all files in user's VHD"""
        vhd_info = self.get_vhd_info(user_id)

        if not vhd_info:
            return []

        vhd_path = Path(vhd_info["path"])
        metadata_dir = vhd_path / ".metadata"

        files = []
        for metadata_file in metadata_dir.glob("*.json"):
            with open(metadata_file, 'r') as f:
                files.append(json.load(f))

        return files

    def delete_file(self, user_id: str, file_id: str) -> Dict:
        """Delete a file from user's VHD"""
        vhd_info = self.get_vhd_info(user_id)

        if not vhd_info:
            return {
                "status": "error",
                "message": f"VHD not found for user {user_id}"
            }

        vhd_path = Path(vhd_info["path"])
        file_path = vhd_path / "files" / file_id
        metadata_path = vhd_path / ".metadata" / f"{file_id}.json"

        if not file_path.exists():
            return {
                "status": "error",
                "message": "File not found"
            }

        # Load file size before deleting
        with open(metadata_path, 'r') as f:
            file_metadata = json.load(f)
            file_size = file_metadata["size_bytes"]

        # Delete file and metadata
        file_path.unlink()
        metadata_path.unlink()

        # Update VHD metadata
        vhd_info["used_bytes"] -= file_size
        vhd_info["file_count"] -= 1
        self.metadata[user_id] = vhd_info
        self._save_metadata()

        return {
            "status": "success",
            "message": "File deleted successfully"
        }

    def get_storage_usage(self, user_id: str) -> Optional[Dict]:
        """Get storage usage statistics for a user"""
        vhd_info = self.get_vhd_info(user_id)

        if not vhd_info:
            return None

        return {
            "user_id": user_id,
            "used_bytes": vhd_info["used_bytes"],
            "total_bytes": vhd_info["size_bytes"],
            "used_mb": round(vhd_info["used_bytes"] / (1024 * 1024), 2),
            "total_mb": round(vhd_info["size_bytes"] / (1024 * 1024), 2),
            "usage_percent": round((vhd_info["used_bytes"] / vhd_info["size_bytes"]) * 100, 2),
            "file_count": vhd_info["file_count"]
        }