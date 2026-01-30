"use client";

import { useRouter } from 'next/navigation';
import { LogOut, Stethoscope } from 'lucide-react';

export default function PharmacyLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();

    const handleLogout = () => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('user_role');
            router.push('/pharmacy/login');
        }
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Top Navigation Bar */}
            <nav className="bg-emerald-700 text-white shadow-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <div className="flex items-center gap-2">
                            <div className="bg-white/10 p-2 rounded-lg backdrop-blur-sm">
                                <Stethoscope className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="font-bold text-lg leading-none">Wali Pro</h1>
                                <span className="text-[10px] text-emerald-200 uppercase tracking-widest font-semibold">Pharmacie</span>
                            </div>
                        </div>

                        {/* Right Side Actions */}
                        <div className="flex items-center gap-4">
                            <div className="hidden md:block text-right">
                                <div className="text-sm font-medium">Pharmacie de la Paix</div>
                                <div className="text-xs text-emerald-200">ID: PH-002</div>
                            </div>
                            <button
                                onClick={handleLogout}
                                className="p-2 hover:bg-white/10 rounded-full transition"
                                title="Se déconnecter"
                            >
                                <LogOut className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content Area */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
            </main>
        </div>
    );
}
