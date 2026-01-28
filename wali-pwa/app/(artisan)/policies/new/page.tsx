'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { policyService, paymentService } from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';

const COVERAGE_TYPES = [
    { value: 'health', label: 'Santé', icon: '🏥', description: 'Consultations, médicaments, hospitalisation' },
    { value: 'equipment', label: 'Équipement', icon: '🔧', description: 'Outils et matériel professionnel' },
    { value: 'theft', label: 'Vol', icon: '🔒', description: 'Protection contre le vol' },
    { value: 'bundle', label: 'Pack Complet', icon: '📦', description: 'Santé + Équipement + Vol' },
];

const PAYMENT_FREQUENCIES = [
    { value: 'daily', label: 'Journalier', multiplier: 1 },
    { value: 'weekly', label: 'Hebdomadaire', multiplier: 7 },
    { value: 'monthly', label: 'Mensuel', multiplier: 30 },
];

const REGIONS = [
    'Abidjan', 'Yamoussoukro', 'Bouaké', 'Daloa', 'San-Pédro',
    'Korhogo', 'Man', 'Gagnoa', 'Divo', 'Abengourou'
];

export default function NewPolicyPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [formData, setFormData] = useState({
        coverageType: 'health',
        maxCoverage: 50000,
        paymentFrequency: 'monthly',
        region: 'Abidjan',
    });

    const [calculatedPremium, setCalculatedPremium] = useState(0);
    const [policyId, setPolicyId] = useState('');

    const calculatePremium = () => {
        const baseRates: Record<string, number> = {
            health: 150,
            equipment: 200,
            theft: 100,
            bundle: 400,
        };

        const regionMultipliers: Record<string, number> = {
            'Abidjan': 1.2,
            'Yamoussoukro': 1.0,
            'Bouaké': 1.1,
            'Daloa': 1.0,
            'San-Pédro': 1.15,
            'default': 1.0,
        };

        const base = baseRates[formData.coverageType] || 150;
        const regionMult = regionMultipliers[formData.region] || regionMultipliers['default'];
        const coverageMult = formData.maxCoverage / 50000;

        const monthlyPremium = Math.round(base * regionMult * coverageMult);
        setCalculatedPremium(monthlyPremium);
    };

    const handleCreatePolicy = async () => {
        setLoading(true);
        setError('');

        try {
            const userId = localStorage.getItem('user_id') || 'temp-user';
            const response = await policyService.createPolicy({
                user_id: userId,
                coverage_type: formData.coverageType,
                coverage_details: { max_coverage_amount: formData.maxCoverage },
                payment_frequency: formData.paymentFrequency,
                region: formData.region,
            });

            setPolicyId(response.data.id);
            setStep(2);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Erreur lors de la création de la police');
        } finally {
            setLoading(false);
        }
    };

    const handlePayment = async (provider: 'orange' | 'mtn' | 'wave') => {
        setLoading(true);
        setError('');

        try {
            const userId = localStorage.getItem('user_id') || 'temp-user';
            const phone = localStorage.getItem('user_phone') || '+2250123456789';

            const response = await paymentService.initiatePayment({
                user_id: userId,
                policy_id: policyId,
                amount: calculatedPremium,
                phone: phone,
                provider: provider,
            });

            setStep(3);
            // Poll for payment status (simplified)
            setTimeout(() => {
                router.push('/dashboard');
            }, 3000);
        } catch (err: any) {
            setError(err.response?.data?.message || 'Erreur lors du paiement');
        } finally {
            setLoading(false);
        }
    };

    if (step === 1) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="max-w-3xl mx-auto px-4">
                    <h1 className="text-3xl font-bold text-gray-800 mb-8">Nouvelle Police d'Assurance</h1>

                    {/* Coverage Type */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-semibold mb-4">1. Type de couverture</h2>
                        <div className="grid grid-cols-2 gap-4">
                            {COVERAGE_TYPES.map((type) => (
                                <button
                                    key={type.value}
                                    onClick={() => setFormData({ ...formData, coverageType: type.value })}
                                    className={`p-4 border-2 rounded-lg text-left transition ${formData.coverageType === type.value
                                            ? 'border-green-600 bg-green-50'
                                            : 'border-gray-200 hover:border-green-300'
                                        }`}
                                >
                                    <div className="text-3xl mb-2">{type.icon}</div>
                                    <div className="font-semibold">{type.label}</div>
                                    <div className="text-sm text-gray-600">{type.description}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Coverage Amount */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-semibold mb-4">2. Montant maximum</h2>
                        <div className="space-y-4">
                            <input
                                type="range"
                                min="25000"
                                max="200000"
                                step="25000"
                                value={formData.maxCoverage}
                                onChange={(e) => setFormData({ ...formData, maxCoverage: parseInt(e.target.value) })}
                                className="w-full"
                            />
                            <div className="text-center text-2xl font-bold text-green-600">
                                {formatCurrency(formData.maxCoverage)}
                            </div>
                        </div>
                    </div>

                    {/* Payment Frequency */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-semibold mb-4">3. Fréquence de paiement</h2>
                        <div className="grid grid-cols-3 gap-4">
                            {PAYMENT_FREQUENCIES.map((freq) => (
                                <button
                                    key={freq.value}
                                    onClick={() => setFormData({ ...formData, paymentFrequency: freq.value })}
                                    className={`p-4 border-2 rounded-lg transition ${formData.paymentFrequency === freq.value
                                            ? 'border-green-600 bg-green-50'
                                            : 'border-gray-200 hover:border-green-300'
                                        }`}
                                >
                                    <div className="font-semibold">{freq.label}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Region */}
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-semibold mb-4">4. Région</h2>
                        <select
                            value={formData.region}
                            onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                        >
                            {REGIONS.map((region) => (
                                <option key={region} value={region}>{region}</option>
                            ))}
                        </select>
                    </div>

                    {/* Premium Calculation */}
                    <div className="bg-green-50 rounded-lg p-6 mb-6">
                        <button
                            onClick={calculatePremium}
                            className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 mb-4"
                        >
                            Calculer la prime
                        </button>
                        {calculatedPremium > 0 && (
                            <div className="text-center">
                                <div className="text-gray-600 mb-2">Prime mensuelle</div>
                                <div className="text-4xl font-bold text-green-600">
                                    {formatCurrency(calculatedPremium)}
                                </div>
                            </div>
                        )}
                    </div>

                    {error && (
                        <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-6">
                            {error}
                        </div>
                    )}

                    <button
                        onClick={handleCreatePolicy}
                        disabled={loading || calculatedPremium === 0}
                        className="w-full bg-green-600 text-white py-4 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Création...' : 'Continuer vers le paiement'}
                    </button>
                </div>
            </div>
        );
    }

    if (step === 2) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="max-w-2xl mx-auto px-4">
                    <h1 className="text-3xl font-bold text-gray-800 mb-8">Choisissez votre mode de paiement</h1>

                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <div className="text-center mb-6">
                            <div className="text-gray-600">Montant à payer</div>
                            <div className="text-4xl font-bold text-green-600">
                                {formatCurrency(calculatedPremium)}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <button
                                onClick={() => handlePayment('orange')}
                                disabled={loading}
                                className="w-full flex items-center justify-between p-4 border-2 border-orange-500 rounded-lg hover:bg-orange-50 transition"
                            >
                                <div className="flex items-center">
                                    <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold mr-4">
                                        OM
                                    </div>
                                    <div className="text-left">
                                        <div className="font-semibold">Orange Money</div>
                                        <div className="text-sm text-gray-600">Paiement instantané</div>
                                    </div>
                                </div>
                                <div className="text-orange-600">→</div>
                            </button>

                            <button
                                onClick={() => handlePayment('mtn')}
                                disabled={loading}
                                className="w-full flex items-center justify-between p-4 border-2 border-yellow-500 rounded-lg hover:bg-yellow-50 transition"
                            >
                                <div className="flex items-center">
                                    <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center text-white font-bold mr-4">
                                        MM
                                    </div>
                                    <div className="text-left">
                                        <div className="font-semibold">MTN MoMo</div>
                                        <div className="text-sm text-gray-600">Paiement sécurisé</div>
                                    </div>
                                </div>
                                <div className="text-yellow-600">→</div>
                            </button>

                            <button
                                onClick={() => handlePayment('wave')}
                                disabled={loading}
                                className="w-full flex items-center justify-between p-4 border-2 border-blue-500 rounded-lg hover:bg-blue-50 transition"
                            >
                                <div className="flex items-center">
                                    <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold mr-4">
                                        W
                                    </div>
                                    <div className="text-left">
                                        <div className="font-semibold">Wave</div>
                                        <div className="text-sm text-gray-600">Sans frais</div>
                                    </div>
                                </div>
                                <div className="text-blue-600">→</div>
                            </button>
                        </div>

                        {error && (
                            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mt-6">
                                {error}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
                <div className="text-6xl mb-4">✅</div>
                <h1 className="text-3xl font-bold text-green-600 mb-2">Paiement en cours...</h1>
                <p className="text-gray-600">Vous serez redirigé vers le tableau de bord</p>
            </div>
        </div>
    );
}
