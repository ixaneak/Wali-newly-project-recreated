"use client";

// ... imports
import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Heart, AlertTriangle, Home, FileText, Camera, X, Check, Loader2 } from 'lucide-react';
import { ClaimType, CLAIM_TYPE_CONFIG } from '@/types/claims';
import { claimsService, policyService } from '@/lib/api-client';
import { CoverageSubscription } from '@/types/app'; // New Import
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
    // Update state to CoverageSubscription
    const [activePolicy, setActivePolicy] = useState<CoverageSubscription | null>(null);
    const [userId, setUserId] = useState<string | null>(null);

    // Load active policy
    useEffect(() => {
        const loadPolicy = async () => {
            setLoadingPolicy(true);

            // Determine user ID: Firebase auth first, then localStorage fallback
            let uid: string | null = null;
            if (auth.currentUser) {
                uid = auth.currentUser.uid;
            } else {
                // Mock login fallback — use stored token to derive a user ID
                const storedToken = localStorage.getItem('wali_token');
                if (storedToken) {
                    uid = 'mock-user-001'; // Consistent with backend mock token
                }
            }

            if (!uid) {
                setLoadingPolicy(false);
                return;
            }

            setUserId(uid);

            try {
                const policies = await policyService.getUserPolicies(uid) as unknown as CoverageSubscription[];
                const active = policies.find((p) => p.status === 'active' || p.status === 'pending_payment');

                if (active) {
                    setActivePolicy(active);
                } else {
                    console.log("No active coverage found");
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
            if (auth.currentUser) {
                loadPolicy();
            } else {
                // Check localStorage fallback immediately too
                const storedToken = localStorage.getItem('wali_token');
                if (storedToken) {
                    loadPolicy();
                } else {
                    // Listen for Firebase auth state change
                    const unsubscribe = auth.onAuthStateChanged((user) => {
                        if (user) loadPolicy();
                        else setLoadingPolicy(false);
                    });
                    return () => unsubscribe();
                }
            }
        }, 500);
        return () => clearTimeout(timer);
    }, []);

    // Helper to create test policy (DEV ONLY)
    const handleCreateTestPolicy = async () => {
        const uid = userId || (auth.currentUser?.uid) || 'mock-user-001';
        try {
            toast.loading("Souscription d'une couverture test...");
            const result = await policyService.createPolicy({
                user_id: uid,
                planId: "NSIA-BASIC-01", // Product ID
                phone: "0000000000",
                isTest: true
            });
            // Use the returned enrollment directly (mock enrollments aren't persisted to DB)
            const enrollment = result as unknown as CoverageSubscription;
            if (enrollment) {
                setActivePolicy(enrollment);
            }
            toast.dismiss();
            toast.success("Couverture activée! Vous pouvez maintenant signaler un incident.");
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
            toast.error(`Erreur souscription: ${detailedError || e.message}`);
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

                // Compress image - COSUMAF Requirement: Low bandwidth optimization
                const options = {
                    maxSizeMB: 0.5,           // Strict 500KB limit
                    maxWidthOrHeight: 1920,   // Reasonable HD resolution
                    useWebWorker: true,
                    initialQuality: 0.7,      // Aggressive initial quality for smaller size
                    alwaysKeepResolution: true // Try to keep resolution if possible within size limit
                };

                let compressed;
                try {
                    compressed = await imageCompression(file, options);
                    console.log(`Original: ${(file.size / 1024 / 1024).toFixed(2)}MB, Compressed: ${(compressed.size / 1024 / 1024).toFixed(2)}MB`);
                } catch (e) {
                    console.warn("Compression failed, using original", e);
                    compressed = file;
                }

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
                type: claimType, // Changed from claim_type
                reported_amount: parseFloat(amount), // Changed from amount
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
                    <div key="loading" className="flex flex-col items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-4" />
                        <p>Vérification de votre couverture...</p>
                    </div>
                ) : !activePolicy ? (
                    <div key="no-policy" className="text-center py-12">
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 p-6 rounded-2xl border border-yellow-200 dark:border-yellow-800 mb-6">
                            <AlertTriangle className="w-12 h-12 text-yellow-600 dark:text-yellow-400 mx-auto mb-4" />
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Aucune couverture active</h3>
                            <p className="text-gray-600 dark:text-gray-400 mb-4">
                                Vous devez avoir une couverture active pour signaler un incident.
                            </p>
                            <button
                                onClick={handleCreateTestPolicy}
                                className="bg-emerald-600 text-white px-6 py-2 rounded-xl"
                            >
                                Souscrire une couverture (Test)
                            </button>
                        </div>
                    </div>
                ) : (
                    <div key="form">
                        {step === 'type' && (
                            <div className="space-y-3">
                                <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                                    Type d'incident
                                </h2>
                                {(Object.keys(CLAIM_TYPE_CONFIG) as ClaimType[]).map((type) => {
                                    const config = CLAIM_TYPE_CONFIG[type];

                                    const Icon = {
                                        Heart,
                                        AlertTriangle,
                                        Home,
                                        FileText
                                    }[config.icon] || FileText;

                                    return (
                                        <button
                                            key={type}
                                            onClick={() => {
                                                setClaimType(type);
                                                setStep('details');
                                            }}
                                            className={`w-full p-4 rounded-xl border-2 text-left transition-all flex items-center gap-4 ${claimType === type
                                                ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                                                : 'border-transparent bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700'
                                                }`}
                                        >
                                            <div className={`p-3 rounded-lg ${claimType === type ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400' : 'bg-white dark:bg-slate-700 text-gray-500 dark:text-gray-400'
                                                }`}>
                                                <Icon className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-gray-900 dark:text-white">
                                                    {config.label}
                                                </h3>
                                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                                    {config.description}
                                                </p>
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {step === 'details' && (
                    <div className="space-y-4">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                            Détails de l'incident
                        </h2>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Montant estimé (XOF)
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
                                Date de l'incident
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
                                placeholder="Décrivez l'incident en détail..."
                                className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
                            />
                        </div>
                    </div>
                )}

                {step === 'photos' && (
                    <div className="space-y-4">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                            Photos de l'incident
                        </h2>

                        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl flex gap-3 items-start mb-4">
                            <Camera className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-blue-800 dark:text-blue-200">
                                Ajoutez des photos claires de l'incident (max 3).
                                Elles seront compressées automatiquement.
                            </p>
                        </div>

                        {/* Photo Grid */}
                        <div className="grid grid-cols-2 gap-3 mb-4">
                            {photos.map((photo, index) => (
                                <div key={index} className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden border border-gray-200 dark:border-slate-700">
                                    <img src={photo} alt={`Preuve ${index + 1}`} className="w-full h-full object-cover" />
                                    <button
                                        onClick={() => removePhoto(index)}
                                        className="absolute top-1 right-1 p-1 bg-black/50 text-white rounded-full hover:bg-red-500 transition"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>
                            ))}

                            {/* Add Button */}
                            {photos.length < 3 && (
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={uploading}
                                    className="aspect-video flex flex-col items-center justify-center bg-gray-50 dark:bg-slate-800 border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition"
                                >
                                    {uploading ? (
                                        <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
                                    ) : (
                                        <>
                                            <Camera className="w-6 h-6 text-gray-400 mb-1" />
                                            <span className="text-xs text-gray-500">Ajouter</span>
                                        </>
                                    )}
                                </button>
                            )}
                        </div>

                        <input
                            type="file"
                            ref={fileInputRef}
                            accept="image/*"
                            multiple
                            className="hidden"
                            onChange={handlePhotoUpload}
                        />
                    </div>
                )}

                {step === 'review' && claimType && (
                    <div className="space-y-4">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                            Vérification
                        </h2>

                        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
                            <p className="text-sm text-yellow-800 dark:text-yellow-300">
                                En signalant cet incident, vous confirmez que les informations fournies sont exactes et véridiques.
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Footer Actions */}
            <div className="fixed bottom-0 left-0 right-0 px-6 pt-4 pb-12 bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800 shadow-lg">
                <div className="flex gap-3">

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
                                Envoi en cours...
                            </>
                        ) : step === 'review' ? (
                            'Signaler l\'incident'
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
