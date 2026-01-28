import { Claim } from '@/types/claims';

export const MOCK_CLAIMS: Claim[] = [
    {
        id: 'claim-001',
        userId: 'user-123',
        policyId: 'policy-456',
        tier: 'classique',
        type: 'medical',
        status: 'under_review',
        amount: 35000,
        description: 'Consultation et médicaments pour traitement paludisme',
        incidentDate: new Date('2026-01-20'),
        photos: [
            '/images/placeholder-receipt.jpg',
            '/images/placeholder-prescription.jpg'
        ],
        createdAt: new Date('2026-01-21'),
        updatedAt: new Date('2026-01-22'),
    },
    {
        id: 'claim-002',
        userId: 'user-123',
        policyId: 'policy-456',
        tier: 'classique',
        type: 'accident',
        status: 'approved',
        amount: 125000,
        description: 'Accident de moto - soins d\'urgence et radiographie',
        incidentDate: new Date('2026-01-10'),
        photos: [
            '/images/placeholder-xray.jpg'
        ],
        createdAt: new Date('2026-01-11'),
        updatedAt: new Date('2026-01-15'),
        reviewNotes: 'Claim approuvé. Paiement en cours de traitement.',
        reviewedBy: 'Admin',
        reviewedAt: new Date('2026-01-14'),
    },
    {
        id: 'claim-003',
        userId: 'user-123',
        policyId: 'policy-456',
        tier: 'classique',
        type: 'medical',
        status: 'paid',
        amount: 50000,
        description: 'Consultation spécialiste et analyses médicales',
        incidentDate: new Date('2025-12-28'),
        photos: [],
        createdAt: new Date('2025-12-29'),
        updatedAt: new Date('2026-01-05'),
        reviewNotes: 'Claim validé et payé.',
        reviewedBy: 'Admin',
        reviewedAt: new Date('2026-01-02'),
        paidAt: new Date('2026-01-05'),
    },
    {
        id: 'claim-004',
        userId: 'user-123',
        policyId: 'policy-456',
        tier: 'classique',
        type: 'property',
        status: 'rejected',
        amount: 200000,
        description: 'Dégât des eaux - réparation plafond',
        incidentDate: new Date('2025-12-15'),
        photos: [
            '/images/placeholder-damage.jpg'
        ],
        createdAt: new Date('2025-12-16'),
        updatedAt: new Date('2025-12-20'),
        reviewNotes: 'Claim rejeté - Sinistre non couvert par le plan Classique. Ce type de dommage nécessite le plan Pro.',
        reviewedBy: 'Admin',
        reviewedAt: new Date('2025-12-18'),
    }
];
