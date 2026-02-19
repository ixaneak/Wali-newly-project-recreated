import {
    PharmacyPartner,
    PharmacyVerification,
    DrugFormularyItem,
    Partner
} from '@/types/app';

export interface PharmacyNotification {
    id: string;
    type: 'new_pharmacy' | 'subscription_expiring' | 'quota_alert' | 'payment_received';
    title: string;
    message: string;
    pharmacy_id?: string;
    pharmacy_name?: string;
    created_at: string;
    read: boolean;
}

export const MOCK_PARTNERS: Partner[] = [
    {
        id: "NSIA",
        name: "NSIA Assurance",
        logo_url: "/partners/nsia.png",
        color_theme: "#1e3a8a",
        is_default: true,
        support_phone: "+225 27 20 20 20 20"
    }
];

export const MOCK_PHARMACIES: PharmacyPartner[] = [
    {
        id: 'PHARM-001',
        name: 'Pharmacie de la Paix',
        email: 'contact@paix-pharma.ci',
        phone: '+225 27 20 30 40 50',
        address: 'Rue des Jardins, Cocody',
        city: 'Abidjan',
        license_number: 'PH-ABJ-2023-001',
        contact_name: 'Dr. Amadou Koné',
        subscription_status: 'active',
        subscription_plan: 'professional',
        monthly_fee: 50000,
        api_quota_remaining: 850,
        verification_count: 1450,
        verifications_today: 12,
        total_verifications: 1450,
        total_claims: 890,
        total_amount_processed: 45000000,
        created_at: '2024-01-15T10:00:00Z',
        last_active_at: '2024-02-18T14:30:00Z'
    },
    {
        id: 'PHARM-002',
        name: 'Pharmacie Centrale Angré',
        email: 'info@pharmacieangre.ci',
        phone: '+225 27 22 33 44 55',
        address: 'Boulevard de France, Angré',
        city: 'Abidjan',
        license_number: 'PH-ABJ-2023-045',
        contact_name: 'Dr. Fatou Diallo',
        subscription_status: 'active',
        subscription_plan: 'basic',
        monthly_fee: 30000,
        api_quota_remaining: 420,
        verification_count: 680,
        verifications_today: 8,
        total_verifications: 680,
        total_claims: 420,
        total_amount_processed: 21000000,
        created_at: '2024-02-01T09:00:00Z',
        last_active_at: '2024-02-18T11:15:00Z'
    },
    {
        id: 'PHARM-003',
        name: 'Pharmacie du Plateau',
        email: 'plateau@pharma.ci',
        phone: '+225 27 20 25 30 35',
        address: 'Avenue du Plateau, Zone 4',
        city: 'Abidjan',
        license_number: 'PH-ABJ-2024-012',
        contact_name: 'Dr. Yves Kouassi',
        subscription_status: 'trial',
        trial_ends_at: '2024-03-01T00:00:00Z',
        subscription_plan: 'professional',
        monthly_fee: 50000,
        api_quota_remaining: 150,
        verification_count: 120,
        verifications_today: 3,
        total_verifications: 120,
        total_claims: 85,
        total_amount_processed: 4200000,
        created_at: '2024-02-10T14:00:00Z',
        last_active_at: '2024-02-17T16:45:00Z'
    },
    {
        id: 'PHARM-004',
        name: 'Pharmacie Santé Plus Bouaké',
        email: 'santeplus.bouake@gmail.com',
        phone: '+225 27 30 40 50 60',
        address: 'Rue Principale, Bouaké',
        city: 'Bouaké',
        license_number: 'PH-BKE-2023-089',
        contact_name: 'Dr. Marie Touré',
        subscription_status: 'expired',
        subscription_plan: 'basic',
        monthly_fee: 30000,
        api_quota_remaining: 0,
        verification_count: 320,
        verifications_today: 0,
        total_verifications: 320,
        total_claims: 180,
        total_amount_processed: 9000000,
        created_at: '2024-01-20T08:30:00Z',
        last_active_at: '2024-02-01T10:00:00Z'
    },
    {
        id: 'PHARM-005',
        name: 'Grande Pharmacie de San Pedro',
        email: 'contact@gpsanpedro.ci',
        phone: '+225 27 35 45 55 65',
        address: 'Zone Portuaire, San Pedro',
        city: 'San Pedro',
        license_number: 'PH-SPD-2024-003',
        contact_name: 'Dr. Jean-Baptiste NGuessan',
        subscription_status: 'active',
        subscription_plan: 'enterprise',
        monthly_fee: 100000,
        api_quota_remaining: 1200,
        verification_count: 2100,
        verifications_today: 25,
        total_verifications: 2100,
        total_claims: 1560,
        total_amount_processed: 78000000,
        created_at: '2023-11-15T11:00:00Z',
        last_active_at: '2024-02-18T15:20:00Z'
    }
];

