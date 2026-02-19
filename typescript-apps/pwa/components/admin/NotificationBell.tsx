"use client";

import React, { useState, useEffect } from 'react';
import { Bell, CheckCircle, Building2, AlertTriangle, CreditCard, X } from 'lucide-react';
import { adminPharmacyService, PharmacyNotification } from '@/lib/api-client';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface NotificationBellProps {
    className?: string;
}

export default function NotificationBell({ className }: NotificationBellProps) {
    const [notifications, setNotifications] = useState<PharmacyNotification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isOpen, setIsOpen] = useState(false);

    const fetchNotifications = async () => {
        try {
            const [notifs, count] = await Promise.all([
                adminPharmacyService.getNotifications(),
                adminPharmacyService.getUnreadCount()
            ]);
            setNotifications(notifs);
            setUnreadCount(count);
        } catch (e) {
            console.error('Failed to fetch notifications', e);
        }
    };

    useEffect(() => {
        fetchNotifications();
        // Refresh every 30 seconds
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleMarkRead = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const success = await adminPharmacyService.markNotificationRead(id);
        if (success) {
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
            setUnreadCount(prev => Math.max(0, prev - 1));
        }
    };

    const handleMarkAllRead = async () => {
        const success = await adminPharmacyService.markAllNotificationsRead();
        if (success) {
            setNotifications(prev => prev.map(n => ({ ...n, read: true })));
            setUnreadCount(0);
            toast.success('Toutes les notifications marquees comme lues');
        }
    };

    const getNotificationIcon = (type: string) => {
        switch (type) {
            case 'new_pharmacy':
                return <Building2 size={16} className="text-emerald-500" />;
            case 'subscription_expiring':
                return <AlertTriangle size={16} className="text-amber-500" />;
            case 'quota_alert':
                return <AlertTriangle size={16} className="text-rose-500" />;
            case 'payment_received':
                return <CreditCard size={16} className="text-sky-500" />;
            default:
                return <Bell size={16} className="text-slate-400" />;
        }
    };

    const getNotificationColor = (type: string) => {
        switch (type) {
            case 'new_pharmacy':
                return 'bg-emerald-500/10 border-emerald-500/20';
            case 'subscription_expiring':
                return 'bg-amber-500/10 border-amber-500/20';
            case 'quota_alert':
                return 'bg-rose-500/10 border-rose-500/20';
            case 'payment_received':
                return 'bg-sky-500/10 border-sky-500/20';
            default:
                return 'bg-slate-800';
        }
    };

    return (
        <div className={cn("relative", className)}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-800 transition-all"
            >
                <Bell size={20} className="text-slate-400" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-rose-500 rounded-full text-[10px] font-black text-white flex items-center justify-center animate-pulse">
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
                    <div className="absolute right-0 top-full mt-3 w-96 bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl shadow-black/50 z-50 overflow-hidden">
                        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                            <div>
                                <h3 className="text-sm font-black text-white uppercase tracking-widest">Notifications</h3>
                                <p className="text-[10px] text-slate-500 mt-1">{unreadCount} non lues</p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleMarkAllRead}
                                    className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                                    title="Marquer tout comme lu"
                                >
                                    <CheckCircle size={16} />
                                </button>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        </div>

                        <div className="max-h-96 overflow-y-auto">
                            {notifications.length === 0 ? (
                                <div className="p-8 text-center">
                                    <Bell size={32} className="text-slate-700 mx-auto mb-3" />
                                    <p className="text-slate-500 text-xs font-bold uppercase">Aucune notification</p>
                                </div>
                            ) : (
                                notifications.map((notification) => (
                                    <div
                                        key={notification.id}
                                        className={cn(
                                            "p-4 border-b border-slate-800 hover:bg-slate-900/50 transition-colors cursor-pointer group",
                                            !notification.read && getNotificationColor(notification.type)
                                        )}
                                        onClick={() => handleMarkRead(notification.id, { stopPropagation: () => {} } as any)}
                                    >
                                        <div className="flex gap-3">
                                            <div className="mt-0.5">
                                                {getNotificationIcon(notification.type)}
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-xs font-bold text-white">{notification.title}</p>
                                                <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">{notification.message}</p>
                                                {notification.pharmacy_name && (
                                                    <p className="text-[10px] text-cyan-500/70 font-mono mt-2">
                                                        {notification.pharmacy_name}
                                                    </p>
                                                )}
                                                <div className="flex items-center justify-between mt-2">
                                                    <span className="text-[9px] text-slate-600 uppercase tracking-wider">
                                                        {new Date(notification.created_at).toLocaleString('fr-FR', { 
                                                            hour: '2-digit', 
                                                            minute: '2-digit',
                                                            day: '2-digit',
                                                            month: 'short'
                                                        })}
                                                    </span>
                                                    {!notification.read && (
                                                        <span className="w-2 h-2 rounded-full bg-cyan-500" />
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
