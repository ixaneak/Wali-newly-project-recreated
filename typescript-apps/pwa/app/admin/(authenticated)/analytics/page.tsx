"use client";

import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    Download,
    PieChart as PieChartIcon,
    Activity,
    Map,
    Building2,
    FileText,
    ArrowUpRight,
    ArrowDownRight,
    Wallet,
    PiggyBank,
    Pill
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Line,
    ComposedChart,
    Legend
} from 'recharts';
import { complianceService } from '@/lib/api-client';
import AdminHeader from '@/components/admin/AdminHeader';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const COLORS = ['#0ea5e9', '#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#8b5cf6'];

// ═════════════════════════════════════════════════════════════════
// ADMIN UNIFIED FINANCIAL ANALYTICS
// Combines: Pharmacies + Claims + Payments + Platform Revenue
// ═════════════════════════════════════════════════════════════════

interface UnifiedAdminAnalytics {
    // Overall platform health
    platform: {
        totalRevenue: number;
        totalPayouts: number;
        netPosition: number;
        activeUsers: number;
        totalTransactions: number;
    };
    
    // Revenue breakdown by source
    revenueBySource: {
        premiums: number;           // User cotisations
        pharmacyFees: number;       // SaaS fees from pharmacies
        otherRevenue: number;
    };
    
    // Outflows/Payouts
    payouts: {
        claimPayouts: number;       // Insurance reimbursements to users
        pharmacyReimbursements: number;  // Direct pharmacy payments
        refunds: number;
    };
    
    // Pharmacy ecosystem
    pharmacyMetrics: {
        activePharmacies: number;
        totalPharmacyRevenue: number;
        avgTransactionValue: number;
        topPharmacies: PharmacyData[];
    };
    
    // Claims ecosystem
    claimsMetrics: {
        totalSubmitted: number;
        totalApproved: number;
        totalRejected: number;
        avgPayoutAmount: number;
        approvalRate: number;
    };
    
    // Time series data
    timeSeries: TimeSeriesPoint[];
    
    // Distribution data
    categoryDistribution: CategoryData[];
}

interface PharmacyData {
    id: string;
    name: string;
    revenue: number;
    transactions: number;
    location: string;
    growth: number;
}

interface TimeSeriesPoint {
    date: string;
    label: string;
    premiums: number;
    claimPayouts: number;
    pharmacyRevenue: number;
    netPosition: number;
    transactionCount: number;
}

interface CategoryData {
    name: string;
    value: number;
    color: string;
}

