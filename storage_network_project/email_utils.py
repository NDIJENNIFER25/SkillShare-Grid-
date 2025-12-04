import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp, username):
    """
    Send OTP via email
    For now, just prints to console (you can add real email later)
    """
    print("\n" + "=" * 60)
    print("📧 OTP EMAIL NOTIFICATION")
    print("=" * 60)
    print(f"To: {to_email}")
    print(f"Username: {username}")
    print(f"OTP Code: {otp}")
    print("=" * 60)
    print("✅ OTP would be sent to user's email in production")
    print("=" * 60 + "\n")

    # Uncomment below to send real emails (need Gmail App Password)
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = 'your_email@gmail.com'
        msg['To'] = to_email
        msg['Subject'] = 'Your OTP Code - Cloud Storage Network'

        body = f'''
        Hello {username},

        Your OTP code is: {otp}

        This code is valid for 10 minutes.

        If you did not request this code, please ignore this email.

        Best regards,
        Cloud Storage Team
        '''

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('your_email@gmail.com', 'your_app_password')
            server.send_message(msg)
            print(f"✅ OTP sent to {to_email}")
            return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False
    """

    return True

def print_otp_console(email, otp):
    """Print OTP to console for testing"""
    print("\n" + "🔑 " * 20)
    print(f"OTP for {email}: {otp}")
    print("🔑 " * 20 + "\n")