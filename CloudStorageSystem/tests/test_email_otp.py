import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth_system.user_manager import UserManager

def test_email_otp():
    print("=" * 70)
    print("Testing Email OTP System")
    print("=" * 70)

    # Initialize UserManager
    user_mgr = UserManager()

    # Register a test user with YOUR real email
    print("\n📝 Register a test user...")
    print("⚠️  IMPORTANT: Use YOUR real email address to receive OTP!")
    print()

    # You can change this to your email
    test_email = input("Enter your email address: ")

    result = user_mgr.register_user("testuser", test_email, "TestPass123")
    print(f"\n   Registration: {result['status']} - {result['message']}")

    if result['status'] == 'success':
        # Test authentication with email
        print("\n🔐 Testing authentication with email OTP...")
        print("   Password: TestPass123")

        auth_result = user_mgr.authenticate("testuser", "TestPass123", send_email=True)

        print(f"\n   Status: {auth_result['status']}")
        print(f"   Message: {auth_result['message']}")
        print(f"   Email sent: {auth_result.get('email_sent', False)}")

        if auth_result['status'] == 'otp_required':
            print(f"\n   📧 Check your email: {test_email}")
            print("   📧 You should receive an OTP code")
            print()

            # Get OTP from user
            otp = input("   Enter the OTP you received: ")

            # Complete login
            print("\n🔑 Completing login with OTP...")
            login_result = user_mgr.complete_login("testuser", otp)

            print(f"   Status: {login_result['status']}")
            print(f"   Message: {login_result['message']}")

            if login_result['status'] == 'success':
                user_info = login_result['user']
                print(f"\n   ✅ Successfully logged in!")
                print(f"      Username: {user_info['username']}")
                print(f"      Email: {user_info['email']}")
                print(f"      Storage: {user_info['storage_quota_gb']}GB")

    print("\n" + "=" * 70)
    print("✅ Email OTP Test Complete!")
    print("=" * 70)

if __name__ == '__main__':

    test_email_otp()
