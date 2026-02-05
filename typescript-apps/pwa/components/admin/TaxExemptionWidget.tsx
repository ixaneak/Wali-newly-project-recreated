import React from 'react';
import { ComplianceStatus, FinancialSummary, complianceService } from '@/lib/api-client';
import {
    ShieldCheck,
    TrendingUp,
    FileText,
    Activity,
    Download,
    History
} from 'lucide-react';
import { toast } from 'sonner';
import {
    ResponsiveContainer,
    RadialBarChart,
    RadialBar,
    PolarAngleAxis,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    Cell
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface TaxExemptionWidgetProps {
    data: ComplianceStatus | null;
    summary: FinancialSummary | null;
    loading: boolean;
}

export default function TaxExemptionWidget({ data, summary, loading }: TaxExemptionWidgetProps) {
    const handleGenerateReport = async () => {
        const loadingToast = toast.loading("Génération du rapport XML (COSUMAF)...");
        try {
            const date = new Date();
            const monthStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            const report = await complianceService.getMonthlyReport(monthStr);

            const blob = new Blob([report.xml_content], { type: 'text/xml' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Wali_COSUMAF_${monthStr}.xml`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

            toast.success("Rapport XML exporté avec succès", { id: loadingToast });
        } catch (e) {
            toast.error("Échec de l'export XML", { id: loadingToast });
        }
    };

    if (loading && !data) {
        return (
            <Card className="col-span-1 xl:col-span-2 animate-pulse h-[500px] border-slate-800 bg-[#111827]/60">
                <CardHeader>
                    <div className="h-8 w-48 bg-slate-800 rounded"></div>
                </CardHeader>
                <CardContent className="h-full flex items-center justify-center">
                    <div className="w-32 h-32 rounded-full border-4 border-slate-800 border-t-sky-500 animate-spin"></div>
                </CardContent>
            </Card>
        );
    }

    const progressValue = data?.percentage || 38.9;
    const currentMonth = data?.currentMonth || 14;
    const totalMonths = data?.totalMonths || 36;
    const exemptAmount = summary?.exemptIncome.amount || 45000000;
    const taxableAmount = summary?.taxableIncome.amount || 1200000;
    const exemptTrend = summary?.exemptIncome.trend || 12.4;

    const radialData = [{ name: 'Progress', value: progressValue, fill: '#0ea5e9' }];

    const barData = [
        { name: 'Exempt', value: exemptAmount, color: '#10b981' },
        { name: 'Taxable', value: taxableAmount, color: '#f59e0b' }
    ];

    return (
        <Card className="col-span-1 xl:col-span-2 overflow-hidden relative border-slate-800 bg-[#0f172a]/80 backdrop-blur-2xl shadow-2xl group">
            {/* Design elements */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/5 rounded-full blur-[80px] -mr-16 -mt-16 group-hover:bg-sky-500/10 transition-colors" />

            <CardHeader className="flex flex-row items-center justify-between pb-8">
                <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center border border-sky-500/20 shadow-lg shadow-sky-500/10">
                        <ShieldCheck className="text-[#0ea5e9]" size={24} />
                    </div>
                    <div>
                        <CardTitle className="text-xl">COSUMAF COMPLIANCE</CardTitle>
                        <CardDescription>Période d'Exonération Fiscale</CardDescription>
                    </div>
                </div>
                <div className={`px-4 py-1.5 rounded-full border text-[10px] font-black tracking-widest ${data?.status === 'COMPLIANT'
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500'
                        : 'bg-rose-500/10 border-rose-500/20 text-rose-500'
                    }`}>
                    {data?.status || 'COMPLIANT'}
                </div>
            </CardHeader>

            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                    {/* Visual Progress */}
                    <div className="relative flex flex-col items-center justify-center p-6 bg-slate-900/40 rounded-3xl border border-slate-800/50">
                        <div className="w-full h-[200px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadialBarChart
                                    innerRadius="70%"
                                    outerRadius="100%"
                                    data={radialData}
                                    startAngle={90}
                                    endAngle={450}
                                >
                                    <PolarAngleAxis
                                        type="number"
                                        domain={[0, 100]}
                                        angleAxisId={0}
                                        tick={false}
                                    />
                                    <RadialBar
                                        background
                                        dataKey="value"
                                        cornerRadius={10}
                                        angleAxisId={0}
                                    />
                                </RadialBarChart>
                            </ResponsiveContainer>
                            <div className="absolute inset-0 flex flex-col items-center justify-center pt-6">
                                <span className="text-4xl font-black text-white">{progressValue}%</span>
                                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mt-1">Actif</span>
                            </div>
                        </div>
                        <div className="text-center mt-4">
                            <p className="text-sm font-bold text-slate-300">
                                {currentMonth} <span className="text-slate-500 mx-1">sur</span> {totalMonths} mois
                            </p>
                        </div>
                    </div>

                    {/* Stats Breakdown */}
                    <div className="flex flex-col justify-between">
                        <div className="space-y-6">
                            <div className="group/item">
                                <div className="flex justify-between items-end mb-2">
                                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest group-hover/item:text-emerald-500 transition-colors">Revenus Exonérés</label>
                                    <span className="text-xs font-bold text-emerald-400">+{exemptTrend}%</span>
                                </div>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-2xl font-black text-white">{Intl.NumberFormat('fr-FR').format(exemptAmount)}</span>
                                    <span className="text-xs font-bold text-slate-600">XOF</span>
                                </div>
                                <div className="w-full h-1.5 bg-slate-800 rounded-full mt-3 overflow-hidden">
                                    <div className="h-full bg-emerald-500 transition-all duration-1000" style={{ width: '85%' }}></div>
                                </div>
                            </div>

                            <div className="group/item">
                                <div className="flex justify-between items-end mb-2">
                                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest group-hover/item:text-amber-500 transition-colors">Revenus Taxables</label>
                                    <span className="text-xs font-bold text-slate-500">Normal</span>
                                </div>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-2xl font-black text-white">{Intl.NumberFormat('fr-FR').format(taxableAmount)}</span>
                                    <span className="text-xs font-bold text-slate-600">XOF</span>
                                </div>
                                <div className="w-full h-1.5 bg-slate-800 rounded-full mt-3 overflow-hidden">
                                    <div className="h-full bg-amber-500 transition-all duration-1000" style={{ width: '15%' }}></div>
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-4 mt-10">
                            <Button variant="cyan" size="xl" className="flex-1 gap-3 h-14" onClick={handleGenerateReport}>
                                <Download size={18} />
                                RAPPORT XML
                            </Button>
                            <Button variant="outline" size="xl" className="flex-1 gap-3 h-14 border-slate-700 bg-slate-800/10 hover:bg-slate-800" >
                                <History size={18} />
                                AUDIT TRAIL
                            </Button>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
