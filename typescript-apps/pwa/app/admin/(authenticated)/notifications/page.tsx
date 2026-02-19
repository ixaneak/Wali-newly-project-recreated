"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
    Filter,
    Search,
    Trash2,
    CheckCheck,
    RefreshCw,
    ArrowRight,
    Calendar,
    Clock
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import AdminHeader from '@/components/admin/AdminHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { 
    adminNotificationService, 
    AdminNotification, 
    getCategoryColor, 
    getPriorityColor,
    formatTimeAgo 
} from '@/lib/admin-notifications';

// Icon mapping
const iconComponents: Record<string, React.ElementType> = {
    Building2, FileText, User, CreditCard, ShieldAlert, Activity,
    CheckCircle, XCircle, AlertCircle, AlertTriangle, AlertOctagon,
    Eye, Ban, Flag, RotateCcw, TrendingUp, Bell
};

const categoryConfig = {
    pharmacy: { label: 'Pharmacies', icon: Building2, color: 'emerald' },
    claim: { label: 'Sinistres', icon: FileText, color: 'blue' },
    user: { label: 'Utilisateurs', icon: User, color: 'purple' },
    payment: { label: 'Paiements', icon: CreditCard, color: 'sky' },
    compliance: { label: 'Compliance', icon: ShieldAlert, color: 'red' },
    analytics: { label: 'Analytics', icon: Activity, color: 'amber' }
};

