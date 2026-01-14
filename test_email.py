"""
Test email sending with Gmail App Password
"""
import os
from dotenv import load_dotenv
from auth_system.complete_auth import AuthenticationSystem

# Load environment variables
load_dotenv()

# Check if credentials are loaded
print("Checking email configuration...")
print(f"SMTP Server: {os.getenv('SMTP_SERVER')}")
print(f"SMTP Port: {os.getenv('SMTP_PORT')}")
print(f"Username: {os.getenv('SMTP_USERNAME')}")
print(f"Password: {'*' * len(os.getenv('SMTP_PASSWORD', ''))}")

# Test email
auth = AuthenticationSystem()

print("\nSending test email...")
result = auth.send_email(
    to_email="ndijennifernkeh@gmail.com",
    subject="Test Email from Cloud Storage System",
    body="This is a test email. If you receive this, email sending is working!"
)

if result:
    print("✓ Email sent successfully!")
else:
    print("✗ Email sending failed!")
