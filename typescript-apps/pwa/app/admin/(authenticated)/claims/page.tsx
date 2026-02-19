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
    Download,
    AlertCircle
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

// Mock claims for development fallback
const MOCK_CLAIMS: ClaimData[] = [
    { 
        id: "CLM-2024-001", 
        user_id: "USR-001", 
        policy_id: "POL-001",
        claim_type: "Accident de travail", 
        amount: 150000, 
        description: "Blessure au bras lors du travail",
        status: "submitted", 
        incident_date: "2024-03-15",
        photos: [],
        created_at: "2024-03-16T10:30:00Z",
        updated_at: "2024-03-16T10:30:00Z"
    },
    { 
        id: "CLM-2024-002", 
        user_id: "USR-002", 
        policy_id: "POL-002",
        claim_type: "Vol d'outil", 
        amount: 75000, 
        description: "Vol de matériel sur le chantier",
        status: "under_review", 
        incident_date: "2024-03-10",
        photos: [],
        created_at: "2024-03-12T14:15:00Z",
        updated_at: "2024-03-14T09:00:00Z"
    },
    { 
        id: "CLM-2024-003", 
        user_id: "USR-003", 
        policy_id: "POL-003",
        claim_type: "Maladie", 
        amount: 50000, 
        description: "Hospitalisation pour paludisme",
        status: "approved", 
        incident_date: "2024-02-28",
        photos: [],
        created_at: "2024-03-01T08:00:00Z",
        updated_at: "2024-03-05T16:30:00Z",
        review_notes: "Validé après vérification des documents",
        reviewed_at: "2024-03-05T16:30:00Z"
    },
    { 
        id: "CLM-2024-004", 
        user_id: "USR-001", 
        policy_id: "POL-001",
        claim_type: "Dommage matériel", 
        amount: 200000, 
        description: "Échafaudage endommagé",
        status: "paid", 
        incident_date: "2024-02-15",
        photos: [],
        created_at: "2024-02-16T11:00:00Z",
        updated_at: "2024-02-20T14:00:00Z",
        review_notes: "Paiement effectué",
        reviewed_at: "2024-02-20T14:00:00Z"
    },
    { 
        id: "CLM-2024-005", 
        user_id: "USR-004", 
        policy_id: "POL-004",
        claim_type: "Accident de travail", 
        amount: 300000, 
        description: "Chute depuis échafaudage",
        status: "rejected", 
        incident_date: "2024-01-20",
        photos: [],
        created_at: "2024-01-21T09:30:00Z",
        updated_at: "2024-01-25T10:00:00Z",
        review_notes: "Non couvert - police suspendue",
        reviewed_at: "2024-01-25T10:00:00Z"
    },
    { 
        id: "CLM-2024-006", 
        user_id: "USR-005", 
        policy_id: "POL-005",
        claim_type: "Responsabilité civile", 
        amount: 450000, 
        description: "Dommage causé à un tiers",
        status: "submitted", 
        incident_date: "2024-03-18",
        photos: [],
        created_at: "2024-03-19T16:45:00Z",
        updated_at: "2024-03-19T16:45:00Z"
    },
];

