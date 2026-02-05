"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Bell, CheckCheck, Trash2, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import { notificationService, WaliNotification } from '@/lib/notification-service';

export default function NotificationInbox() {
    const router = useRouter();
    const [notifications, setNotifications] = useState<WaliNotification[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadNotifications();
    }, []);

    const loadNotifications = async () => {
        try {
            const data = await notificationService.getNotifications();
            setNotifications(data);
        } finally {
            setLoading(false);
        }
    };

    const handleMarkAllRead = async () => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        // await notificationService.markAllRead(); // Ideally api supports this
    };

    const handleClearAll = async () => {
        await notificationService.clearAll();
        setNotifications([]);
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'success': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
            case 'warning': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
            case 'alert': return <AlertTriangle className="w-5 h-5 text-red-500" />;
            default: return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-20">
            {/* Header */}
            <div className="bg-white dark:bg-slate-900 sticky top-0 z-10 px-4 py-3 shadow-sm flex items-center justify-between border-b dark:border-slate-800">
                <button
                    onClick={() => router.back()}
                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition"
                >
                    <ArrowLeft className="w-6 h-6 text-gray-700 dark:text-gray-200" />
                </button>
                <h1 className="font-bold text-lg text-gray-900 dark:text-white">Notifications</h1>
                <div className="flex gap-1">
                    <button
                        onClick={handleMarkAllRead}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition text-gray-500 dark:text-gray-400"
                        title="Tout marquer comme lu"
                    >
                        <CheckCheck className="w-5 h-5" />
                    </button>
                    <button
                        onClick={handleClearAll}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition text-gray-500 dark:text-gray-400"
                        title="Tout effacer"
                    >
                        <Trash2 className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* List */}
            <div className="p-4 space-y-3">
                {loading ? (
                    [1, 2, 3].map(i => (
                        <div key={i} className="animate-pulse bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm h-24"></div>
                    ))
                ) : notifications.length === 0 ? (
                    <div className="text-center py-12 text-gray-400">
                        <Bell className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p>Aucune notification</p>
                    </div>
                ) : (
                    notifications.map(notif => (
                        <div
                            key={notif.id}
                            onClick={() => notif.actionLink && router.push(notif.actionLink)}
                            className={`
                                relative p-4 rounded-xl shadow-sm border transition active:scale-[0.99]
                                ${notif.read ? 'bg-white dark:bg-slate-900 border-gray-100 dark:border-slate-800' : 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-100 dark:border-emerald-800/30'}
                                ${notif.actionLink ? 'cursor-pointer hover:shadow-md' : ''}
                            `}
                        >
                            <div className="flex gap-4">
                                <div className={`shrink-0 mt-1`}>
                                    {getIcon(notif.type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-start mb-1">
                                        <h3 className={`font-semibold ${notif.read ? 'text-gray-900 dark:text-gray-100' : 'text-emerald-900 dark:text-emerald-100'}`}>
                                            {notif.title}
                                        </h3>
                                        <span className="text-[10px] text-gray-400 whitespace-nowrap ml-2">
                                            {new Date(notif.date).toLocaleDateString()}
                                        </span>
                                    </div>
                                    <p className={`text-sm ${notif.read ? 'text-gray-600 dark:text-gray-400' : 'text-emerald-800 dark:text-emerald-200/80'} line-clamp-2`}>
                                        {notif.message}
                                    </p>
                                    {!notif.read && (
                                        <span className="absolute top-4 right-4 w-2 h-2 rounded-full bg-emerald-500"></span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
