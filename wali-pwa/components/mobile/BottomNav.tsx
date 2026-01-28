"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, History, FileText, User } from 'lucide-react';
import { cn } from '@/lib/utils'; // Assuming cn utility exists, otherwise I'll need to create it or import differently

// Fallback utility if not present
// function cn(...classes: (string | undefined)[]) { return classes.filter(Boolean).join(' '); }

export default function BottomNav() {
    const pathname = usePathname();

    const tabs = [
        {
            name: 'Accueil',
            href: '/dashboard',
            icon: Home,
            active: pathname === '/dashboard',
        },
        {
            name: 'Historique',
            href: '/dashboard/history',
            icon: History,
            active: pathname === '/dashboard/history',
        },
        {
            name: 'Mes Claims',
            href: '/dashboard/claims',
            icon: FileText,
            active: pathname === '/dashboard/claims',
        },
        {
            name: 'Profil',
            href: '/dashboard/profile',
            icon: User,
            active: pathname === '/dashboard/profile',
        },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 h-16 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800 flex items-center justify-around z-50 safe-area-bottom">
            {tabs.map((tab) => (
                <Link
                    key={tab.name}
                    href={tab.href}
                    className="flex flex-col items-center justify-center w-full h-full"
                >
                    <tab.icon
                        className={cn(
                            "w-6 h-6 mb-1 transition-colors",
                            tab.active ? "text-emerald-600" : "text-gray-400"
                        )}
                    />
                    <span
                        className={cn(
                            "text-[10px] font-medium transition-colors",
                            tab.active ? "text-emerald-600" : "text-gray-400"
                        )}
                    >
                        {tab.name}
                    </span>
                </Link>
            ))}
        </div>
    );
}
