"""
Direct SMTP test to debug Gmail authentication
"""
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('SMTP_USERNAME')
password = os.getenv('SMTP_PASSWORD')
server = os.getenv('SMTP_SERVER')
port = int(os.getenv('SMTP_PORT'))

print(f"Testing SMTP connection...")
print(f"Server: {server}:{port}")
print(f"Username: {username}")
print(f"Password length: {len(password)}")

try:
    print("\n1. Connecting to SMTP server...")
    server_obj = smtplib.SMTP(server, port)
    print("   ✓ Connected")

    print("2. Starting TLS...")
    server_obj.starttls()
    print("   ✓ TLS started")

    print("3. Attempting login...")
    server_obj.login(username, password)
    print("   ✓ Login successful!")

    print("\n✓ All checks passed! SMTP is working.")
    server_obj.quit()

except smtplib.SMTPAuthenticationError as e:
    print(f"   ✗ Authentication failed: {e}")
    print("\n   Possible fixes:")
    print("   1. Verify app password at: https://myaccount.google.com/apppasswords")
    print("   2. Ensure 2-Step Verification is enabled")
    print("   3. Try generating a new app password")

except Exception as e:
    print(f"   ✗ Connection error: {e}")
