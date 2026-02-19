# Wali Testing - Quick Commands

## Currently Running ✅

### PWA
- **Port**: 3000
- **URL**: http://localhost:3000
- **Status**: Running in background (PID: e06aff4d)

### Notification Service  
- **Port**: 8003
- **Status**: Running in background (PID: 9bf94566)
- **Warning**: Redis not connected

---

## Start Redis (Required for OTP)

```powershell
docker run -d -p 6379:6379 redis:7-alpine
```

Then restart Notification Service:
```powershell
# It should auto-reconnect to Redis
```

---

## Open in Browser

```
http://localhost:3000
```

---

## Stop Services

```powershell
# Find process using port
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess

# Kill process
Stop-Process -Id <PID>
```

---

## Test OTP Flow (With Redis)

1. Start Redis (command above)
2. Open http://localhost:3000
3. Enter: `+2250123456789`
4. Click "Recevoir le code OTP"
5. Check Notification Service terminal for OTP code
6. Enter the code
7. Should redirect to dashboard
