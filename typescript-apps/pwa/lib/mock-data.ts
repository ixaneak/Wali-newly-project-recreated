"use client";

import {
    ComplianceStatus,
    FinancialSummary,
    DashboardCounts,
    RecentTransaction,
    ClaimData,
    UserData,
    AnalyticsData,
    PaymentStats
} from './api-client';

export const MOCK_COMPLIANCE: ComplianceStatus = {
    currentMonth: 14,
    totalMonths: 36,
    percentage: 38.9,
    status: 'COMPLIANT'
};

export const MOCK_FINANCIAL_SUMMARY: FinancialSummary = {
    exemptIncome: {
        amount: 45000000,
        currency: 'FCFA',
        trend: 12.4
    },
    taxableIncome: {
        amount: 1200000,
        currency: 'FCFA',
        trend: -2.1
    },
    lastUpdated: new Date().toISOString()
};

export const MOCK_COUNTS: DashboardCounts = {
    claims: 125,
    users: 1250,
    payments: 450,
    issues: 12
};

export const MOCK_TRANSACTIONS: RecentTransaction[] = [
    { id: 'TX-8821', type: 'Prime', amount: 2500, status: 'EXEMPT', date: new Date().toISOString() },
    { id: 'TX-8822', type: 'Prime', amount: 5000, status: 'EXEMPT', date: new Date().toISOString() },
    { id: 'TX-8823', type: 'Ajustement', amount: 1200, status: 'TAXABLE', date: new Date().toISOString() },
];

export const MOCK_CLAIMS: ClaimData[] = [
    {
        id: 'CLM-001',
        user_id: 'USER-782',
        policy_id: 'POL-991',
        claim_type: 'medical',
        amount: 15000,
        description: 'Consultation paludisme',
        incident_date: new Date().toISOString(),
        status: 'submitted',
        photos: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        review_notes: 'En attente de justificatifs complémentaires.',
        reviewed_by: 'Admin',
        reviewed_at: undefined
    },
    {
        id: 'CLM-002',
        user_id: 'USER-901',
        policy_id: 'POL-102',
        claim_type: 'accident',
        amount: 45000,
        description: 'Accident de travail (Atelier)',
        incident_date: new Date().toISOString(),
        status: 'under_review',
        photos: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        review_notes: 'Rapport d\'incident validé. Paiement en cours.',
        reviewed_by: 'Supervisor',
        reviewed_at: new Date().toISOString()
    }
];

export const MOCK_USERS: UserData[] = [
    {
        id: 'USR-CI-001',
        phone: '+225 07070707',
        name: 'Amadou Koné',
        kyc_status: 'verified',
        role: 'artisan',
        region: 'Lagunes',
        created_at: new Date().toISOString()
    },
    {
        id: 'USR-CI-002',
        phone: '+225 05050505',
        name: 'Binta Diop',
        kyc_status: 'pending',
        role: 'artisan',
        region: 'Haut-Sassandra',
        created_at: new Date().toISOString()
    }
];

export const MOCK_PAYMENT_STATS: PaymentStats = {
    total_volume: 1250000,
    pending_volume: 45000,
    failed_volume: 12000,
    success_rate: 98.4,
    provider_breakdown: {
        'MTN': 642000,
        'Orange': 418000,
        'Moov': 190000
    }
};

export const MOCK_ANALYTICS: AnalyticsData = {
    revenue_series: [
        { date: '01/01', value: 450000 },
        { date: '10/01', value: 480000 },
        { date: '20/01', value: 590000 },
        { date: '30/01', value: 850000 },
    ],
    claims_series: [
        { date: 'Jan', count: 12 },
        { date: 'Fév', count: 18 },
        { date: 'Mar', count: 15 },
    ],
    top_regions: [
        { region: 'Lagunes', count: 850 },
        { region: 'San-Pédro', count: 210 },
    ],
    premium_by_type: {
        'Wali Medical': 78,
        'Wali Artisan': 15,
        'Wali Famille': 7
    }
};

// Mobile PWA Mocks
export const MOCK_MOBILE_DASHBOARD = {
    user: {
        id: 'USR-ART-001',
        name: 'Amadou Koné',
        phone: '+225 07070707',
        tier: 'Standard',
        planName: 'Wali Artisan Standard',
        planStatus: 'actif',
        memberSince: '2023-11-12'
    },
    coverage: {
        used: 75000,
        total: 150000,
        currency: 'FCFA'
    },
    notifications: 3,
    recentTransactions: [
        { id: 'MT-1', type: 'utilisation', title: 'Pharmacie Ivoire Santé', amount: 12500, date: new Date().toISOString() },
        { id: 'MT-2', type: 'cotisation', title: 'Cotisation Mensuelle', amount: 2500, date: new Date().toISOString() }
    ]
};

export const MOCK_MOBILE_TRANSACTIONS = [
    { id: 'T-1', type: 'utilisation', title: 'Pharmacie Ivoire Santé', amount: 12500, date: '2024-01-20T10:00:00Z', location: 'Marcory' },
    { id: 'T-2', type: 'cotisation', title: 'Cotisation Janvier', amount: 2500, date: '2024-01-15T09:00:00Z' },
    { id: 'T-3', type: 'utilisation', title: 'Clinique Farandole', amount: 45000, date: '2024-01-10T14:30:00Z', location: 'Treichville' },
];

export const MOCK_PHARMACIES = [
    { id: 'P-1', name: 'Pharmacie St. Jean', address: 'Cocody, Boulevard de France', status: 'ouvert', distance: 0.8, duration: 5, phone: '+225 2722441234', coordinates: { lat: 5.348, lng: -4.0 } },
    { id: 'P-2', name: 'Pharmacie du Plateau', address: 'Plateau, Rue du Commerce', status: 'ouvert', distance: 2.4, duration: 15, phone: '+225 2720214567', coordinates: { lat: 5.328, lng: -4.01 } },
];

export const MOCK_REIMBURSEMENT_STATS = {
    totalSaved: 125000,
    count: 14
};
