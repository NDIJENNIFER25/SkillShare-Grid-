import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage_system.enhanced_storage_node import StorageNode, StorageNetwork

def test_storage_network():
    print("=" * 70)
    print("Testing Enhanced Storage Network with Real Files")
    print("=" * 70)

    # Create network
    print("\n📡 Creating storage network...")
    network = StorageNetwork("TestCloudNetwork")

    # Create nodes with different IP addresses
    print("\n🖥️  Creating storage nodes...")
    node1 = StorageNode("node-us-east", "192.168.1.10", storage_capacity_gb=20)
    node2 = StorageNode("node-eu-west", "192.168.1.20", storage_capacity_gb=20)
    node3 = StorageNode("node-asia", "192.168.1.30", storage_capacity_gb=20)

    # Add nodes to network
    print("\n➕ Adding nodes to network...")
    network.add_node(node1)
    network.add_node(node2)
    network.add_node(node3)

    # Connect nodes
    print("\n🔗 Connecting nodes...")
    network.connect_nodes("node-us-east", "node-eu-west")
    network.connect_nodes("node-eu-west", "node-asia")
    network.connect_nodes("node-us-east", "node-asia")

    # Create user storage on node1
    print("\n" + "=" * 70)
    print("👤 Setting up user 'bob' with 1GB storage")
    print("=" * 70)
    result = node1.create_user_storage("bob", size_gb=1)
    print(f"Result: {result['status']}")

    # Upload files
    print("\n📤 Uploading files for user 'bob'...")

    # Upload document
    doc_data = b"This is Bob's important document. " * 200
    result1 = node1.upload_file("bob", "document.txt", doc_data)
    print(f"   Document: {result1['status']}")

    # Upload image (simulated)
    image_data = b"\x89PNG\r\n\x1a\n\x00\x00" * 500
    result2 = node1.upload_file("bob", "photo.png", image_data)
    print(f"   Photo: {result2['status']}")

    # Upload video (simulated)
    video_data = b"VIDEO_DATA" * 10000
    result3 = node1.upload_file("bob", "video.mp4", video_data)
    print(f"   Video: {result3['status']}")

    # List files
    print("\n📋 Listing Bob's files...")
    files = node1.list_user_files("bob")
    for i, file in enumerate(files, 1):
        size_kb = file['size_bytes'] / 1024
        print(f"   {i}. {file['original_name']} - {size_kb:.2f} KB - {file['uploaded_at'][:19]}")

    # Check storage usage
    print("\n💾 Checking storage usage...")
    usage = node1.get_user_storage_info("bob")
    if usage:
        print(f"   Used: {usage['used_mb']:.2f} MB / {usage['total_mb']:.2f} MB")
        print(f"   Usage: {usage['usage_percent']:.2f}%")
        print(f"   Files: {usage['file_count']}")

    # Download a file
    print("\n📥 Downloading document.txt...")
    file_id = result1['file_id']
    downloaded = node1.download_file("bob", file_id)
    if downloaded:
        print(f"   ✅ Downloaded: {downloaded['metadata']['original_name']}")
        print(f"   Size: {len(downloaded['file_data'])} bytes")
        print(f"   Preview: {downloaded['file_data'][:50]}...")

    # Replicate file to another node
    print("\n🔄 Replicating file to node-eu-west...")
    # First create storage for bob on node2
    node2.create_user_storage("bob", size_gb=1)
    # Then replicate
    replication_result = node1.replicate_file_to_node("bob", file_id, "node-eu-west")
    print(f"   Replication: {replication_result['status']}")

    # Verify file exists on node2
    print("\n🔍 Verifying file on node-eu-west...")
    files_on_node2 = node2.list_user_files("bob")
    print(f"   Files on node-eu-west: {len(files_on_node2)}")

    # Node statistics
    print("\n📊 Node Statistics:")
    print("-" * 70)
    for node in [node1, node2, node3]:
        stats = node.get_node_stats()
        print(f"\n   Node: {stats['node_id']}")
        print(f"   IP: {stats['ip_address']}")
        print(f"   Requests: {stats['total_requests']}")
        print(f"   Uploads: {stats['total_uploads']}")
        print(f"   Downloads: {stats['total_downloads']}")
        print(f"   Data transferred: {stats['total_mb_transferred']} MB")
        print(f"   Connected to: {', '.join(stats['connected_nodes'])}")

    # Network statistics
    print("\n🌐 Network Statistics:")
    print("-" * 70)
    net_stats = network.get_network_stats()
    print(f"   Network: {net_stats['network_name']}")
    print(f"   Total nodes: {net_stats['total_nodes']}")
    print(f"   Total requests: {net_stats['total_requests']}")
    print(f"   Total uploads: {net_stats['total_uploads']}")
    print(f"   Total downloads: {net_stats['total_downloads']}")
    print(f"   Total data transferred: {net_stats['total_mb_transferred']} MB")

    # Find user files across network
    print("\n🔎 Finding all files for user 'bob' across network...")
    all_files = network.find_user_files("bob")
    for node_id, files in all_files.items():
        print(f"   On {node_id}: {len(files)} file(s)")

    print("\n" + "=" * 70)
    print("✅ Storage Network Test Complete!")
    print("=" * 70)

if __name__ == '__main__':
    test_storage_network()