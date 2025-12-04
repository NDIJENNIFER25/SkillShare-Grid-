from file_transfer import FileTransferManager
import sys
import os

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python test_transfer.py <file_path> <target_node_port>")
        print("Example: python test_transfer.py test.txt 5002")
        sys.exit(1)

    file_path = sys.argv[1]
    target_port = sys.argv[2]
    target_url = f"http://127.0.0.1:{target_port}"

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Transfer the file
    success = FileTransferManager.transfer_file(file_path, target_url, chunks_per_window=3)

    if success:
        print("\n🎉 Transfer completed successfully!")
    else:
        print("\n❌ Transfer failed!")