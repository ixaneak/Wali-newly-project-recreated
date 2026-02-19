'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { 
    Search, 
    Scan, 
    X, 
    CheckCircle, 
    AlertCircle, 
    AlertTriangle,
    Package,
    TrendingUp,
    Pill,
    Barcode,
    Loader2,
    Clock,
    Filter,
    RotateCcw,
    Heart,
    FileDown,
    SlidersHorizontal,
    ChevronDown,
    ChevronUp,
    Info
} from 'lucide-react';
import { toast } from 'sonner';
import { drugFormularyService } from '@/lib/api-client';
import { DrugFormularyItem, DrugCategory, DrugStatus } from '@/types/app';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface MedicationSearchProps {
    onSelect: (drug: DrugFormularyItem, quantity: number) => void;
    patientCopay?: number;
    existingMedications?: DrugFormularyItem[];
}

const CATEGORY_LABELS: Record<DrugCategory, string> = {
    pain_relief: 'Antalgiques',
    antibiotics: 'Antibiotiques',
    chronic: 'Chroniques',
    vitamins: 'Vitamines',
    other: 'Autres'
};

const CATEGORY_COLORS: Record<DrugCategory, string> = {
    pain_relief: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    antibiotics: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    chronic: 'bg-violet-500/10 text-violet-500 border-violet-500/20',
    vitamins: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    other: 'bg-slate-500/10 text-slate-500 border-slate-500/20'
};

const STATUS_CONFIG: Record<DrugStatus, { color: string; label: string; icon: any; bgColor: string }> = {
    covered: { 
        color: 'text-emerald-600', 
        label: 'Couvert', 
        icon: CheckCircle,
        bgColor: 'bg-emerald-50 dark:bg-emerald-900/20'
    },
    restricted: { 
        color: 'text-yellow-600', 
        label: 'Restreint', 
        icon: AlertCircle,
        bgColor: 'bg-yellow-50 dark:bg-yellow-900/20'
    },
    not_covered: { 
        color: 'text-red-600', 
        label: 'Non couvert', 
        icon: X,
        bgColor: 'bg-red-50 dark:bg-red-900/20'
    },
    prior_auth_required: { 
        color: 'text-orange-600', 
        label: 'Autorisation requise', 
        icon: AlertCircle,
        bgColor: 'bg-orange-50 dark:bg-orange-900/20'
    }
};

const SEVERITY_CONFIG = {
    contraindicated: { color: 'text-red-600 bg-red-50 border-red-200', label: 'CONTRE-INDIQUÉ', icon: AlertTriangle },
    major: { color: 'text-orange-600 bg-orange-50 border-orange-200', label: 'MAJEURE', icon: AlertTriangle },
    moderate: { color: 'text-yellow-600 bg-yellow-50 border-yellow-200', label: 'MODÉRÉE', icon: AlertCircle },
    minor: { color: 'text-blue-600 bg-blue-50 border-blue-200', label: 'MINEURE', icon: Info }
};

