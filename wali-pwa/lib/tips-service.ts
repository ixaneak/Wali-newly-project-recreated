
export interface HealthTip {
    id: number;
    title: string;
    text: string;
    color: string;
    textColor: string;
    iconColor: string;
    active: boolean;
}

const MOCK_TIPS: HealthTip[] = [
    {
        id: 1,
        title: "Hydratation",
        text: "Buvez au moins 1,5L d'eau par jour pour rester en forme.",
        color: "bg-blue-100 dark:bg-blue-900/30",
        textColor: "text-blue-700 dark:text-blue-300",
        iconColor: "text-blue-500",
        active: true
    },
    {
        id: 2,
        title: "Vaccination",
        text: "Vérifiez que vos vaccins sont à jour, surtout pour les enfants.",
        color: "bg-emerald-100 dark:bg-emerald-900/30",
        textColor: "text-emerald-700 dark:text-emerald-300",
        iconColor: "text-emerald-500",
        active: true
    },
    {
        id: 3,
        title: "Activité Physique",
        text: "30 minutes de marche par jour réduisent les risques cardiaques.",
        color: "bg-orange-100 dark:bg-orange-900/30",
        textColor: "text-orange-700 dark:text-orange-300",
        iconColor: "text-orange-500",
        active: true
    },
    {
        id: 4,
        title: "Sommeil",
        text: "Dormez au moins 7h par nuit pour une bonne immunité.",
        color: "bg-purple-100 dark:bg-purple-900/30",
        textColor: "text-purple-700 dark:text-purple-300",
        iconColor: "text-purple-500",
        active: true
    }
];

export const tipsService = {
    getTips: async (): Promise<HealthTip[]> => {
        // Mock API call
        await new Promise(resolve => setTimeout(resolve, 400));
        return MOCK_TIPS.filter(t => t.active);
    },

    getAllTipsAdmin: async (): Promise<HealthTip[]> => {
        await new Promise(resolve => setTimeout(resolve, 400));
        return MOCK_TIPS;
    },

    toggleTip: async (id: number): Promise<void> => {
        const tip = MOCK_TIPS.find(t => t.id === id);
        if (tip) tip.active = !tip.active;
    }
};