export const MOCK_PHARMACY_VERIFICATIONS: PharmacyVerification[] = [
    {
        id: 'PV-2024-001',
        pharmacy_id: 'PHARM-001',
        pharmacy_name: 'Pharmacie de la Paix',
        patient_name: 'Koffi Mensah',
        patient_phone: '0707070707',
        medications: [
            { code: 'MED-PARA-500', name: 'Doliprane 500mg', quantity: 2, unit_price: 150, total: 300 },
            { code: 'MED-AMOX-500', name: 'Amoxicilline 500mg', quantity: 1, unit_price: 350, total: 350 }
        ],
        total_amount: 650,
        wali_covered: 520,
        wali_covered_amount: 520,
        patient_paid: 130,
        status: 'paid',
        created_at: '2024-02-18T10:30:00Z',
        processed_at: '2024-02-18T10:35:00Z',
        processed_by: 'admin@wali.ci'
    },
    {
        id: 'PV-2024-002',
        pharmacy_id: 'PHARM-002',
        pharmacy_name: 'Pharmacie Centrale Angré',
        patient_name: 'Aminata Traoré',
        patient_phone: '0708080808',
        medications: [
            { code: 'MED-IBU-400', name: 'Nurofen 400mg', quantity: 1, unit_price: 200, total: 200 }
        ],
        total_amount: 200,
        wali_covered: 160,
        wali_covered_amount: 160,
        patient_paid: 40,
        status: 'pending',
        created_at: '2024-02-18T11:00:00Z'
    },
    {
        id: 'PV-2024-003',
        pharmacy_id: 'PHARM-001',
        pharmacy_name: 'Pharmacie de la Paix',
        patient_name: 'Yao Kouassi',
        patient_phone: '0709090909',
        medications: [
            { code: 'MED-MET-500', name: 'Glucophage 500mg', quantity: 2, unit_price: 450, total: 900 }
        ],
        total_amount: 900,
        wali_covered: 810,
        wali_covered_amount: 810,
        patient_paid: 90,
        status: 'approved',
        created_at: '2024-02-18T09:15:00Z',
        processed_at: '2024-02-18T14:00:00Z'
    },
    {
        id: 'PV-2024-004',
        pharmacy_id: 'PHARM-003',
        pharmacy_name: 'Pharmacie du Plateau',
        patient_name: 'Marie Kone',
        patient_phone: '0701010101',
        medications: [
            { code: 'MED-CET-10', name: 'Zyrtec 10mg', quantity: 1, unit_price: 400, total: 400 },
            { code: 'MED-PARA-500', name: 'Doliprane 500mg', quantity: 1, unit_price: 150, total: 150 }
        ],
        total_amount: 550,
        wali_covered: 440,
        wali_covered_amount: 440,
        patient_paid: 110,
        status: 'pending',
        created_at: '2024-02-18T08:30:00Z'
    },
    {
        id: 'PV-2024-005',
        pharmacy_id: 'PHARM-005',
        pharmacy_name: 'Grande Pharmacie de San Pedro',
        patient_name: 'Bakary Diallo',
        patient_phone: '0702020202',
        medications: [
            { code: 'MED-AMPL-500', name: 'Augmentin 500mg', quantity: 2, unit_price: 600, total: 1200 }
        ],
        total_amount: 1200,
        wali_covered: 960,
        wali_covered_amount: 960,
        patient_paid: 240,
        status: 'paid',
        created_at: '2024-02-17T16:45:00Z',
        processed_at: '2024-02-17T17:00:00Z'
    },
    {
        id: 'PV-2024-006',
        pharmacy_id: 'PHARM-001',
        pharmacy_name: 'Pharmacie de la Paix',
        patient_name: 'Esther Yao',
        patient_phone: '0703030303',
        medications: [
            { code: 'MED-VIT-C-500', name: 'Vitamine C 500mg', quantity: 2, unit_price: 100, total: 200 }
        ],
        total_amount: 200,
        wali_covered: 100,
        wali_covered_amount: 100,
        patient_paid: 100,
        status: 'rejected',
        created_at: '2024-02-17T14:20:00Z',
        processed_at: '2024-02-17T15:00:00Z'
    }
];

