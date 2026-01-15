import json
import bcrypt
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class UserManager:
    """Manages user accounts and authentication with email OTP"""

    def __init__(self, users_db_path: str = "auth_system/users.json",
                 email_config: Optional[Dict] = None):
        self.users_db_path = Path(users_db_path)
        self.users_db_path.parent.mkdir(exist_ok=True)
        self.users = self._load_users()

        # Email configuration
        self.email_config = email_config or {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "from_email": "sasbergson@gmail.com",
            "app_password": "tgnw azxw lfjr jsuz"  # From your params.py
        }

        # OTP storage (in-memory for now)
        self.active_otps: Dict[str, Dict] = {}

    def _load_users(self) -> Dict:
        """Load users from JSON database"""
        if self.users_db_path.exists():
            with open(self.users_db_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_users(self):
        """Save users to JSON database"""
        with open(self.users_db_path, 'w') as f:
            json.dump(self.users, f, indent=2)

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def _send_otp_email(self, to_email: str, otp: str, username: str) -> bool:
        """Send OTP via email"""
        try:
            # Create email message
            subject = "Your Cloud Storage Login OTP"
            body = f"""
Hello {username},

Your One-Time Password (OTP) for logging into Cloud Storage System is:

{otp}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

Best regards,
Cloud Storage System Team
            """

            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            print(f"📧 Connecting to SMTP server...")
            with smtplib.SMTP(self.email_config['smtp_server'],
                            self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['from_email'],
                           self.email_config['app_password'])
                server.send_message(msg)
                print(f"✅ OTP email sent to {to_email}")
                return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def register_user(self, username: str, email: str, password: str) -> Dict:
        """
        Register a new user

        Args:
            username: Unique username
            email: User's email address
            password: Plain text password (will be hashed)

        Returns:
            Dict with status and message
        """
        # Validate username
        if username in self.users:
            return {
                "status": "error",
                "message": "Username already exists"
            }

        # Validate email format (basic check)
        if '@' not in email or '.' not in email:
            return {
                "status": "error",
                "message": "Invalid email format"
            }

        # Check if email already registered
        for user_data in self.users.values():
            if user_data['email'] == email:
                return {
                    "status": "error",
                    "message": "Email already registered"
                }

        # Validate password strength
        if len(password) < 6:
            return {
                "status": "error",
                "message": "Password must be at least 6 characters"
            }

        # Create user
        user_id = f"user_{secrets.token_hex(8)}"
        self.users[username] = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "created_at": datetime.now().isoformat(),
            "storage_quota_gb": 1,
            "verified": False
        }

        self._save_users()

        return {
            "status": "success",
            "message": "User registered successfully",
            "user_id": user_id
        }

    def generate_otp(self, username: str) -> Optional[str]:
        """Generate a 6-digit OTP for a user"""
        if username not in self.users:
            return None

        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

        # Store OTP with 5-minute expiry
        self.active_otps[username] = {
            "otp": otp,
            "generated_at": datetime.now().isoformat(),
            "expires_in_seconds": 300  # 5 minutes
        }

        return otp

    def verify_otp(self, username: str, otp: str) -> bool:
        """Verify an OTP for a user"""
        if username not in self.active_otps:
            return False

        stored_otp = self.active_otps[username]['otp']

        if stored_otp == otp:
            # Mark user as verified
            if username in self.users:
                self.users[username]['verified'] = True
                self._save_users()

            # Remove used OTP
            del self.active_otps[username]
            return True

        return False

    def authenticate(self, username: str, password: str, send_email: bool = False) -> Dict:
        """
        Authenticate a user (Step 1 of 2FA)

        Args:
            username: Username
            password: Password
            send_email: If True, send OTP via email

        Returns:
            Dict with authentication status
        """
        if username not in self.users:
            return {
                "status": "error",
                "message": "Invalid username or password"
            }

        user = self.users[username]

        if not self._verify_password(password, user['password_hash']):
            return {
                "status": "error",
                "message": "Invalid username or password"
            }

        # Generate OTP for 2FA
        otp = self.generate_otp(username)

        # Send email if requested
        email_sent = False
        if send_email:
            email_sent = self._send_otp_email(user['email'], otp, username)

        return {
            "status": "otp_required",
            "message": "Password correct. OTP sent to email." if email_sent else "Password correct. Check console for OTP.",
            "otp": otp if not send_email else None,  # Only show OTP if not sending email
            "email": user['email'],
            "email_sent": email_sent
        }

    def complete_login(self, username: str, otp: str) -> Dict:
        """
        Complete login with OTP (Step 2 of 2FA)

        Returns:
            Dict with login status and user info
        """
        if not self.verify_otp(username, otp):
            return {
                "status": "error",
                "message": "Invalid or expired OTP"
            }

        user = self.users[username]

        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "user_id": user['user_id'],
                "username": user['username'],
                "email": user['email'],
                "storage_quota_gb": user['storage_quota_gb']
            }
        }

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user information (without sensitive data)"""
        if username not in self.users:
            return None

        user = self.users[username].copy()
        del user['password_hash']  # Don't expose password hash
        return user

    def list_users(self) -> list:
        """List all usernames"""
        return list(self.users.keys())