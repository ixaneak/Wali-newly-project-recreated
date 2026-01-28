"use client";

import { useDashboard } from '@/hooks/useMobileData';
import { User, FileText, Map, Bell, Phone, HelpCircle, LogOut, ChevronRight, Shield, CreditCard } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ThemeToggle } from '@/components/theme-toggle';

export default function ProfilePage() {
    const { data } = useDashboard();
    const router = useRouter();

    const handleLogout = () => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_id');
            router.push('/login');
        }
    };

    const sections = [
        {
            title: "MON ASSURANCE",
            items: [
                {
                    icon: Shield,
                    label: "Mon plan",
                    value: data?.user.planName,
                    onClick: () => router.push(`/dashboard/plan?tier=${data?.user.tier}`)
                },
                {
                    icon: FileText,
                    label: "Mes documents",
                    value: "7 docs",
                    onClick: () => router.push('/dashboard/documents')
                },
                {
                    icon: Map,
                    label: "Pharmacies partenaires",
                    value: "",
                    onClick: () => router.push('/dashboard/pharmacies')
                },
                {
                    icon: CreditCard,
                    label: "Historique paiements",
                    value: "",
                    onClick: () => router.push('/dashboard/history')
                },
            ]
        },
        {
            title: "PARAMÈTRES",
            items: [
                {
                    icon: Bell,
                    label: "Notifications",
                    value: "On",
                    onClick: () => router.push('/dashboard/notifications')
                },
                {
                    icon: Phone,
                    label: "Modifier mon profil",
                    value: "",
                    onClick: () => router.push('/dashboard/profile/edit')
                },
                {
                    icon: HelpCircle,
                    label: "Aide et support",
                    value: "",
                    onClick: () => router.push('/dashboard/support')
                },
            ]
        }
    ];

    const AppearanceSection = () => (
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 overflow-hidden divide-y divide-gray-50 dark:divide-slate-800">
            <div className="w-full p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gray-50 dark:bg-slate-800 flex items-center justify-center text-gray-500 dark:text-slate-400">
                        <User className="w-4 h-4" /> {/* Reusing User icon as placeholder or Moon/Sun */}
                    </div>
                    <span className="font-medium text-gray-700 dark:text-slate-200 text-sm">Apparence</span>
                </div>
                <ThemeToggle />
            </div>
        </div>
    );

    if (!data) return null;

    return (
        <div className="p-6 pb-24 min-h-screen bg-gray-50/50">
            <h1 className="text-2xl font-bold text-gray-900 mb-8">Profil</h1>

            {/* Profile Header */}
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 flex items-center gap-4 mb-8">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center text-2xl border-4 border-emerald-50">
                    {data.user.avatarUrl ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={data.user.avatarUrl} alt="Avatar" className="w-full h-full rounded-full object-cover" />
                    ) : (
                        <span className="">👨🏾‍🔧</span>
                    )}
                </div>
                <div>
                    <h2 className="font-bold text-lg text-gray-900">{data.user.name}</h2>
                    <p className="text-gray-500 text-sm mb-1">{data.user.phone}</p>
                    <div className="inline-flex items-center gap-1 bg-emerald-50 px-2 py-0.5 rounded text-[10px] font-bold text-emerald-700 border border-emerald-100">
                        MOUVEMENT ACTIF
                    </div>
                </div>
            </div>

            {/* Settings Sections */}
            <div className="space-y-6">
                {sections.map((section, idx) => (
                    <div key={idx}>
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 ml-2">{section.title}</h3>
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden divide-y divide-gray-50">
                            {section.items.map((item, i) => (
                                <button
                                    key={i}
                                    onClick={item.onClick}
                                    disabled={!item.onClick}
                                    className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-800 transition text-left group disabled:cursor-default disabled:hover:bg-transparent"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-gray-50 dark:bg-slate-800 flex items-center justify-center text-gray-500 dark:text-slate-400 group-hover:bg-emerald-50 dark:group-hover:bg-emerald-900/20 group-hover:text-emerald-600 transition">
                                            <item.icon className="w-4 h-4" />
                                        </div>
                                        <span className="font-medium text-gray-700 dark:text-slate-200 text-sm">{item.label}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {item.value && <span className="text-xs text-gray-400 font-medium">{item.value}</span>}
                                        <ChevronRight className="w-4 h-4 text-gray-300" />
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-6">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 ml-2">PERSONNALISATION</h3>
                <AppearanceSection />
            </div>

            {/* Logout */}
            <button
                onClick={handleLogout}
                className="w-full mt-8 p-4 bg-white border border-red-100 rounded-2xl text-red-600 font-semibold text-sm flex items-center justify-center gap-2 hover:bg-red-50 transition shadow-sm"
            >
                <LogOut className="w-4 h-4" />
                Se déconnecter
            </button>

            <p className="text-center text-xs text-gray-300 mt-6">
                Version 1.0.2 (Build 20240125)
            </p>
        </div>
    );
}
