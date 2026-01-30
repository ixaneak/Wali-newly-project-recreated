"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Activity,
    ShieldCheck,
    Smartphone,
    TrendingUp,
    FileText,
    Download,
    History,
    ChevronRight,
    ArrowUpRight,
    Search,
    Filter
} from 'lucide-react';
import {
    ResponsiveContainer,
    RadialBarChart,
    RadialBar,
    PolarAngleAxis,
} from 'recharts';
import {
    complianceService,
    ComplianceStatus,
    FinancialSummary,
    DashboardCounts,
    RecentTransaction
} from '@/lib/api-client';
import AdminHeader from '@/components/admin/AdminHeader';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

export default function AdminDashboard() {
    const [transactions, setTransactions] = useState<RecentTransaction[]>([]);
    const [complianceStatus, setComplianceStatus] = useState<ComplianceStatus | null>(null);
    const [financialSummary, setFinancialSummary] = useState<FinancialSummary | null>(null);
    const [counts, setCounts] = useState<DashboardCounts | null>(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    const fetchData = async () => {
        try {
            setLoading(true);
            const [status, summary, recent, stats] = await Promise.all([
                complianceService.getDashboardStatus(),
                complianceService.getFinancialSummary(),
                complianceService.getRecentTransactions(10),
                complianceService.getDashboardCounts()
            ]);
            setComplianceStatus(status);
            setFinancialSummary(summary);
            setTransactions(recent || []);
            setCounts(stats);
        } catch (error) {
            console.error("Dashboard hydration error:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Tableau de Bord Admin"
                description="Console de supervision COSUMAF & Flux Financiers"
                counts={counts || { issues: 0 }}
            />

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Compliance Widget */}
                <div className="xl:col-span-2">
                    <TaxExemptionWidget
                        data={complianceStatus}
                        summary={financialSummary}
                        loading={loading}
                    />
                </div>

                {/* Quick Stats Sidebar */}
                <div className="space-y-8">
                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardHeader className="p-6 pb-2">
                            <CardTitle className="text-sm font-black text-slate-500 uppercase tracking-widest">En Direct</CardTitle>
                        </CardHeader>
                        <CardContent className="p-6 space-y-6">
                            {[
                                { label: 'Artisans Actifs', value: counts?.users || 0, icon: Smartphone, color: 'sky' },
                                { label: 'Claims Ouverts', value: counts?.claims || 0, icon: FileText, color: 'rose' },
                                { label: 'Alertes Système', value: counts?.issues || 0, icon: ShieldCheck, color: 'amber' },
                            ].map((stat, i) => (
                                <div key={i} className="flex items-center justify-between group">
                                    <div className="flex items-center gap-4">
                                        <div className={cn(
                                            "w-10 h-10 rounded-xl flex items-center justify-center transition-colors",
                                            stat.color === 'sky' ? "bg-sky-500/10 text-sky-500" :
                                                stat.color === 'rose' ? "bg-rose-500/10 text-rose-500" : "bg-amber-500/10 text-amber-500"
                                        )}>
                                            <stat.icon size={18} />
                                        </div>
                                        <span className="text-xs font-bold text-slate-400 group-hover:text-white transition-colors">{stat.label}</span>
                                    </div>
                                    <span className="text-xl font-black text-white">{stat.value.toLocaleString()}</span>
                                </div>
                            ))}
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-900/40 overflow-hidden group">
                        <CardHeader className="p-6">
                            <CardTitle className="text-sm font-black text-slate-500 uppercase tracking-widest">Raccourcis</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            {[
                                { label: 'Examiner les Claims', href: '/admin/claims' },
                                { label: 'Vérifier Artisans', href: '/admin/users' },
                                { label: 'Audit Paiements', href: '/admin/payments' },
                            ].map((link, i) => (
                                <Link
                                    key={i}
                                    href={link.href}
                                    className="flex items-center justify-between p-6 border-t border-slate-800/50 hover:bg-slate-800/40 transition-all group/link"
                                >
                                    <span className="text-xs font-black text-white uppercase tracking-tighter">{link.label}</span>
                                    <ChevronRight size={16} className="text-slate-600 group-hover/link:text-cyan-500 transition-colors" />
                                </Link>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Recent Activity Table */}
            <Card className="border-slate-800 bg-slate-900/40">
                <CardHeader className="p-8 border-b border-slate-800 flex flex-row items-center justify-between">
                    <div>
                        <CardTitle className="text-lg uppercase font-black tracking-widest">Flux Récent de Primes</CardTitle>
                        <CardDescription>Dernières transactions enregistrées sur la passerelle</CardDescription>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="pl-8">TRANSACTION ID</TableHead>
                                <TableHead>TYPE</TableHead>
                                <TableHead>MONTANT</TableHead>
                                <TableHead>CONFORMITÉ</TableHead>
                                <TableHead className="text-right pr-8">DATE</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {transactions.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="h-40 text-center text-slate-600 font-bold uppercase tracking-widest text-xs">
                                        AUCUNE TRANSACTION TROUVÉE
                                    </TableCell>
                                </TableRow>
                            ) : transactions.map((tx) => (
                                <TableRow key={tx.id} className="group hover:bg-slate-800/20 transition-colors">
                                    <TableCell className="pl-8 py-5 font-mono text-[10px] text-sky-500/70 font-bold">{tx.id}</TableCell>
                                    <TableCell className="text-xs font-bold text-slate-400 capitalize">{tx.type}</TableCell>
                                    <TableCell className="text-sm font-black text-white">{tx.amount.toLocaleString()} <span className="text-[10px] text-slate-600">FCFA</span></TableCell>
                                    <TableCell>
                                        <Badge variant={tx.status === 'EXEMPT' ? 'success' : 'warning'}>
                                            {tx.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right pr-8 text-[10px] font-bold text-slate-500">
                                        {new Date(tx.date).toLocaleDateString('fr-FR')} {new Date(tx.date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}

// Sub-component for clarity and resilience
function TaxExemptionWidget({ data, summary, loading }: { data: ComplianceStatus | null, summary: FinancialSummary | null, loading: boolean }) {
    const progress = data?.percentage ?? 38.9;
    const radialData = [{ name: 'Progress', value: progress, fill: '#0ea5e9' }];

    return (
        <Card className="h-full border-slate-800 bg-slate-900/60 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-[80px] -mr-16 -mt-16" />

            <CardHeader className="p-8 flex flex-row items-center justify-between relative z-10">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20 shadow-lg shadow-cyan-500/5">
                        <ShieldCheck className="text-cyan-500" size={24} />
                    </div>
                    <div>
                        <CardTitle className="text-xl font-black">COSUMAF COMPLIANCE</CardTitle>
                        <CardDescription>Surveillance de l'exonération (Art. 14.b)</CardDescription>
                    </div>
                </div>
                <Badge variant="success" className="px-4 py-1.5 h-auto text-[10px]">
                    {data?.status ?? 'COMPLIANT'}
                </Badge>
            </CardHeader>

            <CardContent className="p-8 pt-0 grid grid-cols-1 md:grid-cols-2 gap-10 relative z-10">
                <div className="relative flex items-center justify-center bg-slate-800/20 rounded-[2rem] border border-slate-700/30 p-8">
                    <div className="w-full h-[220px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadialBarChart innerRadius="70%" outerRadius="100%" data={radialData} startAngle={90} endAngle={450}>
                                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                                <RadialBar background dataKey="value" cornerRadius={12} />
                            </RadialBarChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pt-8">
                            <span className="text-4xl font-black text-white">{progress}%</span>
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Actif</span>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col justify-between py-2">
                    <div className="space-y-8">
                        <div>
                            <div className="flex justify-between items-end mb-3">
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Revenus Exonérés</p>
                                <span className="text-xs font-bold text-emerald-500 flex items-center gap-1">
                                    <TrendingUp size={12} /> +{summary?.exemptIncome.trend ?? 12.4}%
                                </span>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-3xl font-black text-white">{(summary?.exemptIncome.amount ?? 45000000).toLocaleString()}</span>
                                <span className="text-sm font-bold text-slate-600">FCFA</span>
                            </div>
                            <div className="h-1.5 w-full bg-slate-800 rounded-full mt-4 overflow-hidden">
                                <div className="h-full bg-emerald-500 rounded-full w-[85%]" />
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between items-end mb-3">
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Revenus Taxables</p>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-2xl font-black text-white">{(summary?.taxableIncome.amount ?? 1200000).toLocaleString()}</span>
                                <span className="text-sm font-bold text-slate-600">FCFA</span>
                            </div>
                            <div className="h-1.5 w-full bg-slate-800 rounded-full mt-4 overflow-hidden">
                                <div className="h-full bg-cyan-500 rounded-full w-[15%]" />
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4 mt-10">
                        <Button variant="cyan" className="flex-1 h-12 uppercase font-black text-[10px] tracking-widest gap-2">
                            <Download size={16} /> RAPPORT XML
                        </Button>
                        <Button variant="outline" className="flex-1 h-12 border-slate-700 bg-slate-800/20 uppercase font-black text-[10px] tracking-widest gap-2">
                            <History size={16} /> AUDIT TRAIL
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
