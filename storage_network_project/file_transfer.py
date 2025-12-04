import os
import hashlib
import math
import requests
import time
from typing import List, Dict, Optional


class FileChunk:
    """Represents a piece of a file"""

    def __init__(self, chunk_id, data, checksum):
        self.chunk_id = chunk_id
        self.data = data
        self.checksum = checksum
        self.size = len(data)


class FileTransferManager:
    """Handles file chunking and transfer between nodes"""

    CHUNK_SIZE = 1024 * 1024  # 1MB chunks

    @staticmethod
    def chunk_file(file_path: str) -> tuple:
        """
        Break a file into chunks
        Returns: (file_id, file_name, file_size, chunks_list)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_id = hashlib.md5(f"{file_name}-{time.time()}".encode()).hexdigest()

        chunks = []
        chunk_id = 0

        print(f"📦 Chunking file: {file_name} ({file_size} bytes)")

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(FileTransferManager.CHUNK_SIZE)
                if not data:
                    break

                # Calculate checksum for this chunk
                checksum = hashlib.md5(data).hexdigest()

                chunk = FileChunk(chunk_id, data, checksum)
                chunks.append(chunk)
                chunk_id += 1

        print(f"✂️  Created {len(chunks)} chunks")
        return file_id, file_name, file_size, chunks

    @staticmethod
    def send_chunk(target_node_url: str, file_id: str, chunk: FileChunk) -> bool:
        """
        Send a single chunk to a target node
        Returns: True if successful (ACK received), False otherwise
        """
        try:
            # Convert binary data to hex string for JSON transfer
            chunk_data_hex = chunk.data.hex()

            response = requests.post(
                f"{target_node_url}/receive_chunk",
                json={
                    "file_id": file_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_data": chunk_data_hex,
                    "checksum": chunk.checksum,
                    "size": chunk.size
                },
                timeout=10
            )

            if response.status_code == 200:
                ack_data = response.json()
                if ack_data.get('ack') == chunk.chunk_id:
                    print(f"✅ ACK received for chunk {chunk.chunk_id}")
                    return True

            print(f"❌ Failed to send chunk {chunk.chunk_id}")
            return False

        except Exception as e:
            print(f"❌ Error sending chunk {chunk.chunk_id}: {e}")
            return False

    @staticmethod
    def transfer_file(source_file_path: str, target_node_url: str, chunks_per_window: int = 3) -> bool:
        """
        Transfer entire file to target node using TCP-style windowing
        chunks_per_window: How many chunks to send before waiting for ACKs
        """
        print("=" * 60)
        print(f"🚀 Starting file transfer to {target_node_url}")
        print("=" * 60)

        # Chunk the file
        file_id, file_name, file_size, chunks = FileTransferManager.chunk_file(source_file_path)

        # Send metadata first
        try:
            response = requests.post(
                f"{target_node_url}/prepare_receive",
                json={
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "total_chunks": len(chunks)
                },
                timeout=5
            )

            if response.status_code != 200:
                print(f"❌ Target node rejected file transfer")
                return False

        except Exception as e:
            print(f"❌ Could not prepare target node: {e}")
            return False

        # Transfer chunks in windows (simulating TCP windowing)
        total_chunks = len(chunks)
        chunks_sent = 0

        for i in range(0, total_chunks, chunks_per_window):
            window_chunks = chunks[i:i + chunks_per_window]

            print(f"\n📤 Sending window: chunks {i} to {i + len(window_chunks) - 1}")

            # Send all chunks in this window
            window_success = True
            for chunk in window_chunks:
                if FileTransferManager.send_chunk(target_node_url, file_id, chunk):
                    chunks_sent += 1
                else:
                    window_success = False
                    break

                # Show progress
                progress = (chunks_sent / total_chunks) * 100
                print(f"📊 Progress: {chunks_sent}/{total_chunks} chunks ({progress:.1f}%)")

            if not window_success:
                print(f"❌ Transfer failed at chunk {i}")
                return False

        print("\n" + "=" * 60)
        print(f"✅ File transfer completed successfully!")
        print(f"📁 File: {file_name}")
        print(f"📦 Total chunks: {total_chunks}")
        print(f"💾 Total size: {file_size} bytes")
        print("=" * 60)

        return True