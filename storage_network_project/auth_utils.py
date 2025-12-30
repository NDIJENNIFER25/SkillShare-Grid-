import bcrypt
import random

def hash_password(password):
    """Encrypt a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password, hashed_password):
    """Check if a password matches the hashed version"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_otp():
    """Generate a 6-digit OTP code"""
    return str(random.randint(100000, 999999))

def load_credentials():
    """Load user credentials from file"""
    credentials = {}
    emails = {}

    try:
        with open('credentials.txt', 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    username, email, password = parts
                    # Hash the password if it's not already hashed
                    if not password.startswith('$2b$'):
                        password = hash_password(password)
                    credentials[username] = password
                    emails[username] = email
    except FileNotFoundError:
        print("⚠️  credentials.txt not found!")

    return credentials, emails

def verify_node_credentials(username, password):
    """Verify if a node's username and password are correct"""
    credentials, emails = load_credentials()

    if username not in credentials:
        return False, None

    if check_password(password, credentials[username]):
        return True, emails[username]

    return False, None

def print_otp(otp, email):
    """Print OTP to console (since we won't send real emails for now)"""
    print("=" * 60)
    print("📧 OTP VERIFICATION")
    print("=" * 60)
    print(f"📬 Email: {email}")
    print(f"🔑 OTP Code: {otp}")
    print(f"⏰ This code would be sent to the node operator")

    print("=" * 60)
