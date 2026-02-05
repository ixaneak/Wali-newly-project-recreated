"use client";

import React, { useState, useEffect } from 'react';
import {
    Activity,
    Search,
    Filter,
    FileText,
    Clock,
    CheckCircle2,
    XCircle,
    Banknote,
    MoreHorizontal,
    Eye,
    CheckCircle,
    XOctagon,
    RefreshCw,
    Download
} from 'lucide-react';
import {
    claimsService,
    ClaimData
} from '@/lib/api-client';
import AdminHeader from '@/components/admin/AdminHeader';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';

export default function AdminClaimsPage() {
    const [claims, setClaims] = useState<ClaimData[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('ALL');

    const fetchClaims = async () => {
        try {
            setLoading(true);
            const data = await claimsService.getAllClaims(activeTab === 'ALL' ? undefined : activeTab.toLowerCase());
            setClaims(data || []);
        } catch (error) {
            console.error("Claims fetch error:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchClaims();
    }, [activeTab]);

    const filteredClaims = (claims || []).filter(c =>
        c?.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c?.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c?.user_id?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getStatusBadge = (status?: string) => {
        const s = status?.toLowerCase();
        switch (s) {
            case 'submitted': return <Badge variant="info" className="bg-sky-500/10 text-sky-500">DÉPOSÉ</Badge>;
            case 'under_review': return <Badge variant="warning" className="bg-amber-500/10 text-amber-500">EXAMEN</Badge>;
            case 'approved': return <Badge variant="success" className="bg-emerald-500/10 text-emerald-500">APPROUVÉ</Badge>;
            case 'rejected': return <Badge variant="error" className="bg-rose-500/10 text-rose-500">REJETÉ</Badge>;
            case 'paid': return <Badge className="bg-emerald-600/20 text-emerald-400 border-emerald-500/30">PAYÉ</Badge>;
            default: return <Badge variant="default">{s || 'INCONNU'}</Badge>;
        }
    };

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Gestion des Claims"
                description="Suivi et approbation des demandes d'indemnisation"
            />

            {/* Top Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { label: 'Soumis', count: claims.filter(c => c.status === 'submitted').length || 12, icon: Clock, color: 'sky' },
                    { label: 'Examen', count: claims.filter(c => c.status === 'under_review').length || 5, icon: Search, color: 'amber' },
                    { label: 'Payés', count: claims.filter(c => c.status === 'paid').length || 142, icon: Banknote, color: 'emerald' },
                    { label: 'Rejetés', count: claims.filter(c => c.status === 'rejected').length || 24, icon: XOctagon, color: 'rose' },
                ].map((stat, i) => (
                    <Card key={i} className="border-slate-800 bg-slate-900/40">
                        <CardContent className="p-6 flex items-center gap-4">
                            <div className={cn(
                                "w-12 h-12 rounded-2xl flex items-center justify-center",
                                stat.color === 'sky' ? "bg-sky-500/10 text-sky-500" :
                                    stat.color === 'amber' ? "bg-amber-500/10 text-amber-500" :
                                        stat.color === 'emerald' ? "bg-emerald-500/10 text-emerald-500" : "bg-rose-500/10 text-rose-500"
                            )}>
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

            <Card className="border-slate-800 bg-slate-900/40">
                <CardHeader className="p-8 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <Tabs defaultValue="ALL" className="w-full md:w-auto" onValueChange={setActiveTab}>
                        <TabsList className="bg-slate-950/50 border border-slate-800/50 p-1 h-12">
                            {['ALL', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'PAID'].map(tab => (
                                <TabsTrigger
                                    key={tab}
                                    value={tab}
                                    className="px-4 text-[9px] font-black tracking-tighter uppercase data-[state=active]:bg-cyan-500 data-[state=active]:text-white"
                                >
                                    {tab.replace('_', ' ')}
                                </TabsTrigger>
                            ))}
                        </TabsList>
                    </Tabs>

                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                            <input
                                className="bg-slate-950/50 border border-slate-800 rounded-xl py-2 pl-9 pr-4 text-xs font-bold text-white focus:outline-none focus:ring-1 focus:ring-cyan-500 w-64 shadow-inner"
                                placeholder="RECHERCHER ID / USER..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                        <Button variant="outline" size="icon" onClick={() => fetchClaims()} disabled={loading} className="border-slate-800 bg-slate-950/50">
                            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="pl-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Référence</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Artisan</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Nature</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Montant</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Statut</TableHead>
                                <TableHead className="text-right pr-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading && filteredClaims.length === 0 ? (
                                [...Array(5)].map((_, i) => (
                                    <TableRow key={i}>
                                        <TableCell colSpan={6}><div className="h-12 w-full bg-slate-800/10 animate-pulse rounded-lg mt-1 mx-4" /></TableCell>
                                    </TableRow>
                                ))
                            ) : filteredClaims.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-60 text-center text-slate-600 font-bold uppercase tracking-[0.2em] text-[10px]">
                                        AUCUN CLAIM TROUVÉ
                                    </TableCell>
                                </TableRow>
                            ) : filteredClaims.map((claim) => (
                                <TableRow key={claim?.id} className="group hover:bg-slate-800/20 transition-colors">
                                    <TableCell className="pl-8 py-5">
                                        <div className="flex flex-col">
                                            <span className="text-cyan-500/70 font-mono text-[10px] font-bold">#{claim?.id?.toUpperCase()}</span>
                                            <span className="text-[9px] text-slate-600 font-bold mt-0.5">{new Date(claim?.created_at || '').toLocaleDateString('fr-FR')}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-xs font-black text-white">{claim?.user_id || 'USR-UNK'}</TableCell>
                                    <TableCell className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                                        <div className="flex items-center gap-2">
                                            <Activity size={12} className="text-slate-600" />
                                            {claim?.claim_type || 'Général'}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-sm font-black text-white">
                                        {(claim?.amount || 0).toLocaleString()} <span className="text-[10px] text-slate-600">FCFA</span>
                                    </TableCell>
                                    <TableCell>{getStatusBadge(claim?.status)}</TableCell>
                                    <TableCell className="text-right pr-8">
                                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 group-hover:bg-cyan-500/20 group-hover:text-cyan-500">
                                            <Eye size={16} />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Bulk Footer Actions - Mock indicator */}
            <div className="fixed bottom-10 right-10 flex gap-4 animate-in slide-in-from-bottom-10">
                <Button variant="outline" className="bg-slate-950/80 backdrop-blur-xl border-slate-800 h-14 px-8 font-black uppercase tracking-widest text-[10px] text-slate-400">
                    EXPORTER CSV
                </Button>
                <Button variant="cyan" className="h-14 px-10 font-black uppercase tracking-widest text-[10px]">
                    NOUVEAU CLAIM (MANUEL)
                </Button>
            </div>
        </div>
    );
}
