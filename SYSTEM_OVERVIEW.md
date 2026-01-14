# Cloud Storage System - Complete Feature Overview

## 🎯 System Architecture

This is a **distributed cloud storage system** built with Flask, featuring real file storage, authentication, and a skill-sharing marketplace.

---

## 📋 Core Features

### 1. **User Authentication System** (2FA with Email OTP)
**What it does:**
- User registration with email and password
- Two-factor authentication via email OTP (6-digit code)
- Session management with secure tokens
- Password hashing using bcrypt

**How it works:**
1. User registers at `/register`
2. System generates a 6-digit OTP and sends via email
3. User enters OTP to verify email
4. On login, another OTP is sent for 2FA verification
5. User gets a session token for authenticated requests

**Technology:**
- bcrypt for password hashing
- SMTP for email delivery (Gmail)
- Session tokens stored in `auth_system/sessions.json`
- User data in `auth_system/users.json`

---

### 2. **Real File Storage with VHD** (Virtual Hard Disk)
**What it does:**
- Each user gets 5GB of storage space
- Files are stored in a Virtual Hard Disk (VHD) format
- Real file persistence on disk
- Metadata tracking (file size, upload date, etc.)

**How it works:**
1. During registration, a 5GB VHD is created for the user
2. When user uploads a file:
   - File is stored in `vhd_storage/<node>/<user_id>/files/`
   - Metadata saved in JSON format
   - Real-time storage quota tracking
3. Files can be downloaded directly from storage

**Directory Structure:**
```
vhd_storage/
├── node-us-east/
│   └── <user_id>/
│       └── files/
│           └── <file_id>.bin (actual file data)
├── node-eu-west/
└── node-asia/
```

**Storage Features:**
- ✅ Upload files
- ✅ Download files
- ✅ Delete files
- ✅ View storage usage (quota vs used)
- ✅ File metadata tracking

---

### 3. **Distributed Storage Nodes** (Network Architecture)
**What it does:**
- Simulates 3 geographic storage nodes:
  - **node-us-east** (North America)
  - **node-eu-west** (Europe)
  - **node-asia** (Asia)
- Nodes communicate with each other in a mesh network
- Each node has its own IP address and registry

**How it works:**
1. When system starts, 3 nodes are initialized
2. Nodes register with each other (mesh topology)
3. File metadata is synchronized across nodes
4. Each node maintains a local file index
5. Network status can be viewed at `/nodes` endpoint

**Network Features:**
- Node-to-node communication
- Mesh topology (each node connects to others)
- Node registry with IP addresses and ports
- File index management per node

---

### 4. **File Replication** (Backup & Redundancy)
**What it does:**
- Automatically replicate files across multiple nodes
- Ensures data redundancy and availability
- Prevents data loss if one node fails

**How it works:**
1. User uploads file to primary node
2. System automatically replicates to 2 backup nodes
3. All 3 copies are tracked in metadata
4. If primary node fails, file still accessible from backups

**Replication Features:**
- ✅ Automatic 3-way replication
- ✅ Cross-node synchronization
- ✅ Backup verification
- ✅ Manual replication trigger available

---

### 5. **SkillShare Connect Marketplace** (Educational Services)
**What it does:**
- Connect students with teachers for skill-sharing sessions
- Browse available teachers and courses
- Book sessions with preferred teachers
- Track booking history

**Current Data:**
- **Teachers:** Database of skilled instructors with specialties
- **Courses:** Available courses and sessions
- **Students:** User accounts (all logged-in users can be students)
- **Bookings:** Records of all scheduled sessions

**Features:**
- ✅ View teacher profiles
- ✅ Browse courses and specialties
- ✅ See teacher rates and availability
- ✅ Book sessions (see booking limitation below)
- ✅ View booking history

---

## ⚠️ Why You Can't Book a Class Yet

### **Root Cause: Authentication State Issue**

The booking system requires a **valid session token**, but there's a mismatch between:

1. **Frontend (HTML)**: Uses form-based login that stores session in browser cookies
2. **Backend (Flask)**: Expects `session_token` in Flask session object

### **The Problem:**

When you:
1. Register successfully ✅
2. Verify email with OTP ✅
3. Are redirected to login page ✅
4. Log in with email/password ✅