export default function MedicationSearch({ 
    onSelect, 
    patientCopay = 20,
    existingMedications = []
}: MedicationSearchProps) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<DrugFormularyItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const [selectedDrug, setSelectedDrug] = useState<DrugFormularyItem | null>(null);
    const [quantity, setQuantity] = useState('1');
    const [scanningBarcode, setScanningBarcode] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [activeCategory, setActiveCategory] = useState<DrugCategory | null>(null);
    const [recentlyUsed, setRecentlyUsed] = useState<DrugFormularyItem[]>([]);
    const [favorites, setFavorites] = useState<DrugFormularyItem[]>([]);
    const [alternativeDrugs, setAlternativeDrugs] = useState<DrugFormularyItem[]>([]);
    const [showAlternatives, setShowAlternatives] = useState(false);
    const [interactions, setInteractions] = useState<Array<{
        drug1: string;
        drug2: string;
        interaction: { severity: string; description: string; recommendation: string };
    }>>([]);
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState({
        inStockOnly: false,
        prescriptionOnly: false,
        coveredOnly: false,
        minCoverage: 0
    });
    const searchRef = useRef<HTMLDivElement>(null);
    const barcodeScannerRef = useRef<Html5Qrcode | null>(null);

    // Load data on mount
    useEffect(() => {
        loadRecentlyUsed();
        loadFavorites();
    }, []);

    const loadRecentlyUsed = async () => {
        const recent = await drugFormularyService.getRecentlyUsedDrugs();
        setRecentlyUsed(recent);
    };

    const loadFavorites = async () => {
        const favs = await drugFormularyService.getFavoriteDrugs();
        setFavorites(favs);
    };

    // Close results when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowResults(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Search drugs
    useEffect(() => {
        const search = async () => {
            if (query.length < 2 && !activeCategory) {
                setResults([]);
                return;
            }
            
            setLoading(true);
            try {
                let response = await drugFormularyService.searchDrugs(query, activeCategory || undefined);
                let drugs = response.drugs;
                
                // Apply filters
                if (filters.inStockOnly) {
                    drugs = drugs.filter(d => d.in_stock);
                }
                if (filters.prescriptionOnly) {
                    drugs = drugs.filter(d => d.requires_prescription);
                }
                if (filters.coveredOnly) {
                    drugs = drugs.filter(d => d.status === 'covered');
                }
                if (filters.minCoverage > 0) {
                    drugs = drugs.filter(d => d.coverage_percentage >= filters.minCoverage);
                }
                
                setResults(drugs);
                setShowResults(true);
            } catch (error) {
                console.error('Search error:', error);
            } finally {
                setLoading(false);
            }
        };

        const timeoutId = setTimeout(search, 300);
        return () => clearTimeout(timeoutId);
    }, [query, activeCategory, filters]);

    // Cleanup barcode scanner
    useEffect(() => {
        return () => {
            if (barcodeScannerRef.current) {
                barcodeScannerRef.current.stop().catch(console.error);
            }
        };
    }, []);

    const handleSelectDrug = (drug: DrugFormularyItem) => {
        setSelectedDrug(drug);
        setQuery(`${drug.code} - ${drug.name}`);
        setShowResults(false);
        setValidationError(null);
        setAlternativeDrugs([]);
        setShowAlternatives(false);
        
        // Check interactions with existing medications
        const existingCodes = existingMedications.map(m => m.code);
        const newInteractions = drugFormularyService.checkInteractions([...existingCodes, drug.code]);
        setInteractions(newInteractions);
        
        // Validate immediately
        validateAndShow(drug, parseInt(quantity) || 1);
        
        // Load alternatives if not covered or not in stock
        if (drug.status === 'not_covered' || !drug.in_stock) {
            loadAlternatives(drug.code);
        }
    };

    const loadAlternatives = async (code: string) => {
        const alts = await drugFormularyService.getAlternativeDrugs(code);
        if (alts.length > 0) {
            setAlternativeDrugs(alts);
            setShowAlternatives(true);
        }
    };

    const validateAndShow = async (drug: DrugFormularyItem, qty: number) => {
        const validation = await drugFormularyService.validateDrug(drug.code, qty);
        
        if (!validation.valid) {
            setValidationError(validation.error || 'Médicament invalide');
            if (validation.alternative_drugs?.length) {
                setAlternativeDrugs(validation.alternative_drugs);
                setShowAlternatives(true);
            }
        } else {
            setValidationError(null);
        }
    };

    const handleQuantityChange = (value: string) => {
        setQuantity(value);
        if (selectedDrug) {
            validateAndShow(selectedDrug, parseInt(value) || 1);
        }
    };

    const handleAddMedication = () => {
        if (!selectedDrug) {
            toast.error('Veuillez sélectionner un médicament');
            return;
        }

        const qty = parseInt(quantity) || 1;
        
        if (validationError) {
            toast.error(validationError);
            return;
        }

        // Warn about interactions
        const severeInteractions = interactions.filter(i => 
            i.interaction.severity === 'contraindicated' || i.interaction.severity === 'major'
        );
        
        if (severeInteractions.length > 0) {
            const confirm = window.confirm(
                `ATTENTION: ${severeInteractions.length} interaction(s) potentiellement dangereuse(s) détectée(s).\n\n` +
                severeInteractions.map(i => `- ${i.interaction.description}`).join('\n') +
                '\n\nVoulez-vous quand même ajouter ce médicament?'
            );
            if (!confirm) return;
        }

        onSelect(selectedDrug, qty);
        
        // Add to recently used
        drugFormularyService.addRecentlyUsedDrug(selectedDrug.code);
        loadRecentlyUsed();
        
        // Reset
        setSelectedDrug(null);
        setQuery('');
        setQuantity('1');
        setValidationError(null);
        setAlternativeDrugs([]);
        setShowAlternatives(false);
        setInteractions([]);
    };

    const toggleFavorite = (drug: DrugFormularyItem, e: React.MouseEvent) => {
        e.stopPropagation();
        if (drugFormularyService.isFavoriteDrug(drug.code)) {
            drugFormularyService.removeFavoriteDrug(drug.code);
            toast.success(`${drug.name} retiré des favoris`);
        } else {
            drugFormularyService.addFavoriteDrug(drug.code);
            toast.success(`${drug.name} ajouté aux favoris`);
        }
        loadFavorites();
    };

    const startBarcodeScan = async () => {
        setScanningBarcode(true);
        
        try {
            const scanner = new Html5Qrcode('medication-barcode-reader');
            barcodeScannerRef.current = scanner;
            
            await scanner.start(
                { facingMode: 'environment' },
                { fps: 10, qrbox: { width: 300, height: 150 } },
                async (decodedText) => {
                    await scanner.stop();
                    setScanningBarcode(false);
                    
                    const drug = await drugFormularyService.getDrugByCode(decodedText);
                    if (drug) {
                        handleSelectDrug(drug);
                        toast.success(`Médicament trouvé: ${drug.name}`);
                    } else {
                        toast.error('Médicament non trouvé: ' + decodedText);
                        setQuery(decodedText);
                    }
                },
                () => {}
            );
        } catch (error) {
            console.error('Barcode scan error:', error);
            toast.error('Erreur d\'accès à la caméra');
            setScanningBarcode(false);
        }
    };

    const stopBarcodeScan = async () => {
        if (barcodeScannerRef.current) {
            await barcodeScannerRef.current.stop();
            barcodeScannerRef.current = null;
        }
        setScanningBarcode(false);
    };

    const handleExport = () => {
        const csv = drugFormularyService.exportFormularyToCSV();
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `formulary_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        toast.success('Formulaire exporté');
    };

    const getReimbursementInfo = () => {
        if (!selectedDrug) return null;
        const qty = parseInt(quantity) || 1;
        return drugFormularyService.calculateReimbursement(selectedDrug, qty, patientCopay);
    };

    const reimbursement = getReimbursementInfo();
    const categories: (DrugCategory | null)[] = [null, 'pain_relief', 'antibiotics', 'chronic', 'vitamins', 'other'];

    return (
        <div className="space-y-4">
            {/* Barcode Scanner Modal */}
            {scanningBarcode && (
                <div className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center p-4">
                    <div className="w-full max-w-lg">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-white font-bold text-lg flex items-center gap-2">
                                <Barcode className="w-6 h-6" />
                                Scanner le code-barres
                            </h3>
                            <button onClick={stopBarcodeScan} className="text-white/80 hover:text-white p-2">
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        <div id="medication-barcode-reader" className="w-full rounded-xl overflow-hidden" />
                        <p className="text-white/60 text-center mt-4 text-sm">
                            Placez le code-barres dans le cadre
                        </p>
                    </div>
                </div>
            )}

            {/* Header with Export */}
            <div className="flex items-center justify-between">
                <h3 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <Pill className="w-5 h-5 text-emerald-600" />
                    Rechercher un médicament
                </h3>
                <Button variant="ghost" size="sm" onClick={handleExport} className="text-slate-500">
                    <FileDown className="w-4 h-4 mr-1" />
                    Export
                </Button>
            </div>

            {/* Category Filters */}
            <div className="flex flex-wrap gap-2">
                {categories.map((cat) => (
                    <button
                        key={cat || 'all'}
                        onClick={() => {
                            setActiveCategory(cat);
                            if (cat) setShowResults(true);
                        }}
                        className={cn(
                            "px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all",
                            activeCategory === cat
                                ? (cat ? CATEGORY_COLORS[cat] : 'bg-slate-800 text-white border border-slate-700')
                                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                        )}
                    >
                        {cat ? CATEGORY_LABELS[cat] : 'Tous'}
                    </button>
                ))}
            </div>

            {/* Advanced Filters Toggle */}
            <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            >
                <SlidersHorizontal className="w-4 h-4" />
                Filtres avancés
                {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {/* Advanced Filters Panel */}
            {showFilters && (
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 space-y-3">
                    <div className="flex flex-wrap gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={filters.inStockOnly}
                                onChange={(e) => setFilters({...filters, inStockOnly: e.target.checked})}
                                className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                            />
                            <span className="text-sm text-gray-700 dark:text-gray-300">En stock uniquement</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={filters.coveredOnly}
                                onChange={(e) => setFilters({...filters, coveredOnly: e.target.checked})}
                                className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                            />
                            <span className="text-sm text-gray-700 dark:text-gray-300">Couvert uniquement</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={filters.prescriptionOnly}
                                onChange={(e) => setFilters({...filters, prescriptionOnly: e.target.checked})}
                                className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                            />
                            <span className="text-sm text-gray-700 dark:text-gray-300">Ordonnance requise</span>
                        </label>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-700 dark:text-gray-300">Couverture min:</span>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            step="10"
                            value={filters.minCoverage}
                            onChange={(e) => setFilters({...filters, minCoverage: parseInt(e.target.value)})}
                            className="w-32"
                        />
                        <span className="text-sm font-medium text-emerald-600">{filters.minCoverage}%</span>
                    </div>
                </div>
            )}

            {/* Favorites Section */}
            {favorites.length > 0 && !selectedDrug && (
                <div className="bg-pink-50 dark:bg-pink-900/10 rounded-xl p-3 border border-pink-200 dark:border-pink-800">
                    <p className="text-xs font-bold text-pink-600 dark:text-pink-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                        <Heart className="w-3 h-3 fill-current" />
                        Favoris
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {favorites.map((drug) => (
                            <button
                                key={drug.id}
                                onClick={() => handleSelectDrug(drug)}
                                className="px-3 py-1.5 bg-white dark:bg-slate-700 rounded-lg text-xs font-medium text-pink-700 dark:text-pink-300 border border-pink-200 dark:border-pink-700 hover:bg-pink-50 transition flex items-center gap-1"
                            >
                                <Heart className="w-3 h-3 fill-current" />
                                {drug.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Recently Used */}
            {recentlyUsed.length > 0 && !selectedDrug && (
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-3">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Récemment utilisés
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {recentlyUsed.map((drug) => (
                            <button
                                key={drug.id}
                                onClick={() => handleSelectDrug(drug)}
                                className="px-3 py-1.5 bg-white dark:bg-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600 hover:border-emerald-500 hover:text-emerald-600 transition"
                            >
                                {drug.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Search Input */}
            <div className="relative" ref={searchRef}>
                <div className="relative">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value);
                            setSelectedDrug(null);
                            setValidationError(null);
                            setAlternativeDrugs([]);
                        }}
                        placeholder="Nom, code ou molécule..."
                        className="w-full pl-10 pr-12 py-3 rounded-xl border border-gray-200 dark:border-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 dark:bg-slate-800 dark:text-white"
                    />
                    <Search className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                    <button
                        onClick={startBarcodeScan}
                        className="absolute right-3 top-3 p-1 text-gray-400 hover:text-emerald-600 transition"
                        title="Scanner le code-barres"
                    >
                        <Scan className="w-5 h-5" />
                    </button>
                </div>

                {/* Search Results */}
                {showResults && results.length > 0 && (
                    <div className="absolute z-20 w-full mt-1 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-700 shadow-lg max-h-80 overflow-auto">
                        <div className="sticky top-0 bg-gray-50 dark:bg-slate-800 px-4 py-2 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-gray-100 dark:border-slate-700 flex justify-between">
                            <span>{results.length} médicament{results.length > 1 ? 's' : ''}</span>
                            {(activeCategory || filters.inStockOnly || filters.coveredOnly) && (
                                <button 
                                    onClick={() => {
                                        setActiveCategory(null);
                                        setFilters({...filters, inStockOnly: false, coveredOnly: false, prescriptionOnly: false, minCoverage: 0});
                                    }}
                                    className="text-emerald-600 hover:text-emerald-700"
                                >
                                    Réinit.
                                </button>
                            )}
                        </div>
                        {results.map((drug) => {
                            const statusConfig = STATUS_CONFIG[drug.status];
                            const StatusIcon = statusConfig.icon;
                            const isFav = drugFormularyService.isFavoriteDrug(drug.code);
                            
                            return (
                                <div
                                    key={drug.id}
                                    className="w-full px-4 py-3 hover:bg-gray-50 dark:hover:bg-slate-800 border-b border-gray-100 dark:border-slate-800 last:border-0 flex items-start gap-3 group"
                                >
                                    <button
                                        onClick={() => handleSelectDrug(drug)}
                                        className="flex-1 flex items-start gap-3 text-left"
                                    >
                                        <div className={`p-2 rounded-lg ${statusConfig.bgColor} ${statusConfig.color}`}>
                                            <StatusIcon className="w-4 h-4" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-gray-900 dark:text-white truncate flex items-center gap-2">
                                                {drug.name}
                                                {(drug.stock_quantity || 0) < 30 && drug.in_stock && (
                                                    <span className="text-xs px-1.5 py-0.5 bg-orange-100 text-orange-600 rounded">
                                                        Stock faible
                                                    </span>
                                                )}
                                            </p>
                                            <p className="text-sm text-gray-500">
                                                {drug.code} • {drug.generic_name}
                                            </p>
                                            <div className="flex items-center gap-2 mt-1 text-xs">
                                                <span className={`px-2 py-0.5 rounded-full ${statusConfig.bgColor} ${statusConfig.color}`}>
                                                    {statusConfig.label}
                                                </span>
                                                <span className={`px-2 py-0.5 rounded-full ${CATEGORY_COLORS[drug.category]}`}>
                                                    {CATEGORY_LABELS[drug.category]}
                                                </span>
                                                <span className="text-gray-400">
                                                    {drug.strength} • {drug.unit_price} FCFA
                                                </span>
                                            </div>
                                        </div>
                                        {!drug.in_stock && (
                                            <span className="text-xs text-red-500 font-medium px-2 py-1 bg-red-50 rounded">
                                                Rupture
                                            </span>
                                        )}
                                    </button>
                                    <button
                                        onClick={(e) => toggleFavorite(drug, e)}
                                        className="p-2 text-gray-400 hover:text-pink-500 transition"
                                    >
                                        <Heart className={cn("w-4 h-4", isFav && "fill-pink-500 text-pink-500")} />
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}

                {showResults && query.length >= 2 && !loading && results.length === 0 && (
                    <div className="absolute z-20 w-full mt-1 bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-700 shadow-lg p-4 text-center">
                        <p className="text-gray-500">Aucun médicament trouvé</p>
                        <p className="text-sm text-gray-400 mt-1">Essayez avec d&apos;autres critères</p>
                    </div>
                )}
            </div>

            {/* Interactions Warning */}
            {interactions.length > 0 && (
                <div className="space-y-2">
                    {interactions.map((interaction, idx) => {
                        const config = SEVERITY_CONFIG[interaction.interaction.severity as keyof typeof SEVERITY_CONFIG];
                        const Icon = config.icon;
                        const drug1Name = results.find(d => d.code === interaction.drug1)?.name || interaction.drug1;
                        const drug2Name = results.find(d => d.code === interaction.drug2)?.name || interaction.drug2;
                        
                        return (
                            <div key={idx} className={`p-3 rounded-xl border ${config.color}`}>
                                <div className="flex items-start gap-2">
                                    <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                    <div className="flex-1">
                                        <p className="font-bold text-sm">
                                            Interaction {config.label}: {drug1Name} + {drug2Name}
                                        </p>
                                        <p className="text-sm mt-1 opacity-90">
                                            {interaction.interaction.description}
                                        </p>
                                        <p className="text-xs mt-1 opacity-75">
                                            Recommandation: {interaction.interaction.recommendation}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Alternative Drugs */}
            {showAlternatives && alternativeDrugs.length > 0 && (
                <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-4 border border-amber-200 dark:border-amber-800">
                    <p className="text-sm font-bold text-amber-800 dark:text-amber-400 mb-2 flex items-center gap-2">
                        <Info className="w-4 h-4" />
                        Alternatives disponibles
                    </p>
                    <div className="space-y-2">
                        {alternativeDrugs.map((drug) => (
                            <button
                                key={drug.id}
                                onClick={() => {
                                    handleSelectDrug(drug);
                                    setShowAlternatives(false);
                                }}
                                className="w-full flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition"
                            >
                                <div className="text-left">
                                    <p className="font-medium text-gray-900 dark:text-white">{drug.name}</p>
                                    <p className="text-xs text-gray-500">{drug.generic_name}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm font-bold text-emerald-600">{drug.coverage_percentage}% couvert</p>
                                    <p className="text-xs text-gray-400">{drug.unit_price} FCFA</p>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Selected Drug Info */}
            {selectedDrug && (
                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-xl p-4 space-y-4">
                    {/* Drug Header */}
                    <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-lg ${STATUS_CONFIG[selectedDrug.status].bgColor}`}>
                                <Pill className={cn("w-5 h-5", STATUS_CONFIG[selectedDrug.status].color)} />
                            </div>
                            <div>
                                <h4 className="font-bold text-gray-900 dark:text-white">
                                    {selectedDrug.name}
                                </h4>
                                <p className="text-sm text-gray-500">
                                    {selectedDrug.generic_name} • {selectedDrug.strength}
                                </p>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${CATEGORY_COLORS[selectedDrug.category]}`}>
                                        {CATEGORY_LABELS[selectedDrug.category]}
                                    </span>
                                    <span className="text-xs text-gray-400">
                                        {selectedDrug.manufacturer}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={(e) => toggleFavorite(selectedDrug, e)}
                                className="p-2 text-gray-400 hover:text-pink-500 transition"
                            >
                                <Heart className={cn("w-5 h-5", drugFormularyService.isFavoriteDrug(selectedDrug.code) && "fill-pink-500 text-pink-500")} />
                            </button>
                            <button
                                onClick={() => {
                                    setSelectedDrug(null);
                                    setQuery('');
                                    setValidationError(null);
                                    setAlternativeDrugs([]);
                                    setShowAlternatives(false);
                                    setInteractions([]);
                                }}
                                className="text-gray-400 hover:text-red-500"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Coverage & Stock Info */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white dark:bg-slate-800 rounded-lg p-3">
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
                                <TrendingUp className="w-4 h-4" />
                                Couverture Wali
                            </div>
                            <p className="text-2xl font-bold text-emerald-600">
                                {selectedDrug.coverage_percentage}%
                            </p>
                        </div>
                        <div className="bg-white dark:bg-slate-800 rounded-lg p-3">
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
                                <Package className="w-4 h-4" />
                                Stock
                            </div>
                            <p className={cn(
                                "text-2xl font-bold",
                                !selectedDrug.in_stock ? 'text-red-500' :
                                (selectedDrug.stock_quantity || 0) < 30 ? 'text-orange-500' : 'text-emerald-600'
                            )}>
                                {!selectedDrug.in_stock ? 'Rupture' :
                                 (selectedDrug.stock_quantity || 0) < 30 ? `${selectedDrug.stock_quantity} rest.` : 'Disponible'}
                            </p>
                        </div>
                    </div>

                    {/* Warnings */}
                    {selectedDrug.requires_prescription && (
                        <div className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-yellow-700 dark:text-yellow-400">
                                Ce médicament nécessite une ordonnance
                            </p>
                        </div>
                    )}

                    {!selectedDrug.in_stock && (
                        <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm text-red-700 dark:text-red-400 font-medium">
                                    Produit en rupture de stock
                                </p>
                                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                                    Consultez les alternatives disponibles ci-dessus
                                </p>
                            </div>
                        </div>
                    )}

                    {validationError && (
                        <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-600 dark:text-red-400">
                                {validationError}
                            </p>
                        </div>
                    )}

                    {/* Quantity and Price */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Quantité
                            </label>
                            <input
                                type="number"
                                min="1"
                                max={selectedDrug.max_quantity_per_claim}
                                value={quantity}
                                onChange={(e) => handleQuantityChange(e.target.value)}
                                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-slate-700 focus:ring-2 focus:ring-emerald-500 dark:bg-slate-800 dark:text-white"
                            />
                            <p className="text-xs text-gray-400 mt-1">
                                Max: {selectedDrug.max_quantity_per_claim} unités
                            </p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Prix unitaire
                            </label>
                            <div className="px-3 py-2 bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {selectedDrug.unit_price.toLocaleString()} FCFA
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Reimbursement Preview */}
                    {reimbursement && !validationError && (
                        <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600 dark:text-gray-400">Total</span>
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {reimbursement.total.toLocaleString()} FCFA
                                </span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-emerald-600">
                                    Wali couvre ({reimbursement.coveragePercent}%)
                                </span>
                                <span className="font-bold text-emerald-600">
                                    {reimbursement.waliCovers.toLocaleString()} FCFA
                                </span>
                            </div>
                            <div className="flex justify-between text-base border-t border-emerald-200 dark:border-emerald-800 pt-2">
                                <span className="text-gray-700 dark:text-gray-300 font-medium">
                                    Patient paie
                                </span>
                                <span className="font-bold text-gray-900 dark:text-white">
                                    {reimbursement.patientPays.toLocaleString()} FCFA
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Add Button */}
                    <button
                        onClick={handleAddMedication}
                        disabled={!!validationError || !selectedDrug.in_stock}
                        className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-xl font-bold flex items-center justify-center gap-2 transition"
                    >
                        <CheckCircle className="w-5 h-5" />
                        {!selectedDrug.in_stock ? 'Produit indisponible' : 'Ajouter à la prestation'}
                    </button>
                </div>
            )}
        </div>
    );
}