export const MOCK_MONTHLY_PERFORMANCE = [
    { month: 'Jan', pharmacies: 2, verifications: 450, amount: 12500000 },
    { month: 'Fév', pharmacies: 3, verifications: 680, amount: 18900000 },
    { month: 'Mar', pharmacies: 4, verifications: 890, amount: 24500000 },
    { month: 'Avr', pharmacies: 4, verifications: 920, amount: 26800000 },
    { month: 'Mai', pharmacies: 5, verifications: 1150, amount: 32400000 },
    { month: 'Juin', pharmacies: 5, verifications: 1280, amount: 35600000 }
];

export const MOCK_NOTIFICATIONS: PharmacyNotification[] = [
    {
        id: 'notif-001',
        type: 'new_pharmacy',
        title: 'Nouvelle pharmacie inscrite',
        message: 'Pharmacie du Plateau a complété son inscription',
        pharmacy_id: 'PHARM-003',
        pharmacy_name: 'Pharmacie du Plateau',
        created_at: '2024-02-18T09:00:00Z',
        read: false
    },
    {
        id: 'notif-002',
        type: 'subscription_expiring',
        title: 'Abonnement expirant',
        message: 'L\'abonnement de Pharmacie Santé Plus expire dans 3 jours',
        pharmacy_id: 'PHARM-004',
        pharmacy_name: 'Pharmacie Santé Plus Bouaké',
        created_at: '2024-02-17T10:00:00Z',
        read: false
    },
    {
        id: 'notif-003',
        type: 'quota_alert',
        title: 'Quota API faible',
        message: 'Pharmacie du Plateau a moins de 200 requêtes restantes',
        pharmacy_id: 'PHARM-003',
        pharmacy_name: 'Pharmacie du Plateau',
        created_at: '2024-02-16T14:30:00Z',
        read: true
    }
];

