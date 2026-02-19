# Unified Financial Analytics System - Admin Portal Only

## Overview

This document describes the **Unified Financial Analytics** system that combines pharmacy expenses, claims payments, and regular transactions into a comprehensive **admin-only** financial overview for platform management.

**Important**: This feature is **only available on the admin portal** (`/admin/analytics`), not for regular users.

---

## 🏢 Admin Portal Analytics (`/admin/analytics`)

### Problem Statement
Administrators needed a consolidated view of the entire platform's financial health:
- Revenue from premiums vs pharmacy fees
- Claims payout obligations
- Pharmacy ecosystem performance
- Platform profitability metrics

### Solution
A comprehensive admin dashboard with four tabs:

#### 1. Vue Globale (Global Overview)
- **KPI Cards**:
  - Total Revenue (Premiums + Pharmacy Fees)
  - Claims Payments (Payouts to users)
  - Pharmacy Volume (Partner ecosystem)
  - Net Position (Platform profitability)
- **Combined Flow Chart**: Visual comparison of all revenue streams vs payouts
- **Revenue Distribution**: Pie chart showing breakdown by source
- **Key Metrics**: Claims approval rate, average transaction values, user engagement

#### 2. Pharmacies
- Performance ranking of partner pharmacies
- Revenue per pharmacy with growth indicators
- Transaction counts and averages
- Geographic distribution

#### 3. Sinistres (Claims)
- Claims submission statistics
- Approval/rejection breakdown
- Average payout amounts
- Approval rate tracking

#### 4. Flux Détaillés (Detailed Flows)
- Complete breakdown of all revenue sources:
  - Insurance premiums (user cotisations)
  - SaaS fees from pharmacies (15%)
  - Other revenue streams
- Complete breakdown of all payouts:
  - Claims reimbursements
  - Direct pharmacy payments
  - Refunds
- Net position calculation with profitability indicator

---

## 📊 Data Sources Integrated

| Source | Admin View | Description |
|--------|------------|-------------|
| `premiums` | Revenue | Monthly cotisations from users |
| `pharmacy_fees` | Revenue | SaaS fees from pharmacy partners (15%) |
| `claim_payouts` | Payout | Insurance reimbursements to users |
| `pharmacy_reimbursements` | Payout | Direct payments to pharmacies |

---

## 🔌 API Implementation

### Backend Routes (`python-services/policy-service/app/routes/analytics.py`)

```
GET /api/v1/analytics/admin/unified     # Complete platform analytics
GET /api/v1/analytics/admin/summary     # Quick admin summary
```

### Frontend API Client (`typescript-apps/pwa/lib/api-client.ts`)

```typescript
complianceService.getAdminUnifiedAnalytics(timeframe)  // Admin analytics
complianceService.getAdminFinancialSummary()           // Admin summary
```

---

## 📁 Files Modified/Created

### Frontend - Admin Portal Only
| File | Description |
|------|-------------|
| `typescript-apps/pwa/app/admin/(authenticated)/analytics/page.tsx` | **UPDATED** Admin unified analytics |
| `typescript-apps/pwa/lib/api-client.ts` | Added `getAdminUnifiedAnalytics()` method + mock generator |

### Backend
| File | Description |
|------|-------------|
| `python-services/policy-service/app/routes/analytics.py` | **UPDATED** Admin-only analytics API routes |
| `python-services/policy-service/app/main.py` | Registered analytics router |

---

## 🎨 Key Features for Admins

1. **Platform Health Overview**: Overall revenue vs payouts
2. **Pharmacy Ecosystem**: Partner performance tracking
3. **Claims Management**: Approval rates and payout monitoring
4. **Profitability Analysis**: Net position and trends
5. **Multi-timeframe**: 7D, 30D, 90D, 1Y views

---

## 📈 Mock Data (Development)

The system uses realistic mock data for development:

- 47 active pharmacy partners
- 2,847 active users
- 156 claims submitted (79.5% approval rate)
- Daily revenue/payout time series
- Platform net position tracking

---

## 🔄 Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Pharmacy       │     │  Claims         │     │  Payments       │
│  Service        │     │  Service        │     │  Service        │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │  Admin Analytics API      │
                    │  /api/v1/analytics/admin  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Admin Dashboard          │
                    │  /admin/analytics         │
                    └───────────────────────────┘
```

---

## 📝 Usage

### Access Admin Analytics
1. Navigate to `/admin/analytics`
2. Select time period (7D, 30D, 90D, 1Y)
3. Explore tabs: Vue Globale, Pharmacies, Sinistres, Flux Détaillés
4. Review KPI cards and charts
5. Export detailed reports if needed

---

## 🔐 Security

- Admin routes require admin privileges (`verify_admin`)
- Data is scoped to platform-wide metrics only
- No individual user data exposure
- Exports include audit trails

---

## 🚀 Future Enhancements

1. **Real-time Data**: Connect to actual databases
2. **AI Insights**: ML-powered revenue predictions
3. **Comparative Analytics**: Period-over-period analysis
4. **Alert System**: Notifications for anomalies
5. **Drill-down**: Click into specific pharmacies or claims

---

## ⚠️ Note: User Dashboard Unchanged

The user dashboard (`/dashboard`) does **NOT** include financial analytics. Users continue to see:
- Coverage card only
- Recent activity list
- Standard dashboard features

Financial performance analytics are **admin-only**.
