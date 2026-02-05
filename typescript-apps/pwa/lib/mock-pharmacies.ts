export interface Pharmacy {
    id: string;
    name: string;
    address: string;
    coordinates: {
        lat: number;
        lng: number;
    };
    phone: string;
    hours: string;
    isPartner: boolean;
    services: string[];
}

export const MOCK_PHARMACIES: Pharmacy[] = [
    // Abidjan pharmacies
    {
        id: "ph-001",
        name: "Pharmacie du Plateau",
        address: "Boulevard Clozel, Plateau, Abidjan",
        coordinates: { lat: 5.3197, lng: -4.0081 },
        phone: "+225 27 20 21 30 40",
        hours: "Lun-Sam: 8h-20h, Dim: 9h-18h",
        isPartner: true,
        services: ["Médicaments", "Conseil", "Tests rapides"]
    },
    {
        id: "ph-002",
        name: "Pharmacie Cocody",
        address: "Rue des Jardins, Cocody, Abidjan",
        coordinates: { lat: 5.3474, lng: -3.9870 },
        phone: "+225 27 22 41 50 60",
        hours: "Lun-Sam: 7h-21h, Dim: 8h-19h",
        isPartner: true,
        services: ["Médicaments", "Parapharmacie", "Livraison"]
    },
    {
        id: "ph-003",
        name: "Pharmacie Marcory",
        address: "Zone 4, Marcory, Abidjan",
        coordinates: { lat: 5.2892, lng: -3.9984 },
        phone: "+225 27 21 35 42 51",
        hours: "Lun-Dim: 8h-22h",
        isPartner: true,
        services: ["Médicaments", "Urgences", "Tests"]
    },
    {
        id: "ph-004",
        name: "Pharmacie Yopougon",
        address: "Quartier Sicogi, Yopougon, Abidjan",
        coordinates: { lat: 5.3362, lng: -4.0890 },
        phone: "+225 27 23 45 67 89",
        hours: "Lun-Sam: 8h-20h",
        isPartner: true,
        services: ["Médicaments", "Conseil"]
    },
    {
        id: "ph-005",
        name: "Pharmacie Adjamé",
        address: "Marché Adjamé, Abidjan",
        coordinates: { lat: 5.3536, lng: -4.0205 },
        phone: "+225 27 20 30 40 50",
        hours: "Lun-Dim: 7h-21h",
        isPartner: true,
        services: ["Médicaments", "Tests rapides", "Vaccination"]
    },

    // Yamoussoukro pharmacies
    {
        id: "ph-101",
        name: "Pharmacie Centrale de Yamoussoukro",
        address: "Avenue Houphouët-Boigny, Yamoussoukro",
        coordinates: { lat: 6.8276, lng: -5.2893 },
        phone: "+225 27 30 64 20 30",
        hours: "Lun-Sam: 8h-20h, Dim: 9h-17h",
        isPartner: true,
        services: ["Médicaments", "Conseil", "Tests rapides", "Urgences"]
    },
    {
        id: "ph-102",
        name: "Pharmacie du Lac",
        address: "Quartier Habitat, Yamoussoukro",
        coordinates: { lat: 6.8156, lng: -5.2765 },
        phone: "+225 27 30 64 25 40",
        hours: "Lun-Dim: 7h-21h",
        isPartner: true,
        services: ["Médicaments", "Parapharmacie", "Livraison"]
    },
    {
        id: "ph-103",
        name: "Pharmacie de la Basilique",
        address: "Face Basilique, Yamoussoukro",
        coordinates: { lat: 6.8189, lng: -5.2982 },
        phone: "+225 27 30 64 30 50",
        hours: "Lun-Sam: 8h-19h",
        isPartner: true,
        services: ["Médicaments", "Conseil"]
    },

    // Bouaké pharmacies
    {
        id: "ph-201",
        name: "Pharmacie Dar Es Salam",
        address: "Boulevard de la Paix, Bouaké",
        coordinates: { lat: 7.6887, lng: -5.0304 },
        phone: "+225 27 31 63 25 30",
        hours: "Lun-Sam: 8h-20h, Dim: 9h-18h",
        isPartner: true,
        services: ["Médicaments", "Tests", "Vaccination"]
    },
    {
        id: "ph-202",
        name: "Pharmacie Saint-Michel",
        address: "Quartier Commerce, Bouaké",
        coordinates: { lat: 7.6945, lng: -5.0268 },
        phone: "+225 27 31 63 30 40",
        hours: "Lun-Dim: 8h-21h",
        isPartner: true,
        services: ["Médicaments", "Urgences", "Conseil"]
    },

    // San-Pédro pharmacies
    {
        id: "ph-301",
        name: "Pharmacie du Port",
        address: "Centre-ville, San-Pédro",
        coordinates: { lat: 4.7489, lng: -6.6363 },
        phone: "+225 27 34 71 20 30",
        hours: "Lun-Sam: 8h-19h",
        isPartner: true,
        services: ["Médicaments", "Parapharmacie"]
    },
    {
        id: "ph-302",
        name: "Pharmacie Balmer",
        address: "Quartier Balmer, San-Pédro",
        coordinates: { lat: 4.7534, lng: -6.6415 },
        phone: "+225 27 34 71 25 35",
        hours: "Lun-Sam: 8h-20h, Dim: 9h-17h",
        isPartner: true,
        services: ["Médicaments", "Conseil", "Tests"]
    },

    // Daloa pharmacies
    {
        id: "ph-401",
        name: "Pharmacie Centrale de Daloa",
        address: "Avenue de la République, Daloa",
        coordinates: { lat: 6.8770, lng: -6.4503 },
        phone: "+225 27 32 78 20 30",
        hours: "Lun-Sam: 8h-20h",
        isPartner: true,
        services: ["Médicaments", "Urgences", "Vaccination"]
    },

    // Korhogo pharmacies
    {
        id: "ph-501",
        name: "Pharmacie du Nord",
        address: "Centre-ville, Korhogo",
        coordinates: { lat: 9.4580, lng: -5.6294 },
        phone: "+225 27 35 86 20 30",
        hours: "Lun-Sam: 8h-19h, Dim: 9h-17h",
        isPartner: true,
        services: ["Médicaments", "Conseil", "Tests"]
    },

    // Man pharmacies
    {
        id: "ph-601",
        name: "Pharmacie des Montagnes",
        address: "Centre-ville, Man",
        coordinates: { lat: 7.4125, lng: -7.5544 },
        phone: "+225 27 33 79 20 30",
        hours: "Lun-Sam: 8h-19h",
        isPartner: true,
        services: ["Médicaments", "Parapharmacie"]
    },
];
