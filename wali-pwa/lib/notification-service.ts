import { toast } from "sonner";

export interface WaliNotification {
    id: string;
    title: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'alert';
    date: string;
    read: boolean;
    actionLink?: string;
}

const MOCK_NOTIFICATIONS: WaliNotification[] = [
    {
        id: 'n-1',
        title: 'Remboursement Approuvé',
        message: 'Votre demande de remboursement pour "Pharmacie de la Paix" a été approuvée.',
        type: 'success',
        date: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 mins ago
        read: false,
        actionLink: '/dashboard/history'
    },
    {
        id: 'n-2',
        title: 'Rappel de Cotisation',
        message: 'Votre cotisation mensuelle de Février arrive à échéance dans 3 jours.',
        type: 'warning',
        date: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
        read: false,
        actionLink: '/dashboard/payment'
    },
    {
        id: 'n-3',
        title: 'Conseil Santé',
        message: 'Découvrez nos astuces pour éviter le paludisme en saison des pluies.',
        type: 'info',
        date: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // 2 days ago
        read: true,
    }
];

export const notificationService = {
    getNotifications: async (): Promise<WaliNotification[]> => {
        // Mock API call
        await new Promise(resolve => setTimeout(resolve, 600));
        return [...MOCK_NOTIFICATIONS];
    },

    markAsRead: async (id: string): Promise<void> => {
        await new Promise(resolve => setTimeout(resolve, 300));
        // In real app, call API
        console.log(`Notification ${id} marked as read`);
    },

    clearAll: async (): Promise<void> => {
        await new Promise(resolve => setTimeout(resolve, 500));
        toast.success("Notifications effacées");
    }
};