export const MOCK_FORMULARY: DrugFormularyItem[] = [
    {
        id: 'drug-001',
        code: 'MED-PARA-500',
        name: 'Doliprane',
        generic_name: 'Paracétamol',
        category: 'pain_relief',
        manufacturer: 'Sanofi',
        dosage_form: 'tablet',
        strength: '500mg',
        package_size: '16 tablets',
        unit_price: 150,
        package_price: 2400,
        status: 'covered',
        coverage_percentage: 80,
        max_quantity_per_claim: 3,
        requires_prescription: false,
        in_stock: true,
        stock_quantity: 150,
        description: 'Analgésique et antipyrétique',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    },
    {
        id: 'drug-002',
        code: 'MED-AMOX-500',
        name: 'Amoxicilline 500mg',
        generic_name: 'Amoxicilline',
        category: 'antibiotics',
        manufacturer: 'GSK',
        dosage_form: 'capsule',
        strength: '500mg',
        package_size: '12 capsules',
        unit_price: 350,
        package_price: 4200,
        status: 'covered',
        coverage_percentage: 90,
        max_quantity_per_claim: 2,
        requires_prescription: true,
        in_stock: true,
        stock_quantity: 85,
        description: 'Antibiotique de la famille des pénicillines',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    },
    {
        id: 'drug-003',
        code: 'MED-IBU-400',
        name: 'Nurofen 400mg',
        generic_name: 'Ibuprofène',
        category: 'pain_relief',
        manufacturer: 'Reckitt',
        dosage_form: 'tablet',
        strength: '400mg',
        package_size: '12 tablets',
        unit_price: 200,
        package_price: 2400,
        status: 'covered',
        coverage_percentage: 80,
        max_quantity_per_claim: 2,
        requires_prescription: false,
        in_stock: true,
        stock_quantity: 120,
        description: 'Anti-inflammatoire non stéroïdien',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    },
    {
        id: 'drug-004',
        code: 'MED-MET-500',
        name: 'Glucophage 500mg',
        generic_name: 'Metformine',
        category: 'chronic',
        manufacturer: 'Merck',
        dosage_form: 'tablet',
        strength: '500mg',
        package_size: '30 tablets',
        unit_price: 450,
        package_price: 13500,
        status: 'covered',
        coverage_percentage: 90,
        max_quantity_per_claim: 1,
        requires_prescription: true,
        in_stock: true,
        stock_quantity: 65,
        description: 'Traitement du diabète de type 2',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    },
    {
        id: 'drug-005',
        code: 'MED-CET-10',
        name: 'Zyrtec 10mg',
        generic_name: 'Cétirizine',
        category: 'pain_relief',
        manufacturer: 'UCB',
        dosage_form: 'tablet',
        strength: '10mg',
        package_size: '7 tablets',
        unit_price: 400,
        package_price: 2800,
        status: 'covered',
        coverage_percentage: 80,
        max_quantity_per_claim: 2,
        requires_prescription: false,
        in_stock: true,
        stock_quantity: 200,
        description: 'Antihistaminique pour allergies',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    },
    {
        id: 'drug-006',
        code: 'MED-VIT-C-500',
        name: 'Vitamine C 500mg',
        generic_name: 'Acide ascorbique',
        category: 'vitamins',
        manufacturer: 'Bayer',
        dosage_form: 'tablet',
        strength: '500mg',
        package_size: '30 tablets',
        unit_price: 100,
        package_price: 3000,
        status: 'restricted',
        coverage_percentage: 50,
        max_quantity_per_claim: 1,
        requires_prescription: false,
        in_stock: true,
        stock_quantity: 300,
        description: 'Complément alimentaire',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    },
    {
        id: 'drug-007',
        code: 'MED-AMPL-500',
        name: 'Augmentin 500mg',
        generic_name: 'Amoxicilline/Ac. clavulanique',
        category: 'antibiotics',
        manufacturer: 'GSK',
        dosage_form: 'tablet',
        strength: '500mg/125mg',
        package_size: '12 tablets',
        unit_price: 600,
        package_price: 7200,
        status: 'covered',
        coverage_percentage: 80,
        max_quantity_per_claim: 1,
        requires_prescription: true,
        in_stock: false,
        stock_quantity: 0,
        description: 'Antibiotique à large spectre',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    },
    {
        id: 'drug-008',
        code: 'MED-INS-HUM',
        name: 'Humalog',
        generic_name: 'Insuline lispro',
        category: 'chronic',
        manufacturer: 'Eli Lilly',
        dosage_form: 'injection',
        strength: '100 UI/mL',
        package_size: '1 cartridge',
        unit_price: 8500,
        package_price: 8500,
        status: 'covered',
        coverage_percentage: 95,
        max_quantity_per_claim: 1,
        requires_prescription: true,
        in_stock: true,
        stock_quantity: 25,
        description: 'Insuline rapide pour diabète',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
    }
];

// Alias for backward compatibility
export const MOCK_DRUGS = MOCK_FORMULARY;

export const findMockVerification = (id: string) =>
    MOCK_PHARMACY_VERIFICATIONS.find(v => v.id === id);

export const findMockDrug = (code: string): DrugFormularyItem | null =>
    MOCK_FORMULARY.find(d => d.code === code || d.id === code) || null;

// Drug Interactions Database
export interface DrugInteraction {
    severity: 'contraindicated' | 'major' | 'moderate' | 'minor';
    description: string;
    recommendation: string;
}

