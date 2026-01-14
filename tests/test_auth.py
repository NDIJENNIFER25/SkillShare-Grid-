import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth_system.user_manager import UserManager

def test_authentication():
    print("=" * 70)
    print("Testing Authentication System")
    print("=" * 70)

    # Initialize UserManager
    user_mgr = UserManager()

    # Test 1: Register users
    print("\n📝 Registering users...")

    result1 = user_mgr.register_user("alice", "alice@example.com", "password123")
    print(f"   Alice: {result1['status']} - {result1['message']}")

    result2 = user_mgr.register_user("bob", "bob@example.com", "securePass456")
    print(f"   Bob: {result2['status']} - {result2['message']}")

    # Test duplicate username
    result3 = user_mgr.register_user("alice", "alice2@example.com", "password123")
    print(f"   Duplicate: {result3['status']} - {result3['message']}")

    # Test 2: List users
    print("\n👥 Registered users:")
    users = user_mgr.list_users()
    for user in users:
        print(f"   - {user}")

    # Test 3: Authentication (Step 1 - Password)
    print("\n🔐 Testing authentication for Alice...")
    auth_result = user_mgr.authenticate("alice", "password123")
    print(f"   Status: {auth_result['status']}")
    print(f"   Message: {auth_result['message']}")

    if auth_result['status'] == 'otp_required':
        otp = auth_result['otp']
        print(f"   📧 OTP generated: {otp}")
        print(f"   📧 Email: {auth_result['email']}")

        # Test 4: Complete login with OTP (Step 2 - 2FA)
        print("\n🔑 Completing login with OTP...")
        login_result = user_mgr.complete_login("alice", otp)
        print(f"   Status: {login_result['status']}")
        print(f"   Message: {login_result['message']}")

        if login_result['status'] == 'success':
            user_info = login_result['user']
            print(f"\n   ✅ Logged in as:")
            print(f"      User ID: {user_info['user_id']}")
            print(f"      Username: {user_info['username']}")
            print(f"      Email: {user_info['email']}")
            print(f"      Storage: {user_info['storage_quota_gb']}GB")

    # Test 5: Wrong password
    print("\n❌ Testing wrong password...")
    wrong_auth = user_mgr.authenticate("alice", "wrongpassword")
    print(f"   Status: {wrong_auth['status']}")
    print(f"   Message: {wrong_auth['message']}")

    # Test 6: Wrong OTP
    print("\n❌ Testing wrong OTP...")
    auth_result2 = user_mgr.authenticate("bob", "securePass456")
    if auth_result2['status'] == 'otp_required':
        wrong_otp_result = user_mgr.complete_login("bob", "000000")
        print(f"   Status: {wrong_otp_result['status']}")
        print(f"   Message: {wrong_otp_result['message']}")

    # Test 7: Get user info
    print("\n📋 Getting user info for Alice...")
    user_info = user_mgr.get_user("alice")
    if user_info:
        print(f"   Username: {user_info['username']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Verified: {user_info['verified']}")
        print(f"   Created: {user_info['created_at'][:19]}")

    print("\n" + "=" * 70)
    print("✅ Authentication System Test Complete!")
    print("=" * 70)

if __name__ == '__main__':
    test_authentication()