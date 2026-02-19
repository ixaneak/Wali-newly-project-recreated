"use client";

import React, { useState, useCallback } from 'react';
import {
    Shield, AlertTriangle, Eye, FileText, CheckCircle, RefreshCw,
    Search, Download, AlertOctagon, Ban, Activity, TrendingUp,
    Send, X, Image as ImageIcon, Printer
} from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

import AdminHeader from '@/components/admin/AdminHeader';
import DocumentViewer from '@/components/admin/sar/DocumentViewer';
import RiskHeatmap from '@/components/admin/sar/RiskHeatmap';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { sarService } from '@/lib/api-client';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface SARReport {
    id: string;
    report_reference: string;
    status: 'draft' | 'submitted' | 'under_review' | 'closed';
    subject_name: string;
    subject_phone: string;
    activity_type: string;
    risk_score: number;
    description: string;
    amount_involved: number;
    evidence_photos: string[];
    assigned_analyst: string;
    created_at: string;
}

// ═══════════════════════════════════════════════════════════════
// MOCK DATA
// ═══════════════════════════════════════════════════════════════

const MOCK_QUEUE: SARReport[] = [
    {
        id: "sar-001", report_reference: "SAR-2026-000042", status: "draft",
        subject_name: "Koné Amadou", subject_phone: "+225 07 12 34 56",
        activity_type: "structuring", risk_score: 85,
        description: "3 policies totaling 1,450,000 CFA within 48h",
        amount_involved: 1450000, evidence_photos: ["/evidence/receipt1.jpg", "/evidence/receipt2.jpg"],
        assigned_analyst: "", created_at: "2026-02-18T10:30:00Z"
    },
    {
        id: "sar-002", report_reference: "SAR-2026-000041", status: "under_review",
        subject_name: "Yao Sarah", subject_phone: "+225 05 98 76 54",
        activity_type: "rapid_claim", risk_score: 72,
        description: "Claim filed 18h after policy creation",
        amount_involved: 750000, evidence_photos: ["/evidence/claim-photo.jpg"],
        assigned_analyst: "analyst@wali.ci", created_at: "2026-02-17T14:20:00Z"
    },
    {
        id: "sar-003", report_reference: "SAR-2026-000040", status: "draft",
        subject_name: "Bakayoko Issouf", subject_phone: "+225 01 23 45 67",
        activity_type: "document_forgery", risk_score: 90,
        description: "Medical receipts show signs of digital editing",
        amount_involved: 2500000, evidence_photos: ["/evidence/forged-doc1.jpg", "/evidence/forged-doc2.jpg", "/evidence/forged-doc3.jpg"],
        assigned_analyst: "", created_at: "2026-02-16T09:15:00Z"
    },
    {
        id: "sar-004", report_reference: "SAR-2026-000039", status: "submitted",
        subject_name: "Diallo Fatou", subject_phone: "+225 07 55 66 77",
        activity_type: "threshold_breach", risk_score: 60,
        description: "Single transaction of 650,000 XOF",
        amount_involved: 650000, evidence_photos: [],
        assigned_analyst: "compliance@wali.ci", created_at: "2026-02-15T16:45:00Z"
    },
    {
        id: "sar-005", report_reference: "SAR-2026-000038", status: "closed",
        subject_name: "Kouassi Marie", subject_phone: "+225 07 89 01 23",
        activity_type: "geolocation_anomaly", risk_score: 45,
        description: "Claim in Yamoussoukro, phone registered in Abidjan",
        amount_involved: 500000, evidence_photos: [],
        assigned_analyst: "analyst@wali.ci", created_at: "2026-02-14T11:30:00Z"
    }
];

const TREND_DATA = [
    { date: "Feb 12", sars: 2, flags: 8, score: 45 },
    { date: "Feb 13", sars: 1, flags: 5, score: 38 },
    { date: "Feb 14", sars: 3, flags: 12, score: 52 },
    { date: "Feb 15", sars: 2, flags: 7, score: 41 },
    { date: "Feb 16", sars: 4, flags: 15, score: 58 },
    { date: "Feb 17", sars: 2, flags: 9, score: 44 },
    { date: "Feb 18", sars: 1, flags: 6, score: 39 },
];

const COLORS = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' };
const PIE_DATA = [
    { name: 'Low', value: 45, color: COLORS.low },
    { name: 'Medium', value: 32, color: COLORS.medium },
    { name: 'High', value: 18, color: COLORS.high },
    { name: 'Critical', value: 8, color: COLORS.critical },
];

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

