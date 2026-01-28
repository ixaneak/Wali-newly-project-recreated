'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { claimsService } from '@/lib/api-client';
import { formatCurrency } from '@/lib/utils';

export default function NewClaimPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [images, setImages] = useState<File[]>([]);
    const [imagePreviews, setImagePreviews] = useState<string[]>([]);

    const [formData, setFormData] = useState({
        policyId: '',
        claimType: 'health',
        description: '',
        claimedAmount: '',
    });

    const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);

        if (images.length + files.length > 5) {
            setError('Maximum 5 images');
            return;
        }

        // Validate file sizes
        for (const file of files) {
            if (file.size > 5 * 1024 * 1024) {
                setError(`Image ${file.name} dépasse 5MB`);
                return;
            }
        }

        setImages([...images, ...files]);

        // Create previews
        files.forEach(file => {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreviews(prev => [...prev, reader.result as string]);
            };
            reader.readAsDataURL(file);
        });
    };

    const removeImage = (index: number) => {
        setImages(images.filter((_, i) => i !== index));
        setImagePreviews(imagePreviews.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const userId = localStorage.getItem('user_id') || 'temp-user';

            const formDataToSend = new FormData();
            formDataToSend.append('user_id', userId);
            formDataToSend.append('policy_id', formData.policyId);
            formDataToSend.append('claim_type', formData.claimType);
            formDataToSend.append('description', formData.description);
            formDataToSend.append('claimed_amount', formData.claimedAmount);

            images.forEach((image, index) => {
                formDataToSend.append('images', image);
            });

            const response = await claimsService.submitClaim(formDataToSend);

            if (response.data.fraud_score > 50) {
                alert(`Attention: Cette réclamation a été marquée pour examen (score de fraude: ${response.data.fraud_score})`);
            }

            router.push('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Erreur lors de la soumission');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-3xl mx-auto px-4">
                <h1 className="text-3xl font-bold text-gray-800 mb-8">Nouvelle Réclamation</h1>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Policy Selection */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Numéro de police
                        </label>
                        <input
                            type="text"
                            value={formData.policyId}
                            onChange={(e) => setFormData({ ...formData, policyId: e.target.value })}
                            placeholder="WLI-20260127-000001"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                            required
                        />
                    </div>

                    {/* Claim Type */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Type de réclamation
                        </label>
                        <select
                            value={formData.claimType}
                            onChange={(e) => setFormData({ ...formData, claimType: e.target.value })}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                        >
                            <option value="health">Santé</option>
                            <option value="equipment">Équipement</option>
                            <option value="theft">Vol</option>
                        </select>
                    </div>

                    {/* Description */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Description
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            placeholder="Décrivez votre réclamation..."
                            rows={4}
                            maxLength={500}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                            required
                        />
                        <div className="text-right text-sm text-gray-500 mt-1">
                            {formData.description.length}/500
                        </div>
                    </div>

                    {/* Claimed Amount */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Montant réclamé (XOF)
                        </label>
                        <input
                            type="number"
                            value={formData.claimedAmount}
                            onChange={(e) => setFormData({ ...formData, claimedAmount: e.target.value })}
                            placeholder="5000"
                            min="0"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                            required
                        />
                    </div>

                    {/* Image Upload */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Photos (max 5, 5MB chacune)
                        </label>

                        <input
                            type="file"
                            accept="image/jpeg,image/png"
                            multiple
                            onChange={handleImageSelect}
                            className="hidden"
                            id="image-upload"
                        />

                        <label
                            htmlFor="image-upload"
                            className="block w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-green-500 transition"
                        >
                            <div className="text-4xl mb-2">📸</div>
                            <div className="text-gray-600">Cliquez pour ajouter des photos</div>
                            <div className="text-sm text-gray-500 mt-1">JPG ou PNG, max 5MB</div>
                        </label>

                        {imagePreviews.length > 0 && (
                            <div className="grid grid-cols-3 gap-4 mt-4">
                                {imagePreviews.map((preview, index) => (
                                    <div key={index} className="relative">
                                        <img
                                            src={preview}
                                            alt={`Preview ${index + 1}`}
                                            className="w-full h-32 object-cover rounded-lg"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => removeImage(index)}
                                            className="absolute top-2 right-2 bg-red-500 text-white w-6 h-6 rounded-full hover:bg-red-600"
                                        >
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {error && (
                        <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg">
                            {error}
                        </div>
                    )}

                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="font-medium text-yellow-800 mb-2">⚠️ Important</div>
                        <ul className="text-sm text-yellow-700 space-y-1">
                            <li>• Les photos doivent être prises dans les 24 heures</li>
                            <li>• Les captures d'écran seront rejetées</li>
                            <li>• La localisation GPS sera vérifiée</li>
                        </ul>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || images.length === 0}
                        className="w-full bg-green-600 text-white py-4 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Envoi...' : 'Soumettre la réclamation'}
                    </button>
                </form>
            </div>
        </div>
    );
}