// Mock data generator for admin analytics
function generateAdminAnalytics(timeframe: string): UnifiedAdminAnalytics {
    const days = timeframe === '7D' ? 7 : timeframe === '30D' ? 30 : timeframe === '90D' ? 90 : 365;
    
    // Generate time series
    const timeSeries: TimeSeriesPoint[] = [];
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        
        const isWeekend = date.getDay() === 0 || date.getDay() === 6;
        const basePremium = isWeekend ? 50000 : 250000;
        const basePayout = isWeekend ? 100000 : 450000;
        const basePharmacy = isWeekend ? 75000 : 380000;
        
        // Add some randomness
        const variance = 0.2;
        const premiums = Math.floor(basePremium * (1 + (Math.random() - 0.5) * variance));
        const payouts = Math.floor(basePayout * (1 + (Math.random() - 0.5) * variance));
        const pharmacyRev = Math.floor(basePharmacy * (1 + (Math.random() - 0.5) * variance));
        
        timeSeries.push({
            date: date.toISOString().split('T')[0],
            label: date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
            premiums,
            claimPayouts: payouts,
            pharmacyRevenue: pharmacyRev,
            netPosition: premiums + pharmacyRev - payouts,
            transactionCount: Math.floor(Math.random() * 50) + 20
        });
    }
    
    // Calculate totals from time series
    const totalPremiums = timeSeries.reduce((sum, d) => sum + d.premiums, 0);
    const totalPayouts = timeSeries.reduce((sum, d) => sum + d.claimPayouts, 0);
    const totalPharmacyRev = timeSeries.reduce((sum, d) => sum + d.pharmacyRevenue, 0);
    
    return {
        platform: {
            totalRevenue: totalPremiums + totalPharmacyRev + 1250000, // + other revenue
            totalPayouts: totalPayouts,
            netPosition: totalPremiums + totalPharmacyRev - totalPayouts,
            activeUsers: 2847,
            totalTransactions: timeSeries.reduce((sum, d) => sum + d.transactionCount, 0)
        },
        
        revenueBySource: {
            premiums: totalPremiums,
            pharmacyFees: Math.floor(totalPharmacyRev * 0.15), // 15% SaaS fee
            otherRevenue: 1250000
        },
        
        payouts: {
            claimPayouts: totalPayouts,
            pharmacyReimbursements: Math.floor(totalPharmacyRev * 0.85),
            refunds: 450000
        },
        
        pharmacyMetrics: {
            activePharmacies: 47,
            totalPharmacyRevenue: totalPharmacyRev,
            avgTransactionValue: 8750,
            topPharmacies: [
                { id: 'p1', name: 'Pharmacie Ivoire Santé - Cocody', revenue: 2845000, transactions: 342, location: 'Cocody', growth: 12.5 },
                { id: 'p2', name: 'Pharmacie de la Paix - Plateau', revenue: 2150000, transactions: 268, location: 'Plateau', growth: 8.3 },
                { id: 'p3', name: 'Grande Pharmacie d\'Abidjan', revenue: 1890000, transactions: 221, location: 'Treichville', growth: -2.1 },
                { id: 'p4', name: 'Pharmacie du Centre - Marcory', revenue: 1650000, transactions: 198, location: 'Marcory', growth: 15.7 },
                { id: 'p5', name: 'Pharmacie Riviera Bonoumin', revenue: 1420000, transactions: 175, location: 'Riviera', growth: 5.2 },
            ]
        },
        
        claimsMetrics: {
            totalSubmitted: 156,
            totalApproved: 124,
            totalRejected: 32,
            avgPayoutAmount: 125000,
            approvalRate: 79.5
        },
        
        timeSeries,
        
        categoryDistribution: [
            { name: 'Primes Assurance', value: totalPremiums, color: COLORS[0] },
            { name: 'Frais Pharmacies', value: Math.floor(totalPharmacyRev * 0.15), color: COLORS[1] },
            { name: 'Remb. Sinistres', value: totalPayouts, color: COLORS[3] },
            { name: 'Remb. Pharmacies', value: Math.floor(totalPharmacyRev * 0.85), color: COLORS[5] },
            { name: 'Autres Revenus', value: 1250000, color: COLORS[4] },
        ]
    };
}

