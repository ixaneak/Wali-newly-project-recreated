'use client';

import React, { useState, useEffect } from 'react';
import { 
    Pill, 
    Search, 
    Plus, 
    Edit3,
    Trash2,
    AlertTriangle,
    CheckCircle,
    X,
    Upload,
    Download,
    Package
} from 'lucide-react';
import { drugFormularyService } from '@/lib/api-client';
import { DrugFormularyItem, DrugCategory, DrugStatus } from '@/types/app';
import AdminHeader from '@/components/admin/AdminHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const CATEGORY_LABELS: Record<DrugCategory, string> = {
    pain_relief: 'Antalgiques',
    antibiotics: 'Antibiotiques',
    chronic: 'Chroniques',
    vitamins: 'Vitamines',
    other: 'Autres'
};

const STATUS_LABELS: Record<DrugStatus, string> = {
    covered: 'Couvert',
    restricted: 'Restreint',
    not_covered: 'Non couvert',
    prior_auth_required: 'Autorisation requise'
};

const STATUS_COLORS: Record<DrugStatus, string> = {
    covered: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    restricted: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    not_covered: 'bg-red-500/10 text-red-500 border-red-500/20',
    prior_auth_required: 'bg-orange-500/10 text-orange-500 border-orange-500/20'
};

export default function AdminFormularyPage() {
    const [drugs, setDrugs] = useState<DrugFormularyItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [categoryFilter, setCategoryFilter] = useState<DrugCategory | 'all'>('all');
    const [statusFilter, setStatusFilter] = useState<DrugStatus | 'all'>('all');
    const [showImportPanel, setShowImportPanel] = useState(false);
    const [importContent, setImportContent] = useState('');
    const [importResults, setImportResults] = useState<{ success: number; errors: string[] } | null>(null);

    useEffect(() => {
        fetchDrugs();
    }, []);

    const fetchDrugs = async () => {
        try {
            setLoading(true);
            const response = await drugFormularyService.getAllDrugs(1, 100);
            setDrugs(response.drugs);
        } catch (error) {
            toast.error('Erreur de chargement du formulaire');
        } finally {
            setLoading(false);
        }
    };

    const filteredDrugs = drugs.filter(drug => {
        const matchesSearch = 
            drug.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            drug.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
            drug.generic_name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesCategory = categoryFilter === 'all' || drug.category === categoryFilter;
        const matchesStatus = statusFilter === 'all' || drug.status === statusFilter;
        return matchesSearch && matchesCategory && matchesStatus;
    });

    const handleExport = () => {
        const csv = drugFormularyService.exportFormularyToCSV();
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `formulary_export_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        toast.success('Formulaire exporté avec succès');
    };

    const handleImport = async () => {
        if (!importContent.trim()) {
            toast.error('Veuillez coller le contenu CSV');
            return;
        }

        try {
            const results = await drugFormularyService.importFormularyFromCSV(importContent);
            setImportResults(results);
            if (results.success > 0) {
                toast.success(`${results.success} médicaments importés`);
                fetchDrugs();
            }
            if (results.errors.length > 0) {
                toast.error(`${results.errors.length} erreurs détectées`);
            }
        } catch (error) {
            toast.error('Erreur lors de l\'import');
        }
    };

    const handleDelete = async (code: string) => {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce médicament?')) return;
        
        toast.success('Médicament supprimé (simulation)');
        setDrugs(drugs.filter(d => d.code !== code));
    };

    // Calculate stats
    const totalDrugs = drugs.length;
    const coveredDrugs = drugs.filter(d => d.status === 'covered').length;
    const lowStockDrugs = drugs.filter(d => d.in_stock && (d.stock_quantity || 0) < 30).length;
    const outOfStockDrugs = drugs.filter(d => !d.in_stock).length;

    return (
        <div className="space-y-10 min-h-screen bg-slate-950 pb-20">
            <AdminHeader 
                title="Gestion du Formulaire" 
                description="Gérer les médicaments et leur couverture"
            />

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6 flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                            <Pill size={22} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Total Médicaments</p>
                            <p className="text-2xl font-black text-white">{totalDrugs}</p>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6 flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                            <CheckCircle size={22} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Couvert</p>
                            <p className="text-2xl font-black text-white">{coveredDrugs}</p>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6 flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-orange-500/10 flex items-center justify-center text-orange-500">
                            <AlertTriangle size={22} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Stock Faible</p>
                            <p className="text-2xl font-black text-white">{lowStockDrugs}</p>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6 flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-red-500/10 flex items-center justify-center text-red-500">
                            <Package size={22} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Rupture</p>
                            <p className="text-2xl font-black text-white">{outOfStockDrugs}</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Import Panel */}
            {showImportPanel && (
                <Card className="border-slate-800 bg-slate-900/40">
                    <CardContent className="p-6 space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-bold text-white uppercase tracking-wider">Import CSV</h3>
                            <button 
                                onClick={() => setShowImportPanel(false)}
                                className="text-slate-400 hover:text-white"
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <p className="text-sm text-slate-400">
                            Format: Code,Nom,Generique,Categorie,Prix,Couverture,Stock,Ordonnance
                        </p>
                        <textarea
                            value={importContent}
                            onChange={(e) => setImportContent(e.target.value)}
                            className="w-full h-32 bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300"
                            placeholder="MED-001,Doliprane,Paracetamol,pain_relief,150,80,true,false"
                        />
                        {importResults && (
                            <div className="p-4 bg-slate-950 rounded-xl">
                                <p className="text-emerald-400 font-bold">{importResults.success} importés avec succès</p>
                                {importResults.errors.length > 0 && (
                                    <div className="mt-2">
                                        <p className="text-red-400 text-sm">{importResults.errors.length} erreurs:</p>
                                        <ul className="text-xs text-red-400 mt-1 max-h-24 overflow-auto">
                                            {importResults.errors.map((err, i) => (
                                                <li key={i}>{err}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                        <div className="flex gap-3">
                            <Button onClick={handleImport} className="bg-emerald-600 hover:bg-emerald-700">
                                <Upload size={16} className="mr-2" />
                                Importer
                            </Button>
                            <Button variant="outline" onClick={() => setImportContent('')} className="border-slate-700">
                                Effacer
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Filters and Actions */}
            <Card className="border-slate-800 bg-slate-900/40">
                <CardContent className="p-6">
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                        <div className="flex flex-wrap gap-4">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                                <input 
                                    className="bg-slate-950/50 border border-slate-800 rounded-xl py-2 pl-9 pr-4 text-xs font-bold text-white w-64" 
                                    placeholder="RECHERCHER MÉDICAMENT..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            
                            <select
                                value={categoryFilter}
                                onChange={(e) => setCategoryFilter(e.target.value as DrugCategory | 'all')}
                                className="bg-slate-950/50 border border-slate-800 rounded-xl py-2 px-4 text-xs font-bold text-white"
                            >
                                <option value="all">Toutes catégories</option>
                                {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                                    <option key={key} value={key}>{label}</option>
                                ))}
                            </select>

                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value as DrugStatus | 'all')}
                                className="bg-slate-950/50 border border-slate-800 rounded-xl py-2 px-4 text-xs font-bold text-white"
                            >
                                <option value="all">Tous statuts</option>
                                {Object.entries(STATUS_LABELS).map(([key, label]) => (
                                    <option key={key} value={key}>{label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex gap-3">
                            <Button variant="outline" onClick={handleExport} className="border-slate-700 bg-slate-950/50">
                                <Download size={16} className="mr-2" />
                                Export CSV
                            </Button>
                            
                            <Button 
                                variant="outline" 
                                onClick={() => setShowImportPanel(!showImportPanel)} 
                                className="border-slate-700 bg-slate-950/50"
                            >
                                <Upload size={16} className="mr-2" />
                                Import
                            </Button>

                            <Button className="bg-emerald-600 hover:bg-emerald-700">
                                <Plus size={16} className="mr-2" />
                                Ajouter
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Drugs Table */}
            <Card className="border-slate-800 bg-slate-900/40">
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow className="border-slate-800 hover:bg-transparent">
                                <TableHead className="pl-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Médicament</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Catégorie</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Prix</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Couverture</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Stock</TableHead>
                                <TableHead className="uppercase text-[10px] font-black tracking-widest text-slate-500">Statut</TableHead>
                                <TableHead className="text-right pr-8 uppercase text-[10px] font-black tracking-widest text-slate-500">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading ? (
                                [...Array(5)].map((_, i) => (
                                    <TableRow key={i}>
                                        <TableCell colSpan={7}>
                                            <div className="h-12 w-full bg-slate-800/10 animate-pulse rounded-lg mt-1 mx-4" />
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : filteredDrugs.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="h-60 text-center text-slate-600 font-bold uppercase tracking-[0.2em] text-[10px]">
                                        AUCUN MÉDICAMENT TROUVÉ
                                    </TableCell>
                                </TableRow>
                            ) : filteredDrugs.map((drug) => (
                                <TableRow key={drug.id} className="border-slate-800/50 hover:bg-slate-800/30">
                                    <TableCell className="pl-8 py-5">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                                                <Pill size={20} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-white">{drug.name}</p>
                                                <p className="text-xs text-slate-400">{drug.code}</p>
                                                <p className="text-[10px] text-slate-500">{drug.generic_name} • {drug.strength}</p>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge className={cn("text-[10px] uppercase", STATUS_COLORS[drug.status])}>
                                            {CATEGORY_LABELS[drug.category]}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="text-sm text-white">{drug.unit_price.toLocaleString()} FCFA</div>
                                        <p className="text-xs text-slate-500">{drug.package_price.toLocaleString()} FCFA</p>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                                                <div 
                                                    className="h-full bg-emerald-500 rounded-full"
                                                    style={{ width: `${drug.coverage_percentage}%` }}
                                                />
                                            </div>
                                            <span className="text-sm font-bold text-emerald-400">{drug.coverage_percentage}%</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        {drug.in_stock ? (
                                            <div>
                                                <span className={cn(
                                                    "text-sm font-bold",
                                                    (drug.stock_quantity || 0) < 30 ? "text-orange-400" : "text-emerald-400"
                                                )}>
                                                    {drug.stock_quantity || 0} unités
                                                </span>
                                                {(drug.stock_quantity || 0) < 30 && (
                                                    <span className="text-[10px] text-orange-400 block">Stock faible</span>
                                                )}
                                            </div>
                                        ) : (
                                            <span className="text-sm font-bold text-red-500">Rupture</span>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <Badge className={cn("text-[10px] uppercase", STATUS_COLORS[drug.status])}>
                                            {STATUS_LABELS[drug.status]}
                                        </Badge>
                                        {drug.requires_prescription && (
                                            <span className="text-[10px] text-yellow-400 block mt-1">Ordonnance requise</span>
                                        )}
                                    </TableCell>
                                    <TableCell className="text-right pr-8">
                                        <div className="flex items-center justify-end gap-2">
                                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                                <Edit3 size={14} className="text-slate-400" />
                                            </Button>
                                            <Button 
                                                variant="ghost" 
                                                size="sm" 
                                                className="h-8 w-8 p-0"
                                                onClick={() => handleDelete(drug.code)}
                                            >
                                                <Trash2 size={14} className="text-red-400" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Summary Footer */}
            <div className="flex items-center justify-between text-xs text-slate-500">
                <p>{filteredDrugs.length} médicament{filteredDrugs.length > 1 ? 's' : ''} affiché{filteredDrugs.length > 1 ? 's' : ''}</p>
                <p>Total: {totalDrugs} médicaments dans le formulaire</p>
            </div>
        </div>
    );
}
