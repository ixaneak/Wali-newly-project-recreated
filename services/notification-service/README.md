# Notification Service

Node.js/TypeScript service for SMS notifications and OTP authentication.

## Features

- **OTP Generation & Verification** (6-digit codes, 5-minute expiry)
- **Rate Limiting** (3 SMS per phone per hour)
- **Orange SMS Integration** with OAuth2
- **Notification Templates** (Payment, Claims, Policy expiring)

## API Endpoints

### OTP
- `POST /api/v1/notifications/otp/generate` - Generate OTP
- `POST /api/v1/notifications/otp/verify` - Verify OTP
- `GET /api/v1/notifications/otp/status/:phone` - Check OTP status

### Notifications
- `POST /api/v1/notifications/send` - Send notification

## Development

```bash
npm install
npm run dev
```

## Environment Variables

```
PORT=8003
REDIS_URL=redis://localhost:6379
ORANGE_SMS_CLIENT_ID=your_client_id
ORANGE_SMS_CLIENT_SECRET=your_client_secret
ORANGE_SENDER_NAME=Wali
```