export default function ComplianceDashboard() {
    const [queue, setQueue] = useState<SARReport[]>(MOCK_QUEUE);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('queue');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSar, setSelectedSar] = useState<SARReport | null>(null);
    const [viewerOpen, setViewerOpen] = useState(false);
    const [viewerSar, setViewerSar] = useState<SARReport | null>(null);
    const [submitting, setSubmitting] = useState<string | null>(null);

    const pendingCount = queue.filter(s => s.status === 'draft').length;
    const reviewCount = queue.filter(s => s.status === 'under_review').length;

    const refreshData = async () => {
        setLoading(true);
        try {
            const data = await sarService.getReports();
            if (data?.sar_reports?.length) setQueue(data.sar_reports);
        } catch (e) { /* keep mock */ }
        setLoading(false);
    };

    const handleSubmitTracfin = async (sar: SARReport) => {
        setSubmitting(sar.id);
        try {
            await sarService.submitTracfin(sar.id);
            setQueue(q => q.map(s => s.id === sar.id ? { ...s, status: 'submitted' as const } : s));
        } catch (e) {
            // Mock: update locally
            setQueue(q => q.map(s => s.id === sar.id ? { ...s, status: 'submitted' as const } : s));
        }
        setSubmitting(null);
    };

    const handleClose = async (sar: SARReport, resolution: string) => {
        try {
            await sarService.closeSar(sar.id, resolution);
        } catch (e) { /* fallback */ }
        setQueue(q => q.map(s => s.id === sar.id ? { ...s, status: 'closed' as const } : s));
        setSelectedSar(null);
    };

    const handleExportPdf = (sar: SARReport) => {
        const content = `
SAR REPORT — ${sar.report_reference}
Generated: ${new Date().toISOString()}
${'═'.repeat(50)}

Subject: ${sar.subject_name}
Phone: ${sar.subject_phone}
Activity: ${sar.activity_type.replace(/_/g, ' ').toUpperCase()}
Risk Score: ${sar.risk_score}/100
Amount: ${sar.amount_involved.toLocaleString()} XOF
Status: ${sar.status.toUpperCase()}
Analyst: ${sar.assigned_analyst || 'Unassigned'}

Description:
${sar.description}

Created: ${new Date(sar.created_at).toLocaleString()}
Evidence Photos: ${sar.evidence_photos.length} document(s)
        `.trim();

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${sar.report_reference}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const filteredQueue = queue.filter(s =>
        !searchQuery || s.subject_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.report_reference.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.subject_phone.includes(searchQuery)
    );

    return (
        <div className="space-y-6 min-h-screen pb-20">
            <AdminHeader title="Compliance Officer Dashboard" description="SAR Management • CIMA AML Compliance • TRACFIN Reporting" />

            {/* Controls */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <Input placeholder="Search SARs, names, phone..." value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 bg-slate-900 border-slate-800 text-white" />
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={refreshData} disabled={loading} className="border-slate-800 bg-slate-900/40">
                        <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} /> Refresh
                    </Button>
                </div>
            </div>

            {/* KPI Strip */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <KPICard title="Pending Queue" value={pendingCount} sub="Requires action" icon={FileText} color="red" pulse />
                <KPICard title="Under Review" value={reviewCount} sub="Analyst assigned" icon={Eye} color="amber" />
                <KPICard title="Submitted to TRACFIN" value={queue.filter(s => s.status === 'submitted').length} sub="Awaiting confirmation" icon={Send} color="cyan" />
                <KPICard title="Closed" value={queue.filter(s => s.status === 'closed').length} sub="Resolved cases" icon={CheckCircle} color="emerald" />
            </div>

            {/* Main Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                <TabsList className="bg-slate-900/60 p-1 rounded-xl border border-slate-800">
                    {[
                        { id: 'queue', label: `Pending Queue (${pendingCount})`, icon: AlertTriangle },
                        { id: 'all', label: 'All Reports', icon: FileText },
                        { id: 'heatmap', label: 'Risk Heatmap', icon: Activity },
                        { id: 'trends', label: 'Trends', icon: TrendingUp },
                    ].map((tab) => (
                        <TabsTrigger key={tab.id} value={tab.id}
                            className="px-4 py-2 rounded-lg text-sm font-medium data-[state=active]:bg-cyan-500 data-[state=active]:text-white data-[state=inactive]:text-slate-400">
                            <tab.icon className="w-4 h-4 mr-2" /> {tab.label}
                        </TabsTrigger>
                    ))}
                </TabsList>

                {/* PENDING QUEUE TAB */}
                <TabsContent value="queue" className="space-y-3">
                    {filteredQueue.filter(s => s.status === 'draft' || s.status === 'under_review').length === 0 ? (
                        <Card className="border-slate-800 bg-slate-900/40">
                            <CardContent className="p-12 text-center">
                                <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                                <p className="text-lg font-semibold text-white">Queue Clear</p>
                                <p className="text-sm text-slate-400 mt-1">No pending SAR reports require attention</p>
                            </CardContent>
                        </Card>
                    ) : (
                        filteredQueue.filter(s => s.status === 'draft' || s.status === 'under_review').map((sar) => (
                            <QueueCard key={sar.id} sar={sar}
                                onViewDocs={() => { setViewerSar(sar); setViewerOpen(true); }}
                                onSubmitTracfin={() => handleSubmitTracfin(sar)}
                                onExportPdf={() => handleExportPdf(sar)}
                                onClose={(res) => handleClose(sar, res)}
                                isSubmitting={submitting === sar.id}
                            />
                        ))
                    )}
                </TabsContent>

                {/* ALL REPORTS TAB */}
                <TabsContent value="all" className="space-y-4">
                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardContent className="p-0">
                            <table className="w-full">
                                <thead className="bg-slate-800/50">
                                    <tr>
                                        {['Reference', 'Subject', 'Type', 'Risk', 'Status', 'Actions'].map(h => (
                                            <th key={h} className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase">{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {filteredQueue.map((sar) => (
                                        <tr key={sar.id} className="hover:bg-slate-800/30 transition">
                                            <td className="px-4 py-3 font-mono text-sm text-cyan-400">{sar.report_reference}</td>
                                            <td className="px-4 py-3">
                                                <div className="text-sm text-white">{sar.subject_name}</div>
                                                <div className="text-xs text-slate-500">{sar.subject_phone}</div>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-slate-300 capitalize">{sar.activity_type.replace(/_/g, ' ')}</td>
                                            <td className="px-4 py-3"><RiskBadge score={sar.risk_score} /></td>
                                            <td className="px-4 py-3"><StatusBadge status={sar.status} /></td>
                                            <td className="px-4 py-3">
                                                <div className="flex gap-1">
                                                    {sar.evidence_photos.length > 0 && (
                                                        <Button size="sm" variant="ghost" onClick={() => { setViewerSar(sar); setViewerOpen(true); }}>
                                                            <ImageIcon className="w-4 h-4" />
                                                        </Button>
                                                    )}
                                                    <Button size="sm" variant="ghost" onClick={() => handleExportPdf(sar)}>
                                                        <Download className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* HEATMAP TAB */}
                <TabsContent value="heatmap" className="space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <Card className="lg:col-span-2 border-slate-800 bg-slate-900/40">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-cyan-500" /> Risk Score Heatmap
                                </CardTitle>
                            </CardHeader>
                            <CardContent><RiskHeatmap /></CardContent>
                        </Card>
                        <Card className="border-slate-800 bg-slate-900/40">
                            <CardHeader><CardTitle className="text-lg">Risk Distribution</CardTitle></CardHeader>
                            <CardContent>
                                <div className="h-[250px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={60} outerRadius={80} dataKey="value">
                                                {PIE_DATA.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                                            </Pie>
                                            <Tooltip contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b' }} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="grid grid-cols-2 gap-2 mt-4">
                                    {PIE_DATA.map((item) => (
                                        <div key={item.name} className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                                            <span className="text-sm text-slate-400">{item.name}: {item.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* TRENDS TAB */}
                <TabsContent value="trends">
                    <Card className="border-slate-800 bg-slate-900/40">
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-cyan-500" /> 7-Day Risk Activity
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="h-[350px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={TREND_DATA}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis dataKey="date" stroke="#475569" fontSize={12} />
                                        <YAxis stroke="#475569" fontSize={12} />
                                        <Tooltip contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b' }} />
                                        <Line type="monotone" dataKey="sars" name="SARs Created" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} />
                                        <Line type="monotone" dataKey="flags" name="Flags Raised" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                                        <Line type="monotone" dataKey="score" name="Avg Risk Score" stroke="#0ea5e9" strokeWidth={2} dot={{ r: 4 }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Document Viewer Modal */}
            <DocumentViewer
                isOpen={viewerOpen}
                onClose={() => setViewerOpen(false)}
                title={viewerSar ? `Evidence — ${viewerSar.report_reference}` : 'Documents'}
                photos={viewerSar?.evidence_photos || []}
            />
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ═══════════════════════════════════════════════════════════════

function KPICard({ title, value, sub, icon: Icon, color, pulse }: {
    title: string; value: number; sub: string; icon: any; color: string; pulse?: boolean;
}) {
    const c: Record<string, { bg: string; text: string }> = {
        red: { bg: 'bg-red-500/10', text: 'text-red-400' },
        amber: { bg: 'bg-amber-500/10', text: 'text-amber-400' },
        cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400' },
        emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
    };
    const col = c[color] || c.cyan;
    return (
        <Card className={cn("border-slate-800 bg-slate-900/40", pulse && value > 0 && "border-red-500/30")}>
            <CardContent className="p-5">
                <div className="flex items-start justify-between">
                    <div className={cn("p-2.5 rounded-xl", col.bg)}>
                        <Icon className={cn("w-5 h-5", col.text)} />
                    </div>
                    {pulse && value > 0 && <span className="relative flex h-3 w-3"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" /><span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" /></span>}
                </div>
                <div className="mt-3">
                    <div className="text-3xl font-black text-white">{value}</div>
                    <div className="text-sm font-medium text-slate-400">{title}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{sub}</div>
                </div>
            </CardContent>
        </Card>
    );
}

function QueueCard({ sar, onViewDocs, onSubmitTracfin, onExportPdf, onClose, isSubmitting }: {
    sar: SARReport; onViewDocs: () => void; onSubmitTracfin: () => void;
    onExportPdf: () => void; onClose: (res: string) => void; isSubmitting: boolean;
}) {
    const [showCloseMenu, setShowCloseMenu] = useState(false);

    return (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className={cn(
                "p-5 rounded-xl border transition-all",
                sar.risk_score >= 70 ? "bg-red-500/5 border-red-500/20" :
                    sar.risk_score >= 40 ? "bg-amber-500/5 border-amber-500/20" :
                        "bg-slate-900/40 border-slate-800"
            )}>
            <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-mono text-sm text-cyan-400">{sar.report_reference}</span>
                        <StatusBadge status={sar.status} />
                        <RiskBadge score={sar.risk_score} />
                    </div>
                    <h4 className="text-base font-semibold text-white mt-2">{sar.subject_name}</h4>
                    <p className="text-sm text-slate-400 mt-0.5">{sar.subject_phone}</p>
                    <p className="text-sm text-slate-300 mt-2">{sar.description}</p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                        <span>Type: <span className="text-slate-300 capitalize">{sar.activity_type.replace(/_/g, ' ')}</span></span>
                        <span>Amount: <span className="text-white font-medium">{sar.amount_involved.toLocaleString()} XOF</span></span>
                        <span>{new Date(sar.created_at).toLocaleDateString()}</span>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-2 shrink-0">
                    {sar.evidence_photos.length > 0 && (
                        <Button size="sm" variant="outline" onClick={onViewDocs} className="border-slate-700 text-xs">
                            <ImageIcon className="w-3.5 h-3.5 mr-1.5" /> Photos ({sar.evidence_photos.length})
                        </Button>
                    )}
                    {sar.status === 'draft' && (
                        <Button size="sm" onClick={onSubmitTracfin} disabled={isSubmitting}
                            className="bg-cyan-600 hover:bg-cyan-700 text-xs">
                            <Send className={cn("w-3.5 h-3.5 mr-1.5", isSubmitting && "animate-pulse")} />
                            {isSubmitting ? 'Submitting...' : 'Submit TRACFIN'}
                        </Button>
                    )}
                    <Button size="sm" variant="outline" onClick={onExportPdf} className="border-slate-700 text-xs">
                        <Download className="w-3.5 h-3.5 mr-1.5" /> Export PDF
                    </Button>
                    {sar.status !== 'closed' && (
                        <div className="relative">
                            <Button size="sm" variant="outline" onClick={() => setShowCloseMenu(!showCloseMenu)}
                                className="border-slate-700 text-xs w-full">
                                <X className="w-3.5 h-3.5 mr-1.5" /> Close
                            </Button>
                            {showCloseMenu && (
                                <div className="absolute right-0 top-full mt-1 bg-slate-800 border border-slate-700 rounded-lg p-1 z-10 min-w-[160px]">
                                    <button onClick={() => { onClose('false_positive'); setShowCloseMenu(false); }}
                                        className="w-full text-left px-3 py-2 text-xs text-emerald-400 hover:bg-slate-700 rounded">
                                        ✓ False Positive
                                    </button>
                                    <button onClick={() => { onClose('confirmed_fraud'); setShowCloseMenu(false); }}
                                        className="w-full text-left px-3 py-2 text-xs text-red-400 hover:bg-slate-700 rounded">
                                        ✕ Confirmed Fraud
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

function RiskBadge({ score }: { score: number }) {
    const color = score >= 70 ? 'bg-red-500/20 text-red-400 border-red-500/30' :
        score >= 40 ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
            score >= 20 ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    return <Badge variant="outline" className={cn("font-mono", color)}>{score}</Badge>;
}

function StatusBadge({ status }: { status: string }) {
    const styles: Record<string, string> = {
        draft: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
        submitted: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        under_review: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        closed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    };
    return <Badge variant="outline" className={cn("capitalize text-[10px]", styles[status] || styles.draft)}>{status.replace(/_/g, ' ')}</Badge>;
}
