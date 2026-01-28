"use client";

import React from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Calendar, DollarSign, FileText, Image as ImageIcon, Phone } from 'lucide-react';
import { MOCK_CLAIMS } from '@/lib/mock-claims';
import { CLAIM_TYPE_CONFIG } from '@/types/claims';
import ClaimStatusBadge from '@/components/claims/ClaimStatusBadge';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

export default function ClaimDetailsPage() {
    const router = useRouter();
    const params = useParams();
    const claimId = params?.id as string;

    const claim = MOCK_CLAIMS.find(c => c.id === claimId);

    if (!claim) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center p-6">
                <div className="text-center">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Claim non trouvé</h2>
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

    const typeConfig = CLAIM_TYPE_CONFIG[claim.type];

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-24">
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
                        <ClaimStatusBadge status={claim.status} />
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
                {/* Amount Card */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-100 dark:border-slate-800">
                    <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-2">
                        <DollarSign className="w-4 h-4" />
                        <span className="text-sm font-medium">Montant réclamé</span>
                    </div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white">
                        {claim.amount.toLocaleString()} <span className="text-xl text-gray-400">XOF</span>
                    </div>
                </div>

                {/* Details Card */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-100 dark:border-slate-800">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-4">Détails</h3>

                    <div className="space-y-4">
                        <DetailRow
                            icon={Calendar}
                            label="Date du sinistre"
                            value={format(new Date(claim.incidentDate), 'dd MMMM yyyy', { locale: fr })}
                        />
                        <DetailRow
                            icon={FileText}
                            label="Date de soumission"
                            value={format(new Date(claim.createdAt), 'dd MMMM yyyy à HH:mm', { locale: fr })}
                        />
                        <DetailRow
                            icon={FileText}
                            label="ID du claim"
                            value={claim.id}
                            mono
                        />
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
                                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                                        <ImageIcon className="w-12 h-12" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Review Notes */}
                {claim.reviewNotes && (
                    <div className={`rounded-2xl p-6 border ${claim.status === 'rejected'
                        ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                        : 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800'
                        }`}>
                        <h3 className={`font-bold mb-2 ${claim.status === 'rejected'
                            ? 'text-red-900 dark:text-red-400'
                            : 'text-emerald-900 dark:text-emerald-400'
                            }`}>
                            {claim.status === 'rejected' ? 'Motif du rejet' : 'Notes de révision'}
                        </h3>
                        <p className={
                            claim.status === 'rejected'
                                ? 'text-red-700 dark:text-red-300'
                                : 'text-emerald-700 dark:text-emerald-300'
                        }>
                            {claim.reviewNotes}
                        </p>
                        {claim.reviewedAt && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                Révisé le {format(new Date(claim.reviewedAt), 'dd MMM yyyy', { locale: fr })}
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
