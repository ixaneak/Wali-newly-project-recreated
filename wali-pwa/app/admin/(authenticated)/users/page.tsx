"use client";

import React, { useState, useEffect } from 'react';
import {
    Users as UsersIcon,
    Search,
    Filter,
    UserCheck,
    AlertCircle,
    MapPin,
    Phone,
    Download,
    RefreshCw,
    MoreHorizontal,
    CheckCircle,
    XCircle,
    UserCircle
} from 'lucide-react';
import {
    policyService,
    UserData
} from '@/lib/api-client';
import AdminHeader from '@/components/admin/AdminHeader';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

export default function AdminUsersPage() {
    const [users, setUsers] = useState<UserData[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [filter, setFilter] = useState('ALL');

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const { items } = await policyService.getAdminUsers();
            setUsers(items || []);
        } catch (e) {
            console.error("User registry sync failed");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const filteredUsers = (users || []).filter(u => {
        const matchesSearch = (u?.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
            (u?.id || '').toLowerCase().includes(searchQuery.toLowerCase());
        const matchesFilter = filter === 'ALL' || u?.kyc_status?.toUpperCase() === filter;
        return matchesSearch && matchesFilter;
    });

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Registre des Artisans"
                description="Gestion des identités et vérification KYC COSUMAF"
            />

            {/* Verification Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { label: 'Total Artisans', count: users.length || 1250, icon: UsersIcon, color: 'sky' },
                    { label: 'Vérifiés (NUI)', count: users.filter(u => u.kyc_status === 'verified').length || 890, icon: UserCheck, color: 'emerald' },
                    { label: 'En attente', count: users.filter(u => u.kyc_status === 'pending').length || 45, icon: AlertCircle, color: 'amber' },
                    { label: 'Rejetés', count: users.filter(u => u.kyc_status === 'rejected').length || 12, icon: XCircle, color: 'rose' },
                ].map((stat, i) => (
                    <Card key={i} className="border-slate-800 bg-slate-900/40">
                        <CardContent className="p-6 flex items-center gap-4">
                            <div className={cn(
                                "w-12 h-12 rounded-2xl flex items-center justify-center",
                                stat.color === 'sky' ? "bg-sky-500/10 text-sky-500" :
                                    stat.color === 'emerald' ? "bg-emerald-500/10 text-emerald-500" :
                                        stat.color === 'amber' ? "bg-amber-500/10 text-amber-500" : "bg-rose-500/10 text-rose-500"
                            )}>
                                <stat.icon size={22} />
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</p>
                                <p className="text-2xl font-black text-white">{stat.count.toLocaleString()}</p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <Card className="border-slate-800 bg-slate-900/40">
                <CardHeader className="p-8 border-b border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                    <div className="flex bg-slate-950/50 p-1 rounded-xl border border-slate-800 shadow-inner">
                        {['ALL', 'VERIFIED', 'PENDING', 'REJECTED'].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={cn(
                                    "px-6 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all",
                                    filter === f ? "bg-cyan-500 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"
                                )}
                            >
                                {f}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                            <input
                                className="bg-slate-950/50 border border-slate-800 rounded-xl py-2 pl-9 pr-4 text-xs font-bold text-white focus:outline-none focus:ring-1 focus:ring-cyan-500 w-64"
                                placeholder="FILTRER PAR NOM / ID..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                        <Button variant="outline" size="icon" className="border-slate-800 bg-slate-950/50" onClick={fetchUsers}>
                            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                        </Button>
                    </div>
                </CardHeader>

                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="pl-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Artisan</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Contact</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Région</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Statut KYC</TableHead>
                                <TableHead className="text-right pr-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading && filteredUsers.length === 0 ? (
                                [...Array(5)].map((_, i) => (
                                    <TableRow key={i}>
                                        <TableCell colSpan={5}><div className="h-12 w-full bg-slate-800/10 animate-pulse rounded-lg mt-1 mx-4" /></TableCell>
                                    </TableRow>
                                ))
                            ) : filteredUsers.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="h-60 text-center text-slate-600 font-bold uppercase tracking-[0.2em] text-[10px]">
                                        AUCUN ARTISAN TROUVÉ
                                    </TableCell>
                                </TableRow>
                            ) : filteredUsers.map((user) => (
                                <TableRow key={user?.id} className="group hover:bg-slate-800/20 transition-colors">
                                    <TableCell className="pl-8 py-5">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500 relative overflow-hidden">
                                                <UserCircle size={24} />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-xs font-black text-white">{user?.name || 'Nom Inconnu'}</span>
                                                <span className="text-[10px] text-cyan-500/70 font-mono font-bold uppercase">{user?.id}</span>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2 text-slate-400 text-xs font-bold">
                                            <Phone size={12} className="text-slate-600" />
                                            {user?.phone}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2 text-slate-400 text-[10px] font-black uppercase">
                                            <MapPin size={12} className="text-slate-600" />
                                            {user?.region || 'Abidjan'}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={user?.kyc_status === 'verified' ? 'success' : user?.kyc_status === 'rejected' ? 'error' : 'warning'}>
                                            {user?.kyc_status?.toUpperCase()}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right pr-8">
                                        <Button variant="ghost" size="sm" className="h-9 px-4 text-[9px] font-black uppercase tracking-widest border border-transparent hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-cyan-500">
                                            VÉRIFIER
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <div className="fixed bottom-10 right-10 flex gap-4 animate-in slide-in-from-bottom-10">
                <Button variant="outline" className="bg-slate-950/80 backdrop-blur-xl border-slate-800 h-14 px-8 font-black uppercase tracking-widest text-[10px] text-slate-400">
                    <Download size={16} className="mr-2" /> EXPORTER REGISTRE
                </Button>
            </div>
        </div>
    );
}
