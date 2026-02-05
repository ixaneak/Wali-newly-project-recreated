# Wali PWA - Next.js 14

Progressive Web App for Wali micro-insurance platform.

## Features

- **Phone OTP Authentication** (5-minute codes)
- **Artisan Dashboard** (policies, claims, payments)
- **Responsive Design** (mobile-first)
- **PWA Support** (offline, installable)
- **French UI** (Côte d'Ivoire market)

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- Axios (API client)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local`:
```bash
cp .env.local.example .env.local
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Backend Services

Make sure all 5 backend services are running:
- Policy Service: `localhost:8000`
- Payment Service: `localhost:8080`
- Claims Service: `localhost:8001`
- Compliance Service: `localhost:8002`
- Notification Service: `localhost:8003`

## Key Routes

- `/login` - Phone OTP authentication
- `/dashboard` - Artisan dashboard
- `/admin` - Admin panel (TODO)
- `/pharmacy` - Pharmacy dashboard (TODO)
