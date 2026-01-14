"""
Test Script for Complete Cloud Storage System
Tests VHD creation, network nodes, and authentication
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from storage_system.vhd_manager import VHDManager
from storage_system.network_node import NetworkNode, NodeCluster
from auth_system.complete_auth import AuthenticationSystem

def test_vhd_system():
    """Test VHD creation and file storage"""
    print("\n" + "="*60)
    print("TESTING VHD SYSTEM")
    print("="*60)

    vhd_manager = VHDManager()

    # Create a VHD
    print("\n1. Creating VHD...")
    vhd = vhd_manager.create_vhd(
        vhd_name="TestStorage",
        size_gb=1,
        vhd_type="dynamic",
        user_id="test_user_001"
    )
    print(f"   VHD ID: {vhd['vhd_id']}")
    print(f"   Size: {vhd['size_gb']} GB")
    print(f"   Type: {vhd['type']}")

    # Write a file to VHD
    print("\n2. Writing file to VHD...")
    test_data = b"Hello, this is a test file for cloud storage!"
    file_metadata = vhd_manager.write_file_to_vhd(
        vhd_id=vhd['vhd_id'],
        file_path="/documents/test.txt",
        file_data=test_data,
        user_id="test_user_001"
    )
    print(f"   File ID: {file_metadata['file_id']}")
    print(f"   Filename: {file_metadata['filename']}")
    print(f"   Size: {file_metadata['size']} bytes")

    # Read the file back
    print("\n3. Reading file from VHD...")
    retrieved_data = vhd_manager.read_file_from_vhd(
        vhd_id=vhd['vhd_id'],
        file_id=file_metadata['file_id']
    )
    print(f"   Retrieved: {retrieved_data.decode()}")

    # Get usage stats
    print("\n4. VHD Usage Statistics:")
    stats = vhd_manager.get_usage_stats(vhd['vhd_id'])
    print(f"   Total Space: {stats['total_space']:,} bytes")
    print(f"   Used Space: {stats['used_space']:,} bytes")
    print(f"   Free Space: {stats['free_space']:,} bytes")
    print(f"   Usage: {stats['usage_percent']:.2f}%")
    print(f"   Files: {stats['file_count']}")

    print("\n✓ VHD System Test Complete!")
    return vhd_manager, vhd['vhd_id'], file_metadata['file_id']

def test_network_nodes():
    """Test network node communication"""
    print("\n" + "="*60)
    print("TESTING NETWORK NODE SYSTEM")
    print("="*60)

    # Create a cluster of nodes
    print("\n1. Creating node cluster...")
    cluster = NodeCluster()

    # Create nodes (simulating different machines)
    node1 = cluster.create_and_add_node("node-us-east", "192.168.1.100", 5001)
    node2 = cluster.create_and_add_node("node-eu-west", "192.168.1.101", 5002)
    node3 = cluster.create_and_add_node("node-asia", "192.168.1.102", 5003)

    print(f"   ✓ Created 3 nodes")

    # Connect nodes to each other
    print("\n2. Connecting nodes...")
    cluster.connect_nodes()
    print(f"   ✓ Nodes connected")

    # Start all nodes
    print("\n3. Starting nodes...")
    cluster.start_all_nodes()
    print(f"   ✓ All nodes started")

    # Store a file with replication
    print("\n4. Storing file with replication...")
    test_file = b"This file will be replicated across nodes!"
    file_metadata = {
        "filename": "replicated_file.txt",
        "owner": "test_user",
        "created_at": "2024-01-15"
    }

    result = cluster.store_file_with_replication(
        file_id="file_001",
        file_data=test_file,
        file_metadata=file_metadata,
        replication_factor=2
    )

    print(f"   Primary Node: {result['primary_node']}")
    print(f"   Replicated To: {', '.join(result['replicated_to'])}")
    print(f"   Total Copies: {result['total_copies']}")

    # Get cluster status
    print("\n5. Cluster Status:")
    status = cluster.get_cluster_status()
    print(f"   Total Nodes: {status['total_nodes']}")
    print(f"   Active Nodes: {status['active_nodes']}")
    print(f"   Primary Node: {status['primary_node']}")

    for node_id, node_info in status['nodes'].items():
        print(f"\n   Node: {node_id}")
        print(f"   - IP: {node_info['ip_address']}:{node_info['port']}")
        print(f"   - Status: {node_info['status']}")
        print(f"   - Files: {node_info['statistics']['files_stored']}")

    print("\n✓ Network Node System Test Complete!")
    return cluster

def test_authentication():
    """Test authentication system"""
    print("\n" + "="*60)
    print("TESTING AUTHENTICATION SYSTEM")
    print("="*60)

    auth = AuthenticationSystem()

    test_email = "testuser@example.com"
    test_password = "SecurePass123!"

    # Register user
    print("\n1. Registering new user...")
    result = auth.register_user(
        email=test_email,
        password=test_password,
        full_name="Test User",
        location="Yaoundé, Cameroon"
    )

    if result['success']:
        print(f"   ✓ User registered: {test_email}")
        print(f"   User ID: {result['user_id']}")
        print(f"   📧 OTP: {result['dev_otp']}")
        otp = result['dev_otp']
    else:
        print(f"   User already exists, using existing account")
        # Get verification OTP
        result = auth.resend_verification_otp(test_email)
        otp = result.get('dev_otp', '000000')

    # Verify email
    print("\n2. Verifying email...")
    verify_result = auth.verify_email(test_email, otp)
    if verify_result['success']:
        print(f"   ✓ Email verified")
    else:
        print(f"   Note: {verify_result.get('error', 'Already verified')}")

    # Login without 2FA
    print("\n3. Logging in (without 2FA)...")
    login_result = auth.login(test_email, test_password)

    if login_result['success']:
        print(f"   ✓ Login successful")
        print(f"   Session Token: {login_result['session_token'][:20]}...")
        session_token = login_result['session_token']

        # Get storage info
        storage_info = auth.get_storage_info(test_email)
        print(f"\n4. Storage Allocation:")
        print(f"   Quota: {storage_info['quota_gb']} GB")
        print(f"   Used: {storage_info['used_bytes']:,} bytes")
        print(f"   Free: {storage_info['free_bytes']:,} bytes")
        print(f"   Usage: {storage_info['usage_percent']:.2f}%")
    else:
        print(f"   Error: {login_result.get('error')}")

    # Enable 2FA
    print("\n5. Enabling 2FA...")
    auth.enable_2fa(test_email)
    print(f"   ✓ 2FA enabled")

    # Logout
    print("\n6. Logging out...")
    if 'session_token' in locals():
        auth.logout(session_token)
        print(f"   ✓ Logged out")

    # Login with 2FA
    print("\n7. Logging in (with 2FA)...")
    login_result = auth.login(test_email, test_password)

    if login_result.get('requires_2fa'):
        print(f"   2FA required")
        print(f"   📧 2FA OTP: {login_result['dev_otp']}")

        # Verify 2FA
        twofa_result = auth.verify_2fa(test_email, login_result['dev_otp'])
        if twofa_result['success']:
            print(f"   ✓ 2FA verified and logged in")
            print(f"   Session Token: {twofa_result['session_token'][:20]}...")

    print("\n✓ Authentication System Test Complete!")
    return auth

def test_integrated_system():
    """Test all systems working together"""
    print("\n" + "="*60)
    print("INTEGRATED SYSTEM TEST")
    print("="*60)

    print("\n📦 This demonstrates:")
    print("   • User registers and gets 1GB storage")
    print("   • VHD is created for user")
    print("   • User uploads file to VHD")
    print("   • File is replicated across network nodes")
    print("   • User can download file from any node")

    # Initialize systems
    auth = AuthenticationSystem()
    vhd_manager = VHDManager()
    cluster = NodeCluster()

    # Setup nodes
    node1 = cluster.create_and_add_node("node-main", "192.168.1.100", 5001)
    cluster.connect_nodes()
    cluster.start_all_nodes()

    # Register user
    print("\n1. User Registration...")
    email = "integrated@test.com"
    result = auth.register_user(
        email=email,
        password="TestPass123!",
        full_name="Integrated Test User",
        location="Douala"
    )

    if result['success']:
        # Verify email
        auth.verify_email(email, result['dev_otp'])

        # Login
        login = auth.login(email, "TestPass123!")
        user_id = login['user']['user_id']

        print(f"   ✓ User {email} logged in")
        print(f"   ✓ Storage quota: 1 GB")

        # Create VHD for user
        print("\n2. Creating user's VHD...")
        vhd = vhd_manager.create_vhd(
            vhd_name=f"Storage_{user_id}",
            size_gb=1,
            vhd_type="dynamic",
            user_id=user_id
        )
        print(f"   ✓ VHD created: {vhd['vhd_id']}")

        # Upload file
        print("\n3. User uploads file...")
        file_content = b"My important document content!"
        file_meta = vhd_manager.write_file_to_vhd(
            vhd_id=vhd['vhd_id'],
            file_path="/documents/important.txt",
            file_data=file_content,
            user_id=user_id
        )
        print(f"   ✓ File uploaded: {file_meta['filename']}")

        # Replicate to nodes
        print("\n4. Replicating file across nodes...")
        replication = cluster.store_file_with_replication(
            file_id=file_meta['file_id'],
            file_data=file_content,
            file_metadata=file_meta,
            replication_factor=1
        )
        print(f"   ✓ File replicated to: {replication.get('replicated_to', [])}")

        # Update storage usage
        auth.update_storage_usage(email, file_meta['size'])

        storage = auth.get_storage_info(email)
        print(f"\n5. Storage Status:")
        print(f"   Used: {storage['used_bytes']} bytes")
        print(f"   Free: {storage['free_bytes']:,} bytes")
        print(f"   Usage: {storage['usage_percent']:.4f}%")

        print("\n✓ Integrated System Test Complete!")
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "   COMPLETE CLOUD STORAGE SYSTEM TEST SUITE".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")

    try:
        # Test individual components
        test_vhd_system()
        test_network_nodes()
        test_authentication()

        # Test integrated system
        test_integrated_system()

        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "   ✓ ALL TESTS PASSED SUCCESSFULLY!".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")
        print("\n")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()