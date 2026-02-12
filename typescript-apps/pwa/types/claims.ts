export type ClaimType = 'medical' | 'accident' | 'property' | 'other';

export type ClaimStatus =
    | 'draft'           // Saved locally, not submitted
    | 'submitted'       // Sent to server, awaiting review
    | 'under_review'    // Being reviewed by admin
    | 'approved'        // Claim approved, payment processing
    | 'rejected'        // Claim denied
    | 'paid';           // Payment completed

export interface Claim {
    id: string;
    userId: string;
    policyId?: string;
    tier: string;
    type: ClaimType;
    status: ClaimStatus;
    amount: number;
    description: string;
    incidentDate: Date;
    photos: string[]; // URLs or base64 encoded images
    createdAt: Date;
    updatedAt: Date;
    reviewNotes?: string;
    reviewedBy?: string;
    reviewedAt?: Date;
    paidAt?: Date;
}

export interface CreateClaimRequest {
    type: ClaimType;
    amount: number;
    description: string;
    incidentDate: Date;
    photos: string[];
}

export interface ClaimStatusUpdate {
    claimId: string;
    status: ClaimStatus;
    notes?: string;
}

// Claim type configurations
export const CLAIM_TYPE_CONFIG = {
    medical: {
        label: 'Frais médicaux',
        icon: 'Heart',
        color: 'text-red-600',
        bgColor: 'bg-red-50 dark:bg-red-900/20',
        description: 'Consultations, médicaments, analyses'
    },
    accident: {
        label: 'Accident',
        icon: 'AlertTriangle',
        color: 'text-orange-600',
        bgColor: 'bg-orange-50 dark:bg-orange-900/20',
        description: 'Incidents corporels'
    },
    property: {
        label: 'Dommages matériels',
        icon: 'Home',
        color: 'text-blue-600',
        bgColor: 'bg-blue-50 dark:bg-blue-900/20',
        description: 'Dégâts domicile, équipements'
    },
    other: {
        label: 'Autre',
        icon: 'FileText',
        color: 'text-gray-600',
        bgColor: 'bg-gray-50 dark:bg-gray-800',
        description: 'Autres incidents couverts'
    }
} as const;

// Status configurations
export const CLAIM_STATUS_CONFIG = {
    draft: {
        label: 'Brouillon',
        color: 'text-gray-600',
        bgColor: 'bg-gray-100 dark:bg-gray-800'
    },
    submitted: {
        label: 'Transmis à NSIA', // More accurate for SaaS
        color: 'text-blue-600',
        bgColor: 'bg-blue-100 dark:bg-blue-900/30'
    },
    under_review: {
        label: 'En analyse chez NSIA',
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100 dark:bg-yellow-900/30'
    },
    approved: {
        label: 'Pris en charge',
        color: 'text-emerald-600',
        bgColor: 'bg-emerald-100 dark:bg-emerald-900/30'
    },
    rejected: {
        label: 'Non pris en charge', // Softer than "Rejeté"
        color: 'text-red-600',
        bgColor: 'bg-red-100 dark:bg-red-900/30'
    },
    paid: {
        label: 'Réréglé par NSIA',
        color: 'text-green-600',
        bgColor: 'bg-green-100 dark:bg-green-900/30'
    }
} as const;
