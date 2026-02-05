"use client";

import { useDashboard } from '@/hooks/useMobileData';
import { User, FileText, Map, Bell, Phone, HelpCircle, LogOut, ChevronRight, Shield, CreditCard, Moon } from 'lucide-react';
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
                    value: "We",
                    onClick: () => router.push('/dashboard/notifications')
                },
                {
                    icon: Phone,
                    label: "Modifier mon profil",
                    value: "",
                    onClick: () => router.push('/dashboard/profile/edit')
                },
                {
                    icon: (props: any) => <User {...props} />,
                    label: "Ma Famille",
                    value: "2 membres",
                    onClick: () => router.push('/dashboard/family')
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
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm dark:shadow-none 
                        border border-gray-100 dark:border-slate-800 
                        overflow-hidden divide-y divide-gray-50 dark:divide-slate-800">
            <div className="w-full p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 
                                    flex items-center justify-center 
                                    text-slate-600 dark:text-emerald-400 transition-colors">
                        <Moon className="w-5 h-5" />
                    </div>
                    <span className="font-medium text-gray-700 dark:text-slate-200">Apparence</span>
                </div>
                <ThemeToggle />
            </div>
        </div>
    );

    if (!data) return null;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 p-6 pb-24 transition-colors duration-200">
            {/* Page Title */}
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">Profil</h1>

            {/* Profile Header Card */}
            <section className="bg-white dark:bg-slate-900 p-6 rounded-3xl 
                              shadow-sm dark:shadow-none 
                              border border-gray-100 dark:border-slate-800 
                              flex items-center gap-4 mb-8 transition-colors">
                {/* Avatar */}
                <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full 
                              flex items-center justify-center text-2xl 
                              border-4 border-emerald-50 dark:border-emerald-900/50">
                    {data.user.avatarUrl ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={data.user.avatarUrl} alt="Avatar" className="w-full h-full rounded-full object-cover" />
                    ) : (
                        <span>👨🏾‍🔧</span>
                    )}
                </div>

                {/* User Info */}
                <div>
                    <h2 className="font-bold text-lg text-gray-900 dark:text-white">{data.user.name}</h2>
                    <p className="text-gray-500 dark:text-slate-400 text-sm mb-1">{data.user.phone}</p>
                    {/* Status Badge */}
                    <span className="inline-flex items-center gap-1 
                                   bg-emerald-100 dark:bg-emerald-900/30 
                                   px-3 py-1 rounded-full 
                                   text-xs font-bold 
                                   text-emerald-700 dark:text-emerald-400 
                                   border border-emerald-100 dark:border-emerald-800/50">
                        MOUVEMENT ACTIF
                    </span>
                </div>
            </section>

            {/* Settings Sections */}
            <div className="space-y-6">
                {sections.map((section, idx) => (
                    <div key={idx}>
                        {/* Section Header */}
                        <h3 className="text-xs font-semibold text-gray-500 dark:text-slate-500 
                                     uppercase tracking-wider mb-3 ml-2">
                            {section.title}
                        </h3>

                        {/* Menu Group Card */}
                        <div className="bg-white dark:bg-slate-900 rounded-2xl 
                                      shadow-sm dark:shadow-none 
                                      border border-gray-100 dark:border-slate-800 
                                      overflow-hidden 
                                      divide-y divide-gray-100 dark:divide-slate-800">
                            {section.items.map((item, i) => (
                                <button
                                    key={i}
                                    onClick={item.onClick}
                                    disabled={!item.onClick}
                                    className="w-full p-4 flex items-center justify-between 
                                             hover:bg-gray-50 dark:hover:bg-slate-800/50 
                                             transition-colors text-left group 
                                             disabled:cursor-default disabled:hover:bg-transparent"
                                >
                                    <div className="flex items-center gap-3">
                                        {/* Icon Container */}
                                        <div className="w-10 h-10 rounded-xl 
                                                      bg-slate-100 dark:bg-slate-800 
                                                      flex items-center justify-center 
                                                      text-slate-600 dark:text-slate-400 
                                                      group-hover:bg-emerald-50 dark:group-hover:bg-emerald-900/20 
                                                      group-hover:text-emerald-600 dark:group-hover:text-emerald-400 
                                                      transition-colors">
                                            <item.icon className="w-5 h-5" />
                                        </div>
                                        {/* Label */}
                                        <span className="font-medium text-gray-700 dark:text-slate-200">
                                            {item.label}
                                        </span>
                                    </div>

                                    {/* Value & Chevron */}
                                    <div className="flex items-center gap-2">
                                        {item.value && (
                                            <span className="text-sm text-gray-400 dark:text-slate-500 font-medium">
                                                {item.value}
                                            </span>
                                        )}
                                        <ChevronRight className="w-5 h-5 text-gray-300 dark:text-slate-600" />
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Personalization Section */}
            <div className="mt-6">
                <h3 className="text-xs font-semibold text-gray-500 dark:text-slate-500 
                             uppercase tracking-wider mb-3 ml-2">
                    PERSONNALISATION
                </h3>
                <AppearanceSection />
            </div>

            {/* Logout Button */}
            <button
                onClick={handleLogout}
                className="w-full mt-8 p-4 rounded-xl font-semibold text-sm 
                         flex items-center justify-center gap-2 transition-colors
                         bg-white dark:bg-slate-900 
                         border border-red-100 dark:border-red-900/30 
                         text-red-600 dark:text-red-400 
                         hover:bg-red-50 dark:hover:bg-red-900/20 
                         shadow-sm dark:shadow-none"
            >
                <LogOut className="w-4 h-4" />
                Se déconnecter
            </button>

            {/* Version */}
            <p className="text-center text-xs text-gray-400 dark:text-slate-600 mt-6">
                Version 1.0.2 (Build 20240125)
            </p>
        </div>
    );
}
