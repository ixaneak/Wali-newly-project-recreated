'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { policyService, claimsService } from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';

interface Policy {
    id: string;
    policy_number: string;
    coverage_type: string;
    status: string;
}

export default function NewClaimPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [policies, setPolicies] = useState<Policy[]>([]);
    const [selectedPolicyId, setSelectedPolicyId] = useState('');
    const [amount, setAmount] = useState('');
    const [description, setDescription] = useState('');
    const [files, setFiles] = useState<FileList | null>(null);
    const [error, setError] = useState('');

    useEffect(() => {
        const userId = localStorage.getItem('user_id');
        if (!userId) {
            router.push('/login');
            return;
        }

        // Load active policies
        policyService.getUserPolicies(userId)
            .then(res => {
                const active = res.data.filter((p: any) => p.status === 'active');
                setPolicies(active);
            })
            .catch(err => console.error("Failed to load policies", err));
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const userId = localStorage.getItem('user_id');
        if (!userId || !selectedPolicyId) return;

        try {
            const policy = policies.find(p => p.id === selectedPolicyId);
            if (!policy) throw new Error("Policy not found");

            const formData = new FormData();
            formData.append('user_id', userId);
            formData.append('policy_id', selectedPolicyId);
            formData.append('claim_type', policy.coverage_type);
            formData.append('description', description);
            formData.append('claimed_amount', amount);

            if (files) {
                for (let i = 0; i < files.length; i++) {
                    formData.append('images', files[i]);
                }
            }

            await claimsService.submitClaim(formData);

            // Redirect to dashboard with success (or claims list if we had one)
            alert('Réclamation soumise avec succès!');
            router.push('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Une erreur est survenue');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-xl mx-auto">
                <div className="bg-white rounded-lg shadow px-6 py-8">
                    <h1 className="text-2xl font-bold text-gray-900 mb-6">Déclarer un Sinistre</h1>

                    {error && (
                        <div className="bg-red-50 text-red-700 p-4 rounded mb-6 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Policy Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Contrat d'assurance</label>
                            <select
                                required
                                value={selectedPolicyId}
                                onChange={(e) => setSelectedPolicyId(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 py-2 px-3 border"
                            >
                                <option value="">Sélectionner un contrat actif</option>
                                {policies.map(p => (
                                    <option key={p.id} value={p.id}>
                                        {p.policy_number} ({p.coverage_type})
                                    </option>
                                ))}
                            </select>
                            {policies.length === 0 && (
                                <p className="mt-2 text-sm text-yellow-600">
                                    Aucun contrat actif trouvé. Veuillez d'abord souscrire une assurance.
                                </p>
                            )}
                        </div>

                        {/* Amount */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Montant réclamé (XOF)</label>
                            <input
                                type="number"
                                required
                                min="1000"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 py-2 px-3 border"
                                placeholder="ex: 50000"
                            />
                        </div>

                        {/* Description */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Description de l'incident</label>
                            <textarea
                                required
                                rows={4}
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 py-2 px-3 border"
                                placeholder="Décrivez ce qui s'est passé..."
                            />
                        </div>

                        {/* Evidence Upload */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Preuves (Photos, Documents)</label>
                            <input
                                type="file"
                                required
                                multiple
                                accept="image/*"
                                onChange={(e) => setFiles(e.target.files)}
                                className="mt-1 block w-full text-sm text-gray-500
                                    file:mr-4 file:py-2 file:px-4
                                    file:rounded-full file:border-0
                                    file:text-sm file:font-semibold
                                    file:bg-green-50 file:text-green-700
                                    hover:file:bg-green-100"
                            />
                            <p className="mt-1 text-xs text-gray-500">JPG ou PNG, max 5MB par fichier.</p>
                        </div>

                        {/* Submit Button */}
                        <div className="pt-4">
                            <button
                                type="submit"
                                disabled={loading || policies.length === 0}
                                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white 
                                    ${loading || policies.length === 0 ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'}`}
                            >
                                {loading ? 'Envoi en cours...' : 'Soumettre la demande'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
