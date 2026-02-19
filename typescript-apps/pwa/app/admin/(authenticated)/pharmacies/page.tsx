"use client";

import React, { useState, useEffect } from 'react';
import { Building2, Search, MapPin, Phone, Mail, CreditCard, Activity, Clock, RefreshCw, Ban, TrendingUp, FileDown, Edit3, RotateCcw, BarChart3, Download, XCircle, CheckCircle, XOctagon, Eye } from 'lucide-react';
import { adminPharmacyService, PharmacyPartner } from '@/lib/api-client';
import AdminHeader from '@/components/admin/AdminHeader';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function AdminPharmaciesPage() {
    const [pharmacies, setPharmacies] = useState<PharmacyPartner[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [monthlyData, setMonthlyData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('ALL');
    const [selectedPharmacy, setSelectedPharmacy] = useState<PharmacyPartner | null>(null);
    const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
    const [showTransactionsModal, setShowTransactionsModal] = useState(false);
    const [transactions, setTransactions] = useState<any[]>([]);
    const [performanceData, setPerformanceData] = useState<any>(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [pharmaciesData, statsData, monthly] = await Promise.all([
                adminPharmacyService.getPharmacies(),
                adminPharmacyService.getPharmacyStats(),
                adminPharmacyService.getMonthlyPerformance()
            ]);
            setPharmacies(pharmaciesData || []);
            setStats(statsData);
            setMonthlyData(monthly);
        } catch (error) {
            toast.error('Erreur de chargement');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const filteredPharmacies = pharmacies.filter(p => {
        const matchesSearch = (p?.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
            (p?.id || '').toLowerCase().includes(searchQuery.toLowerCase());
        const matchesFilter = activeTab === 'ALL' || p?.subscription_status?.toUpperCase() === activeTab;
        return matchesSearch && matchesFilter;
    });

    const getStatusBadge = (status?: string) => {
        const s = status?.toLowerCase();
        if (s === 'active') return <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">ACTIF</Badge>;
        if (s === 'trial') return <Badge className="bg-sky-500/10 text-sky-500 border-sky-500/20">ESSAI</Badge>;
        if (s === 'expired') return <Badge className="bg-rose-500/10 text-rose-500 border-rose-500/20">EXPIRE</Badge>;
        if (s === 'suspended') return <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20">SUSPENDU</Badge>;
        return <Badge>{s || 'INCONNU'}</Badge>;
    };

    const handleExportPharmacies = async (format: 'csv' | 'json') => {
        const data = await adminPharmacyService.exportPharmacies(format);
        const blob = new Blob([data], { type: format === 'csv' ? 'text/csv' : 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pharmacies_${new Date().toISOString().split('T')[0]}.${format}`;
        a.click();
        toast.success('Export telecharge');
    };

    const handleExportTransactions = async () => {
        const data = await adminPharmacyService.exportTransactions();
        const blob = new Blob([data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        toast.success('Export telecharge');
    };

    const handleUpdateSubscription = async (plan: 'basic' | 'professional' | 'enterprise') => {
        if (!selectedPharmacy) return;
        await adminPharmacyService.updateSubscription(selectedPharmacy.id, plan);
        toast.success('Plan mis a jour');
        fetchData();
        setShowSubscriptionModal(false);
    };

    const handleRenewSubscription = async () => {
        if (!selectedPharmacy) return;
        await adminPharmacyService.renewSubscription(selectedPharmacy.id);
        toast.success('Abonnement renouvele');
        fetchData();
        setShowSubscriptionModal(false);
    };

    const handleToggleStatus = async (pharmacy: PharmacyPartner) => {
        const result = await adminPharmacyService.togglePharmacyStatus(pharmacy.id);
        if (result.success) {
            toast.success(`Statut: ${result.newStatus}`);
            fetchData();
        }
    };

    const viewTransactions = async (pharmacy: PharmacyPartner) => {
        setSelectedPharmacy(pharmacy);
        const [verifications, performance] = await Promise.all([
            adminPharmacyService.getPharmacyVerifications({ pharmacyId: pharmacy.id }),
            adminPharmacyService.getPharmacyPerformance(pharmacy.id)
        ]);
        setTransactions(verifications.verifications);
        setPerformanceData(performance);
        setShowTransactionsModal(true);
    };

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader title="Gestion des Pharmacies" description="Suivi des partenaires pharmaceutiques" />

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[ 
                    { label: 'Actives', count: stats?.active_pharmacies || 0, icon: Building2, color: 'emerald' },
                    { label: 'En Essai', count: stats?.trial_pharmacies || 0, icon: Clock, color: 'sky' },
                    { label: 'Verifications Auj', count: stats?.total_verifications_today || 0, icon: Activity, color: 'amber' },
                    { label: 'Montant Traite', count: `${((stats?.total_amount_processed || 0) / 1000000).toFixed(1)}M`, icon: CreditCard, color: 'violet' }
                ].map((stat, i) => (
                    <Card key={i} className="border-slate-800 bg-slate-900/40">
                        <CardContent className="p-6 flex items-center gap-4">
                            <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center", 
                                stat.color === 'emerald' ? "bg-emerald-500/10 text-emerald-500" :
                                stat.color === 'sky' ? "bg-sky-500/10 text-sky-500" :
                                stat.color === 'amber' ? "bg-amber-500/10 text-amber-500" : "bg-violet-500/10 text-violet-500")}>
                                <stat.icon size={22} />
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</p>
                                <p className="text-2xl font-black text-white">{stat.count}</p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Performance Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="border-slate-800 bg-slate-900/40">
                    <CardHeader className="p-6 border-b border-slate-800">
                        <CardTitle className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
                            <TrendingUp size={16} className="text-cyan-500" />
                            Evolution Mensuelle
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={monthlyData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                    <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                                    <YAxis stroke="#64748b" fontSize={12} />
                                    <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                                    <Line type="monotone" dataKey="verifications" stroke="#0ea5e9" strokeWidth={2} dot={{ fill: '#0ea5e9' }} />
                                    <Line type="monotone" dataKey="pharmacies" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-900/40">
                    <CardHeader className="p-6 border-b border-slate-800">
                        <CardTitle className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
                            <CreditCard size={16} className="text-emerald-500" />
                            Volume Transactions (M FCFA)
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6">
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={monthlyData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                    <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                                    <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `${(v/1000000).toFixed(0)}M`} />
                                    <RechartsTooltip formatter={(v) => [`${((v as number)/1000000).toFixed(1)}M FCFA`, 'Montant']} />
                                    <Bar dataKey="amount" fill="#10b981" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Quota API Utilise</p>
                                <p className="text-xl font-black text-white mt-1">
                                    {stats?.api_quota_used || 0} / {stats?.api_quota_total || 0}
                                </p>
                            </div>
                            <div className="w-16 h-16 rounded-full border-4 border-slate-800 flex items-center justify-center">
                                <span className="text-sm font-bold text-sky-500">
                                    {Math.round(((stats?.api_quota_used || 0) / (stats?.api_quota_total || 1)) * 100)}%
                                </span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6 flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 text-rose-500 flex items-center justify-center">
                            <XOctagon size={22} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Abonnements Expires</p>
                            <p className="text-2xl font-black text-white">{stats?.expired_pharmacies || 0}</p>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6 flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                            <CreditCard size={22} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">MRR</p>
                            <p className="text-2xl font-black text-white">{(stats?.monthly_recurring_revenue || 0).toLocaleString()} FCFA</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Pharmacies Table */}
            <Card className="border-slate-800 bg-slate-900/40">
                <CardContent className="p-0">
                    <div className="p-8 border-b border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                        <Tabs defaultValue="ALL" onValueChange={setActiveTab}>
                            <TabsList className="bg-slate-950/50 border border-slate-800/50 p-1 h-12">
                                {['ALL', 'ACTIVE', 'TRIAL', 'EXPIRED', 'SUSPENDED'].map(tab => (
                                    <TabsTrigger key={tab} value={tab} className="px-4 text-[9px] font-black tracking-tighter uppercase data-[state=active]:bg-cyan-500 data-[state=active]:text-white">
                                        {tab === 'ALL' ? 'TOUTES' : tab}
                                    </TabsTrigger>
                                ))}
                            </TabsList>
                        </Tabs>

                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                                <input className="bg-slate-950/50 border border-slate-800 rounded-xl py-2 pl-9 pr-4 text-xs font-bold text-white w-64" 
                                    placeholder="RECHERCHER PHARMACIE..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
                            </div>
                            <Button variant="outline" size="icon" onClick={() => fetchData()} className="border-slate-800 bg-slate-950/50">
                                <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                            </Button>
                        </div>
                    </div>

                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="pl-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Pharmacie</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Contact</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Ville</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Plan</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Statut</TableHead>
                                <TableHead className="text-right pr-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading && filteredPharmacies.length === 0 ? (
                                [...Array(5)].map((_, i) => (
                                    <TableRow key={i}>
                                        <TableCell colSpan={6}>
                                            <div className="h-12 w-full bg-slate-800/10 animate-pulse rounded-lg mt-1 mx-4" />
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : filteredPharmacies.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-60 text-center text-slate-600 font-bold uppercase tracking-[0.2em] text-[10px]">
                                        AUCUNE PHARMACIE TROUVEE
                                    </TableCell>
                                </TableRow>
                            ) : filteredPharmacies.map((pharmacy) => (
                                <TableRow key={pharmacy?.id} className="hover:bg-slate-800/20 transition-colors">
                                    <TableCell className="pl-8 py-5">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                                                <Building2 size={20} />
                                            </div>
                                            <div>
                                                <span className="text-xs font-black text-white">{pharmacy?.name}</span>
                                                <span className="text-[10px] text-cyan-500/70 block font-mono font-bold uppercase">{pharmacy?.id}</span>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="space-y-1">
                                            <div className="text-xs text-slate-400">{pharmacy?.contact_name}</div>
                                            <div className="text-[10px] text-slate-500 flex items-center gap-1"><Phone size={10} /> {pharmacy?.phone}</div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="text-xs text-white">{pharmacy?.city}</div>
                                    </TableCell>
                                    <TableCell>
                                        <span className={cn("text-[10px] uppercase font-bold",
                                            pharmacy?.subscription_plan === 'enterprise' ? 'text-violet-400' :
                                            pharmacy?.subscription_plan === 'professional' ? 'text-cyan-400' : 'text-slate-400'
                                        )}>{pharmacy?.subscription_plan}</span>
                                    </TableCell>
                                    <TableCell>{getStatusBadge(pharmacy?.subscription_status)}</TableCell>
                                    <TableCell className="text-right pr-8">
                                        <div className="flex items-center justify-end gap-2">
                                            <Button variant="ghost" size="sm" onClick={() => viewTransactions(pharmacy)}
                                                className="h-8 px-3 text-[9px] font-black uppercase tracking-widest border border-transparent hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-cyan-500">
                                                <BarChart3 size={14} className="mr-1" /> Stats
                                            </Button>
                                            <Button variant="ghost" size="sm" onClick={() => { setSelectedPharmacy(pharmacy); setShowSubscriptionModal(true); }}
                                                className="h-8 px-3 text-[9px] font-black uppercase tracking-widest border border-transparent hover:border-emerald-500/30 hover:bg-emerald-500/10 hover:text-emerald-500">
                                                <Edit3 size={14} className="mr-1" /> Gerer
                                            </Button>
                                            <Button variant="ghost" size="sm" onClick={() => handleToggleStatus(pharmacy)}
                                                className="h-8 w-8 p-0 text-[9px] font-black uppercase tracking-widest border border-transparent hover:border-rose-500/30 hover:bg-rose-500/10 hover:text-rose-500">
                                                <Ban size={14} />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Floating Actions */}
            <div className="fixed bottom-10 right-10 flex gap-4">
                <Button variant="outline" className="bg-slate-950/80 backdrop-blur-xl border-slate-800 h-14 px-8" onClick={() => handleExportPharmacies('csv')}>
                    <FileDown size={16} className="mr-2" /> Export CSV
                </Button>
                <Button variant="outline" className="bg-slate-950/80 backdrop-blur-xl border-slate-800 h-14 px-8" onClick={handleExportTransactions}>
                    <Download size={16} className="mr-2" /> Transactions
                </Button>
                <Button className="bg-emerald-500 hover:bg-emerald-600 h-14 px-10 font-black uppercase tracking-widest text-[10px]">
                    <Building2 size={16} className="mr-2" /> Ajouter Pharmacie
                </Button>
            </div>

            {/* Subscription Management Modal */}
            {showSubscriptionModal && selectedPharmacy && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg">
                        <div className="p-6 border-b border-slate-800">
                            <h2 className="text-xl font-black text-white">Gestion Abonnement</h2>
                            <p className="text-slate-400 text-sm mt-1">{selectedPharmacy.name}</p>
                        </div>
                        <div className="p-6 space-y-6">
                            <div>
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Changer de Plan</p>
                                <div className="grid grid-cols-3 gap-3">
                                    {[
                                        { plan: 'basic', price: 30000, quota: 500 },
                                        { plan: 'professional', price: 50000, quota: 1000 },
                                        { plan: 'enterprise', price: 100000, quota: 2500 }
                                    ].map((p) => (
                                        <button key={p.plan} onClick={() => handleUpdateSubscription(p.plan as any)}
                                            className={cn("p-4 rounded-xl border transition-all",
                                                selectedPharmacy.subscription_plan === p.plan
                                                    ? "border-cyan-500 bg-cyan-500/10"
                                                    : "border-slate-700 hover:border-slate-600"
                                            )}>
                                            <p className="text-sm font-bold text-white uppercase">{p.plan}</p>
                                            <p className="text-lg font-black text-cyan-400 mt-1">{p.price.toLocaleString()}</p>
                                            <p className="text-[10px] text-slate-500">FCFA/mois</p>
                                            <p className="text-[10px] text-slate-400 mt-2">{p.quota} requetes</p>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="pt-4 border-t border-slate-800">
                                <Button className="w-full bg-emerald-500 hover:bg-emerald-600" onClick={handleRenewSubscription}
                                    disabled={selectedPharmacy.subscription_status === 'active'}>
                                    <RotateCcw size={16} className="mr-2" /> Renouveler l&apos;abonnement
                                </Button>
                            </div>
                        </div>
                        <div className="p-6 border-t border-slate-800 flex justify-end">
                            <Button variant="outline" onClick={() => setShowSubscriptionModal(false)}>Fermer</Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Transactions Modal */}
            {showTransactionsModal && selectedPharmacy && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-auto">
                        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-black text-white">Transactions & Performance</h2>
                                <p className="text-slate-400 text-sm mt-1">{selectedPharmacy.name}</p>
                            </div>
                            <button onClick={() => setShowTransactionsModal(false)} className="text-slate-400 hover:text-white">
                                <XCircle size={24} />
                            </button>
                        </div>
                        <div className="p-6 space-y-6">
                            {/* Performance Stats */}
                            {performanceData && (
                                <div className="grid grid-cols-4 gap-4">
                                    <div className="bg-slate-950/50 rounded-xl p-4 text-center border border-slate-800">
                                        <p className="text-[10px] text-slate-500 uppercase">Total Transactions</p>
                                        <p className="text-2xl font-black text-white">{performanceData.total_verifications}</p>
                                    </div>
                                    <div className="bg-slate-950/50 rounded-xl p-4 text-center border border-slate-800">
                                        <p className="text-[10px] text-slate-500 uppercase">Montant Total</p>
                                        <p className="text-xl font-black text-emerald-400">{(performanceData.total_amount / 1000000).toFixed(1)}M</p>
                                    </div>
                                    <div className="bg-slate-950/50 rounded-xl p-4 text-center border border-slate-800">
                                        <p className="text-[10px] text-slate-500 uppercase">Wali Couvre</p>
                                        <p className="text-xl font-black text-sky-400">{(performanceData.total_wali_covered / 1000000).toFixed(1)}M</p>
                                    </div>
                                    <div className="bg-slate-950/50 rounded-xl p-4 text-center border border-slate-800">
                                        <p className="text-[10px] text-slate-500 uppercase">Moyenne</p>
                                        <p className="text-xl font-black text-white">{Math.round(performanceData.average_claim_amount).toLocaleString()}</p>
                                    </div>
                                </div>
                            )}
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="text-[10px] text-slate-500">ID</TableHead>
                                        <TableHead className="text-[10px] text-slate-500">Date</TableHead>
                                        <TableHead className="text-[10px] text-slate-500">Patient</TableHead>
                                        <TableHead className="text-[10px] text-slate-500">Montant</TableHead>
                                        <TableHead className="text-[10px] text-slate-500">Statut</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {transactions.map((tx) => (
                                        <TableRow key={tx.id}>
                                            <TableCell className="text-xs text-cyan-500/70 font-mono">{tx.id}</TableCell>
                                            <TableCell className="text-xs text-slate-400">{new Date(tx.created_at).toLocaleDateString('fr-FR')}</TableCell>
                                            <TableCell className="text-xs text-white">{tx.patient_name}</TableCell>
                                            <TableCell className="text-xs text-white">{tx.total_amount.toLocaleString()} FCFA</TableCell>
                                            <TableCell>{getStatusBadge(tx.status)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
