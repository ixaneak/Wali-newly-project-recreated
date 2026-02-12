"use client";

import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    Download,
    BarChart,
    PieChart as PieChartIcon,
    Calendar,
    ChevronDown,
    Activity,
    Layers,
    Map
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart as ReBarChart,
    Bar,
    PieChart,
    Pie,
    Cell
} from 'recharts';
import {
    complianceService,
    AnalyticsData
} from '@/lib/api-client';
import AdminHeader from '@/components/admin/AdminHeader';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const COLORS = ['#0ea5e9', '#6366f1', '#f43f5e', '#10b981', '#f59e0b'];

export default function AdminAnalyticsPage() {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [timeframe, setTimeframe] = useState('30D');

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            const result = await complianceService.getAdminAnalytics();
            setData(result);
        } catch (error) {
            console.error("Analytics fetch failure:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, [timeframe]);

    // RESILIENCE FIX: Null-check for premium_by_type
    const pieData = Object.entries(data?.premium_by_type ?? {}).map(([name, value]) => ({
        name,
        value
    }));

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader
                title="Intelligence d'Affaires"
                description="Visualisation des tendances et mix de produits Wali"
            />

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
                    <Download size={16} /> EXPORTER BI (.XLSX)
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                {/* Revenue Growth - Main Chart */}
                <Card className="border-slate-800 bg-slate-900/40 lg:col-span-2">
                    <CardHeader className="p-10 pb-4 flex flex-row items-center justify-between">
                        <div>
                            <CardTitle className="text-xl font-black uppercase tracking-tight">Performance Financière</CardTitle>
                            <CardDescription>Flux net des primes collectées par période</CardDescription>
                        </div>
                        <div className="text-right">
                            <span className="text-2xl font-black text-white">+12.4%</span>
                            <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mt-1">vs Période Précédente</p>
                        </div>
                    </CardHeader>
                    <CardContent className="p-10 pt-0">
                        <div className="h-[350px] w-full mt-10">
                            {data?.revenue_series ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={data.revenue_series}>
                                        <defs>
                                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis dataKey="date" stroke="#475569" fontSize={10} fontWeight="900" tickLine={false} axisLine={false} dy={10} />
                                        <YAxis stroke="#475569" fontSize={10} fontWeight="900" tickLine={false} axisLine={false} tickFormatter={(v) => `${v / 1000}k`} />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: '12px', fontSize: '10px', fontWeight: 'bold' }}
                                        />
                                        <Area type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-full flex items-center justify-center text-slate-700 font-black uppercase tracking-[0.5em] text-xs">PAS DE DONNÉES</div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Claims Density */}
                <Card className="border-slate-800 bg-slate-900/40">
                    <CardHeader className="p-10 pb-4">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center text-orange-500">
                                <Activity size={20} />
                            </div>
                            <CardTitle className="text-xl font-black uppercase tracking-tight">Densité d'incidents</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="p-10 pt-0">
                        <div className="h-[250px] w-full mt-10">
                            {data?.claims_series ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <ReBarChart data={data.claims_series}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis dataKey="date" stroke="#475569" fontSize={10} fontWeight="900" tickLine={false} axisLine={false} dy={10} />
                                        <YAxis stroke="#475569" fontSize={10} fontWeight="900" tickLine={false} axisLine={false} />
                                        <Bar dataKey="count" fill="#f97316" radius={[4, 4, 0, 0]} barSize={24} />
                                    </ReBarChart>
                                </ResponsiveContainer>
                            ) : null}
                        </div>
                    </CardContent>
                </Card>

                {/* Premium Mix - Pie chart fix */}
                <Card className="border-slate-800 bg-slate-900/40">
                    <CardHeader className="p-10 pb-4">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-500">
                                <Layers size={20} />
                            </div>
                            <CardTitle className="text-xl font-black uppercase tracking-tight">Mix de Produits</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="p-10 pt-0 flex flex-col items-center">
                        <div className="h-[200px] w-full mt-10">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={10}
                                        dataKey="value"
                                    >
                                        {pieData.map((_, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="none" />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: '#020617', border: 'none', borderRadius: '8px', fontSize: '10px' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="grid grid-cols-2 gap-4 w-full mt-10">
                            {pieData.map((entry, i) => (
                                <div key={i} className="flex items-center gap-3">
                                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">
                                        {entry.name}: <span className="text-white">{entry.value}%</span>
                                    </span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
