/**
 * Unified Admin Notifications System
 * 
 * Aggregates notifications from all admin sections:
 * - Pharmacies
 * - Claims
 * - Users
 * - Payments
 * - Compliance (SAR)
 * - Analytics
 */

export type AdminNotificationType = 
    // Pharmacy notifications
    | 'new_pharmacy' 
    | 'subscription_expiring' 
    | 'quota_alert' 
    | 'pharmacy_payment_received'
    // Claims notifications
    | 'new_claim'
    | 'claim_approved'
    | 'claim_rejected'
    | 'claim_requires_review'
    // User notifications
    | 'new_user'
    | 'user_verified'
    | 'user_suspended'
    // Payment notifications
    | 'payment_received'
    | 'payment_failed'
    | 'refund_processed'
    // Compliance/SAR notifications
    | 'sar_created'
    | 'sar_flagged'
    | 'sanctions_match'
    | 'high_risk_alert'
    // Analytics notifications
    | 'anomaly_detected'
    | 'threshold_breach';

export interface AdminNotification {
    id: string;
    type: AdminNotificationType;
    category: 'pharmacy' | 'claim' | 'user' | 'payment' | 'compliance' | 'analytics';
    title: string;
    message: string;
    entity_id?: string;
    entity_name?: string;  // e.g., pharmacy name, user name, claim ID
    entity_type?: string;  // e.g., "Pharmacie", "User", "Claim", "SAR"
    metadata?: Record<string, any>;
    created_at: string;
    read: boolean;
    priority: 'low' | 'medium' | 'high' | 'critical';
    action_link?: string;
}

// ═════════════════════════════════════════════════════════════════
// MOCK DATA - Replace with actual API calls
// ═════════════════════════════════════════════════════════════════