export default function AdminClaimsPage() {
    const [claims, setClaims] = useState<ClaimData[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('ALL');
    const [usingMockData, setUsingMockData] = useState(false);

    const fetchClaims = async () => {
        try {
            setLoading(true);
            setUsingMockData(false);
            const status = activeTab === 'ALL' ? undefined : activeTab.toLowerCase();
            const data = await claimsService.getAllClaims(status);
            
            if (data && data.length > 0) {
                setClaims(data);
                if (usingMockData) {
                    toast.success("Données en temps réel chargées");
                }
            } else {
                console.log("No claims from API, using mock data");
                setClaims(MOCK_CLAIMS);
                setUsingMockData(true);
            }
        } catch (error) {
            console.error("Claims fetch error:", error);
            toast.error("Erreur de connexion au serveur. Données de démonstration affichées.");
            setClaims(MOCK_CLAIMS);
            setUsingMockData(true);
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
        c?.user_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c?.claim_type?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getStatusBadge = (status?: string) => {
        const s = status?.toLowerCase();
        switch (s) {
            case 'submitted': return <Badge variant="info" className="bg-sky-500/10 text-sky-500 border-sky-500/20">DÉPOSÉ</Badge>;
            case 'under_review': return <Badge variant="warning" className="bg-amber-500/10 text-amber-500 border-amber-500/20">EXAMEN</Badge>;
            case 'approved': return <Badge variant="success" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">APPROUVÉ</Badge>;
            case 'rejected': return <Badge variant="error" className="bg-rose-500/10 text-rose-500 border-rose-500/20">REJETÉ</Badge>;
            case 'paid': return <Badge className="bg-emerald-600/20 text-emerald-400 border-emerald-500/30">PAYÉ</Badge>;
            default: return <Badge variant="default">{s || 'INCONNU'}</Badge>;
        }
    };

    const getStatusLabel = (status?: string) => {
        const s = status?.toLowerCase();
        switch (s) {
            case 'submitted': return 'Déposé';
            case 'under_review': return 'En examen';
            case 'approved': return 'Approuvé';
            case 'rejected': return 'Rejeté';
            case 'paid': return 'Payé';
            default: return status || 'Inconnu';
        }
    };

    const exportClaims = () => {
        const csv = [
            ['ID', 'Artisan ID', 'Type', 'Montant (FCFA)', 'Statut', 'Date incident', 'Date création'].join(','),
            ...filteredClaims.map(c => [
                c.id,
                c.user_id,
                `"${c.claim_type || ''}"`,
                c.amount,
                c.status,
                new Date(c.incident_date || '').toLocaleDateString('fr-FR'),
                new Date(c.created_at).toLocaleDateString('fr-FR')
            ].join(','))
        ].join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `claims-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        
        toast.success(`${filteredClaims.length} claims exportés`);
    };

    const stats = [
        { label: 'Soumis', count: claims.filter(c => c.status === 'submitted').length, icon: Clock, color: 'sky' as const },
        { label: 'Examen', count: claims.filter(c => c.status === 'under_review').length, icon: Search, color: 'amber' as const },
        { label: 'Payés', count: claims.filter(c => c.status === 'paid').length, icon: Banknote, color: 'emerald' as const },
        { label: 'Rejetés', count: claims.filter(c => c.status === 'rejected').length, icon: XOctagon, color: 'rose' as const },
    ];

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Gestion des Claims"
                description="Suivi et approbation des demandes d'indemnisation"
            />

            {/* Mock Data Warning */}
            {usingMockData && (
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-500" />
                    <p className="text-amber-400 text-sm">
                        Mode démonstration : Données simulées affichées. La connexion au serveur a échoué.
                    </p>
                </div>
            )}

            {/* Top Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {stats.map((stat, i) => (
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
                                    className="px-3 text-[9px] font-black tracking-tighter uppercase data-[state=active]:bg-cyan-500 data-[state=active]:text-white"
                                >
                                    {tab === 'ALL' ? 'TOUS' : 
                                     tab === 'SUBMITTED' ? 'DÉPOSÉS' :
                                     tab === 'UNDER_REVIEW' ? 'EXAMEN' :
                                     tab === 'APPROVED' ? 'APPROUVÉS' :
                                     tab === 'REJECTED' ? 'REJETÉS' : 'PAYÉS'}
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

            {/* Bulk Footer Actions */}
            <div className="fixed bottom-10 right-10 flex gap-4 animate-in slide-in-from-bottom-10">
                <Button 
                    variant="outline" 
                    className="bg-slate-950/80 backdrop-blur-xl border-slate-800 h-14 px-8 font-black uppercase tracking-widest text-[10px] text-slate-400"
                    onClick={exportClaims}
                >
                    <Download size={16} className="mr-2" />
                    EXPORTER CSV
                </Button>
            </div>
        </div>
    );
}
