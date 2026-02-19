'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { pharmacyService } from '@/lib/api-client';
import { CoverageVerificationResult, DrugFormularyItem } from '@/types/app';
import MedicationSearch from '@/components/pharmacy/MedicationSearch';
import { 
    ArrowLeft, 
    Scan, 
    Search, 
    CheckCircle, 
    XCircle, 
    Banknote, 
    Loader2, 
    Printer,
    RefreshCcw,
    AlertCircle,
    Camera,
    X,
    Package,
    Pill,
    TrendingUp
} from 'lucide-react';
import { toast } from 'sonner';

interface MedicationItem extends DrugFormularyItem {
    quantity: number;
    totalPrice: number;
    waliCovers: number;
    patientPays: number;
}

interface VerificationData extends CoverageVerificationResult {
    copay: number;
    plan: string;
}

export default function VerificationPage() {
    const router = useRouter();
    const [step, setStep] = useState<'scan' | 'result'>('scan');
    const [inputCode, setInputCode] = useState('');
    const [verifying, setVerifying] = useState(false);
    const [result, setResult] = useState<VerificationData | null>(null);
    const [medications, setMedications] = useState<MedicationItem[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [cameraError, setCameraError] = useState<string | null>(null);
    const scannerRef = useRef<Html5QrcodeScanner | null>(null);

    // Cleanup scanner on unmount
    useEffect(() => {
        return () => {
            if (scannerRef.current) {
                scannerRef.current.clear().catch(console.error);
            }
        };
    }, []);

    // Initialize QR Scanner
    useEffect(() => {
        if (scanning && step === 'scan') {
            const timeoutId = setTimeout(() => {
                scannerRef.current = new Html5QrcodeScanner(
                    "reader",
                    { 
                        fps: 10, 
                        qrbox: { width: 250, height: 250 },
                        aspectRatio: 1,
                        showZoomSliderIfSupported: true,
                        showTorchButtonIfSupported: true
                    },
                    false
                );

                scannerRef.current.render(
                    handleScanSuccess,
                    handleScanError
                );
            }, 100);

            return () => clearTimeout(timeoutId);
        }
    }, [scanning, step]);

    const handleScanSuccess = async (decodedText: string) => {
        // Stop scanning
        setScanning(false);
        if (scannerRef.current) {
            await scannerRef.current.clear();
        }

        // Parse QR code - expected format: {"uid":"...","token":"..."} or just phone number
        let phone = decodedText;
        let token = '';
        
        try {
            const parsed = JSON.parse(decodedText);
            if (parsed.uid) phone = parsed.uid;
            if (parsed.token) token = parsed.token;
        } catch (e) {
            // Not JSON, use as-is (might be phone:token format)
            const parts = decodedText.split(':');
            if (parts.length === 2) {
                phone = parts[0];
                token = parts[1];
            }
        }

        await verifyCoverage(phone, token);
    };

    const handleScanError = (err: string) => {
        // Only show meaningful errors, ignore "NotFound" spam
        if (typeof err === 'string' && !err.includes('NotFound') && !err.includes('scanning')) {
            console.warn('QR Scan error:', err);
            if (err.includes('NotAllowed')) {
                setCameraError('Permission caméra refusée. Veuillez autoriser l\'accès à la caméra.');
                toast.error('Permission caméra refusée');
            } else if (err.includes('NotFound')) {
                setCameraError('Aucune caméra détectée sur cet appareil.');
                toast.error('Aucune caméra détectée');
            } else {
                setCameraError('Erreur caméra: ' + err);
            }
        }
    };

    const verifyCoverage = async (phone: string, token: string = '') => {
        setVerifying(true);
        setCameraError(null);
        
        try {
            const data = await pharmacyService.verifyCoverage(phone, token);
            
            // Map backend response to frontend type with copay
            const verificationData: VerificationData = {
                ...data,
                copay: data.copay || 20, // Default 20% if not provided
                plan: data.plan || 'Standard'
            };
            
            setResult(verificationData);
            setStep('result');

            if (data.status === 'active') {
                toast.success('Couverture active confirmée');
            } else {
                toast.error('Couverture inactive ou expirée');
            }
        } catch (error: any) {
            console.error(error);
            toast.error(error.response?.data?.detail || 'Erreur de vérification');
        } finally {
            setVerifying(false);
        }
    };

    const handleManualVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputCode) return;
        
        const parts = inputCode.split(':');
        const phone = parts[0];
        const token = parts[1] || '';
        
        await verifyCoverage(phone, token);
    };

    // Handle medication selection from formulary
    const handleMedicationSelect = (drug: DrugFormularyItem, quantity: number) => {
        const totalPrice = drug.unit_price * quantity;
        const waliCovers = Math.round(totalPrice * (drug.coverage_percentage / 100));
        const patientPays = totalPrice - waliCovers;

        const medicationItem: MedicationItem = {
            ...drug,
            quantity,
            totalPrice,
            waliCovers,
            patientPays
        };

        setMedications([...medications, medicationItem]);
        toast.success(`${drug.name} ajouté (${quantity} unité${quantity > 1 ? 's' : ''})`);
    };

    const removeMedication = (index: number) => {
        const med = medications[index];
        setMedications(medications.filter((_, i) => i !== index));
        toast.success(`${med.name} retiré`);
    };

    const calculateTotals = () => {
        const total = medications.reduce((sum, med) => sum + med.totalPrice, 0);
        const waliCovers = medications.reduce((sum, med) => sum + med.waliCovers, 0);
        const patientPays = total - waliCovers;
        
        return {
            total,
            waliCovers,
            patientPays
        };
    };

    const handleSubmitClaim = async () => {
        if (!result || medications.length === 0) {
            toast.error('Veuillez ajouter au moins un médicament');
            return;
        }

        setSubmitting(true);
        try {
            const totals = calculateTotals();
            
            await pharmacyService.submitReimbursement({
                artisan_phone: result.coverage_id,
                amount: totals.waliCovers,
                medication_code: medications.map(m => `${m.code}:${m.quantity}`).join(','),
                medications: medications.map(m => ({
                    code: m.code,
                    name: m.name,
                    quantity: m.quantity,
                    unit_price: m.unit_price,
                    total: m.totalPrice
                }))
            });
            
            toast.success('Demande de remboursement transmise à NSIA');
        } catch (error: any) {
            console.error(error);
            toast.error(error.response?.data?.detail || 'Erreur lors de la transmission');
        } finally {
            setSubmitting(false);
        }
    };

    const handlePrint = () => {
        if (!result) return;
        
        const totals = calculateTotals();
        const date = new Date().toLocaleString('fr-FR');

        const printWindow = window.open('', '_blank');
        if (!printWindow) {
            toast.error('Veuillez autoriser les popups pour imprimer');
            return;
        }

        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reçu - ${result.artisan_name}</title>
                <style>
                    body { font-family: monospace; max-width: 400px; margin: 0 auto; padding: 20px; }
                    .header { text-align: center; border-bottom: 2px dashed #000; padding-bottom: 10px; margin-bottom: 20px; }
                    .title { font-size: 24px; font-weight: bold; }
                    .subtitle { font-size: 14px; color: #666; }
                    .section { margin: 15px 0; }
                    .label { font-weight: bold; }
                    .line { display: flex; justify-content: space-between; margin: 5px 0; }
                    .drug-line { margin: 8px 0; padding: 5px 0; border-bottom: 1px dotted #ccc; }
                    .total { font-size: 18px; font-weight: bold; border-top: 1px solid #000; padding-top: 10px; }
                    .footer { text-align: center; margin-top: 30px; font-size: 12px; border-top: 2px dashed #000; padding-top: 10px; }
                    @media print { body { width: 80mm; } }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="title">🏥 WALI PHARMACIE</div>
                    <div class="subtitle">Reçu de prestation</div>
                    <div>${date}</div>
                </div>
                
                <div class="section">
                    <div class="label">Patient:</div>
                    <div>${result.artisan_name}</div>
                    <div>ID: ${result.coverage_id}</div>
                    <div>Plafond: ${result.max_reimbursement.toLocaleString()} FCFA</div>
                </div>

                <div class="section">
                    <div class="label">Médicaments:</div>
                    ${medications.map(med => `
                        <div class="drug-line">
                            <div class="line">
                                <span>${med.code}</span>
                                <span>${med.totalPrice.toLocaleString()} FCFA</span>
                            </div>
                            <div style="font-size: 12px; color: #666;">
                                ${med.name} x${med.quantity} @ ${med.unit_price} FCFA
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="section total">
                    <div class="line">
                        <span>Total:</span>
                        <span>${totals.total.toLocaleString()} FCFA</span>
                    </div>
                    <div class="line" style="color: #059669;">
                        <span>Wali couvre:</span>
                        <span>${totals.waliCovers.toLocaleString()} FCFA</span>
                    </div>
                    <div class="line" style="color: #dc2626;">
                        <span>Patient paie:</span>
                        <span>${totals.patientPays.toLocaleString()} FCFA</span>
                    </div>
                </div>

                <div class="footer">
                    <div>Référence: ${result.partner_reference}</div>
                    <div>Pharmacien: ________________</div>
                    <div style="margin-top: 10px;">Merci d'avoir choisi Wali! 🙏</div>
                </div>
                
                <script>window.print(); setTimeout(() => window.close(), 500);</script>
            </body>
            </html>
        `);
        printWindow.document.close();
        
        toast.success('Reçu ouvert dans une nouvelle fenêtre');
    };

    const handleReset = () => {
        setStep('scan');
        setInputCode('');
        setResult(null);
        setMedications([]);
        setCameraError(null);
        if (scannerRef.current) {
            scannerRef.current.clear().catch(console.error);
            scannerRef.current = null;
        }
    };

    const totals = calculateTotals();

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
            {/* Header */}
            <div className="bg-white dark:bg-slate-900 p-4 shadow-sm flex items-center gap-4 sticky top-0 z-10">
                <button 
                    onClick={() => step === 'result' ? setStep('scan') : router.back()} 
                    className="text-gray-500 hover:text-gray-900 dark:text-gray-400"
                >
                    <ArrowLeft />
                </button>
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">
                    {step === 'scan' ? 'Vérification Couverture' : 'Détails de la Prestation'}
                </h1>
            </div>

            <div className="p-6 max-w-2xl mx-auto">
                {step === 'scan' ? (
                    <div className="space-y-6">
                        {/* QR Scanner Section */}
                        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-200 dark:border-slate-800">
                            <div className="flex items-center gap-3 mb-4">
                                <Camera className="w-6 h-6 text-emerald-600" />
                                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Scanner le QR Code Patient</h2>
                            </div>
                            
                            {scanning ? (
                                <div className="relative">
                                    <div id="reader" className="w-full overflow-hidden rounded-xl"></div>
                                    <button
                                        onClick={() => {
                                            setScanning(false);
                                            if (scannerRef.current) {
                                                scannerRef.current.clear().catch(console.error);
                                            }
                                        }}
                                        className="absolute top-2 right-2 bg-white/90 p-2 rounded-full text-red-500 hover:bg-white shadow-lg"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                            ) : (
                                <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border-2 border-dashed border-gray-300 dark:border-slate-700 p-8 text-center">
                                    <div className="w-20 h-20 bg-gray-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <Scan className="w-10 h-10 text-gray-400" />
                                    </div>
                                    <p className="text-gray-500 mb-4">Activez la caméra pour scanner le QR Code du patient</p>
                                    <button 
                                        onClick={() => setScanning(true)}
                                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-xl font-medium transition flex items-center gap-2 mx-auto"
                                    >
                                        <Camera className="w-5 h-5" />
                                        Activer la caméra
                                    </button>
                                </div>
                            )}

                            {/* Camera Error */}
                            {cameraError && (
                                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-start gap-3">
                                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <p className="text-red-700 dark:text-red-400 font-medium">Erreur Caméra</p>
                                        <p className="text-red-600 dark:text-red-400 text-sm">{cameraError}</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Divider */}
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-200 dark:border-slate-700"></div>
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-gray-50 dark:bg-slate-950 text-gray-500">ou saisir manuellement</span>
                            </div>
                        </div>

                        {/* Manual Entry */}
                        <form onSubmit={handleManualVerify} className="space-y-4">
                            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-200 dark:border-slate-800">
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Numéro de téléphone ou ID Couverture
                                </label>
                                <div className="relative">
                                    <input
                                        type="text"
                                        value={inputCode}
                                        onChange={(e) => setInputCode(e.target.value)}
                                        placeholder="Ex: 0707070707 ou 0707070707:token"
                                        className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 dark:bg-slate-800 dark:text-white"
                                    />
                                    <Search className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                                </div>
                                <p className="text-xs text-gray-500 mt-2">
                                    Format: numéro de téléphone ou numéro:token
                                </p>
                            </div>
                            
                            <button
                                type="submit"
                                disabled={verifying || !inputCode}
                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50 transition"
                            >
                                {verifying && <Loader2 className="animate-spin w-5 h-5" />}
                                Vérifier la couverture
                            </button>
                        </form>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Result Card */}
                        <div className={`rounded-2xl p-6 border-l-4 shadow-sm ${
                            result?.status === 'active'
                                ? 'bg-white dark:bg-slate-900 border-emerald-500'
                                : 'bg-red-50 dark:bg-red-900/10 border-red-500'
                        }`}>
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                        {result?.artisan_name}
                                    </h2>
                                    <p className="text-gray-500 text-sm">ID: {result?.coverage_id}</p>
                                </div>
                                {result?.status === 'active' ? (
                                    <CheckCircle className="w-8 h-8 text-emerald-500" />
                                ) : (
                                    <XCircle className="w-8 h-8 text-red-500" />
                                )}
                            </div>

                            <div className="grid grid-cols-2 gap-4 mt-4 py-4 border-t border-gray-100 dark:border-slate-800">
                                <div>
                                    <p className="text-xs text-gray-500 uppercase">Statut</p>
                                    <p className={`font-bold ${
                                        result?.status === 'active' ? 'text-emerald-600' : 'text-red-600'
                                    }`}>
                                        {result?.status === 'active' ? 'ACTIF' : 'INACTIF'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 uppercase">Plafond Remb.</p>
                                    <p className="font-bold text-gray-900 dark:text-white">
                                        {result?.max_reimbursement.toLocaleString()} FCFA
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 uppercase">Plan</p>
                                    <p className="font-bold text-gray-900 dark:text-white">{result?.plan}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 uppercase">Ticket Modérateur</p>
                                    <p className="font-bold text-gray-900 dark:text-white">{result?.copay}%</p>
                                </div>
                            </div>

                            <p className="text-xs text-gray-400 mt-2">
                                Réf. Partenaire: {result?.partner_reference}
                            </p>
                        </div>

                        {/* Medications Section - Only for Active Coverage */}
                        {result?.status === 'active' && (
                            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-gray-200 dark:border-slate-800">
                                <h3 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                    <Package className="w-5 h-5 text-emerald-600" />
                                    Médicaments
                                </h3>

                                {/* Medication Search with Formulary */}
                                <MedicationSearch 
                                    onSelect={handleMedicationSelect}
                                    patientCopay={result.copay}
                                    existingMedications={medications}
                                />

                                {/* Medications List */}
                                {medications.length > 0 && (
                                    <div className="mt-6 space-y-3">
                                        <h4 className="font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                            <Pill className="w-4 h-4" />
                                            Médicaments ajoutés ({medications.length})
                                        </h4>
                                        
                                        {medications.map((med, index) => (
                                            <div 
                                                key={`${med.id}-${index}`}
                                                className="flex justify-between items-center p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-slate-700"
                                            >
                                                <div className="flex items-start gap-3">
                                                    <div className={`p-2 rounded-lg ${
                                                        med.status === 'covered' 
                                                            ? 'bg-emerald-100 text-emerald-600' 
                                                            : 'bg-yellow-100 text-yellow-600'
                                                    }`}>
                                                        <Pill className="w-4 h-4" />
                                                    </div>
                                                    <div>
                                                        <p className="font-medium text-gray-900 dark:text-white">
                                                            {med.name}
                                                        </p>
                                                        <p className="text-xs text-gray-500">
                                                            {med.code} • {med.strength}
                                                        </p>
                                                        <p className="text-xs text-gray-400">
                                                            {med.quantity} x {med.unit_price.toLocaleString()} FCFA
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <p className="font-bold text-gray-900 dark:text-white">
                                                        {med.totalPrice.toLocaleString()} FCFA
                                                    </p>
                                                    <button
                                                        onClick={() => removeMedication(index)}
                                                        className="text-xs text-red-500 hover:text-red-700 mt-1"
                                                    >
                                                        Retirer
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Cost Breakdown */}
                                {medications.length > 0 && (
                                    <div className="mt-6 border-t border-gray-200 dark:border-slate-700 pt-4 space-y-3">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-gray-600 dark:text-gray-400">Total</span>
                                            <span className="font-bold text-gray-900 dark:text-white">
                                                {totals.total.toLocaleString()} FCFA
                                            </span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-emerald-600 flex items-center gap-1">
                                                <TrendingUp className="w-4 h-4" />
                                                Wali couvre
                                            </span>
                                            <span className="font-bold text-emerald-600">
                                                {totals.waliCovers.toLocaleString()} FCFA
                                            </span>
                                        </div>
                                        <div className="flex justify-between text-base border-t border-gray-200 dark:border-slate-700 pt-2">
                                            <span className="text-gray-700 dark:text-gray-300 font-medium">
                                                Patient paie ({result?.copay}%)
                                            </span>
                                            <span className="font-bold text-gray-900 dark:text-white">
                                                {totals.patientPays.toLocaleString()} FCFA
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Action Buttons */}
                                {medications.length > 0 && (
                                    <div className="grid grid-cols-2 gap-3 mt-6">
                                        <button
                                            onClick={handlePrint}
                                            className="py-3 bg-gray-100 hover:bg-gray-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-xl font-bold flex items-center justify-center gap-2 transition"
                                        >
                                            <Printer className="w-5 h-5" />
                                            Imprimer le reçu
                                        </button>
                                        <button
                                            onClick={handleSubmitClaim}
                                            disabled={submitting}
                                            className="py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition disabled:opacity-50"
                                        >
                                            {submitting && <Loader2 className="animate-spin w-5 h-5" />}
                                            Transmettre à NSIA
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Next Patient Button */}
                        <button
                            onClick={handleReset}
                            className="w-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-700 dark:text-gray-300 font-medium py-3 rounded-xl flex items-center justify-center gap-2 transition"
                        >
                            <RefreshCcw className="w-5 h-5" />
                            Patient suivant
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