export default function AdminNotificationsPage() {
    const router = useRouter();
    const [notifications, setNotifications] = useState<AdminNotification[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeFilter, setActiveFilter] = useState<{
        category: AdminNotification['category'] | 'all';
        priority: AdminNotification['priority'] | 'all';
        read: 'all' | 'read' | 'unread';
    }>({
        category: 'all',
        priority: 'all',
        read: 'all'
    });

    const loadNotifications = async () => {
        setLoading(true);
        try {
            const notifs = await adminNotificationService.getNotifications();
            setNotifications(notifs);
        } catch (error) {
            console.error('Failed to load notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadNotifications();
    }, []);

    const handleMarkAllRead = async () => {
        await adminNotificationService.markAllAsRead();
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        toast.success('Toutes les notifications marquées comme lues');
    };

    const handleMarkCategoryRead = async (category: AdminNotification['category']) => {
        await adminNotificationService.markCategoryAsRead(category);
        setNotifications(prev => prev.map(n => 
            n.category === category ? { ...n, read: true } : n
        ));
        toast.success(`Notifications ${categoryConfig[category].label} marquées comme lues`);
    };

    const handleClearAll = async () => {
        if (confirm('Voulez-vous vraiment supprimer toutes les notifications ?')) {
            setNotifications([]);
            toast.success('Notifications effacées');
        }
    };

    const filteredNotifications = notifications.filter(n => {
        // Category filter
        if (activeFilter.category !== 'all' && n.category !== activeFilter.category) return false;
        
        // Priority filter
        if (activeFilter.priority !== 'all' && n.priority !== activeFilter.priority) return false;
        
        // Read filter
        if (activeFilter.read === 'read' && !n.read) return false;
        if (activeFilter.read === 'unread' && n.read) return false;
        
        // Search
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            return (
                n.title.toLowerCase().includes(query) ||
                n.message.toLowerCase().includes(query) ||
                n.entity_name?.toLowerCase().includes(query) ||
                n.entity_type?.toLowerCase().includes(query)
            );
        }
        
        return true;
    });

    const unreadCount = notifications.filter(n => !n.read).length;
    const categoryCounts = notifications.reduce((acc, n) => {
        acc[n.category] = (acc[n.category] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const getIcon = (type: string) => {
        const iconMap: Record<string, string> = {
            new_pharmacy: 'Building2',
            subscription_expiring: 'AlertCircle',
            quota_alert: 'AlertTriangle',
            pharmacy_payment_received: 'CreditCard',
            new_claim: 'FileText',
            claim_approved: 'CheckCircle',
            claim_rejected: 'XCircle',
            claim_requires_review: 'Eye',
            new_user: 'User',
            user_verified: 'CheckCircle',
            user_suspended: 'Ban',
            payment_received: 'CreditCard',
            payment_failed: 'AlertCircle',
            refund_processed: 'RotateCcw',
            sar_created: 'ShieldAlert',
            sar_flagged: 'Flag',
            sanctions_match: 'Ban',
            high_risk_alert: 'AlertOctagon',
            anomaly_detected: 'Activity',
            threshold_breach: 'TrendingUp'
        };
        return iconComponents[iconMap[type]] || Bell;
    };

    return (
        <div className="space-y-6 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Centre de Notifications"
                description="Gérez toutes les alertes du portail admin"
            />

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <StatCard 
                    label="Total" 
                    value={notifications.length} 
                    icon={Bell} 
                    color="cyan"
                />
                <StatCard 
                    label="Non lues" 
                    value={unreadCount} 
                    icon={AlertCircle} 
                    color="red"
                    highlight={unreadCount > 0}
                />
                {Object.entries(categoryConfig).map(([key, config]) => (
                    <StatCard 
                        key={key}
                        label={config.label}
                        value={categoryCounts[key] || 0}
                        icon={config.icon}
                        color={config.color}
                    />
                ))}
            </div>

            {/* Filters & Search */}
            <Card className="border-slate-800 bg-slate-900/40">
                <CardContent className="p-4">
                    <div className="flex flex-col lg:flex-row gap-4">
                        {/* Search */}
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <Input
                                placeholder="Rechercher dans les notifications..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 bg-slate-950 border-slate-800"
                            />
                        </div>
                        
                        {/* Filters */}
                        <div className="flex flex-wrap gap-2">
                            <select
                                value={activeFilter.category}
                                onChange={(e) => setActiveFilter(prev => ({ ...prev, category: e.target.value as any }))}
                                className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-300"
                            >
                                <option value="all">Toutes catégories</option>
                                {Object.entries(categoryConfig).map(([key, config]) => (
                                    <option key={key} value={key}>{config.label}</option>
                                ))}
                            </select>
                            
                            <select
                                value={activeFilter.priority}
                                onChange={(e) => setActiveFilter(prev => ({ ...prev, priority: e.target.value as any }))}
                                className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-300"
                            >
                                <option value="all">Toutes priorités</option>
                                <option value="critical">Critique</option>
                                <option value="high">Haute</option>
                                <option value="medium">Moyenne</option>
                                <option value="low">Basse</option>
                            </select>
                            
                            <select
                                value={activeFilter.read}
                                onChange={(e) => setActiveFilter(prev => ({ ...prev, read: e.target.value as any }))}
                                className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-300"
                            >
                                <option value="all">Toutes</option>
                                <option value="unread">Non lues</option>
                                <option value="read">Lues</option>
                            </select>
                        </div>
                        
                        {/* Actions */}
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={loadNotifications} className="border-slate-800">
                                <RefreshCw className="w-4 h-4" />
                            </Button>
                            <Button variant="outline" size="sm" onClick={handleMarkAllRead} className="border-slate-800">
                                <CheckCheck className="w-4 h-4 mr-2" />
                                Tout lire
                            </Button>
                            <Button variant="outline" size="sm" onClick={handleClearAll} className="border-slate-800 text-red-400 hover:text-red-300">
                                <Trash2 className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Notifications List */}
            <div className="space-y-3">
                {loading ? (
                    <div className="space-y-3">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="animate-pulse bg-slate-900 border border-slate-800 rounded-xl p-6 h-32" />
                        ))}
                    </div>
                ) : filteredNotifications.length === 0 ? (
                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardContent className="p-12 text-center">
                            <Bell className="w-16 h-16 mx-auto mb-4 text-slate-700" />
                            <h3 className="text-lg font-semibold text-white mb-2">Aucune notification</h3>
                            <p className="text-slate-500">Aucune notification ne correspond à vos critères de recherche.</p>
                        </CardContent>
                    </Card>
                ) : (
                    filteredNotifications.map((notification) => {
                        const Icon = getIcon(notification.type);
                        const colors = getCategoryColor(notification.category);
                        const config = categoryConfig[notification.category];
                        
                        return (
                            <Card 
                                key={notification.id} 
                                className={cn(
                                    "border-slate-800 bg-slate-900/40 hover:bg-slate-800/40 transition-colors",
                                    !notification.read && "border-l-4 border-l-cyan-500"
                                )}
                            >
                                <CardContent className="p-4">
                                    <div className="flex items-start gap-4">
                                        {/* Icon */}
                                        <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0", colors.bg)}>
                                            <Icon className={cn("w-6 h-6", colors.text)} />
                                        </div>
                                        
                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-4">
                                                <div>
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <h3 className={cn(
                                                            "text-base font-semibold",
                                                            !notification.read ? 'text-white' : 'text-slate-300'
                                                        )}>
                                                            {notification.title}
                                                        </h3>
                                                        {!notification.read && (
                                                            <Badge className="bg-cyan-500/20 text-cyan-400 text-[10px]">Nouveau</Badge>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-slate-400">{notification.message}</p>
                                                </div>
                                                
                                                {/* Meta */}
                                                <div className="text-right flex-shrink-0">
                                                    <Badge 
                                                        variant="outline" 
                                                        className={cn(
                                                            "text-[10px] uppercase",
                                                            notification.priority === 'critical' && "bg-red-500/20 text-red-400 border-red-500/30",
                                                            notification.priority === 'high' && "bg-orange-500/20 text-orange-400 border-orange-500/30",
                                                            notification.priority === 'medium' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                                                            notification.priority === 'low' && "bg-slate-700 text-slate-400 border-slate-600"
                                                        )}
                                                    >
                                                        {notification.priority}
                                                    </Badge>
                                                    <p className="text-xs text-slate-500 mt-1">
                                                        {formatTimeAgo(notification.created_at)}
                                                    </p>
                                                </div>
                                            </div>
                                            
                                            {/* Entity Info */}
                                            {notification.entity_name && (
                                                <div className="flex items-center gap-3 mt-3">
                                                    <Badge variant="outline" className={cn("text-xs", colors.bg, colors.text, colors.border)}>
                                                        <config.icon className="w-3 h-3 mr-1" />
                                                        {notification.entity_type}
                                                    </Badge>
                                                    <span className="text-sm text-cyan-400 font-medium">
                                                        {notification.entity_name}
                                                    </span>
                                                    {notification.metadata?.amount && (
                                                        <span className="text-sm text-slate-400">
                                                            {notification.metadata.amount.toLocaleString()} FCFA
                                                        </span>
                                                    )}
                                                    {notification.metadata?.risk_score && (
                                                        <Badge className={cn(
                                                            "text-[10px]",
                                                            notification.metadata.risk_score >= 70 
                                                                ? "bg-red-500/20 text-red-400" 
                                                                : "bg-amber-500/20 text-amber-400"
                                                        )}>
                                                            Risk Score: {notification.metadata.risk_score}
                                                        </Badge>
                                                    )}
                                                </div>
                                            )}
                                            
                                            {/* Actions */}
                                            <div className="flex items-center gap-2 mt-4">
                                                {notification.action_link && (
                                                    <Button 
                                                        size="sm" 
                                                        variant="outline"
                                                        className="h-8 text-xs border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10"
                                                        onClick={() => router.push(notification.action_link!)}
                                                    >
                                                        Voir détails
                                                        <ArrowRight className="w-3 h-3 ml-1" />
                                                    </Button>
                                                )}
                                                {!notification.read && (
                                                    <Button 
                                                        size="sm" 
                                                        variant="ghost"
                                                        className="h-8 text-xs text-slate-400 hover:text-white"
                                                        onClick={() => adminNotificationService.markAsRead(notification.id)}
                                                    >
                                                        <CheckCheck className="w-3 h-3 mr-1" />
                                                        Marquer lu
                                                    </Button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })
                )}
            </div>
        </div>
    );
}

function StatCard({ label, value, icon: Icon, color, highlight }: {
    label: string;
    value: number;
    icon: any;
    color: string;
    highlight?: boolean;
}) {
    const colorClasses: Record<string, string> = {
        cyan: 'bg-cyan-500/10 text-cyan-400',
        red: 'bg-red-500/10 text-red-400',
        emerald: 'bg-emerald-500/10 text-emerald-400',
        blue: 'bg-blue-500/10 text-blue-400',
        purple: 'bg-purple-500/10 text-purple-400',
        sky: 'bg-sky-500/10 text-sky-400',
        amber: 'bg-amber-500/10 text-amber-400'
    };

    return (
        <Card className={cn("border-slate-800 bg-slate-900/40", highlight && "border-cyan-500/30")}>
            <CardContent className="p-4">
                <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-lg", colorClasses[color])}>
                        <Icon className="w-5 h-5" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{value}</div>
                        <div className="text-xs text-slate-500">{label}</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
