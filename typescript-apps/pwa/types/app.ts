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
    qr_token?: string;
    // Cancellation
    cancellation_reason?: string;
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
    subscription_status: 'active' | 'trial' | 'expired' | 'suspended';
    trial_ends_at?: string;
    api_quota_remaining: number;
    verifications_today: number;
    
    // Extended info for admin
    email?: string;
    phone?: string;
    address?: string;
    city?: string;
    license_number?: string;
    contact_name?: string;
    
    // Stats
    verification_count?: number;
    total_verifications?: number;
    total_claims?: number;
    total_amount_processed?: number;
    
    // Subscription
    subscription_plan?: 'basic' | 'professional' | 'enterprise';
    monthly_fee?: number;
    
    // Timestamps
    created_at?: string;
    last_active_at?: string;
}

// Admin Pharmacy View
export interface PharmacyVerification {
    id: string;
    pharmacy_id: string;
    pharmacy_name: string;
    patient_name: string;
    patient_phone: string;
    medications: {
        code: string;
        name: string;
        quantity: number;
        unit_price: number;
        total: number;
    }[];
    medication_code?: string;
    total_amount: number;
    wali_covered: number;
    wali_covered_amount?: number;
    patient_paid: number;
    status: 'pending' | 'approved' | 'rejected' | 'paid';
    created_at: string;
    processed_at?: string;
    processed_by?: string;
}

export interface CoverageVerificationResult {
    status: 'active' | 'inactive' | 'expired';
    artisan_name: string;
    max_reimbursement: number;
    coverage_id: string;
    partner_reference: string;
    copay: number;  // Patient's share percentage (e.g., 20 for 20%)
    plan: string;   // Plan name (e.g., 'Standard', 'Premium')
}

// === PHASE 2C: DRUG FORMULARY DATABASE ===

export type DrugCategory = 'pain_relief' | 'antibiotics' | 'chronic' | 'vitamins' | 'other';
export type DrugStatus = 'covered' | 'restricted' | 'not_covered' | 'prior_auth_required';

export interface DrugFormularyItem {
    id: string;
    code: string;              // Unique drug code (e.g., "MED-PARA-500")
    name: string;              // Commercial name
    generic_name: string;      // Generic/INN name
    category: DrugCategory;
    manufacturer: string;
    dosage_form: string;       // e.g., "tablet", "syrup", "injection"
    strength: string;          // e.g., "500mg", "125mg/5ml"
    package_size: string;      // e.g., "20 tablets", "100ml"
    
    // Pricing (in FCFA)
    unit_price: number;
    package_price: number;
    
    // Coverage info
    status: DrugStatus;
    coverage_percentage: number;  // Wali coverage (e.g., 80 for 80%)
    max_quantity_per_claim: number;
    requires_prescription: boolean;
    
    // Stock info (optional, for pharmacy inventory)
    in_stock?: boolean;
    stock_quantity?: number;
    
    // Metadata
    description?: string;
    side_effects?: string[];
    contraindications?: string[];
    created_at: string;
    updated_at: string;
}

export interface DrugSearchResult {
    drugs: DrugFormularyItem[];
    total: number;
    page: number;
    per_page: number;
}

export interface DrugValidationResult {
    valid: boolean;
    drug?: DrugFormularyItem;
    error?: string;
    alternative_drugs?: DrugFormularyItem[];
    quantity?: number;
    waliCovers?: number;
    patientPays?: number;
}
