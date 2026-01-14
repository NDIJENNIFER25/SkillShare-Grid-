"""
Complete Authentication System
Handles user registration, login, OTP verification, 2FA, and email sending
"""
import os
import json
import hashlib
import secrets
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

class AuthenticationSystem:
    """
    Complete authentication system with:
    - User registration
    - Email verification
    - OTP generation and validation
    - 2FA (Two-Factor Authentication)
    - Session management
    - Password hashing
    """

    def __init__(self, data_path: str = "auth_system"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Data files
        self.users_file = self.data_path / "users.json"
        self.sessions_file = self.data_path / "sessions.json"
        self.otps_file = self.data_path / "active_otps.json"

        # Load data
        self.users = self._load_json(self.users_file, {})
        self.sessions = self._load_json(self.sessions_file, {})
        self.active_otps = self._load_json(self.otps_file, {})

        # Email configuration (will be set via environment variables)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)

        # OTP settings
        self.otp_length = 6
        self.otp_expiry_minutes = 10

        # Session settings
        self.session_expiry_hours = 24

    def _load_json(self, file_path: Path, default_data):
        """Load JSON data from file"""
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return default_data

    def _save_json(self, file_path: Path, data):
        """Save JSON data to file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """
        Hash a password with salt

        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)

        # Use SHA-256 with salt
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()

        return pwd_hash, salt

    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify a password against stored hash"""
        pwd_hash, _ = self._hash_password(password, salt)
        return pwd_hash == stored_hash

    def _generate_otp(self) -> str:
        """Generate a random OTP"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])

    def _generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)

    def send_email(self, to_email: str, subject: str, body: str,
                   is_html: bool = False) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML

        Returns:
            True if sent successfully
        """
        if not self.smtp_username or not self.smtp_password:
            print("⚠ Warning: Email credentials not configured")
            print(f"📧 Would send email to {to_email}:")
            print(f"   Subject: {subject}")
            print(f"   Body: {body}")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            print(f"✓ Email sent to {to_email}")
            return True

        except Exception as e:
            print(f"✗ Error sending email: {e}")
            return False

    def register_user(self, email: str, password: str, full_name: str,
                     location: str = None) -> Dict:
        """
        Register a new user

        Args:
            email: User email
            password: User password
            full_name: User's full name
            location: User location (optional)

        Returns:
            Dictionary with registration result
        """
        # Validate email
        if not email or '@' not in email:
            return {"success": False, "error": "Invalid email address"}

        # Check if user already exists
        if email in self.users:
            return {"success": False, "error": "Email already registered"}

        # Validate password strength
        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}

        # Hash password
        pwd_hash, salt = self._hash_password(password)

        # Generate verification OTP
        verification_otp = self._generate_otp()

        # Create user
        user_id = hashlib.sha256(f"{email}{time.time()}".encode()).hexdigest()[:16]

        user_data = {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "location": location,
            "password_hash": pwd_hash,
            "salt": salt,
            "is_verified": False,
            "is_2fa_enabled": False,
           "storage_quota_gb": 5,  # 5GB free storage
            "storage_used_bytes": 0,
            "created_at": time.time(),
            "last_login": None,
            "login_count": 0
        }

        # Save user
        self.users[email] = user_data
        self._save_json(self.users_file, self.users)

        # Store OTP
        self.active_otps[email] = {
            "otp": verification_otp,
            "type": "verification",
            "created_at": time.time(),
            "expires_at": time.time() + (self.otp_expiry_minutes * 60)
        }
        self._save_json(self.otps_file, self.active_otps)

        # Send verification email
        email_body = f"""
        Welcome to CloudStorage System!

        Hello {full_name},

        Thank you for registering. Please verify your email address using this OTP:

        Verification Code: {verification_otp}

        This code will expire in {self.otp_expiry_minutes} minutes.

        If you didn't register for this account, please ignore this email.

        Best regards,
        CloudStorage Team
        """

        self.send_email(email, "Verify Your Email - CloudStorage", email_body.strip())

        print(f"✓ User registered: {email}")
        print(f"📧 Verification OTP: {verification_otp}")

        return {
            "success": True,
            "user_id": user_id,
            "message": "Registration successful. Please check your email for verification code.",
            "otp_sent": True,
            "dev_otp": verification_otp  # Remove in production!
        }

    def verify_email(self, email: str, otp: str) -> Dict:
        """
        Verify user's email with OTP

        Args:
            email: User email
            otp: OTP code

        Returns:
            Verification result
        """
        if email not in self.users:
            return {"success": False, "error": "User not found"}

        if email not in self.active_otps:
            return {"success": False, "error": "No verification code found. Please request a new one."}

        otp_data = self.active_otps[email]

        # Check if OTP expired
        if time.time() > otp_data['expires_at']:
            del self.active_otps[email]
            self._save_json(self.otps_file, self.active_otps)
            return {"success": False, "error": "Verification code expired. Please request a new one."}

        # Verify OTP
        if otp != otp_data['otp']:
            return {"success": False, "error": "Invalid verification code"}

        # Mark user as verified
        self.users[email]['is_verified'] = True
        self._save_json(self.users_file, self.users)

        # Remove used OTP
        del self.active_otps[email]
        self._save_json(self.otps_file, self.active_otps)

        print(f"✓ Email verified: {email}")

        return {
            "success": True,
            "message": "Email verified successfully. You can now log in."
        }

    def resend_verification_otp(self, email: str) -> Dict:
        """Resend verification OTP"""
        if email not in self.users:
            return {"success": False, "error": "User not found"}

        if self.users[email]['is_verified']:
            return {"success": False, "error": "Email already verified"}

        # Generate new OTP
        verification_otp = self._generate_otp()

        # Store OTP
        self.active_otps[email] = {
            "otp": verification_otp,
            "type": "verification",
            "created_at": time.time(),
            "expires_at": time.time() + (self.otp_expiry_minutes * 60)
        }
        self._save_json(self.otps_file, self.active_otps)

        # Send email
        email_body = f"""
        Your new verification code is: {verification_otp}

        This code will expire in {self.otp_expiry_minutes} minutes.
        """

        self.send_email(email, "New Verification Code - CloudStorage", email_body.strip())

        print(f"✓ Verification OTP resent: {email}")
        print(f"📧 New OTP: {verification_otp}")

        return {
            "success": True,
            "message": "New verification code sent to your email.",
            "dev_otp": verification_otp  # Remove in production!
        }

    def login(self, email: str, password: str, require_2fa: bool = False) -> Dict:
        """
        Log in a user

        Args:
            email: User email
            password: User password
            require_2fa: Whether to require 2FA

        Returns:
            Login result with session token
        """
        # Check if user exists
        if email not in self.users:
            return {"success": False, "error": "Invalid email or password"}

        user = self.users[email]

        # Verify password
        if not self._verify_password(password, user['password_hash'], user['salt']):
            return {"success": False, "error": "Invalid email or password"}

        # Check if email is verified
        if not user['is_verified']:
            return {
                "success": False,
                "error": "Please verify your email before logging in",
                "requires_verification": True
            }

        # Check if 2FA is required
        if user['is_2fa_enabled'] or require_2fa:
            # Generate 2FA OTP
            login_otp = self._generate_otp()

            self.active_otps[email] = {
                "otp": login_otp,
                "type": "2fa",
                "created_at": time.time(),
                "expires_at": time.time() + (self.otp_expiry_minutes * 60)
            }
            self._save_json(self.otps_file, self.active_otps)

            # Send 2FA email
            email_body = f"""
            Your login verification code is: {login_otp}

            If you didn't try to log in, please secure your account immediately.

            This code will expire in {self.otp_expiry_minutes} minutes.
            """

            self.send_email(email, "Login Verification Code - CloudStorage", email_body.strip())

            print(f"📧 2FA OTP sent to: {email}")
            print(f"🔐 2FA OTP: {login_otp}")

            return {
                "success": False,
                "requires_2fa": True,
                "message": "Please enter the verification code sent to your email",
                "dev_otp": login_otp  # Remove in production!
            }

        # Create session
        session_token = self._generate_session_token()

        self.sessions[session_token] = {
            "user_id": user['user_id'],
            "email": email,
            "created_at": time.time(),
            "expires_at": time.time() + (self.session_expiry_hours * 3600),
            "last_activity": time.time()
        }
        self._save_json(self.sessions_file, self.sessions)

        # Update user login info
        user['last_login'] = time.time()
        user['login_count'] += 1
        self._save_json(self.users_file, self.users)

        print(f"✓ User logged in: {email}")

        return {
            "success": True,
            "session_token": session_token,
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "full_name": user['full_name'],
                "storage_quota_gb": user['storage_quota_gb'],
                "storage_used_bytes": user['storage_used_bytes']
            },
            "message": "Login successful"
        }

    def verify_2fa(self, email: str, otp: str) -> Dict:
        """Verify 2FA OTP and create session"""
        if email not in self.users:
            return {"success": False, "error": "User not found"}

        if email not in self.active_otps:
            return {"success": False, "error": "No verification code found"}

        otp_data = self.active_otps[email]

        if otp_data['type'] != '2fa':
            return {"success": False, "error": "Invalid verification code"}

        # Check expiry
        if time.time() > otp_data['expires_at']:
            del self.active_otps[email]
            self._save_json(self.otps_file, self.active_otps)
            return {"success": False, "error": "Verification code expired"}

        # Verify OTP
        if otp != otp_data['otp']:
            return {"success": False, "error": "Invalid verification code"}

        # Remove used OTP
        del self.active_otps[email]
        self._save_json(self.otps_file, self.active_otps)

        # Create session
        user = self.users[email]
        session_token = self._generate_session_token()

        self.sessions[session_token] = {
            "user_id": user['user_id'],
            "email": email,
            "created_at": time.time(),
            "expires_at": time.time() + (self.session_expiry_hours * 3600),
            "last_activity": time.time()
        }
        self._save_json(self.sessions_file, self.sessions)

        # Update user login info
        user['last_login'] = time.time()
        user['login_count'] += 1
        self._save_json(self.users_file, self.users)

        print(f"✓ 2FA verified and user logged in: {email}")

        return {
            "success": True,
            "session_token": session_token,
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "full_name": user['full_name'],
                "storage_quota_gb": user['storage_quota_gb'],
                "storage_used_bytes": user['storage_used_bytes']
            },
            "message": "Login successful"
        }

    def validate_session(self, session_token: str) -> Optional[Dict]:
        """
        Validate a session token

        Returns:
            User data if valid, None otherwise
        """
        if session_token not in self.sessions:
            return None

        session = self.sessions[session_token]

        # Check expiry
        if time.time() > session['expires_at']:
            del self.sessions[session_token]
            self._save_json(self.sessions_file, self.sessions)
            return None

        # Update last activity
        session['last_activity'] = time.time()
        self._save_json(self.sessions_file, self.sessions)

        # Return user data
        email = session['email']
        if email in self.users:
            return self.users[email]

        return None

    def logout(self, session_token: str) -> bool:
        """Log out a user"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            self._save_json(self.sessions_file, self.sessions)
            print(f"✓ User logged out")
            return True
        return False

    def enable_2fa(self, email: str) -> Dict:
        """Enable 2FA for a user"""
        if email not in self.users:
            return {"success": False, "error": "User not found"}

        self.users[email]['is_2fa_enabled'] = True
        self._save_json(self.users_file, self.users)

        print(f"✓ 2FA enabled for: {email}")

        return {"success": True, "message": "Two-factor authentication enabled"}

    def disable_2fa(self, email: str) -> Dict:
        """Disable 2FA for a user"""
        if email not in self.users:
            return {"success": False, "error": "User not found"}

        self.users[email]['is_2fa_enabled'] = False
        self._save_json(self.users_file, self.users)

        print(f"✓ 2FA disabled for: {email}")

        return {"success": True, "message": "Two-factor authentication disabled"}

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user data by email"""
        return self.users.get(email)

    def get_all_users(self):
        """Get all users (for admin)"""
        return list(self.users.values())

    def update_storage_usage(self, email: str, bytes_used: int) -> bool:
        """Update user's storage usage"""
        if email not in self.users:
            return False

        self.users[email]['storage_used_bytes'] = bytes_used
        self._save_json(self.users_file, self.users)
        return True

    def get_storage_info(self, email: str) -> Optional[Dict]:
        """Get user's storage information"""
        if email not in self.users:
            return None

        user = self.users[email]
        quota_bytes = user['storage_quota_gb'] * 1024 * 1024 * 1024
        used_bytes = user['storage_used_bytes']

        return {
            "quota_gb": user['storage_quota_gb'],
            "quota_bytes": quota_bytes,
            "used_bytes": used_bytes,
            "free_bytes": quota_bytes - used_bytes,
            "usage_percent": (used_bytes / quota_bytes * 100) if quota_bytes > 0 else 0
        }