export interface Partner {
    id: string; // 'NSIA', 'SUNU', etc.
    name: string; // 'NSIA Assurance'
    logo_url: string; // Partner branding
    color_theme: string; // NSIA blue vs SUNU green
    is_default: boolean; // Which partner to show first
    support_phone: string;
    api_base_url?: string;
}

export type SubscriptionStatus = 'pending_payment' | 'pending_partner_activation' | 'active' | 'expired' | 'cancelled';

export interface CoverageSubscription {
    id: string;
    subscription_number: string; // "SUB-123456"
    partner: Partner; // NEW: Show who underwrites
    partner_product_id: string; // NSIA's internal product code e.g "NSIA-HEALTH-01"
    partner_product_config: any;
    partner_quoted_amount: number; // Price from NSIA API (not calculated by Wali)
    status: SubscriptionStatus;
    partner_policy_number?: string; // NSIA's policy number (not Wali's)
    start_date?: string;
    end_date?: string;
    payment_frequency: 'daily' | 'weekly' | 'monthly';
    created_at: string;
}

export type IncidentStatus = 'draft' | 'submitted_to_wali' | 'forwarded_to_partner' | 'partner_reviewing' | 'partner_resolved';

export interface IncidentReport {
    id: string;
    user_id: string;
    subscription_id: string;
    partner: Partner; // Which insurer handles it
    type: 'medical' | 'accident' | 'property' | 'other';
    reported_amount: number; // What user declared (not "claimed_amount")
    description: string;
    incident_date: string;
    photos: string[];
    status: IncidentStatus;
    partner_reference?: string; // NSIA's claim number
    partner_notes?: string;
    created_at: string;
    forwarded_at?: string;
    resolved_at?: string;
    // Note: No "payout_amount" - Wali doesn't handle money
}

export interface EnrollmentData {
    phone?: string;
    productId: string;
    partnerId: string;
    userId?: string; // Add optional userId
    trade?: string; // Added for SaaS enrollment
    isTest?: boolean;
}

export interface PharmacyPartner {
    id: string;
    name: string;
    subscription_status: 'active' | 'trial' | 'expired';
    trial_ends_at?: string;
    api_quota_remaining: number;
    verifications_today: number;
}

export interface CoverageVerificationResult {
    status: 'active' | 'inactive' | 'expired';
    artisan_name: string;
    max_reimbursement: number;
    coverage_id: string;
    partner_reference: string;
}