const MOCK_NOTIFICATIONS: AdminNotification[] = [
    // Pharmacy notifications
    {
        id: 'notif-001',
        type: 'new_pharmacy',
        category: 'pharmacy',
        title: 'Nouvelle Pharmacie Partenaire',
        message: 'Une nouvelle pharmacie a complété son inscription',
        entity_id: 'pharm-123',
        entity_name: 'Pharmacie Ivoire Santé - Cocody',
        entity_type: 'Pharmacie',
        created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 mins ago
        read: false,
        priority: 'medium',
        action_link: '/admin/pharmacies'
    },
    {
        id: 'notif-002',
        type: 'subscription_expiring',
        category: 'pharmacy',
        title: 'Abonnement Expire Bientôt',
        message: 'L\'abonnement de cette pharmacie expire dans 3 jours',
        entity_id: 'pharm-456',
        entity_name: 'Pharmacie de la Paix - Plateau',
        entity_type: 'Pharmacie',
        created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
        read: false,
        priority: 'high',
        action_link: '/admin/pharmacies'
    },
    // Claims notifications
    {
        id: 'notif-003',
        type: 'new_claim',
        category: 'claim',
        title: 'Nouveau Sinistre',
        message: 'Un nouveau sinistre nécessite votre attention',
        entity_id: 'claim-789',
        entity_name: 'SIN-2026-008923',
        entity_type: 'Sinistre',
        metadata: { amount: 750000, user: 'Koné Amadou' },
        created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        read: false,
        priority: 'high',
        action_link: '/admin/claims'
    },
    {
        id: 'notif-004',
        type: 'claim_requires_review',
        category: 'claim',
        title: 'Sinistre à Réviser',
        message: 'Ce sinistre dépasse le seuil de 500k CFA et nécessite une approbation manuelle',
        entity_id: 'claim-790',
        entity_name: 'SIN-2026-008924',
        entity_type: 'Sinistre',
        metadata: { amount: 1250000, user: 'Yao Sarah' },
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        read: true,
        priority: 'critical',
        action_link: '/admin/claims'
    },
    // User notifications
    {
        id: 'notif-005',
        type: 'new_user',
        category: 'user',
        title: 'Nouvel Utilisateur',
        message: 'Un nouvel artisan s\'est inscrit sur la plateforme',
        entity_id: 'user-321',
        entity_name: 'Bakayoko Issouf',
        entity_type: 'Utilisateur',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
        read: true,
        priority: 'low',
        action_link: '/admin/users'
    },
    // Payment notifications
    {
        id: 'notif-006',
        type: 'payment_received',
        category: 'payment',
        title: 'Paiement Reçu',
        message: 'Un paiement a été reçu avec succès',
        entity_id: 'pay-654',
        entity_name: 'PAY-2026-004567',
        entity_type: 'Paiement',
        metadata: { amount: 25000, method: 'Orange Money' },
        created_at: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
        read: true,
        priority: 'medium',
        action_link: '/admin/payments'
    },
    {
        id: 'notif-007',
        type: 'payment_failed',
        category: 'payment',
        title: 'Échec de Paiement',
        message: 'Une tentative de paiement a échoué',
        entity_id: 'pay-655',
        entity_name: 'PAY-2026-004568',
        entity_type: 'Paiement',
        metadata: { amount: 15000, reason: 'Solde insuffisant' },
        created_at: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
        read: false,
        priority: 'high',
        action_link: '/admin/payments'
    },
    // Compliance/SAR notifications
    {
        id: 'notif-008',
        type: 'sar_created',
        category: 'compliance',
        title: 'SAR Auto-Généré',
        message: 'Un rapport d\'activité suspecte a été créé automatiquement',
        entity_id: 'sar-042',
        entity_name: 'SAR-2026-000042',
        entity_type: 'SAR',
        metadata: { risk_score: 85, flags: ['structuring', 'rapid_claim'] },
        created_at: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
        read: false,
        priority: 'critical',
        action_link: '/admin/compliance'
    },
    {
        id: 'notif-009',
        type: 'sanctions_match',
        category: 'compliance',
        title: 'Alerte Sanctions',
        message: 'Une correspondance potentielle avec la liste des sanctions a été détectée',
        entity_id: 'user-999',
        entity_name: 'Correspondance: Koné Amadou',
        entity_type: 'Alerte',
        metadata: { list: 'EU Consolidated List', confidence: 0.95 },
        created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        read: false,
        priority: 'critical',
        action_link: '/admin/compliance'
    },
    // Analytics notifications
    {
        id: 'notif-010',
        type: 'anomaly_detected',
        category: 'analytics',
        title: 'Anomalie Détectée',
        message: 'Une anomalie statistique a été détectée dans les paiements',
        entity_id: 'anom-111',
        entity_name: 'Anomalie #A-4521',
        entity_type: 'Anomalie',
        metadata: { deviation: 3.5, metric: 'daily_payments' },
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
        read: true,
        priority: 'medium',
        action_link: '/admin/analytics'
    }
];

// ═════════════════════════════════════════════════════════════════
// SERVICE
// ═════════════════════════════════════════════════════════════════

