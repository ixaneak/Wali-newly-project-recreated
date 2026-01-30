"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Bell, Mail, MessageSquare, Shield, Clock, Heart } from 'lucide-react';
import { toast } from 'sonner';

interface NotificationSetting {
    id: string;
    label: string;
    description: string;
    icon: React.ElementType;
    enabled: boolean;
}

export default function NotificationSettingsPage() {
    const router = useRouter();

    // Initial State
    const [settings, setSettings] = useState<NotificationSetting[]>([
        {
            id: 'push_all',
            label: 'Notifications Push',
            description: 'Recevoir les alertes importantes sur votre téléphone',
            icon: Bell,
            enabled: true
        },
        {
            id: 'email_alerts',
            label: 'Alertes par Email',
            description: 'Récapitulatifs mensuels et documents',
            icon: Mail,
            enabled: true
        },
        {
            id: 'sms_claims',
            label: 'SMS Suivi Claims',
            description: 'Mises à jour de statut de vos remboursements',
            icon: MessageSquare,
            enabled: true
        },
        {
            id: 'payment_reminders',
            label: 'Rappels de Paiement',
            description: 'Pour éviter toute interruption de service',
            icon: Clock,
            enabled: true
        },
        {
            id: 'health_tips',
            label: 'Conseils Santé',
            description: 'Astuces hebdomadaires pour votre bien-être',
            icon: Heart,
            enabled: false
        },
        {
            id: 'security_alert',
            label: 'Alertes de Sécurité',
            description: 'Connexions suspectes et changements de mot de passe',
            icon: Shield,
            enabled: true
        }
    ]);

    const toggleSetting = (id: string) => {
        setSettings(prev => prev.map(setting => {
            if (setting.id === id) {
                const newState = !setting.enabled;
                // Simulating immediate save logic or local optimistic update
                if (newState) {
                    toast.success('Option activée');
                }
                return { ...setting, enabled: newState };
            }
            return setting;
        }));
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-20">
            {/* Header */}
            <div className="bg-white dark:bg-slate-900 sticky top-0 z-10 border-b border-gray-100 dark:border-slate-800">
                <div className="p-4 flex items-center justify-between">
                    <button
                        onClick={() => router.back()}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full text-gray-600 dark:text-gray-400 transition"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <h1 className="text-lg font-bold text-gray-900 dark:text-white">Notifications</h1>
                    <div className="w-10" /> {/* Spacer */}
                </div>
            </div>

            <div className="p-6">
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                    Gérez vos préférences de communication. Les notifications de sécurité et relatives à vos sinistres ne peuvent pas être entièrement désactivées.
                </p>

                <div className="space-y-4">
                    {settings.map((setting) => (
                        <div
                            key={setting.id}
                            className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 flex items-center justify-between"
                        >
                            <div className="flex items-start gap-4 flex-1">
                                <div className={`p-2.5 rounded-xl ${setting.enabled ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400' : 'bg-gray-50 text-gray-400 dark:bg-slate-800 dark:text-gray-500'} transition-colors`}>
                                    <setting.icon className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-900 dark:text-white mb-0.5">
                                        {setting.label}
                                    </h3>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 leading-snug pr-4">
                                        {setting.description}
                                    </p>
                                </div>
                            </div>

                            {/* Toggle Switch */}
                            <button
                                onClick={() => toggleSetting(setting.id)}
                                className={`relative w-12 h-7 rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 ${setting.enabled ? 'bg-emerald-500' : 'bg-gray-200 dark:bg-slate-700'
                                    }`}
                            >
                                <span
                                    className={`inline-block w-5 h-5 bg-white rounded-full shadow transform transition duration-200 ease-in-out ${setting.enabled ? 'translate-x-6' : 'translate-x-1'
                                        } top-1 absolute left-0`}
                                />
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
