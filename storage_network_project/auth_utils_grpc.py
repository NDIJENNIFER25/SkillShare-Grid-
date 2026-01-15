import bcrypt
import time
from email_utils import generate_otp, send_otp_email

# In-memory OTP storage (in production, use database)
otp_storage = {}  # {username: (otp, timestamp)}

def hash_password(password):
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password, hashed_password):
    """Verify password"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def load_credentials():
    """Load credentials from file"""
    credentials = {}
    emails = {}

    try:
        with open('credentials.txt', 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    username, email, password = parts
                    credentials[username] = password
                    emails[username] = email
    except FileNotFoundError:
        print("⚠️  credentials.txt not found, creating default...")
        create_default_credentials()
        return load_credentials()

    return credentials, emails

def create_default_credentials():
    """Create default credentials file"""
    defaults = [
        "node1,node1@example.com,password123",
        "node2,node2@example.com,password456",
        "node3,node3@example.com,password789",
        "node4,node4@example.com,password111",
        "node5,node5@example.com,password222",
    ]

    with open('credentials.txt', 'w') as file:
        for cred in defaults:
            username, email, password = cred.split(',')
            hashed = hash_password(password)
            file.write(f"{username},{email},{hashed}\n")

    print("✅ Created default credentials.txt")

def enroll_user(username, email, password):
    """Add new user to credentials"""
    credentials, emails = load_credentials()

    if username in credentials:
        return False, "Username already exists"

    hashed_password = hash_password(password)

    with open('credentials.txt', 'a') as file:
        file.write(f"{username},{email},{hashed_password}\n")

    return True, "User enrolled successfully"

def verify_credentials(username, password):
    """Verify username and password"""
    credentials, emails = load_credentials()

    if username not in credentials:
        return False, None

    if check_password(password, credentials[username]):
        return True, emails[username]

    return False, None

def create_otp(username, email):
    """Generate and store OTP for user"""
    otp = generate_otp()
    otp_storage[username] = (otp, time.time())
    send_otp_email(email, otp, username)
    return otp

def verify_otp(username, otp):
    """Verify OTP code"""
    if username not in otp_storage:
        return False, "No OTP found for user"

    stored_otp, timestamp = otp_storage[username]

    # Check if OTP expired (10 minutes)
    if time.time() - timestamp > 600:
        del otp_storage[username]
        return False, "OTP expired"

    if stored_otp == otp:
        del otp_storage[username]
        return True, "OTP verified"

    return False, "Invalid OTP"