import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage_system.vhd_manager import VHDManager

def test_vhd_system():
    print("=" * 60)
    print("Testing VHD Manager")
    print("=" * 60)

    # Initialize VHD Manager
    vhd = VHDManager()

    # Test 1: Create VHD for user
    print("\n1. Creating VHD for user 'alice'...")
    result = vhd.create_vhd("alice", size_gb=1)
    print(f"   Result: {result['status']} - {result['message']}")

    # Test 2: Store a file
    print("\n2. Storing a test file...")
    test_data = b"Hello, this is a test file for cloud storage!" * 100
    result = vhd.store_file("alice", "test.txt", test_data)
    print(f"   Result: {result['status']} - {result['message']}")
    if result['status'] == 'success':
        print(f"   File ID: {result['file_id']}")
        file_id = result['file_id']

    # Test 3: List files
    print("\n3. Listing files for user 'alice'...")
    files = vhd.list_files("alice")
    print(f"   Found {len(files)} file(s)")
    for file in files:
        print(f"   - {file['original_name']} ({file['size_bytes']} bytes)")

    # Test 4: Retrieve file
    print("\n4. Retrieving file...")
    file_data = vhd.retrieve_file("alice", file_id)
    if file_data:
        print(f"   Retrieved: {file_data['metadata']['original_name']}")
        print(f"   Size: {len(file_data['file_data'])} bytes")
        print(f"   Content preview: {file_data['file_data'][:50]}...")

    # Test 5: Storage usage
    print("\n5. Checking storage usage...")
    usage = vhd.get_storage_usage("alice")
    print(f"   Used: {usage['used_mb']} MB / {usage['total_mb']} MB")
    print(f"   Usage: {usage['usage_percent']}%")
    print(f"   Files: {usage['file_count']}")

    # Test 6: Delete file
    print("\n6. Deleting file...")
    result = vhd.delete_file("alice", file_id)
    print(f"   Result: {result['status']} - {result['message']}")

    # Test 7: Final storage check
    print("\n7. Final storage check...")
    usage = vhd.get_storage_usage("alice")
    print(f"   Used: {usage['used_mb']} MB / {usage['total_mb']} MB")
    print(f"   Files: {usage['file_count']}")

    print("\n" + "=" * 60)
    print("VHD Manager Test Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_vhd_system()