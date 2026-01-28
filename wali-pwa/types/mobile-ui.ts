import { PlanTier } from './plans';

export interface DashboardData {
    user: {
        id: string;          // Added for payment linkage
        name: string;
        phone: string;
        tier: PlanTier; // Added tier
        planName: string;
        planStatus: 'actif' | 'inactif';
        memberSince: string;
        avatarUrl?: string;
    };
    coverage: {
        used: number;        // 75000
        total: number;       // 150000
        currency: 'FCFA';
    };
    notifications: number; // unread count
    recentTransactions: Transaction[];
}

export interface Transaction {
    id: string;
    type: 'cotisation' | 'utilisation' | 'remboursement';
    title: string;           // "Pharmacie Ivoire Santé" or "Cotisation mensuelle"
    amount: number;          // 2500
    date: string;           // ISO 8601
    location?: string;      // for utilisations
}

export interface Pharmacy {
    id: string;
    name: string;
    address: string;
    status: 'ouvert' | 'fermé';
    distance: number;       // in km
    duration: number;       // in minutes
    phone: string;
    coordinates: { lat: number; lng: number };
}

export interface ReimbursementStats {
    totalSaved: number;
    count: number;
}
