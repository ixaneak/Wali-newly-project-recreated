"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    ArrowLeft,
    Bell,
    Mail,
    MessageSquare,
    Phone,
    Shield,
    CreditCard,
    FileText,
    Check
} from 'lucide-react';
import { toast } from 'sonner';

interface NotificationPreference {
    id: string;
    title: string;
    description: string;
    icon: any;
    channels: {
        push: boolean;
        email: boolean;
        sms: boolean;
    };
}

export default function NotificationsPage() {
    const router = useRouter();
    const [saving, setSaving] = useState(false);

    const [preferences, setPreferences] = useState<NotificationPreference[]>([
        {
            id: 'claims',
            title: 'Mises à jour des claims',
            description: 'Notifications sur le statut de vos claims',
            icon: FileText,
            channels: { push: true, email: true, sms: false }
        },
        {
            id: 'payments',
            title: 'Paiements',
            description: 'Confirmations et rappels de paiement',
            icon: CreditCard,
            channels: { push: true, email: true, sms: true }
        },
        {
            id: 'coverage',
            title: 'Couverture',
            description: 'Alertes de couverture et renouvellement',
            icon: Shield,
            channels: { push: true, email: false, sms: true }
        },
        {
            id: 'marketing',
            title: 'Promotions',
            description: 'Offres spéciales et nouvelles fonctionnalités',
            icon: Bell,
            channels: { push: false, email: true, sms: false }
        }
    ]);

    const toggleChannel = (prefId: string, channel: 'push' | 'email' | 'sms') => {
        setPreferences(preferences.map(pref =>
            pref.id === prefId
                ? {
                    ...pref,
                    channels: {
                        ...pref.channels,
                        [channel]: !pref.channels[channel]
                    }
                }
                : pref
        ));
    };

    const handleSave = async () => {
        setSaving(true);
        await new Promise(resolve => setTimeout(resolve, 1000));
        toast.success('Préférences enregistrées');
        setSaving(false);
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-24">
            {/* Header */}
            <div className="p-6 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4 transition"
                >
                    <ArrowLeft className="w-5 h-5" />
                    <span className="font-medium">Retour</span>
                </button>

                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    Notifications
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Gérez vos préférences de notification
                </p>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
                {/* Channel Legend */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <Bell className="w-5 h-5 text-blue-600" />
                        <h3 className="font-bold text-blue-900 dark:text-blue-400">
                            Canaux de notification
                        </h3>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-sm">
                        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                            <Bell className="w-4 h-4" />
                            <span>Push</span>
                        </div>
                        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                            <Mail className="w-4 h-4" />
                            <span>Email</span>
                        </div>
                        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                            <MessageSquare className="w-4 h-4" />
                            <span>SMS</span>
                        </div>
                    </div>
                </div>

                {/* Preferences List */}
                {preferences.map((pref) => (
                    <PreferenceCard
                        key={pref.id}
                        preference={pref}
                        onToggle={(channel) => toggleChannel(pref.id, channel)}
                    />
                ))}
            </div>

            {/* Save Button */}
            <div className="fixed bottom-0 left-0 right-0 p-6 bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800">
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 dark:disabled:bg-slate-700 text-white py-3.5 rounded-xl font-medium transition flex items-center justify-center gap-2"
                >
                    {saving ? (
                        <>
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Enregistrement...
                        </>
                    ) : (
                        <>
                            <Check className="w-5 h-5" />
                            Enregistrer les préférences
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}

function PreferenceCard({
    preference,
    onToggle
}: {
    preference: NotificationPreference;
    onToggle: (channel: 'push' | 'email' | 'sms') => void
}) {
    const Icon = preference.icon;

    return (
        <div className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-2xl p-4">
            <div className="flex items-start gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 flex-shrink-0">
                    <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-1">
                        {preference.title}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        {preference.description}
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
                <ChannelToggle
                    icon={Bell}
                    label="Push"
                    active={preference.channels.push}
                    onClick={() => onToggle('push')}
                />
                <ChannelToggle
                    icon={Mail}
                    label="Email"
                    active={preference.channels.email}
                    onClick={() => onToggle('email')}
                />
                <ChannelToggle
                    icon={MessageSquare}
                    label="SMS"
                    active={preference.channels.sms}
                    onClick={() => onToggle('sms')}
                />
            </div>
        </div>
    );
}

function ChannelToggle({
    icon: Icon,
    label,
    active,
    onClick
}: {
    icon: any;
    label: string;
    active: boolean;
    onClick: () => void
}) {
    return (
        <button
            onClick={onClick}
            className={`p-2.5 rounded-lg border-2 transition text-center ${active
                    ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600'
                    : 'border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 text-gray-400 hover:border-gray-300 dark:hover:border-slate-600'
                }`}
        >
            <Icon className="w-4 h-4 mx-auto mb-1" />
            <div className="text-xs font-medium">{label}</div>
        </button>
    );
}
