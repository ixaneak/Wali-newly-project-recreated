"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Heart, AlertTriangle, Home, FileText, Camera, X, Check, Loader2 } from 'lucide-react';
import { ClaimType, CLAIM_TYPE_CONFIG } from '@/types/claims';
import { claimsService, policyService, PolicyData } from '@/lib/api-client';
import imageCompression from 'browser-image-compression';
import { toast } from 'sonner';
import { auth } from '@/lib/firebase';

type Step = 'type' | 'details' | 'photos' | 'review';

export default function NewClaimPage() {
    const router = useRouter();
    const [step, setStep] = useState<Step>('type');
    const [claimType, setClaimType] = useState<ClaimType | null>(null);
    const [amount, setAmount] = useState('');
    const [description, setDescription] = useState('');
    const [incidentDate, setIncidentDate] = useState('');
    const [photos, setPhotos] = useState<string[]>([]);
    const [uploading, setUploading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [loadingPolicy, setLoadingPolicy] = useState(true);
    const [activePolicy, setActivePolicy] = useState<PolicyData | null>(null);
    const [userId, setUserId] = useState<string | null>(null);

    // Load active policy
    useEffect(() => {
        const loadPolicy = async () => {
            // Wait for auth to be ready
            if (!auth.currentUser) return;

            const uid = auth.currentUser.uid;
            setUserId(uid);
            setLoadingPolicy(true);

            try {
                const policies = await policyService.getUserPolicies(uid);
                const active = policies.find((p: PolicyData) => p.status === 'active' || p.status === 'pending');
                // Allow 'pending' for dev testing if strict 'active' is blocking

                if (active) {
                    setActivePolicy(active);
                } else {
                    console.log("No active policy found");
                }
            } catch (error) {
                console.error("Failed to load policy", error);
                toast.error("Impossible de vérifier votre couverture d'assurance");
            } finally {
                setLoadingPolicy(false);
            }
        };

        // Delay slightly to ensure auth state is populated
        const timer = setTimeout(() => {
            if (auth.currentUser) loadPolicy();
            else {
                // Listen for auth state change if not ready
                const unsubscribe = auth.onAuthStateChanged((user) => {
                    if (user) loadPolicy();
                    else setLoadingPolicy(false);
                });
                return () => unsubscribe();
            }
        }, 500);
        return () => clearTimeout(timer);
    }, []);

    // Helper to create test policy (DEV ONLY)
    const handleCreateTestPolicy = async () => {
        if (!auth.currentUser) return;
        try {
            toast.loading("Création d'une police de test...");
            const uid = auth.currentUser.uid;
            await policyService.createPolicy({
                user_id: uid,
                coverage_type: 'bundle',
                coverage_details: { max_coverage_amount: 500000, description: "Test Policy" },
                payment_frequency: 'monthly',
                region: 'Abidjan'
            });
            // Reload
            const policies = await policyService.getUserPolicies(uid);
            const active = policies[0]; // Just take first one
            if (active) setActivePolicy(active);
            toast.dismiss();
            toast.success("Police créée! Vous pouvez maintenant faire un claim.");
        } catch (e: any) {
            console.error("Policy creation failed:", e);
            console.error("Error data:", e.response?.data);

            let detailedError = "";
            if (e.response?.data?.detail) {
                detailedError = typeof e.response.data.detail === 'string'
                    ? e.response.data.detail
                    : JSON.stringify(e.response.data.detail);
            }

            toast.dismiss();
            toast.error(`Erreur création police: ${detailedError || e.message}`);
        }
    };


    const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        setUploading(true);
        try {
            const compressedPhotos: string[] = [];

            for (let i = 0; i < files.length; i++) {
                const file = files[i];

                // Compress image
                const compressed = await imageCompression(file, {
                    maxSizeMB: 0.5,
                    maxWidthOrHeight: 1024,
                    useWebWorker: true,
                });

                // Convert to base64
                const reader = new FileReader();
                const base64 = await new Promise<string>((resolve) => {
                    reader.onloadend = () => resolve(reader.result as string);
                    reader.readAsDataURL(compressed);
                });

                compressedPhotos.push(base64);
            }

            setPhotos([...photos, ...compressedPhotos]);
            toast.success(`${compressedPhotos.length} photo${compressedPhotos.length > 1 ? 's' : ''} ajoutée${compressedPhotos.length > 1 ? 's' : ''}`);
        } catch (error) {
            console.error('Photo upload error:', error);
            toast.error('Erreur lors du téléchargement');
        } finally {
            setUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const removePhoto = (index: number) => {
        setPhotos(photos.filter((_, i) => i !== index));
    };

    const handleSubmit = async () => {
        if (!claimType) return;

        setSubmitting(true);

        try {
            // Step 1: Upload photos to the backend if any exist
            let photoUrls: string[] = [];

            if (photos.length > 0) {
                toast.info('Téléchargement des photos...');

                // Convert base64 photos back to File objects for upload
                const photoFiles = await Promise.all(
                    photos.map(async (base64Photo, index) => {
                        const response = await fetch(base64Photo);
                        const blob = await response.blob();
                        return new File([blob], `photo-${index + 1}.jpg`, { type: 'image/jpeg' });
                    })
                );

                // Upload photos to backend
                try {
                    photoUrls = await claimsService.uploadMultiplePhotos(photoFiles);
                    toast.success(`${photoUrls.length} photo${photoUrls.length > 1 ? 's' : ''} téléchargée${photoUrls.length > 1 ? 's' : ''}`);
                } catch (error) {
                    console.error('Photo upload error:', error);
                    toast.error('Erreur lors du téléchargement des photos. Utilisation de photos locales...');
                    // Fallback to base64 photos if upload fails
                    photoUrls = photos;
                }
            }

            // Step 2: Submit claim with photo URLs
            const claimData = {
                user_id: userId || "",
                policy_id: activePolicy?.id || "",
                claim_type: claimType,
                amount: parseFloat(amount),
                description,
                incident_date: incidentDate,
                photos: photoUrls,
            };

            console.log('Submitting claim data:', claimData);
            toast.info('Soumission du claim...');
            const createdClaim = await claimsService.submitClaim(claimData);

            toast.success('Claim soumis avec succès!');
            console.log('Claim created:', createdClaim);

            // Redirect to claims list after a brief delay
            setTimeout(() => {
                router.push('/dashboard/claims');
            }, 500);

        } catch (error: any) {
            console.error('Claim submission error:', error);
            console.error('Error response:', error?.response?.data);

            // Extract error message from various formats
            let errorMessage = 'Une erreur est survenue';

            if (error?.response?.data) {
                const data = error.response.data;

                // FastAPI validation errors (array format)
                if (Array.isArray(data.detail)) {
                    errorMessage = data.detail.map((err: any) =>
                        `${err.loc?.join('.')}: ${err.msg}`
                    ).join(', ');
                }
                // String detail
                else if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                }
                // Object detail
                else if (typeof data.detail === 'object') {
                    errorMessage = JSON.stringify(data.detail);
                }
            } else if (error?.message) {
                errorMessage = error.message;
            }

            toast.error(`Erreur: ${errorMessage}`);
        } finally {
            setSubmitting(false);
        }
    };

    const canProceedFromType = claimType !== null;
    const canProceedFromDetails = amount && description && incidentDate;
    const canSubmit = canProceedFromType && canProceedFromDetails;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-32">
            {/* Header */}
            <div className="p-6 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800">
                <button
                    onClick={() => step === 'type' ? router.back() : setStep('type')}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4 transition"
                >
                    <ArrowLeft className="w-5 h-5" />
                    <span className="font-medium">Retour</span>
                </button>

                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    Nouveau claim
                </h1>

                {/* Progress */}
                <div className="flex items-center gap-2 mt-4">
                    {(['type', 'details', 'photos', 'review'] as Step[]).map((s, index) => (
                        <React.Fragment key={s}>
                            <div className={`h-1.5 flex-1 rounded-full transition ${step === s ? 'bg-emerald-600' :
                                (s === 'type' || (s === 'details' && canProceedFromType) || (s === 'photos' && canProceedFromDetails))
                                    ? 'bg-emerald-200 dark:bg-emerald-900/40'
                                    : 'bg-gray-200 dark:bg-slate-800'
                                }`} />
                        </React.Fragment>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="p-6">
                {loadingPolicy ? (
                    <div className="flex flex-col items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-4" />
                        <p>Vérification de votre couverture...</p>
                    </div>
                ) : !activePolicy ? (
                    <div className="text-center py-12">
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 p-6 rounded-2xl border border-yellow-200 dark:border-yellow-800 mb-6">
                            <AlertTriangle className="w-12 h-12 text-yellow-600 dark:text-yellow-400 mx-auto mb-4" />
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Aucune police active</h3>
                            <p className="text-gray-600 dark:text-gray-400 mb-4">
                                Vous devez avoir une assurance active pour déclarer un sinistre.
                            </p>
                            <button
                                onClick={handleCreateTestPolicy}
                                className="bg-emerald-600 text-white px-6 py-2 rounded-xl"
                            >
                                Créer une Police (Test Mode)
                            </button>
                        </div>
                    </div>
                ) : (
                    <>
                        {step === 'type' && (
                            <div className="space-y-3">
                                <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                                    Type de sinistre
                                </h2>
                                {(Object.keys(CLAIM_TYPE_CONFIG) as ClaimType[]).map((type) => {
                                    const config = CLAIM_TYPE_CONFIG[type];
                                    const Icon = type === 'medical' ? Heart :
                                        type === 'accident' ? AlertTriangle :
                                            type === 'property' ? Home : FileText;

                                    return (
                                        <button
                                            key={type}
                                            onClick={() => setClaimType(type)}
                                            className={`w-full p-4 rounded-2xl border-2 transition text-left ${claimType === type
                                                ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-900/20'
                                                : 'border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-gray-300 dark:hover:border-slate-600'
                                                }`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={`w-12 h-12 rounded-xl ${config.bgColor} flex items-center justify-center ${config.color}`}>
                                                    <Icon className="w-6 h-6" />
                                                </div>
                                                <div className="flex-1">
                                                    <div className="font-bold text-gray-900 dark:text-white mb-1">
                                                        {config.label}
                                                    </div>
                                                    <div className="text-sm text-gray-500 dark:text-gray-400">
                                                        {config.description}
                                                    </div>
                                                </div>
                                                {claimType === type && (
                                                    <Check className="w-5 h-5 text-emerald-600" />
                                                )}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </>
                )}

                {step === 'details' && (
                    <div className="space-y-4">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                            Détails du sinistre
                        </h2>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Montant réclamé (XOF)
                            </label>
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                placeholder="Ex: 50000"
                                className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Date du sinistre
                            </label>
                            <input
                                type="date"
                                value={incidentDate}
                                onChange={(e) => setIncidentDate(e.target.value)}
                                max={new Date().toISOString().split('T')[0]}
                                className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Description
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                rows={4}
                                placeholder="Décrivez le sinistre en détail..."
                                className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
                            />
                        </div>
                    </div>
                )}

                {step === 'photos' && (
                    <div className="space-y-4">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                            Pièces justificatives
                        </h2>

                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Ajoutez des photos des reçus, prescriptions, ou dommages
                        </p>

                        {/* Photo Grid */}
                        <div className="grid grid-cols-2 gap-3">
                            {photos.map((photo, index) => (
                                <div key={index} className="relative aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-slate-800">
                                    <img src={photo} alt={`Photo ${index + 1}`} className="w-full h-full object-cover" />
                                    <button
                                        onClick={() => removePhoto(index)}
                                        className="absolute top-2 right-2 w-8 h-8 bg-red-600 hover:bg-red-700 text-white rounded-full flex items-center justify-center transition"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}

                            {/* Upload Button */}
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={uploading}
                                className="aspect-square border-2 border-dashed border-gray-300 dark:border-slate-700 rounded-xl bg-gray-50 dark:bg-slate-900 hover:bg-gray-100 dark:hover:bg-slate-800 transition flex flex-col items-center justify-center gap-2"
                            >
                                {uploading ? (
                                    <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
                                ) : (
                                    <>
                                        <Camera className="w-8 h-8 text-gray-400" />
                                        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                            Ajouter
                                        </span>
                                    </>
                                )}
                            </button>
                        </div>

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            multiple
                            onChange={handlePhotoUpload}
                            className="hidden"
                        />

                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
                            Vous pouvez aussi passer cette étape et soumettre sans photos
                        </p>
                    </div>
                )}

                {step === 'review' && claimType && (
                    <div className="space-y-4">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                            Vérification
                        </h2>

                        <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-gray-100 dark:border-slate-800 space-y-3">
                            <SummaryRow label="Type" value={CLAIM_TYPE_CONFIG[claimType].label} />
                            <SummaryRow label="Montant" value={`${parseInt(amount).toLocaleString()} XOF`} />
                            <SummaryRow label="Date" value={incidentDate} />
                            <SummaryRow label="Photos" value={`${photos.length} photo${photos.length !== 1 ? 's' : ''}`} />
                        </div>

                        <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-gray-100 dark:border-slate-800">
                            <h4 className="font-bold text-gray-900 dark:text-white mb-2">Description</h4>
                            <p className="text-gray-600 dark:text-gray-300 text-sm">
                                {description}
                            </p>
                        </div>

                        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
                            <p className="text-sm text-yellow-800 dark:text-yellow-300">
                                En soumettant ce claim, vous confirmez que les informations fournies sont exactes et véridiques.
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Footer Actions */}
            <div className="fixed bottom-0 left-0 right-0 px-6 pt-4 pb-12 bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800 shadow-lg">
                <div className="flex gap-3">
                    {step !== 'type' && (
                        <button
                            onClick={() => {
                                const steps: Step[] = ['type', 'details', 'photos', 'review'];
                                const currentIndex = steps.indexOf(step);
                                setStep(steps[currentIndex - 1]);
                            }}
                            className="px-6 py-3 bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-slate-700 transition"
                        >
                            Précédent
                        </button>
                    )}

                    <button
                        onClick={() => {
                            if (step === 'type' && canProceedFromType) setStep('details');
                            else if (step === 'details' && canProceedFromDetails) setStep('photos');
                            else if (step === 'photos') setStep('review');
                            else if (step === 'review') handleSubmit();
                        }}
                        disabled={
                            (step === 'type' && !canProceedFromType) ||
                            (step === 'details' && !canProceedFromDetails) ||
                            (step === 'review' && submitting)
                        }
                        className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white py-3 rounded-xl font-medium transition flex items-center justify-center gap-2"
                    >
                        {submitting ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Soumission...
                            </>
                        ) : step === 'review' ? (
                            'Soumettre le claim'
                        ) : (
                            'Suivant'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
            <span className="font-medium text-gray-900 dark:text-white">{value}</span>
        </div>
    );
}
