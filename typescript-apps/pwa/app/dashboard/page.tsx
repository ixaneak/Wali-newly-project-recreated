"use client";

import { useState, useRef } from 'react';
import { Bell, ShieldCheck, Zap, QrCode, Star, Heart, ChevronRight, Pill, TrendingUp } from 'lucide-react';
import RechargeModal from '@/components/payment/RechargeModal';
import { useDashboard } from '@/hooks/useMobileData';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const healthTips = [
    "Sleep at least 7 hours a night for good immunity.",
    "Drink at least 1.5L of water daily to stay hydrated.",
    "Take a 15-minute walk daily to protect your heart.",
    "Wash your hands regularly to prevent infections.",
];

export default function Dashboard() {
    const router = useRouter();
    const { data, loading, error } = useDashboard();
    const [isRechargeOpen, setIsRechargeOpen] = useState(false);
    const [tipIndex, setTipIndex] = useState(0);
    const touchStartX = useRef<number | null>(null);

    const partnerName = "NSIA Assurance";

    // --- Dark mode color tokens ---
    const C = {
        pageBg: '#111827',
        cardBg: '#1F2937',
        cardBorder: 'rgba(255,255,255,0.08)',
        green: '#059669',
        greenGlow: '0 0 8px rgba(5, 150, 105, 0.4)',
        textPrimary: '#F9FAFB',
        textSecondary: '#E5E7EB',
        textTertiary: '#9CA3AF',
        textSubtle: '#6B7280',
        trackBg: '#374151',
        expense: '#F87171',
        income: '#34D399',
        amber: '#F59E0B',
        navBorder: 'rgba(255,255,255,0.06)',
    };

    if (loading) {
        return (
            <div style={{ background: C.pageBg, minHeight: '100vh', padding: 24 }}>
                <div className="animate-pulse space-y-6">
                    <div style={{ height: 32, background: C.trackBg, borderRadius: 8, width: '50%' }} />
                    <div style={{ height: 200, background: C.cardBg, borderRadius: 16 }} />
                    <div style={{ display: 'flex', gap: 16 }}>
                        <div style={{ flex: 1, height: 80, background: C.cardBg, borderRadius: 12 }} />
                        <div style={{ flex: 1, height: 80, background: C.cardBg, borderRadius: 12 }} />
                    </div>
                </div>
            </div>
        );
    }

    if (error) return <div style={{ background: C.pageBg, minHeight: '100vh', padding: 24, color: C.expense, textAlign: 'center' }}>{error}</div>;
    if (!data) return null;

    const usagePercent = Math.min((data.coverage.used / data.coverage.total) * 100, 100);
    const firstName = data.user.name.split(' ')[0];

    return (
        <div style={{ background: C.pageBg, minHeight: '100vh', paddingBottom: 'calc(80px + env(safe-area-inset-bottom, 0px))' }}>

            {/* ===== HEADER ===== */}
            <header style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '20px 20px 16px', height: 60,
            }}>
                {/* Left: Logo + Wave */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {/* Mini Wali Logo */}
                    <div style={{
                        width: 28, height: 28, backgroundColor: '#FFFFFF',
                        borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                        <svg width="16" height="16" viewBox="0 0 40 40" fill="none">
                            <path d="M8 8 C8 8, 8 28, 20 32 C32 28, 32 8, 32 8" stroke="#059669" strokeWidth="5" strokeLinecap="round" fill="none" />
                        </svg>
                    </div>
                    <span style={{ fontSize: 20 }}>👋</span>
                </div>

                {/* Center: Name */}
                <h1 style={{ fontSize: 24, fontWeight: 700, color: C.textPrimary }}>{firstName}</h1>

                {/* Right: Bell */}
                <button
                    onClick={() => router.push('/dashboard/notifications/inbox')}
                    style={{
                        position: 'relative', padding: 8, background: 'none', border: 'none', cursor: 'pointer',
                    }}
                >
                    <Bell size={24} color={C.textTertiary} strokeWidth={1.5} />
                    {data.notifications > 0 && (
                        <span style={{
                            position: 'absolute', top: 6, right: 6,
                            width: 6, height: 6, borderRadius: '50%',
                            backgroundColor: '#EF4444',
                            boxShadow: '0 0 6px rgba(239,68,68,0.5)',
                            border: '2px solid ' + C.pageBg,
                        }} />
                    )}
                </button>
            </header>

            <main style={{ padding: '0 20px' }}>

                {/* ===== COVERAGE CARD ===== */}
                <div style={{
                    background: `linear-gradient(145deg, ${C.cardBg} 0%, ${C.pageBg} 100%)`,
                    border: `1px solid ${C.cardBorder}`,
                    borderRadius: 16, padding: 24, marginBottom: 20,
                }}>
                    {/* Card Header Row */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <Star size={16} color={C.amber} fill={C.amber} />
                            <div>
                                <p style={{ fontSize: 10, color: C.textSubtle, fontWeight: 500, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 }}>MY PLAN</p>
                                <h3 style={{ fontSize: 16, fontWeight: 600, color: C.textSecondary }}>Wali Startup</h3>
                            </div>
                        </div>
                        {/* Active Pill */}
                        <div style={{
                            background: 'rgba(16, 185, 129, 0.15)',
                            color: '#34D399', fontSize: 12, fontWeight: 500,
                            padding: '4px 12px', borderRadius: 12,
                            boxShadow: '0 0 6px rgba(16, 185, 129, 0.2)',
                        }}>
                            Active
                        </div>
                    </div>

                    {/* Hero Amount */}
                    <div style={{ marginBottom: 24 }}>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                            <span style={{ fontSize: 32, fontWeight: 700, color: C.textPrimary }}>
                                {(data.coverage.total - data.coverage.used).toLocaleString()}
                            </span>
                            <span style={{ fontSize: 16, color: C.textPrimary, verticalAlign: 'super' }}>FCFA</span>
                        </div>
                        <p style={{ fontSize: 14, color: C.textTertiary, marginTop: 4 }}>
                            of {data.coverage.total.toLocaleString()} FCFA
                        </p>
                    </div>

                    {/* Progress Bar */}
                    <div style={{ marginBottom: 20 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span style={{ fontSize: 12, color: C.textSubtle }}>Usage</span>
                            <span style={{ fontSize: 12, color: C.textSubtle }}>{Math.round(usagePercent)}% used</span>
                        </div>
                        <div style={{ height: 8, borderRadius: 4, backgroundColor: C.trackBg, overflow: 'hidden' }}>
                            <div style={{
                                height: '100%', borderRadius: 4,
                                backgroundColor: C.green,
                                boxShadow: C.greenGlow,
                                width: `${usagePercent}%`,
                                transition: 'width 0.5s ease',
                            }} />
                        </div>
                    </div>

                    {/* Meta Row */}
                    <div style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        paddingTop: 12, borderTop: `1px solid ${C.navBorder}`,
                        marginBottom: 16,
                    }}>
                        <span style={{ fontSize: 12, color: C.textSubtle }}>Renewal on 01/02</span>
                        <span style={{ fontSize: 12, fontWeight: 500, color: C.textTertiary }}>Wali Artisan Standard</span>
                    </div>

                    {/* Footer */}
                    <div style={{
                        borderTop: `1px solid ${C.navBorder}`,
                        paddingTop: 12, textAlign: 'center',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                    }}>
                        <ShieldCheck size={12} color={C.textSubtle} />
                        <span style={{ fontSize: 11, color: C.textSubtle }}>Cover provided by {partnerName}</span>
                    </div>
                </div>

                {/* ===== ACTION BUTTONS (GHOST) ===== */}
                <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
                    <button
                        onClick={() => router.push('/dashboard/card')}
                        style={{
                            flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                            gap: 8, padding: '16px 0', background: 'transparent',
                            border: `1px solid #4B5563`, borderRadius: 12, cursor: 'pointer',
                            transition: 'all 0.2s',
                        }}
                        onMouseEnter={e => { const t = e.currentTarget; t.style.background = 'rgba(5,150,105,0.15)'; t.style.borderColor = C.green; }}
                        onMouseLeave={e => { const t = e.currentTarget; t.style.background = 'transparent'; t.style.borderColor = '#4B5563'; }}
                    >
                        <QrCode size={24} color={C.green} />
                        <span style={{ fontSize: 14, fontWeight: 500, color: C.textSecondary }}>Scanner</span>
                    </button>

                    <button
                        onClick={() => setIsRechargeOpen(true)}
                        style={{
                            flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                            gap: 8, padding: '16px 0', background: 'transparent',
                            border: `1px solid #4B5563`, borderRadius: 12, cursor: 'pointer',
                            transition: 'all 0.2s',
                        }}
                        onMouseEnter={e => { const t = e.currentTarget; t.style.background = 'rgba(5,150,105,0.15)'; t.style.borderColor = C.green; }}
                        onMouseLeave={e => { const t = e.currentTarget; t.style.background = 'transparent'; t.style.borderColor = '#4B5563'; }}
                    >
                        <Zap size={24} color={C.green} />
                        <span style={{ fontSize: 14, fontWeight: 500, color: C.textSecondary }}>Recharge</span>
                    </button>
                </div>

                {/* ===== HEALTH ADVICE (Swipeable) ===== */}
                <div
                    style={{
                        background: C.cardBg, border: `1px solid ${C.cardBorder}`,
                        borderRadius: 12, padding: 16, marginBottom: 24,
                        overflow: 'hidden', userSelect: 'none', cursor: 'grab',
                    }}
                    onTouchStart={(e) => { touchStartX.current = e.touches[0].clientX; }}
                    onTouchEnd={(e) => {
                        if (touchStartX.current === null) return;
                        const diff = e.changedTouches[0].clientX - touchStartX.current;
                        if (Math.abs(diff) > 40) {
                            setTipIndex((prev) =>
                                diff < 0
                                    ? (prev + 1) % healthTips.length
                                    : (prev - 1 + healthTips.length) % healthTips.length
                            );
                        }
                        touchStartX.current = null;
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
                            <Heart size={20} color="#F87171" fill="none" style={{ flexShrink: 0, filter: 'drop-shadow(0 0 4px rgba(248,113,113,0.3))' }} />
                            <span
                                key={tipIndex}
                                style={{
                                    fontSize: 14, color: C.textSecondary, lineHeight: 1.4,
                                    animation: 'tipSlide 0.3s ease',
                                }}
                            >
                                {healthTips[tipIndex]}
                            </span>
                        </div>
                        <button
                            onClick={() => setTipIndex((prev) => (prev + 1) % healthTips.length)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4, paddingLeft: 12,
                                background: 'none', border: 'none', cursor: 'pointer',
                            }}
                            aria-label="Next tip"
                        >
                            <span style={{ fontSize: 12, fontWeight: 500, color: C.textSubtle }}>{tipIndex + 1}/{healthTips.length}</span>
                            <ChevronRight size={16} color="#4B5563" />
                        </button>
                    </div>
                    {/* Dot indicators */}
                    <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 10 }}>
                        {healthTips.map((_, i) => (
                            <div
                                key={i}
                                onClick={() => setTipIndex(i)}
                                style={{
                                    width: i === tipIndex ? 16 : 6, height: 6,
                                    borderRadius: 3,
                                    background: i === tipIndex ? '#F87171' : C.trackBg,
                                    transition: 'all 0.3s ease',
                                    cursor: 'pointer',
                                }}
                            />
                        ))}
                    </div>
                </div>

                {/* Keyframe for slide animation */}
                <style>{`
                    @keyframes tipSlide {
                        from { opacity: 0; transform: translateX(20px); }
                        to   { opacity: 1; transform: translateX(0); }
                    }
                `}</style>

                {/* ===== RECENT ACTIVITY ===== */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h3 style={{ fontSize: 18, fontWeight: 600, color: C.textPrimary }}>Recent Activity</h3>
                    <button style={{ fontSize: 14, fontWeight: 500, color: C.green, background: 'none', border: 'none', cursor: 'pointer' }}>
                        View All
                    </button>
                </div>

                {/* Transaction Cards (Dark Mode inline) */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {data.recentTransactions && data.recentTransactions.length > 0 ? (
                        data.recentTransactions.slice(0, 5).map((tx: any) => {
                            const isExpense = tx.type === 'utilisation';
                            const isIncome = tx.type === 'cotisation' || tx.type === 'remboursement';
                            const amountColor = isExpense ? C.expense : C.income;
                            const sign = isExpense ? '-' : '+';
                            const iconBg = isExpense ? 'rgba(239,68,68,0.1)' : 'rgba(5,150,105,0.1)';
                            const accentBorder = isExpense ? C.expense : C.green;

                            return (
                                <div key={tx.id} style={{
                                    background: C.cardBg,
                                    borderLeft: `3px solid ${accentBorder}`,
                                    borderRadius: 12, padding: 16,
                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                    cursor: 'pointer', transition: 'background 0.2s',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        {/* Icon circle */}
                                        <div style={{
                                            width: 40, height: 40, borderRadius: '50%',
                                            backgroundColor: iconBg,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        }}>
                                            {isExpense
                                                ? <Pill size={18} color={C.expense} />
                                                : <TrendingUp size={18} color={C.income} />
                                            }
                                        </div>
                                        <div>
                                            <h4 style={{ fontSize: 16, fontWeight: 600, color: C.textPrimary, marginBottom: 2 }}>
                                                {tx.title}
                                            </h4>
                                            <p style={{ fontSize: 12, color: C.textSubtle }}>
                                                {(() => {
                                                    try {
                                                        return format(new Date(tx.date), "MMMM d, h:mm a", { locale: fr });
                                                    } catch { return tx.date; }
                                                })()}
                                            </p>
                                        </div>
                                    </div>
                                    <span style={{ fontSize: 16, fontWeight: 600, color: amountColor }}>
                                        {sign}{tx.amount.toLocaleString()} F
                                    </span>
                                </div>
                            );
                        })
                    ) : (
                        <div style={{
                            textAlign: 'center', padding: 32, color: C.textSubtle,
                            fontSize: 14, background: C.cardBg, borderRadius: 12,
                            border: `1px dashed ${C.cardBorder}`,
                        }}>
                            No recent transactions
                        </div>
                    )}
                </div>
            </main>

            {/* Recharge Modal */}
            <RechargeModal
                isOpen={isRechargeOpen}
                onClose={() => setIsRechargeOpen(false)}
                userId={data.user.id || "test-user"}
                userPhone={data.user.phone}
            />
        </div>
    );
}