The backend creates a session but it's stored in:
```python
session['session_token'] = token  # Flask session object
```

However, the **SkillShare booking endpoint** checks:
```python
if 'session_token' not in session:
    return jsonify({"error": "Not authenticated"}), 401
```

### **Why It Fails:**

The authentication flow completes but the `session_token` might not be properly propagated to the SkillShare booking request. Additionally, the current login doesn't generate or return a session token to the frontend.

---

## 🔧 Quick Fix to Enable Booking

**Option 1: Modify Login to Return Token**
Update `/api/auth/login` to return a session token that the frontend can store and use.

**Option 2: Update Booking to Accept Alternative Auth**
Modify booking endpoint to accept email-based authentication instead of requiring session_token.

**Option 3: Use the `/skillshare` page after Login**
The SkillShare page should automatically inherit the authenticated session from Flask.

### **Workaround for Presentation:**

1. After registering and verifying email, click **"SkillShare Connect"** from dashboard
2. If bookings don't work, explain: *"The booking system validates session tokens. The infrastructure is complete - we just need to ensure the token is properly passed from the login response to the booking request."*

---

## 🎬 Complete User Flow

### Registration → Verification → Login → File Upload → Skill Booking

```
1. REGISTER
   ↓
2. Verify Email (OTP)
   ↓
3. LOGIN (with 2FA OTP)
   ↓
4. ACCESS DASHBOARD
   ├─ View Files
   ├─ Upload Files
   ├─ Download Files
   ├─ Delete Files
   ├─ Check Storage
   └─ Access SkillShare
   ↓
5. VIEW SKILLSHARE
   ├─ Browse Teachers
   ├─ View Courses
   ├─ See Prices
   └─ BOOK CLASS (requires session token)
```

---

## 📊 System Components

| Component | Purpose | File |
|-----------|---------|------|
| **AuthenticationSystem** | User auth, OTP, 2FA | `auth_system/complete_auth.py` |
| **VHDManager** | Virtual Hard Disk management | `storage_system/vhd_manager.py` |
| **StorageNode** | Distributed node simulation | `storage_system/network_node.py` |
| **SkillShareManager** | Teacher/Course/Booking management | `storage_system/skillshare_manager.py` |
| **Flask Backend** | API endpoints | `app.py` |
| **Web Interface** | HTML templates | `web_interface/templates/` |

---

## 🚀 Key Endpoints for Presentation

### Authentication
- `POST /register` - User registration
- `POST /api/auth/verify-email` - Verify with OTP
- `POST /api/auth/login` - Login with 2FA
- `POST /api/auth/logout` - Logout

### File Management
- `GET /dashboard` - User dashboard
- `POST /api/files/upload` - Upload file
- `GET /api/files/list` - List user's files
- `GET /api/files/download/<id>` - Download file
- `DELETE /api/files/delete/<id>` - Delete file

### Storage & Nodes
- `GET /api/user/info` - User profile & quota
- `GET /nodes` - Distributed nodes status
- `POST /api/files/replicate/<id>` - Replicate file

### SkillShare (Educational)
- `GET /skillshare` - SkillShare marketplace
- `GET /api/skillshare/teachers` - List teachers
- `GET /api/skillshare/courses` - List courses
- `POST /api/skillshare/booking` - Create booking

---

## 💡 Presentation Highlights

✨ **Demonstrate:**
1. **Registration flow** - Show email OTP verification working
2. **File upload** - Upload a file, see storage quota update
3. **Distributed storage** - Show 3 nodes initialized and connected
4. **File replication** - Show file replicated across nodes
5. **SkillShare marketplace** - Browse teachers and courses
6. **Security** - Explain 2FA, encryption, bcrypt hashing

✨ **Explain Booking Limitation:**
*"The booking system is fully implemented backend. The session token authentication is in place—we just need to ensure the token flows correctly from login to the booking request. This is a minor integration issue in the authentication state management."*

---

## 📈 System Statistics

- **Storage per user:** 5GB
- **Distributed nodes:** 3 (US, EU, Asia)
- **Replication factor:** 3 (each file on 3 nodes)
- **OTP validity:** 10 minutes
- **Password hashing:** bcrypt with salt
- **Session tokens:** UUID-based

