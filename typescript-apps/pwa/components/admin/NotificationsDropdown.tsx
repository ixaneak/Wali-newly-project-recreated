"use client";

import React, { useState, useEffect } from 'react';
import { 
    Bell, 
    Building2, 
    FileText, 
    User, 
    CreditCard, 
    ShieldAlert, 
    Activity,
    CheckCircle,
    XCircle,
    AlertCircle,
    AlertTriangle,
    AlertOctagon,
    Eye,
    Ban,
    Flag,
    RotateCcw,
    TrendingUp,
    Filter
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { 
    adminNotificationService, 
    AdminNotification, 
    getCategoryColor, 
    getPriorityColor,
    formatTimeAgo 
} from '@/lib/admin-notifications';

// Icon mapping
const iconComponents: Record<string, React.ElementType> = {
    Building2,
    FileText,
    User,
    CreditCard,
    ShieldAlert,
    Activity,
    CheckCircle,
    XCircle,
    AlertCircle,
    AlertTriangle,
    AlertOctagon,
    Eye,
    Ban,
    Flag,
    RotateCcw,
    TrendingUp,
    Bell
};

export default function NotificationsDropdown() {
    const [notifications, setNotifications] = useState<AdminNotification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [unreadByCategory, setUnreadByCategory] = useState<Record<string, number>>({});
    const [isOpen, setIsOpen] = useState(false);
    const [filter, setFilter] = useState<AdminNotification['category'] | 'all'>('all');
    const [loading, setLoading] = useState(false);

    const fetchNotifications = async () => {
        try {
            setLoading(true);
            const notifs = await adminNotificationService.getNotifications(
                filter === 'all' ? undefined : { category: filter }
            );
            setNotifications(notifs);
            const count = await adminNotificationService.getUnreadCount();
            setUnreadCount(count);
            const byCat = await adminNotificationService.getUnreadCountByCategory();
            setUnreadByCategory(byCat);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30000);
        
        // Subscribe to real-time updates
        const unsubscribe = adminNotificationService.subscribe((newNotif) => {
            setNotifications(prev => [newNotif, ...prev]);
            setUnreadCount(prev => prev + 1);
            toast.info(`Nouvelle notification: ${newNotif.title}`, {
                action: {
                    label: 'Voir',
                    onClick: () => setIsOpen(true)
                }
            });
        });
        
        return () => {
            clearInterval(interval);
            unsubscribe();
        };
    }, [filter]);

    const markAsRead = async (id: string) => {
        try {
            await adminNotificationService.markAsRead(id);
            setNotifications(prev => prev.map(n => 
                n.id === id ? { ...n, read: true } : n
            ));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    };

    const markAllAsRead = async () => {
        try {
            await adminNotificationService.markAllAsRead();
            setNotifications(prev => prev.map(n => ({ ...n, read: true })));
            setUnreadCount(0);
            setUnreadByCategory({ pharmacy: 0, claim: 0, user: 0, payment: 0, compliance: 0, analytics: 0 });
            toast.success('Toutes les notifications ont été marquées comme lues');
        } catch (error) {
            console.error('Failed to mark all as read:', error);
        }
    };

    const getIcon = (type: string) => {
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
        return iconComponents[iconMap[type]] || Bell;
    };

    const categoryLabels: Record<string, string> = {
        all: 'Tout',
        pharmacy: 'Pharmacies',
        claim: 'Sinistres',
        user: 'Utilisateurs',
        payment: 'Paiements',
        compliance: 'Compliance',
        analytics: 'Analytics'
    };

    const filteredNotifications = filter === 'all' 
        ? notifications 
        : notifications.filter(n => n.category === filter);

    return (
        <div className="relative">
            <button 
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-3 bg-[#111827] border border-slate-700/50 rounded-xl text-slate-400 hover:text-[#0ea5e9] hover:border-[#0ea5e9]/30 transition-all group"
            >
                <Bell size={20} />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-black w-5 h-5 flex items-center justify-center rounded-lg ring-4 ring-[#0f172a]">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {isOpen && (
                <>
                    <div 
                        className="fixed inset-0 z-40" 
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-[480px] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl z-50 overflow-hidden">
                        {/* Header */}
                        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                            <div>
                                <h3 className="text-sm font-black text-white uppercase tracking-widest">Notifications</h3>
                                <p className="text-xs text-slate-500 mt-0.5">
                                    {unreadCount} non lue{unreadCount > 1 ? 's' : ''}
                                </p>
                            </div>
                            {unreadCount > 0 && (
                                <button 
                                    onClick={markAllAsRead}
                                    className="text-[10px] text-cyan-500 hover:text-cyan-400 font-bold uppercase"
                                >
                                    Tout marquer lu
                                </button>
                            )}
                        </div>

                        {/* Category Filter */}
                        <div className="flex gap-1 p-2 border-b border-slate-800 overflow-x-auto">
                            {(['all', 'pharmacy', 'claim', 'payment', 'compliance'] as const).map((cat) => (
                                <button
                                    key={cat}
                                    onClick={() => setFilter(cat)}
                                    className={cn(
                                        "px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase whitespace-nowrap transition",
                                        filter === cat 
                                            ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" 
                                            : "bg-slate-800/50 text-slate-400 hover:bg-slate-800"
                                    )}
                                >
                                    {categoryLabels[cat]}
                                    {cat !== 'all' && unreadByCategory[cat] > 0 && (
                                        <span className="ml-1.5 bg-red-500 text-white text-[8px] px-1 rounded">
                                            {unreadByCategory[cat]}
                                        </span>
                                    )}
                                </button>
                            ))}
                        </div>

                        {/* Notifications List */}
                        <div className="max-h-[400px] overflow-y-auto">
                            {loading ? (
                                <div className="p-8 space-y-4">
                                    {[1, 2, 3].map(i => (
                                        <div key={i} className="animate-pulse flex gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-slate-800" />
                                            <div className="flex-1 space-y-2">
                                                <div className="h-4 bg-slate-800 rounded w-3/4" />
                                                <div className="h-3 bg-slate-800 rounded w-1/2" />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : filteredNotifications.length === 0 ? (
                                <div className="p-8 text-center text-slate-500">
                                    <Bell className="w-12 h-12 mx-auto mb-3 opacity-20" />
                                    <p className="text-sm">Aucune notification</p>
                                </div>
                            ) : (
                                filteredNotifications.map((notification) => {
                                    const Icon = getIcon(notification.type);
                                    const colors = getCategoryColor(notification.category);
                                    const priorityDot = getPriorityColor(notification.priority);
                                    
                                    return (
                                        <div 
                                            key={notification.id}
                                            onClick={() => markAsRead(notification.id)}
                                            className={cn(
                                                "p-4 border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-colors relative",
                                                !notification.read && 'bg-slate-800/20'
                                            )}
                                        >
                                            {/* Priority Indicator */}
                                            <div className={cn("absolute left-0 top-0 bottom-0 w-1", priorityDot)} />
                                            
                                            <div className="flex items-start gap-3 pl-2">
                                                {/* Icon */}
                                                <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0", colors.bg)}>
                                                    <Icon className={cn("w-5 h-5", colors.text)} />
                                                </div>
                                                
                                                {/* Content */}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <p className={cn(
                                                            "text-sm font-bold truncate",
                                                            !notification.read ? 'text-white' : 'text-slate-300'
                                                        )}>
                                                            {notification.title}
                                                        </p>
                                                        {!notification.read && (
                                                            <span className="w-2 h-2 bg-cyan-500 rounded-full flex-shrink-0 mt-1.5" />
                                                        )}
                                                    </div>
                                                    
                                                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                                                        {notification.message}
                                                    </p>
                                                    
                                                    {/* Entity Name (like pharmacy_name, user name, etc.) */}
                                                    {notification.entity_name && (
                                                        <div className="flex items-center gap-2 mt-2">
                                                            <span className={cn(
                                                                "text-[10px] px-2 py-0.5 rounded font-medium",
                                                                colors.bg,
                                                                colors.text
                                                            )}>
                                                                {notification.entity_type}
                                                            </span>
                                                            <span className="text-[10px] text-cyan-500/80 font-medium truncate">
                                                                {notification.entity_name}
                                                            </span>
                                                        </div>
                                                    )}
                                                    
                                                    {/* Metadata for specific types */}
                                                    {notification.metadata && (
                                                        <div className="flex flex-wrap gap-1 mt-2">
                                                            {notification.metadata.amount && (
                                                                <span className="text-[10px] text-slate-500">
                                                                    {notification.metadata.amount.toLocaleString()} FCFA
                                                                </span>
                                                            )}
                                                            {notification.metadata.risk_score && (
                                                                <span className={cn(
                                                                    "text-[10px] px-1.5 rounded",
                                                                    notification.metadata.risk_score >= 70 ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"
                                                                )}>
                                                                    Risk: {notification.metadata.risk_score}
                                                                </span>
                                                            )}
                                                        </div>
                                                    )}
                                                    
                                                    <p className="text-[10px] text-slate-500 mt-2">
                                                        {formatTimeAgo(notification.created_at)}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-3 border-t border-slate-800 bg-slate-950/30 flex gap-2">
                            <button 
                                onClick={() => setIsOpen(false)}
                                className="flex-1 py-2 text-xs text-slate-400 hover:text-white transition"
                            >
                                Fermer
                            </button>
                            <button 
                                onClick={() => {
                                    setIsOpen(false);
                                    window.location.href = '/admin/notifications';
                                }}
                                className="flex-1 py-2 text-xs text-cyan-400 hover:text-cyan-300 transition"
                            >
                                Voir Tout
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