export const DRUG_INTERACTIONS: Record<string, Record<string, DrugInteraction>> = {
    'MED-AMOX-500': {
        'MED-AMPL-500': {
            severity: 'major',
            description: 'Double antibiothérapie pénicilline - risque de résistance accrue',
            recommendation: 'Éviter la combinaison. Choisir un antibiotique d\'une autre classe si nécessaire.'
        }
    },
    'MED-AMPL-500': {
        'MED-AMOX-500': {
            severity: 'major',
            description: 'Double antibiothérapie pénicilline - risque de résistance accrue',
            recommendation: 'Éviter la combinaison. Choisir un antibiotique d\'une autre classe si nécessaire.'
        }
    },
    'MED-IBU-400': {
        'MED-MET-500': {
            severity: 'moderate',
            description: 'L\'ibuprofène peut réduire l\'effet hypoglycémique de la metformine',
            recommendation: 'Surveiller la glycémie. Privilégier le paracétamol chez les diabétiques.'
        },
        'MED-INS-HUM': {
            severity: 'moderate',
            description: 'Risque d\'hypoglycémie masquée',
            recommendation: 'Surveillance glycémique renforcée.'
        }
    },
    'MED-MET-500': {
        'MED-IBU-400': {
            severity: 'moderate',
            description: 'L\'ibuprofène peut réduire l\'effet hypoglycémique',
            recommendation: 'Surveiller la glycémie.'
        }
    },
    'MED-INS-HUM': {
        'MED-IBU-400': {
            severity: 'moderate',
            description: 'Risque d\'hypoglycémie masquée',
            recommendation: 'Surveillance glycémique renforcée.'
        }
    }
};

// Check for interactions between drugs
export const checkDrugInteractions = (drugCodes: string[]): Array<{
    drug1: string;
    drug2: string;
    interaction: DrugInteraction;
}> => {
    const interactions: Array<{ drug1: string; drug2: string; interaction: DrugInteraction }> = [];
    
    for (let i = 0; i < drugCodes.length; i++) {
        for (let j = i + 1; j < drugCodes.length; j++) {
            const drug1 = drugCodes[i];
            const drug2 = drugCodes[j];
            
            // Check both directions
            const interaction = DRUG_INTERACTIONS[drug1]?.[drug2] || DRUG_INTERACTIONS[drug2]?.[drug1];
            if (interaction) {
                interactions.push({ drug1, drug2, interaction });
            }
        }
    }
    
    // Sort by severity
    const severityOrder = { contraindicated: 0, major: 1, moderate: 2, minor: 3 };
    return interactions.sort((a, b) => severityOrder[a.interaction.severity] - severityOrder[b.interaction.severity]);
};

// Favorites system (per pharmacy session)
let favoriteDrugCodes: string[] = [];

export const addFavoriteDrug = (code: string) => {
    if (!favoriteDrugCodes.includes(code)) {
        favoriteDrugCodes.push(code);
    }
};

export const removeFavoriteDrug = (code: string) => {
    favoriteDrugCodes = favoriteDrugCodes.filter(c => c !== code);
};

export const isFavoriteDrug = (code: string): boolean => {
    return favoriteDrugCodes.includes(code);
};

export const getFavoriteDrugs = (): DrugFormularyItem[] => {
    return favoriteDrugCodes
        .map(code => findMockDrug(code))
        .filter((d): d is DrugFormularyItem => d !== null);
};

// Alternative drugs mapping for when primary drug is not available/covered
export const getAlternativeDrugs = (drugCode: string): DrugFormularyItem[] => {
    const alternatives: Record<string, string[]> = {
        'MED-AMPL-500': ['MED-AMOX-500'], // Augmentin -> Amoxicilline
        'MED-AMOX-500': ['MED-AMPL-500'], // Amoxicilline -> Augmentin
        'MED-PARA-500': ['MED-IBU-400'],  // Paracetamol -> Ibuprofen
        'MED-IBU-400': ['MED-PARA-500'],  // Ibuprofen -> Paracetamol
    };
    
    const codes = alternatives[drugCode] || [];
    return MOCK_FORMULARY.filter(d => codes.includes(d.code));
};

// Get drugs by category
export const getDrugsByCategory = (category: string): DrugFormularyItem[] => {
    return MOCK_FORMULARY.filter(d => d.category === category);
};

// Recently used medications (simulated per pharmacy session)
let recentlyUsedDrugCodes: string[] = [];

export const addRecentlyUsedDrug = (code: string) => {
    // Remove if already exists to move to front
    recentlyUsedDrugCodes = recentlyUsedDrugCodes.filter(c => c !== code);
    // Add to front
    recentlyUsedDrugCodes.unshift(code);
    // Keep only last 5
    recentlyUsedDrugCodes = recentlyUsedDrugCodes.slice(0, 5);
};

export const getRecentlyUsedDrugs = (): DrugFormularyItem[] => {
    return recentlyUsedDrugCodes
        .map(code => findMockDrug(code))
        .filter((d): d is DrugFormularyItem => d !== null);
};