export default function AdminAnalyticsPage() {
    const [data, setData] = useState<UnifiedAdminAnalytics | null>(null);
    const [loading, setLoading] = useState(true);
    const [timeframe, setTimeframe] = useState('30D');
    const [activeTab, setActiveTab] = useState('overview');

    // Single useEffect to handle data fetching - flows cleanly with timeframe changes
    useEffect(() => {
        let isMounted = true;
        
        const fetchAnalytics = async () => {
            setLoading(true);
            try {
                const result = await complianceService.getAdminUnifiedAnalytics(timeframe as any);
                if (isMounted) {
                    setData(result);
                }
            } catch (error) {
                console.error("Analytics fetch failure:", error);
                if (isMounted) {
                    // Fallback to mock data
                    setData(generateAdminAnalytics(timeframe));
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };
        
        fetchAnalytics();
        
        // Cleanup to prevent state updates on unmounted component
        return () => { isMounted = false; };
    }, [timeframe]);

    if (loading || !data) {
        return (
            <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
                <AdminHeader
                    title="Intelligence d'Affaires"
                    description="Chargement des données financières..."
                />
                <div className="animate-pulse space-y-6">
                    <div className="grid grid-cols-4 gap-6">
                        {[1,2,3,4].map(i => (
                            <div key={i} className="h-32 bg-slate-900 rounded-2xl" />
                        ))}
                    </div>
                    <div className="h-96 bg-slate-900 rounded-2xl" />
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Performance Financière Globale"
                description="Vue consolidée: Pharmacies × Sinistres × Transactions"
            />

            {/* Controls */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex bg-slate-900/60 p-1 rounded-2xl border border-slate-800 shadow-inner">
                    {['7D', '30D', '90D', '1Y'].map((t) => (
                        <button
                            key={t}
                            onClick={() => setTimeframe(t)}
                            className={cn(
                                "px-8 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all",
                                timeframe === t ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            {t}
                        </button>
                    ))}
                </div>

                <Button variant="outline" className="h-12 border-slate-800 bg-slate-900/40 text-[10px] font-black uppercase tracking-widest gap-3 px-6">
                    <Download size={16} /> EXPORTER RAPPORT (.XLSX)
                </Button>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <KPICard
                    title="Revenus Totaux"
                    value={data.platform.totalRevenue}
                    icon={Wallet}
                    trend={+12.4}
                    color="emerald"
                    subtitle="Primes + Frais Pharmacies"
                />
                <KPICard
                    title="Paiements Sinistres"
                    value={data.payouts.claimPayouts}
                    icon={FileText}
                    trend={+8.7}
                    color="rose"
                    subtitle="Remboursements aux artisans"
                />
                <KPICard
                    title="Volume Pharmacies"
                    value={data.pharmacyMetrics.totalPharmacyRevenue}
                    icon={Building2}
                    trend={+15.3}
                    color="cyan"
                    subtitle={`${data.pharmacyMetrics.activePharmacies} partenaires actifs`}
                />
                <KPICard
                    title="Position Nette"
                    value={data.platform.netPosition}
                    icon={PiggyBank}
                    trend={+18.2}
                    color="amber"
                    subtitle="Revenus - Paiements"
                    highlight={data.platform.netPosition > 0}
                />
            </div>

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                <TabsList className="bg-slate-900/60 p-1 rounded-2xl border border-slate-800">
                    {[
                        { id: 'overview', label: 'Vue Globale', icon: TrendingUp },
                        { id: 'pharmacies', label: 'Pharmacies', icon: Building2 },
                        { id: 'claims', label: 'Sinistres', icon: FileText },
                        { id: 'flows', label: 'Flux Détaillés', icon: Activity },
                    ].map((tab) => (
                        <TabsTrigger
                            key={tab.id}
                            value={tab.id}
                            className={cn(
                                "px-6 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all data-[state=active]:bg-cyan-500 data-[state=active]:text-white data-[state=inactive]:text-slate-500 data-[state=inactive]:hover:text-slate-300 gap-2"
                            )}
                        >
                            <tab.icon size={14} />
                            {tab.label}
                        </TabsTrigger>
                    ))}
                </TabsList>

                {/* OVERVIEW TAB */}
                <TabsContent value="overview" className="space-y-6">
                    {/* Main Chart - Combined Flow */}
                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardHeader className="p-8 pb-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle className="text-lg font-black uppercase tracking-tight">Flux Financiers Consolidés</CardTitle>
                                    <CardDescription>Primes collectées vs Paiements effectués</CardDescription>
                                </div>
                                <div className="flex gap-4 text-sm">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-emerald-500" />
                                        <span className="text-slate-400">Revenus</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-rose-500" />
                                        <span className="text-slate-400">Paiements</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-cyan-500" />
                                        <span className="text-slate-400">Position Nette</span>
                                    </div>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="p-8 pt-0">
                            <div className="h-[400px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart data={data.timeSeries}>
                                        <defs>
                                            <linearGradient id="colorPremiums" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="colorPayouts" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis dataKey="label" stroke="#475569" fontSize={10} fontWeight="600" tickLine={false} axisLine={false} />
                                        <YAxis stroke="#475569" fontSize={10} fontWeight="600" tickLine={false} axisLine={false} tickFormatter={(v) => `${v / 1000000}M`} />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: '12px', fontSize: '12px' }}
                                            formatter={(value) => [`${(value as number)?.toLocaleString() || 0} FCFA`, '']}
                                        />
                                        <Legend />
                                        <Area type="monotone" dataKey="premiums" name="Primes Collectées" stroke="#10b981" strokeWidth={2} fill="url(#colorPremiums)" />
                                        <Area type="monotone" dataKey="claimPayouts" name="Paiements Sinistres" stroke="#f43f5e" strokeWidth={2} fill="url(#colorPayouts)" />
                                        <Line type="monotone" dataKey="netPosition" name="Position Nette" stroke="#0ea5e9" strokeWidth={3} dot={false} />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Distribution & Metrics Row */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Revenue Distribution */}
                        <Card className="border-slate-800 bg-slate-900/40">
                            <CardHeader className="p-8 pb-4">
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-500">
                                        <PieChartIcon size={20} />
                                    </div>
                                    <CardTitle className="text-lg font-black uppercase tracking-tight">Répartition des Flux</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent className="p-8 pt-0">
                                <div className="h-[300px] flex items-center">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={data.categoryDistribution}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={80}
                                                outerRadius={120}
                                                paddingAngle={5}
                                                dataKey="value"
                                            >
                                                {data.categoryDistribution.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: '12px', fontSize: '12px' }}
                                                formatter={(value) => `${((value as number) / 1000000 || 0).toFixed(1)}M FCFA`}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="grid grid-cols-2 gap-4 mt-4">
                                    {data.categoryDistribution.map((cat, i) => (
                                        <div key={i} className="flex items-center gap-3">
                                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.color }} />
                                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">
                                                {cat.name}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Key Metrics */}
                        <Card className="border-slate-800 bg-slate-900/40">
                            <CardHeader className="p-8 pb-4">
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-500">
                                        <Activity size={20} />
                                    </div>
                                    <CardTitle className="text-lg font-black uppercase tracking-tight">Métriques Clés</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent className="p-8 pt-0 space-y-6">
                                <MetricRow
                                    label="Taux d'approbation sinistres"
                                    value={`${data.claimsMetrics.approvalRate}%`}
                                    subvalue={`${data.claimsMetrics.totalApproved} / ${data.claimsMetrics.totalSubmitted}`}
                                    progress={data.claimsMetrics.approvalRate}
                                    color="emerald"
                                />
                                <MetricRow
                                    label="Panier moyen pharmacie"
                                    value={`${data.pharmacyMetrics.avgTransactionValue.toLocaleString()} F`}
                                    subvalue="par transaction"
                                    progress={75}
                                    color="cyan"
                                />
                                <MetricRow
                                    label="Ratio Sinistres/Primes"
                                    value={`${((data.payouts.claimPayouts / data.revenueBySource.premiums) * 100).toFixed(1)}%`}
                                    subvalue="Sain: < 80%"
                                    progress={65}
                                    color="amber"
                                />
                                <MetricRow
                                    label="Utilisateurs actifs"
                                    value={data.platform.activeUsers.toLocaleString()}
                                    subvalue={`${data.platform.totalTransactions} transactions`}
                                    progress={82}
                                    color="indigo"
                                />
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* PHARMACIES TAB */}
                <TabsContent value="pharmacies" className="space-y-6">
                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardHeader className="p-8">
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle className="text-lg font-black uppercase tracking-tight">Performance des Pharmacies Partenaires</CardTitle>
                                    <CardDescription>Classement par volume de transactions</CardDescription>
                                </div>
                                <div className="flex gap-4">
                                    <div className="text-right">
                                        <div className="text-2xl font-black text-white">{data.pharmacyMetrics.activePharmacies}</div>
                                        <div className="text-[10px] font-black text-slate-500 uppercase">Partenaires Actifs</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-2xl font-black text-cyan-400">{(data.pharmacyMetrics.totalPharmacyRevenue / 1000000).toFixed(1)}M</div>
                                        <div className="text-[10px] font-black text-slate-500 uppercase">Volume Total</div>
                                    </div>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="p-8 pt-0">
                            <div className="space-y-4">
                                {data.pharmacyMetrics.topPharmacies.map((pharmacy, index) => (
                                    <div key={pharmacy.id} className="flex items-center gap-4 p-4 bg-slate-800/30 rounded-xl">
                                        <div className={cn(
                                            "w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm",
                                            index === 0 ? "bg-yellow-500/20 text-yellow-400" :
                                            index === 1 ? "bg-slate-400/20 text-slate-400" :
                                            index === 2 ? "bg-orange-600/20 text-orange-400" :
                                            "bg-slate-700 text-slate-500"
                                        )}>
                                            {index + 1}
                                        </div>
                                        <div className="flex-1">
                                            <h4 className="font-bold text-white">{pharmacy.name}</h4>
                                            <div className="flex items-center gap-4 text-xs text-slate-400">
                                                <span className="flex items-center gap-1">
                                                    <Map size={12} /> {pharmacy.location}
                                                </span>
                                                <span>{pharmacy.transactions} transactions</span>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="font-black text-white">{pharmacy.revenue.toLocaleString()} F</div>
                                            <div className={cn(
                                                "text-xs font-bold flex items-center gap-1",
                                                pharmacy.growth > 0 ? "text-emerald-400" : "text-rose-400"
                                            )}>
                                                {pharmacy.growth > 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                                                {Math.abs(pharmacy.growth)}%
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* CLAIMS TAB */}
                <TabsContent value="claims" className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <StatCard
                            title="Sinistres Déposés"
                            value={data.claimsMetrics.totalSubmitted}
                            icon={FileText}
                            color="cyan"
                        />
                        <StatCard
                            title="Sinistres Approuvés"
                            value={data.claimsMetrics.totalApproved}
                            icon={TrendingUp}
                            color="emerald"
                        />
                        <StatCard
                            title="Sinistres Rejetés"
                            value={data.claimsMetrics.totalRejected}
                            icon={Activity}
                            color="rose"
                        />
                    </div>

                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardHeader className="p-8">
                            <CardTitle className="text-lg font-black uppercase tracking-tight">Analyse des Paiements Sinistres</CardTitle>
                        </CardHeader>
                        <CardContent className="p-8 pt-0">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div>
                                    <div className="text-sm text-slate-400 mb-2">Montant Total Paiements</div>
                                    <div className="text-4xl font-black text-white">{data.payouts.claimPayouts.toLocaleString()} <span className="text-lg text-slate-500">FCFA</span></div>
                                    <div className="h-2 bg-slate-800 rounded-full mt-4 overflow-hidden">
                                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: '75%' }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="text-sm text-slate-400 mb-2">Montant Moyen par Sinistre</div>
                                    <div className="text-4xl font-black text-white">{data.claimsMetrics.avgPayoutAmount.toLocaleString()} <span className="text-lg text-slate-500">FCFA</span></div>
                                    <div className="h-2 bg-slate-800 rounded-full mt-4 overflow-hidden">
                                        <div className="h-full bg-cyan-500 rounded-full" style={{ width: '60%' }} />
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* DETAILED FLOWS TAB */}
                <TabsContent value="flows" className="space-y-6">
                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardHeader className="p-8">
                            <CardTitle className="text-lg font-black uppercase tracking-tight">Détail des Flux Financiers</CardTitle>
                        </CardHeader>
                        <CardContent className="p-8 pt-0">
                            <div className="space-y-6">
                                {/* Revenue Sources */}
                                <div>
                                    <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-widest mb-4">Revenus (Entrées)</h4>
                                    <div className="space-y-3">
                                        <FlowRow label="Primes Assurance (Artisans)" value={data.revenueBySource.premiums} color="emerald" />
                                        <FlowRow label="Frais SaaS Pharmacies (15%)" value={data.revenueBySource.pharmacyFees} color="cyan" />
                                        <FlowRow label="Autres Revenus" value={data.revenueBySource.otherRevenue} color="amber" />
                                        <div className="pt-3 border-t border-slate-800">
                                            <FlowRow label="TOTAL REVENUS" value={data.platform.totalRevenue} color="white" isTotal />
                                        </div>
                                    </div>
                                </div>

                                {/* Payouts */}
                                <div>
                                    <h4 className="text-sm font-bold text-rose-400 uppercase tracking-widest mb-4">Paiements (Sorties)</h4>
                                    <div className="space-y-3">
                                        <FlowRow label="Remboursements Sinistres" value={data.payouts.claimPayouts} color="rose" />
                                        <FlowRow label="Paiements Directs Pharmacies" value={data.payouts.pharmacyReimbursements} color="orange" />
                                        <FlowRow label="Remboursements Divers" value={data.payouts.refunds} color="slate" />
                                        <div className="pt-3 border-t border-slate-800">
                                            <FlowRow label="TOTAL PAIEMENTS" value={data.platform.totalPayouts} color="white" isTotal />
                                        </div>
                                    </div>
                                </div>

                                {/* Net Position */}
                                <div className="bg-slate-800/50 rounded-xl p-6">
                                    <div className="flex items-center justify-between">
                                        <span className="text-lg font-black text-white">POSITION NETTE PLATEFORME</span>
                                        <span className={cn(
                                            "text-2xl font-black",
                                            data.platform.netPosition > 0 ? "text-emerald-400" : "text-rose-400"
                                        )}>
                                            {data.platform.netPosition > 0 ? '+' : ''}{data.platform.netPosition.toLocaleString()} FCFA
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-400 mt-2">
                                        {data.platform.netPosition > 0 
                                            ? "La plateforme est rentable sur cette période" 
                                            : "La plateforme dépense plus qu'elle ne gagne"}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}

// ═════════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ═════════════════════════════════════════════════════════════════

function KPICard({ title, value, icon: Icon, trend, color, subtitle, highlight }: {
    title: string;
    value: number;
    icon: any;
    trend: number;
    color: string;
    subtitle: string;
    highlight?: boolean;
}) {
    const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
        emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
        rose: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20' },
        cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20' },
        amber: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
    };
    
    const colors = colorClasses[color] || colorClasses.emerald;

    return (
        <Card className={cn("border-slate-800 bg-slate-900/40 relative overflow-hidden", highlight && "border-amber-500/30")}>
            {highlight && <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-[50px]" />}
            <CardContent className="p-6">
                <div className="flex items-start justify-between">
                    <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", colors.bg, colors.text)}>
                        <Icon size={24} />
                    </div>
                    <div className={cn("text-xs font-bold px-2 py-1 rounded-full", colors.bg, colors.text)}>
                        {trend > 0 ? '+' : ''}{trend}%
                    </div>
                </div>
                <div className="mt-4">
                    <div className="text-2xl font-black text-white">{(value / 1000000).toFixed(1)}M <span className="text-sm text-slate-500">FCFA</span></div>
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-1">{title}</div>
                    <div className="text-[10px] text-slate-500 mt-1">{subtitle}</div>
                </div>
            </CardContent>
        </Card>
    );
}

function MetricRow({ label, value, subvalue, progress, color }: {
    label: string;
    value: string;
    subvalue: string;
    progress: number;
    color: string;
}) {
    const colorClasses: Record<string, string> = {
        emerald: 'bg-emerald-500',
        cyan: 'bg-cyan-500',
        amber: 'bg-amber-500',
        indigo: 'bg-indigo-500',
    };

    return (
        <div>
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">{label}</span>
                <div className="text-right">
                    <div className="text-sm font-bold text-white">{value}</div>
                    <div className="text-[10px] text-slate-500">{subvalue}</div>
                </div>
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className={cn("h-full rounded-full transition-all", colorClasses[color])} style={{ width: `${progress}%` }} />
            </div>
        </div>
    );
}

function StatCard({ title, value, icon: Icon, color }: {
    title: string;
    value: number;
    icon: any;
    color: string;
}) {
    const colorClasses: Record<string, { bg: string; text: string }> = {
        cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400' },
        emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
        rose: { bg: 'bg-rose-500/10', text: 'text-rose-400' },
    };
    
    const colors = colorClasses[color] || colorClasses.cyan;

    return (
        <Card className="border-slate-800 bg-slate-900/40">
            <CardContent className="p-6">
                <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center mb-4", colors.bg, colors.text)}>
                    <Icon size={24} />
                </div>
                <div className="text-3xl font-black text-white">{value}</div>
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-1">{title}</div>
            </CardContent>
        </Card>
    );
}

function FlowRow({ label, value, color, isTotal }: { label: string; value: number; color: string; isTotal?: boolean }) {
    const colorClasses: Record<string, string> = {
        emerald: 'text-emerald-400',
        cyan: 'text-cyan-400',
        amber: 'text-amber-400',
        rose: 'text-rose-400',
        orange: 'text-orange-400',
        slate: 'text-slate-400',
        white: 'text-white',
    };

    return (
        <div className={cn("flex items-center justify-between py-2", isTotal && "font-black")}>
            <span className={cn("text-sm", isTotal ? "text-white" : "text-slate-400")}>{label}</span>
            <span className={cn("font-bold", colorClasses[color] || 'text-white')}>
                {value.toLocaleString()} FCFA
            </span>
        </div>
    );
}
