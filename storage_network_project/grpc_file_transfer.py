import grpc
import os
import sys
import hashlib
import math
import storage_pb2
import storage_pb2_grpc

class FileTransferClient:
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks

    @staticmethod
    def transfer_file(file_path, target_host, target_port):
        """Transfer file to target node using gRPC"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_id = hashlib.md5(f"{file_name}-{target_port}".encode()).hexdigest()

        print("=" * 60)
        print(f"🚀 Starting gRPC file transfer")
        print("=" * 60)
        print(f"📁 File: {file_name}")
        print(f"💾 Size: {file_size} bytes")
        print(f"🎯 Target: {target_host}:{target_port}")
        print("=" * 60)

        # Connect to target node
        channel = grpc.insecure_channel(f'{target_host}:{target_port}')
        stub = storage_pb2_grpc.FileTransferServiceStub(channel)

        # Calculate chunks
        num_chunks = math.ceil(file_size / FileTransferClient.CHUNK_SIZE)
        print(f"✂️  Total chunks: {num_chunks}")

        # Prepare target node
        try:
            response = stub.PrepareReceive(storage_pb2.PrepareRequest(
                file_id=file_id,
                file_name=file_name,
                file_size=file_size,
                total_chunks=num_chunks
            ))

            if not response.ready:
                print(f"❌ Target node not ready: {response.message}")
                return False

        except Exception as e:
            print(f"❌ Failed to prepare target: {e}")
            return False

        # Transfer chunks
        chunks_sent = 0
        with open(file_path, 'rb') as f:
            chunk_id = 0
            while True:
                chunk_data = f.read(FileTransferClient.CHUNK_SIZE)
                if not chunk_data:
                    break

                checksum = hashlib.md5(chunk_data).hexdigest()

                try:
                    response = stub.TransferChunk(storage_pb2.ChunkRequest(
                        file_id=file_id,
                        chunk_id=chunk_id,
                        chunk_data=chunk_data,
                        checksum=checksum
                    ))

                    if response.success:
                        chunks_sent += 1
                        progress = (chunks_sent / num_chunks) * 100
                        print(f"✅ Chunk {chunks_sent}/{num_chunks} sent ({progress:.1f}%)")
                    else:
                        print(f"❌ Chunk {chunk_id} failed")
                        return False

                except Exception as e:
                    print(f"❌ Error sending chunk {chunk_id}: {e}")
                    return False

                chunk_id += 1

        channel.close()

        print("\n" + "=" * 60)
        print("✅ File transfer completed successfully!")
        print("=" * 60)
        return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python grpc_file_transfer.py <file_path> <target_port>")
        print("Example: python grpc_file_transfer.py test.txt 5002")
        sys.exit(1)

    file_path = sys.argv[1]
    target_port = int(sys.argv[2])

    FileTransferClient.transfer_file(file_path, 'localhost', target_port)