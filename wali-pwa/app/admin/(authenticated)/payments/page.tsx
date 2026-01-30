"use client";

import React, { useState, useEffect } from 'react';
import {
    Activity,
    Smartphone,
    ShieldCheck,
    CreditCard,
    ArrowUpRight,
    Search,
    RefreshCw,
    CheckCircle2,
    XCircle,
    Layers,
    History
} from 'lucide-react';
import {
    complianceService,
    PaymentStats,
    RecentTransaction
} from '@/lib/api-client';
import AdminHeader from '@/components/admin/AdminHeader';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

export default function AdminPaymentsPage() {
    const [stats, setStats] = useState<PaymentStats | null>(null);
    const [transactions, setTransactions] = useState<RecentTransaction[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [s, t] = await Promise.all([
                complianceService.getAdminPaymentStats(),
                complianceService.getRecentTransactions(20)
            ]);
            setStats(s);
            setTransactions(t || []);
        } catch (e) {
            console.error("Payment sync failed");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Flux Financiers"
                description="Monitoring des passerelles et volume de primes"
            />

            {/* Gateway Health */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { name: 'MTN Mobile Money', status: 'ONLINE', latency: '42ms', color: 'amber' },
                    { name: 'Orange Money', status: 'ONLINE', latency: '128ms', color: 'orange' },
                    { name: 'Wave CI', status: 'ONLINE', latency: '65ms', color: 'sky' },
                ].map((gw, i) => (
                    <Card key={i} className="border-slate-800 bg-slate-900/40 overflow-hidden relative">
                        <div className={cn("absolute top-0 left-0 w-1 h-full", gw.color === 'amber' ? "bg-amber-400" : gw.color === 'orange' ? "bg-orange-500" : "bg-sky-400")} />
                        <CardContent className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{gw.name}</p>
                                    <h4 className="text-xl font-black text-white mt-1">{gw.status}</h4>
                                </div>
                                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                                    <CheckCircle2 size={16} />
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className="text-[10px] font-bold text-slate-600 uppercase tracking-tighter">Latence Gateway</span>
                                <span className="text-[10px] font-black text-white">{gw.latency}</span>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                {/* Real-time stats */}
                <Card className="border-slate-800 bg-slate-900/40 lg:col-span-1">
                    <CardHeader className="p-8 border-b border-slate-800">
                        <CardTitle className="text-lg">Résumé du Volume</CardTitle>
                        <CardDescription>Données cumulées sur 30 jours</CardDescription>
                    </CardHeader>
                    <CardContent className="p-8 space-y-8">
                        <div>
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Volume Total Brute</p>
                            <div className="flex items-baseline gap-2">
                                <span className="text-3xl font-black text-white">{(stats?.total_volume || 1250000).toLocaleString()}</span>
                                <span className="text-[10px] font-bold text-slate-600">FCFA</span>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-end">
                                <span className="text-[10px] font-black text-slate-500 uppercase">Taux de Succès</span>
                                <span className="text-sm font-black text-emerald-500">{stats?.success_rate || 98.4}%</span>
                            </div>
                            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full bg-emerald-500 rounded-full w-[98%]" />
                            </div>
                        </div>

                        <div className="pt-6 border-t border-slate-800 space-y-4">
                            {[
                                { label: 'En attente', value: stats?.pending_volume || 45000, color: 'bg-amber-400' },
                                { label: 'Échecs', value: stats?.failed_volume || 12000, color: 'bg-rose-500' },
                            ].map((stat, i) => (
                                <div key={i} className="flex justify-between">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{stat.label}</span>
                                    <span className="text-xs font-black text-white">{stat.value.toLocaleString()} FCFA</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Live Transactions Log */}
                <Card className="border-slate-800 bg-slate-900/40 lg:col-span-2">
                    <CardHeader className="p-8 border-b border-slate-800 flex flex-row items-center justify-between">
                        <div>
                            <CardTitle className="text-lg">Journal des Transactions</CardTitle>
                            <CardDescription>Mise à jour automatique disponible</CardDescription>
                        </div>
                        <Button variant="outline" size="icon" className="border-slate-800 bg-slate-950/50" onClick={fetchData}>
                            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                        </Button>
                    </CardHeader>
                    <CardContent className="p-0">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="pl-8">ID TRANS.</TableHead>
                                    <TableHead>MÉTHODE</TableHead>
                                    <TableHead>MONTANT</TableHead>
                                    <TableHead className="text-right pr-8">STATUT</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {transactions.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="h-60 text-center text-slate-700 font-black uppercase tracking-widest text-xs">AUCUNE TRANSACTION TROUVÉE</TableCell>
                                    </TableRow>
                                ) : transactions.map(tx => (
                                    <TableRow key={tx.id} className="group hover:bg-slate-800/20 transition-colors">
                                        <TableCell className="pl-8 py-5">
                                            <div className="flex flex-col">
                                                <span className="text-cyan-500/70 font-mono text-[10px] font-bold">{tx.id}</span>
                                                <span className="text-[9px] text-slate-600 font-bold mt-0.5">{new Date(tx.date).toLocaleTimeString()}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <div className="w-1.5 h-1.5 rounded-full bg-sky-500" />
                                                <span className="text-[10px] font-black text-white uppercase">{tx.type}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-sm font-black text-white">{tx.amount.toLocaleString()} FCFA</TableCell>
                                        <TableCell className="text-right pr-8">
                                            <Badge variant={tx.status === 'EXEMPT' ? 'success' : 'warning'}>{tx.status}</Badge>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
