"""
Complete Virtual Hard Disk (VHD) Manager
Creates and manages virtual hard disks for cloud storage
"""
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import struct

class VHDManager:
    """
    Manages Virtual Hard Disks for distributed cloud storage
    Creates VHD files that act as virtual storage devices
    """

    # VHD Footer structure (512 bytes)
    VHD_FOOTER_SIZE = 512
    VHD_COOKIE = b'conectix'  # VHD signature
    VHD_VERSION = 0x00010000
    VHD_TYPE_FIXED = 2
    VHD_TYPE_DYNAMIC = 3

    def __init__(self, storage_path: str = "vhd_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # VHD registry
        self.registry_file = self.storage_path / "vhd_registry.json"
        self.vhd_registry = self._load_registry()

        # File allocation table
        self.fat_file = self.storage_path / "file_allocation.json"
        self.file_allocation = self._load_fat()

    def _load_registry(self) -> Dict:
        """Load VHD registry from disk"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_registry(self):
        """Save VHD registry to disk"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.vhd_registry, f, indent=2)

    def _load_fat(self) -> Dict:
        """Load File Allocation Table"""
        if self.fat_file.exists():
            with open(self.fat_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_fat(self):
        """Save File Allocation Table"""
        with open(self.fat_file, 'w') as f:
            json.dump(self.file_allocation, f, indent=2)

    def create_vhd(self, vhd_name: str, size_gb: int = 1,
                   vhd_type: str = "dynamic", user_id: str = None) -> Dict:
        """
        Create a new Virtual Hard Disk

        Args:
            vhd_name: Name of the VHD
            size_gb: Size in GB
            vhd_type: "fixed" or "dynamic"
            user_id: Optional user ID for ownership

        Returns:
            VHD information dictionary
        """
        vhd_id = hashlib.md5(f"{vhd_name}{time.time()}".encode()).hexdigest()
        vhd_filename = f"{vhd_id}.vhd"
        vhd_path = self.storage_path / vhd_filename

        size_bytes = size_gb * 1024 * 1024 * 1024  # Convert GB to bytes

        print(f"Creating VHD: {vhd_name} ({size_gb}GB, {vhd_type})")

        if vhd_type == "fixed":
            self._create_fixed_vhd(vhd_path, size_bytes)
        else:
            self._create_dynamic_vhd(vhd_path, size_bytes)

        # Create VHD metadata
        vhd_info = {
            "vhd_id": vhd_id,
            "name": vhd_name,
            "filename": vhd_filename,
            "path": str(vhd_path),
            "size_gb": size_gb,
            "size_bytes": size_bytes,
            "type": vhd_type,
            "created_at": time.time(),
            "user_id": user_id,
            "used_space": 0,
            "file_count": 0,
            "status": "active"
        }

        # Register VHD
        self.vhd_registry[vhd_id] = vhd_info
        self._save_registry()

        print(f"✓ VHD created successfully: {vhd_id}")
        return vhd_info

    def _create_fixed_vhd(self, vhd_path: Path, size_bytes: int):
        """Create a fixed-size VHD"""
        # Create VHD footer
        footer = self._create_vhd_footer(size_bytes, self.VHD_TYPE_FIXED)

        # Create file with exact size
        with open(vhd_path, 'wb') as f:
            # Write zeros for the disk (this will be sparse on most filesystems)
            chunk_size = 1024 * 1024  # 1MB chunks
            remaining = size_bytes

            while remaining > 0:
                write_size = min(chunk_size, remaining)
                f.write(b'\x00' * write_size)
                remaining -= write_size

            # Write footer at the end
            f.write(footer)

    def _create_dynamic_vhd(self, vhd_path: Path, max_size_bytes: int):
        """Create a dynamic (sparse) VHD that grows as needed"""
        # Dynamic VHD structure:
        # 1. VHD Footer (copy at beginning)
        # 2. Dynamic Disk Header
        # 3. Block Allocation Table (BAT)
        # 4. Data blocks (allocated on demand)
        # 5. VHD Footer (at end)

        footer = self._create_vhd_footer(max_size_bytes, self.VHD_TYPE_DYNAMIC)
        header = self._create_dynamic_header(max_size_bytes)

        with open(vhd_path, 'wb') as f:
            # Write footer copy at beginning
            f.write(footer)

            # Write dynamic header
            f.write(header)

            # Write minimal BAT (Block Allocation Table)
            # Each entry is 4 bytes, pointing to data blocks
            num_blocks = (max_size_bytes + (2 * 1024 * 1024 - 1)) // (2 * 1024 * 1024)
            bat = b'\xff\xff\xff\xff' * num_blocks  # 0xFFFFFFFF = unallocated
            f.write(bat)

            # Write footer at the end
            f.write(footer)

    def _create_vhd_footer(self, size_bytes: int, disk_type: int) -> bytes:
        """Create VHD footer structure"""
        footer = bytearray(512)

        # Cookie (8 bytes)
        footer[0:8] = self.VHD_COOKIE

        # Features (4 bytes) - reserved
        struct.pack_into('>I', footer, 8, 0x00000002)

        # File Format Version (4 bytes)
        struct.pack_into('>I', footer, 12, self.VHD_VERSION)

        # Data Offset (8 bytes) - 0xFFFFFFFFFFFFFFFF for fixed disks
        if disk_type == self.VHD_TYPE_FIXED:
            struct.pack_into('>Q', footer, 16, 0xFFFFFFFFFFFFFFFF)
        else:
            struct.pack_into('>Q', footer, 16, 512)  # Points to dynamic header

        # Timestamp (4 bytes) - seconds since Jan 1, 2000
        timestamp = int(time.time()) - 946684800
        struct.pack_into('>I', footer, 24, timestamp)

        # Creator Application (4 bytes)
        footer[28:32] = b'pycs'  # Python Cloud Storage

        # Creator Version (4 bytes)
        struct.pack_into('>I', footer, 32, 0x00010000)

        # Creator Host OS (4 bytes) - Windows
        footer[36:40] = b'Wi2k'

        # Original Size (8 bytes)
        struct.pack_into('>Q', footer, 40, size_bytes)

        # Current Size (8 bytes)
        struct.pack_into('>Q', footer, 48, size_bytes)

        # Disk Geometry (4 bytes) - CHS
        cylinders = min(size_bytes // (16 * 63 * 512), 65535)
        heads = 16
        sectors = 63
        struct.pack_into('>HBB', footer, 56, cylinders, heads, sectors)

        # Disk Type (4 bytes)
        struct.pack_into('>I', footer, 60, disk_type)

        # Checksum (4 bytes) - calculated last
        checksum = 0
        for i in range(512):
            if i < 64 or i >= 68:  # Skip checksum field itself
                checksum += footer[i]
        checksum = (~checksum) & 0xFFFFFFFF
        struct.pack_into('>I', footer, 64, checksum)

        # Unique ID (16 bytes) - UUID
        unique_id = os.urandom(16)
        footer[68:84] = unique_id

        # Saved State (1 byte)
        footer[84] = 0

        # Reserved (427 bytes) - already zeros

        return bytes(footer)

    def _create_dynamic_header(self, max_size_bytes: int) -> bytes:
        """Create dynamic disk header"""
        header = bytearray(1024)

        # Cookie (8 bytes)
        header[0:8] = b'cxsparse'

        # Data Offset (8 bytes) - 0xFFFFFFFFFFFFFFFF (none)
        struct.pack_into('>Q', header, 8, 0xFFFFFFFFFFFFFFFF)

        # Table Offset (8 bytes) - points to BAT
        bat_offset = 1536  # After footer + header
        struct.pack_into('>Q', header, 16, bat_offset)

        # Header Version (4 bytes)
        struct.pack_into('>I', header, 24, 0x00010000)

        # Max Table Entries (4 bytes)
        num_blocks = (max_size_bytes + (2 * 1024 * 1024 - 1)) // (2 * 1024 * 1024)
        struct.pack_into('>I', header, 28, num_blocks)

        # Block Size (4 bytes) - 2MB blocks
        struct.pack_into('>I', header, 32, 2 * 1024 * 1024)

        # Checksum (4 bytes)
        checksum = 0
        for i in range(1024):
            if i < 36 or i >= 40:
                checksum += header[i]
        checksum = (~checksum) & 0xFFFFFFFF
        struct.pack_into('>I', header, 36, checksum)

        # Parent Unique ID (16 bytes) - all zeros for no parent

        # Parent Timestamp (4 bytes)
        struct.pack_into('>I', header, 56, 0)

        return bytes(header)

    def write_file_to_vhd(self, vhd_id: str, file_path: str,
                         file_data: bytes, user_id: str = None) -> Dict:
        """
        Write a file to VHD

        Args:
            vhd_id: VHD identifier
            file_path: Virtual path in VHD (e.g., /documents/file.pdf)
            file_data: File binary data
            user_id: User ID for ownership

        Returns:
            File metadata
        """
        if vhd_id not in self.vhd_registry:
            raise ValueError(f"VHD {vhd_id} not found")

        vhd_info = self.vhd_registry[vhd_id]
        vhd_path = Path(vhd_info['path'])

        # Check space
        file_size = len(file_data)
        if vhd_info['used_space'] + file_size > vhd_info['size_bytes']:
            raise ValueError("VHD full - insufficient space")

        # Generate file ID
        file_id = hashlib.sha256(f"{file_path}{time.time()}".encode()).hexdigest()

        # Calculate offset for file data
        # Store files sequentially after VHD headers
        offset = 2048 + vhd_info['used_space']  # Skip VHD headers

        # Write file data
        with open(vhd_path, 'r+b') as f:
            f.seek(offset)
            f.write(file_data)

        # Create file metadata
        file_metadata = {
            "file_id": file_id,
            "filename": os.path.basename(file_path),
            "path": file_path,
            "size": file_size,
            "offset": offset,
            "vhd_id": vhd_id,
            "user_id": user_id,
            "created_at": time.time(),
            "hash": hashlib.sha256(file_data).hexdigest()
        }

        # Update file allocation table
        if vhd_id not in self.file_allocation:
            self.file_allocation[vhd_id] = {}
        self.file_allocation[vhd_id][file_id] = file_metadata
        self._save_fat()

        # Update VHD usage
        vhd_info['used_space'] += file_size
        vhd_info['file_count'] += 1
        self._save_registry()

        print(f"✓ File written to VHD: {file_path} ({file_size} bytes)")
        return file_metadata

    def read_file_from_vhd(self, vhd_id: str, file_id: str) -> bytes:
        """
        Read a file from VHD

        Args:
            vhd_id: VHD identifier
            file_id: File identifier

        Returns:
            File binary data
        """
        if vhd_id not in self.file_allocation:
            raise ValueError(f"No files in VHD {vhd_id}")

        if file_id not in self.file_allocation[vhd_id]:
            raise ValueError(f"File {file_id} not found")

        file_metadata = self.file_allocation[vhd_id][file_id]
        vhd_info = self.vhd_registry[vhd_id]
        vhd_path = Path(vhd_info['path'])

        # Read file data
        with open(vhd_path, 'rb') as f:
            f.seek(file_metadata['offset'])
            file_data = f.read(file_metadata['size'])

        # Verify integrity
        file_hash = hashlib.sha256(file_data).hexdigest()
        if file_hash != file_metadata['hash']:
            raise ValueError("File integrity check failed - data corrupted")

        return file_data

    def delete_file_from_vhd(self, vhd_id: str, file_id: str) -> bool:
        """Delete a file from VHD"""
        if vhd_id not in self.file_allocation:
            return False

        if file_id not in self.file_allocation[vhd_id]:
            return False

        file_metadata = self.file_allocation[vhd_id][file_id]

        # Mark space as free (in production, implement proper space reclamation)
        vhd_info = self.vhd_registry[vhd_id]
        vhd_info['used_space'] -= file_metadata['size']
        vhd_info['file_count'] -= 1

        # Remove from allocation table
        del self.file_allocation[vhd_id][file_id]
        self._save_fat()
        self._save_registry()

        print(f"✓ File deleted from VHD: {file_metadata['filename']}")
        return True

    def list_files_in_vhd(self, vhd_id: str, user_id: str = None) -> List[Dict]:
        """List all files in a VHD"""
        if vhd_id not in self.file_allocation:
            return []

        files = list(self.file_allocation[vhd_id].values())

        # Filter by user if specified
        if user_id:
            files = [f for f in files if f.get('user_id') == user_id]

        return files

    def get_vhd_info(self, vhd_id: str) -> Optional[Dict]:
        """Get VHD information"""
        return self.vhd_registry.get(vhd_id)

    def list_vhds(self, user_id: str = None) -> List[Dict]:
        """List all VHDs"""
        vhds = list(self.vhd_registry.values())

        if user_id:
            vhds = [v for v in vhds if v.get('user_id') == user_id]

        return vhds

    def get_usage_stats(self, vhd_id: str) -> Dict:
        """Get usage statistics for a VHD"""
        if vhd_id not in self.vhd_registry:
            return {}

        vhd_info = self.vhd_registry[vhd_id]

        return {
            "vhd_id": vhd_id,
            "name": vhd_info['name'],
            "total_space": vhd_info['size_bytes'],
            "used_space": vhd_info['used_space'],
            "free_space": vhd_info['size_bytes'] - vhd_info['used_space'],
            "usage_percent": (vhd_info['used_space'] / vhd_info['size_bytes'] * 100) if vhd_info['size_bytes'] > 0 else 0,
            "file_count": vhd_info['file_count']
        }

    def delete_vhd(self, vhd_id: str) -> bool:
        """Delete a VHD (mark as deleted, don't actually remove file)"""
        if vhd_id not in self.vhd_registry:
            return False

        vhd_info = self.vhd_registry[vhd_id]
        vhd_info['status'] = 'deleted'
        vhd_info['deleted_at'] = time.time()

        self._save_registry()

        print(f"✓ VHD marked as deleted: {vhd_id}")
        return True