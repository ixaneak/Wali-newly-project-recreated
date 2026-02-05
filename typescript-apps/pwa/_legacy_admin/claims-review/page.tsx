'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { claimsService } from '@/lib/api-client';
import { formatCurrency, formatDateTime } from '@/lib/utils';

interface Claim {
    id: string;
    claim_number: string;
    user_id: string;
    policy_id: string;
    claim_type: string;
    status: string;
    description: string;
    claimed_amount: number;
    approved_amount?: number;
    fraud_score: number;
    fraud_flags: string[];
    image_urls: string[];
    created_at: string;
}

export default function ClaimsReviewPage() {
    const router = useRouter();
    const [claims, setClaims] = useState<Claim[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
    const [reviewData, setReviewData] = useState({
        status: 'approved',
        approvedAmount: '',
        notes: '',
    });

    useEffect(() => {
        loadClaims();
    }, []);

    const loadClaims = async () => {
        try {
            const response = await claimsService.getPendingClaims();
            setClaims(response.data || []);
        } catch (error) {
            console.error('Failed to load claims:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleReview = async (claimId: string) => {
        try {
            await claimsService.reviewClaim(claimId, {
                status: reviewData.status,
                approved_amount: reviewData.status === 'approved' ? parseInt(reviewData.approvedAmount) : 0,
                review_notes: reviewData.notes,
            });

            setSelectedClaim(null);
            loadClaims();
        } catch (error) {
            console.error('Failed to review claim:', error);
        }
    };

    const getRiskColor = (score: number) => {
        if (score >= 75) return 'text-red-600 bg-red-50';
        if (score >= 50) return 'text-orange-600 bg-orange-50';
        return 'text-green-600 bg-green-50';
    };

    const getRiskLabel = (score: number) => {
        if (score >= 75) return 'Critique';
        if (score >= 50) return 'Moyen';
        return 'Faible';
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Chargement...</p>
                </div>
            </div>
        );
    }

    if (selectedClaim) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="max-w-4xl mx-auto px-4">
                    <button
                        onClick={() => setSelectedClaim(null)}
                        className="mb-4 text-green-600 hover:text-green-700"
                    >
                        ← Retour à la liste
                    </button>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-2xl font-bold text-gray-800">{selectedClaim.claim_number}</h2>
                                <p className="text-gray-600">Type: {selectedClaim.claim_type}</p>
                            </div>
                            <span className={`px-4 py-2 rounded-full font-medium ${getRiskColor(selectedClaim.fraud_score)}`}>
                                Risque: {getRiskLabel(selectedClaim.fraud_score)} ({selectedClaim.fraud_score})
                            </span>
                        </div>

                        {/* Description */}
                        <div className="mb-6">
                            <h3 className="font-semibold mb-2">Description</h3>
                            <p className="text-gray-700">{selectedClaim.description}</p>
                        </div>

                        {/* Amount */}
                        <div className="mb-6">
                            <h3 className="font-semibold mb-2">Montant réclamé</h3>
                            <p className="text-2xl font-bold text-green-600">
                                {formatCurrency(selectedClaim.claimed_amount)}
                            </p>
                        </div>

                        {/* Fraud Flags */}
                        {selectedClaim.fraud_flags && selectedClaim.fraud_flags.length > 0 && (
                            <div className="mb-6">
                                <h3 className="font-semibold mb-2">🚩 Drapeaux de fraude</h3>
                                <div className="space-y-2">
                                    {selectedClaim.fraud_flags.map((flag, index) => (
                                        <div key={index} className="bg-red-50 text-red-700 px-4 py-2 rounded">
                                            {flag}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Images */}
                        <div className="mb-6">
                            <h3 className="font-semibold mb-2">Photos ({selectedClaim.image_urls?.length || 0})</h3>
                            <div className="grid grid-cols-3 gap-4">
                                {selectedClaim.image_urls?.map((url, index) => (
                                    <img
                                        key={index}
                                        src={url}
                                        alt={`Claim image ${index + 1}`}
                                        className="w-full h-48 object-cover rounded-lg cursor-pointer hover:opacity-80"
                                        onClick={() => window.open(url, '_blank')}
                                    />
                                ))}
                            </div>
                        </div>

                        {/* Review Form */}
                        <div className="border-t pt-6">
                            <h3 className="font-semibold mb-4">Décision</h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Statut
                                    </label>
                                    <select
                                        value={reviewData.status}
                                        onChange={(e) => setReviewData({ ...reviewData, status: e.target.value })}
                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                                    >
                                        <option value="approved">Approuvé</option>
                                        <option value="rejected">Rejeté</option>
                                    </select>
                                </div>

                                {reviewData.status === 'approved' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Montant approuvé (XOF)
                                        </label>
                                        <input
                                            type="number"
                                            value={reviewData.approvedAmount}
                                            onChange={(e) => setReviewData({ ...reviewData, approvedAmount: e.target.value })}
                                            placeholder={selectedClaim.claimed_amount.toString()}
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                                        />
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Notes
                                    </label>
                                    <textarea
                                        value={reviewData.notes}
                                        onChange={(e) => setReviewData({ ...reviewData, notes: e.target.value })}
                                        rows={4}
                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                                    />
                                </div>

                                <button
                                    onClick={() => handleReview(selectedClaim.id)}
                                    className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700"
                                >
                                    Soumettre la décision
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-green-600">Admin - Révision des Réclamations</h1>
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="text-gray-600 hover:text-gray-800"
                        >
                            ← Dashboard
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-xl font-bold text-gray-800">
                            Réclamations en attente ({claims.length})
                        </h2>
                    </div>

                    {claims.length === 0 ? (
                        <div className="px-6 py-12 text-center">
                            <p className="text-gray-500">Aucune réclamation en attente</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {claims.map((claim) => (
                                <div
                                    key={claim.id}
                                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                                    onClick={() => setSelectedClaim(claim)}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-3 mb-2">
                                                <h3 className="font-semibold text-gray-800">{claim.claim_number}</h3>
                                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskColor(claim.fraud_score)}`}>
                                                    Score: {claim.fraud_score}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-600 mb-2">{claim.description}</p>
                                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                                                <span>Type: {claim.claim_type}</span>
                                                <span>•</span>
                                                <span>Montant: {formatCurrency(claim.claimed_amount)}</span>
                                                <span>•</span>
                                                <span>{formatDateTime(claim.created_at)}</span>
                                            </div>
                                        </div>
                                        <div className="text-green-600">→</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