export const adminNotificationService = {
    getNotifications: async (filters?: {
        category?: AdminNotification['category'];
        priority?: AdminNotification['priority'];
        read?: boolean;
    }): Promise<AdminNotification[]> => {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        let notifications = [...MOCK_NOTIFICATIONS];
        
        if (filters?.category) {
            notifications = notifications.filter(n => n.category === filters.category);
        }
        if (filters?.priority) {
            notifications = notifications.filter(n => n.priority === filters.priority);
        }
        if (filters?.read !== undefined) {
            notifications = notifications.filter(n => n.read === filters.read);
        }
        
        // Sort by date, newest first
        return notifications.sort((a, b) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
    },

    getUnreadCount: async (): Promise<number> => {
        await new Promise(resolve => setTimeout(resolve, 200));
        return MOCK_NOTIFICATIONS.filter(n => !n.read).length;
    },

    getUnreadCountByCategory: async (): Promise<Record<AdminNotification['category'], number>> => {
        await new Promise(resolve => setTimeout(resolve, 200));
        const counts = { pharmacy: 0, claim: 0, user: 0, payment: 0, compliance: 0, analytics: 0 };
        MOCK_NOTIFICATIONS.filter(n => !n.read).forEach(n => {
            counts[n.category]++;
        });
        return counts;
    },

    markAsRead: async (id: string): Promise<void> => {
        await new Promise(resolve => setTimeout(resolve, 300));
        const notif = MOCK_NOTIFICATIONS.find(n => n.id === id);
        if (notif) notif.read = true;
    },

    markAllAsRead: async (): Promise<void> => {
        await new Promise(resolve => setTimeout(resolve, 500));
        MOCK_NOTIFICATIONS.forEach(n => n.read = true);
    },

    markCategoryAsRead: async (category: AdminNotification['category']): Promise<void> => {
        await new Promise(resolve => setTimeout(resolve, 300));
        MOCK_NOTIFICATIONS.filter(n => n.category === category).forEach(n => n.read = true);
    },

    // Subscribe to real-time updates (WebSocket/SSE simulation)
    subscribe: (callback: (notification: AdminNotification) => void) => {
        // In real implementation, this would connect to WebSocket
        const interval = setInterval(async () => {
            // Simulate occasional new notification
            if (Math.random() > 0.95) {
                const newNotif: AdminNotification = {
                    id: `notif-${Date.now()}`,
                    type: 'new_claim',
                    category: 'claim',
                    title: 'Nouveau Sinistre (Live)',
                    message: 'Un sinistre vient d\'être soumis',
                    entity_id: `claim-${Date.now()}`,
                    entity_name: `SIN-2026-${String(Math.floor(Math.random() * 1000000)).padStart(6, '0')}`,
                    entity_type: 'Sinistre',
                    created_at: new Date().toISOString(),
                    read: false,
                    priority: 'high',
                    action_link: '/admin/claims'
                };
                MOCK_NOTIFICATIONS.unshift(newNotif);
                callback(newNotif);
            }
        }, 10000); // Check every 10 seconds

        return () => clearInterval(interval);
    }
};

// ═════════════════════════════════════════════════════════════════
// HELPERS
// ═════════════════════════════════════════════════════════════════

export const getNotificationIcon = (type: AdminNotificationType): string => {
    const iconMap: Record<string, string> = {
        // Pharmacy
        new_pharmacy: 'Building2',
        subscription_expiring: 'AlertCircle',
        quota_alert: 'AlertTriangle',
        pharmacy_payment_received: 'CreditCard',
        // Claims
        new_claim: 'FileText',
        claim_approved: 'CheckCircle',
        claim_rejected: 'XCircle',
        claim_requires_review: 'Eye',
        // Users
        new_user: 'User',
        user_verified: 'CheckCircle',
        user_suspended: 'Ban',
        // Payments
        payment_received: 'CreditCard',
        payment_failed: 'AlertCircle',
        refund_processed: 'RotateCcw',
        // Compliance
        sar_created: 'ShieldAlert',
        sar_flagged: 'Flag',
        sanctions_match: 'Ban',
        high_risk_alert: 'AlertOctagon',
        // Analytics
        anomaly_detected: 'Activity',
        threshold_breach: 'TrendingUp'
    };
    return iconMap[type] || 'Bell';
};

export const getCategoryColor = (category: AdminNotification['category']): { bg: string; text: string; border: string } => {
    const colors: Record<AdminNotification['category'], { bg: string; text: string; border: string }> = {
        pharmacy: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
        claim: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
        user: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30' },
        payment: { bg: 'bg-sky-500/10', text: 'text-sky-400', border: 'border-sky-500/30' },
        compliance: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
        analytics: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' }
    };
    return colors[category];
};

export const getPriorityColor = (priority: AdminNotification['priority']): string => {
    const colors: Record<AdminNotification['priority'], string> = {
        low: 'bg-slate-500',
        medium: 'bg-blue-500',
        high: 'bg-orange-500',
        critical: 'bg-red-500 animate-pulse'
    };
    return colors[priority];
};

export const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'À l\'instant';
    if (minutes < 60) return `Il y a ${minutes} min`;
    if (hours < 24) return `Il y a ${hours}h`;
    if (days < 7) return `Il y a ${days}j`;
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
};
