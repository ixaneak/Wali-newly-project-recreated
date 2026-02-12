"use client";

// ... imports
import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Calendar, DollarSign, FileText, Image as ImageIcon, Phone } from 'lucide-react';
import { CLAIM_TYPE_CONFIG, ClaimType, ClaimStatus } from '@/types/claims';
import ClaimStatusBadge from '@/components/claims/ClaimStatusBadge';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { claimsService } from '@/lib/api-client';
import type { IncidentReport, IncidentStatus } from '@/types/app'; // Update imports

export default function ClaimDetailsPage() {
    const router = useRouter();
    const params = useParams();
    const claimId = params?.id as string;

    // Update state to IncidentReport
    const [claim, setClaim] = useState<IncidentReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchClaim = async () => {
            try {
                setLoading(true);
                const data = await claimsService.getClaimById(claimId);
                setClaim(data);
            } catch (err: any) {
                console.error('Error fetching claim:', err);
                setError(err?.response?.data?.detail || 'Failed to load claim');
            } finally {
                setLoading(false);
            }
        };

        if (claimId) {
            fetchClaim();
        }
    }, [claimId]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center p-6">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
                    <p className="text-gray-600 dark:text-gray-400">Chargement...</p>
                </div>
            </div>
        );
    }

    if (error || !claim) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center p-6">
                <div className="text-center">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Incident non trouvé</h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
                    <button
                        onClick={() => router.back()}
                        className="text-emerald-600 hover:text-emerald-700"
                    >
                        Retour
                    </button>
                </div>
            </div>
        );
    }

    // Map IncidentReport type to ClaimType config
    const typeConfig = CLAIM_TYPE_CONFIG[claim.type as ClaimType] || CLAIM_TYPE_CONFIG.other;

    // Map IncidentStatus to Legacy ClaimStatus
    const legacyStatus: ClaimStatus = (
        claim.status === 'partner_resolved' ? 'approved' :
            claim.status === 'partner_reviewing' ? 'under_review' :
                'submitted'
    );

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-32">
            {/* Header */}
            <div className="p-6 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4 transition"
                >
                    <ArrowLeft className="w-5 h-5" />
                    <span className="font-medium">Retour</span>
                </button>

                <div className="flex items-start gap-4 mb-4">
                    <div className={`w-14 h-14 rounded-xl ${typeConfig.bgColor} flex items-center justify-center ${typeConfig.color}`}>
                        <FileText className="w-7 h-7" />
                    </div>
                    <div className="flex-1">
                        <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                            {typeConfig.label}
                        </h1>
                        <ClaimStatusBadge status={legacyStatus} />
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
                {/* Amount Card */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-2">
                        <DollarSign className="w-4 h-4" />
                        <span className="text-sm font-medium">Montant déclaré</span>
                    </div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white">
                        {claim.reported_amount.toLocaleString()} <span className="text-xl text-gray-400">XOF</span>
                    </div>
                </div>

                {/* Details Card */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-100 dark:border-slate-800">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-4">Détails</h3>

                    <div className="space-y-4">
                        <DetailRow
                            icon={Calendar}
                            label="Date de l'incident"
                            value={format(new Date(claim.incident_date), 'dd MMMM yyyy', { locale: fr })}
                        />
                        <DetailRow
                            icon={FileText}
                            label="Date de soumission"
                            value={format(new Date(claim.created_at), 'dd MMMM yyyy à HH:mm', { locale: fr })}
                        />
                        <DetailRow
                            icon={FileText}
                            label="Référence incident"
                            value={claim.id}
                            mono
                        />
                        {claim.partner_reference && (
                            <DetailRow
                                icon={FileText}
                                label="Référence partenaire (NSIA)"
                                value={claim.partner_reference}
                                mono
                            />
                        )}
                    </div>
                </div>

                {/* Description */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-100 dark:border-slate-800">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-3">Description</h3>
                    <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                        {claim.description}
                    </p>
                </div>

                {/* Photos */}
                {claim.photos && claim.photos.length > 0 && (
                    <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-100 dark:border-slate-800">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                            <ImageIcon className="w-5 h-5" />
                            Pièces jointes ({claim.photos.length})
                        </h3>
                        <div className="grid grid-cols-2 gap-3">
                            {claim.photos.map((photo, index) => (
                                <div
                                    key={index}
                                    className="aspect-square bg-gray-100 dark:bg-slate-800 rounded-xl overflow-hidden"
                                >
                                    {/* Handle both URL strings and potentially objects if API changes, though types say string[] */}
                                    <img
                                        src={photo}
                                        alt={`Preuve ${index + 1}`}
                                        className="w-full h-full object-cover"
                                        onError={(e) => {
                                            // Fallback if image fails to load
                                            (e.target as HTMLImageElement).src = `https://placehold.co/600x600?text=Image+${index + 1}`;
                                        }}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Review Notes */}
                {claim.partner_notes && (
                    <div className="rounded-2xl p-6 border bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800">
                        <h3 className="font-bold mb-2 text-emerald-900 dark:text-emerald-400">
                            Notes de l'assureur
                        </h3>
                        <p className="text-emerald-700 dark:text-emerald-300">
                            {claim.partner_notes}
                        </p>
                        {claim.resolved_at && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                Résolu le {format(new Date(claim.resolved_at), 'dd MMM yyyy', { locale: fr })}
                            </p>
                        )}
                    </div>
                )}

                {/* Contact Support */}
                <button
                    onClick={() => router.push('/dashboard/support')}
                    className="w-full bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-900 dark:text-white py-3.5 rounded-xl font-medium transition flex items-center justify-center gap-2"
                >
                    <Phone className="w-4 h-4" />
                    Contacter le support
                </button>
            </div>
        </div>
    );
}

function DetailRow({ icon: Icon, label, value, mono = false }: { icon: any; label: string; value: string; mono?: boolean }) {
    return (
        <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-gray-50 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
                <Icon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            </div>
            <div className="flex-1">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-0.5">{label}</div>
                <div className={`font-medium text-gray-900 dark:text-white ${mono ? 'font-mono text-sm' : ''}`}>
                    {value}
                </div>
            </div>
        </div>
    );
}
