"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, History, FileText, User } from 'lucide-react';

export default function BottomNav() {
    const pathname = usePathname();

    const tabs = [
        { name: 'Home', href: '/dashboard', icon: Home, active: pathname === '/dashboard' },
        { name: 'Historical', href: '/dashboard/history', icon: History, active: pathname?.startsWith('/dashboard/history') },
        { name: 'Incidents', href: '/dashboard/claims', icon: FileText, active: pathname?.startsWith('/dashboard/claims') },
        { name: 'Profile', href: '/dashboard/profile', icon: User, active: pathname?.startsWith('/dashboard/profile') },
    ];

    return (
        <div
            style={{
                position: 'fixed',
                bottom: 0,
                left: 0,
                right: 0,
                backgroundColor: '#111827',
                borderTop: '1px solid rgba(255,255,255,0.06)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-around',
                height: 'calc(64px + env(safe-area-inset-bottom, 0px))',
                paddingBottom: 'env(safe-area-inset-bottom, 0px)',
                zIndex: 50,
            }}
        >
            {tabs.map((tab) => (
                <Link
                    key={tab.name}
                    href={tab.href}
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flex: 1,
                        height: '100%',
                        textDecoration: 'none',
                        gap: 4,
                    }}
                >
                    <tab.icon
                        size={24}
                        strokeWidth={1.5}
                        color={tab.active ? '#059669' : '#6B7280'}
                        className={tab.active ? 'fill-[#059669]/20' : ''}
                    />
                    <span style={{
                        fontSize: 10,
                        fontWeight: 500,
                        color: tab.active ? '#E5E7EB' : '#6B7280',
                    }}>
                        {tab.name}
                    </span>
                </Link>
            ))}
        </div>
    );
}
