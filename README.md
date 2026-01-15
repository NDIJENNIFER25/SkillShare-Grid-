# Cloud Storage System
**Distributed Systems and Cloud Computing Project**

## Overview
A fully functional cloud storage system with real file storage, 2-factor authentication, and distributed node architecture.

## 🌟 Features
✅ **User Registration & Authentication** - Secure 2FA with email OTP
✅ **Real File Storage** - 1GB VHD per user with actual file persistence
✅ **File Management** - Upload, download, delete with web interface
✅ **Storage Quota Management** - Real-time tracking and enforcement
✅ **Distributed Architecture** - Multiple storage nodes with IP addressing
✅ **File Replication** - Cross-node file backup capability
✅ **Email Integration** - OTP delivery via SMTP

## 🛠️ Technology Stack
- **Backend**: Python 3.12, Flask
- **Storage**: Custom VHD Manager with JSON metadata
- **Authentication**: bcrypt password hashing, SMTP email OTP
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Architecture**: Distributed storage nodes with network simulation

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Gmail account for OTP emails

### Setup Steps

1. **Clone/Download the project**

2. **Install dependencies:**
```bash
pip install flask flask-cors bcrypt grpcio grpcio-tools python-dotenv
```

3. **Configure email (optional):**
   - Edit `auth_system/user_manager.py`
   - Update email credentials in `email_config`

4. **Run the application:**
```bash
python web_interface/app.py
```

5. **Access the application:**
   - Open browser to: http://127.0.0.1:5000
   - Register at: http://127.0.0.1:5000/register
   - Login at: http://127.0.0.1:5000/login

## 🚀 Usage Guide

### 1. Register New Account
- Navigate to `/register`
- Enter username, email, and password (min 6 characters)
- System creates 1GB storage space automatically

### 2. Login with 2FA
- Enter username and password
- Check email for 6-digit OTP code
- Enter OTP to complete login

### 3. Manage Files
- **Upload**: Click "Choose File" and select file to upload
- **Download**: Click green download button next to file
- **Delete**: Click red delete button (confirmation required)
- **Monitor**: View real-time storage usage at top of dashboard

## 📂 Project Structure
```
CloudStorageSystem/
├── storage_system/              # Core storage functionality
│   ├── __init__.py
│   ├── vhd_manager.py          # Virtual Hard Disk management
│   └── enhanced_storage_node.py # Storage nodes with networking
│
├── auth_system/                 # Authentication & user management
│   ├── __init__.py
│   ├── user_manager.py         # User registration, login, OTP
│   └── users.json              # User database (auto-created)
│
├── web_interface/               # Web application
│   ├── app.py                  # Flask backend API
│   └── templates/              # HTML templates
│       ├── login.html          # Login page with 2FA
│       ├── register.html       # Registration page
│       └── dashboard.html      # File management dashboard
│
├── vhd_storage/                 # Actual file storage location
│   └── [user_folders]/         # Per-user VHD directories
│
├── tests/                       # Test scripts
│   ├── test_vhd.py             # VHD system tests
│   ├── test_network.py         # Network/node tests
│   ├── test_auth.py            # Authentication tests
│   └── test_email_otp.py       # Email OTP tests
│
└── README.md                    # This file
```

## 🏗️ System Architecture

### Storage Layer
- **VHD Manager**: Creates isolated storage spaces per user
- **Storage Nodes**: Distributed nodes with IP addresses and network communication
- **Metadata Management**: JSON-based file metadata with checksums

### Authentication Layer
- **Password Security**: bcrypt hashing with salt
- **2FA**: Email-based OTP with 5-minute expiration
- **Session Management**: Flask sessions for logged-in users

### Web Interface Layer
- **REST API**: Flask endpoints for all operations
- **Responsive UI**: Modern design with real-time updates
- **File Operations**: Chunked uploads, secure downloads

## 🧪 Testing

Run individual test scripts:
```bash
# Test VHD system
python tests/test_vhd.py

# Test storage network
python tests/test_network.py

# Test authentication
python tests/test_auth.py

# Test email OTP (requires real email)
python tests/test_email_otp.py
```

## 🔒 Security Features
- ✅ Password hashing with bcrypt
- ✅ 2-Factor authentication (2FA)
- ✅ Session-based access control
- ✅ Storage quota enforcement
- ✅ File integrity verification (SHA-256 checksums)
- ✅ Input validation on all forms

## 📊 System Capabilities
- **Users**: Unlimited user accounts
- **Storage per User**: 1GB (configurable)
- **File Size**: Limited by storage quota
- **File Types**: All file types supported
- **Concurrent Users**: Multi-user support via Flask
- **Nodes**: Scalable multi-node architecture

## 🎯 Key Achievements
1. **Real File Storage** - Not simulation, actual disk persistence
2. **Production-Ready Authentication** - Industry-standard security
3. **Distributed Design** - Demonstrates cloud architecture concepts
4. **Full-Stack Integration** - Backend, storage, and frontend working together
5. **Professional UI/UX** - Modern, intuitive interface

## 🚧 Future Enhancements
- [ ] Database integration (PostgreSQL/MySQL)
- [ ] Cloud deployment (AWS/Azure/GCP)
- [ ] HTTPS/SSL encryption
- [ ] File sharing between users
- [ ] Advanced file search and filtering
- [ ] File versioning
- [ ] API documentation (Swagger)
- [ ] Automated backups
- [ ] Load balancing across nodes
- [ ] WebSocket for real-time updates

## 👨‍💻 Development Info
- **Developer**: Jennifer Nkeh
- **Course**: Distributed Systems and Cloud Computing
- **Institution**: ICT University, Yaoundé, Cameroon
- **Instructor**: Engr. Daniel Moune
- **Date**: December 2025
- **Development Time**: 1 day intensive development

## 📝 License
Educational Project - ICT University 2025

---

## 🙏 Acknowledgments
Built as a comprehensive demonstration of distributed systems concepts including:
- Virtual storage management
- Distributed node communication
- Network protocols and addressing
- Cloud authentication patterns
- RESTful API design
- Full-stack web development

---

**For questions or issues, contact: ndijennifer.nkeh@ictuniversity.edu.cm**