# Wali Platform - Quick Start Guide

## ⚠️ PowerShell Execution Policy

You need to run this command **once** as Administrator to allow scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🚀 Starting the Web PWA

### Step 1: Install Dependencies

```powershell
cd C:\Users\User\.gemini\antigravity\scratch\wali-backend\wali-pwa
npm install
```

### Step 2: Create Environment File

```powershell
Copy-Item .env.local.example .env.local
```

### Step 3: Start Development Server

```powershell
npm run dev
```

The PWA will be available at: **http://localhost:3000**

---

## 🎯 What You'll See

### Login Page (/)
- Phone number input (+225 format)
- "Recevoir le code OTP" button
- ⚠️ Will show error if Notification Service (port 8003) is not running

### Dashboard (/dashboard)
- Stats cards (policies, claims)
- Quick action buttons
- Policies list
- ⚠️ Will show error if Policy Service (port 8000) is not running

---

## 🔧 Optional: Start Backend Services

If you want full functionality (OTP login, policy management), you need to start backend services.

### Prerequisites
- Docker Desktop installed and running
- Python 3.11+
- Go 1.21+
- Node.js 18+

### Option A: Start with Docker (Infrastructure Only)

```powershell
cd C:\Users\User\.gemini\antigravity\scratch\wali-backend\infrastructure
docker-compose -f docker-compose.dev.yml up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (port 9000, console 9001)
- RabbitMQ (port 5672, UI 15672)

### Option B: Start Individual Services Manually

**1. Notification Service** (for OTP login)
```powershell
cd C:\Users\User\.gemini\antigravity\scratch\wali-backend\services\notification-service
npm install
npm run dev
```
Port: 8003

**2. Policy Service** (for policies)
```powershell
cd C:\Users\User\.gemini\antigravity\scratch\wali-backend\services\policy-service
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```
Port: 8000

**3. Claims Service** (for claims)
```powershell
cd C:\Users\User\.gemini\antigravity\scratch\wali-backend\services\claims-service
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8001 --reload
```
Port: 8001

---

## 📱 Testing the Login Flow

Once Notification Service is running:

1. Navigate to http://localhost:3000
2. Enter phone: `+2250123456789` (test number)
3. Click "Recevoir le code OTP"
4. Check Notification Service logs for the generated OTP code
5. Enter the 6-digit code
6. You'll be redirected to `/dashboard`

**Note**: Without real Orange SMS credentials, the OTP will only be logged to console, not sent via SMS.

---

## 🎨 UI Features

### Login Page
- ✅ Responsive design
- ✅ Green theme (Wali branding)
- ✅ 2-step authentication (phone → OTP)
- ✅ 5-minute countdown timer
- ✅ French UI

### Dashboard
- ✅ Stats overview
- ✅ Quick actions (new policy, submit claim)
- ✅ Policies list
- ✅ Logout functionality

---

## 🐛 Troubleshooting

### "Cannot load scripts" error
Run as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port already in use
```powershell
# Find process using port 3000
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess
# Kill it if needed
Stop-Process -Id <process-id>
```

### Notification Service connection error
Check if service is running:
```powershell
Test-NetConnection localhost -Port 8003
```

### Policy Service connection error
Check if service is running:
```powershell
Test-NetConnection localhost -Port 8000
```

---

## 📚 Next Steps

1. **Test UI Only**: Just start PWA to see the interface
2. **Test OTP Flow**: Start Notification Service + PWA
3. **Full Stack**: Start all services (Docker + microservices + PWA)
4. **Production**: Deploy to Côte d'Ivoire hosting

---

## 🔗 Quick Links

- **PWA**: http://localhost:3000
- **Policy API Docs**: http://localhost:8000/docs
- **Claims API Docs**: http://localhost:8001/docs
- **MinIO Console**: http://localhost:9001
- **RabbitMQ UI**: http://localhost:15672

Default credentials for infrastructure services are in `.env.example`.
