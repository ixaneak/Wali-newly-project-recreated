"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Camera, User, Phone, MapPin, Mail, Save } from 'lucide-react';
import { toast } from 'sonner';

export default function EditProfilePage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    // Initial State (Mock Data)
    const [formData, setFormData] = useState({
        name: 'Amadou Koné',
        phone: '07 07 07 07 07',
        email: 'amadou.kone@example.com',
        address: 'Cocody, Abidjan',
        city: 'Abidjan',
        avatar: 'https://i.pravatar.cc/150?u=amadou'
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        // Simulate API Update
        setTimeout(() => {
            setLoading(false);
            toast.success('Profil mis à jour avec succès');

            // In a real app, we would re-fetch user data here or update global state
            setTimeout(() => router.back(), 1000);
        }, 1500);
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-20">
            {/* Header */}
            <div className="bg-white dark:bg-slate-900 sticky top-0 z-10 border-b border-gray-100 dark:border-slate-800">
                <div className="p-4 flex items-center justify-between">
                    <button
                        onClick={() => router.back()}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full text-gray-600 dark:text-gray-400 transition"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <h1 className="text-lg font-bold text-gray-900 dark:text-white">Modifier le profil</h1>
                    <div className="w-10" /> {/* Spacer */}
                </div>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">

                {/* Avatar Upload */}
                <div className="flex flex-col items-center">
                    <div className="relative">
                        <div className="w-28 h-28 rounded-full overflow-hidden border-4 border-white dark:border-slate-800 shadow-lg">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={formData.avatar} alt="Avatar" className="w-full h-full object-cover" />
                        </div>
                        <button
                            type="button"
                            className="absolute bottom-0 right-0 p-2 bg-emerald-600 text-white rounded-full shadow-md hover:bg-emerald-700 transition"
                        >
                            <Camera className="w-4 h-4" />
                        </button>
                    </div>
                    <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                        Appuyez pour changer la photo
                    </p>
                </div>

                {/* Form Fields */}
                <div className="space-y-4">

                    {/* Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nom complet</label>
                        <div className="relative">
                            <span className="absolute left-4 top-3.5 text-gray-400">
                                <User className="w-5 h-5" />
                            </span>
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition dark:text-white"
                                placeholder="Votre nom"
                                required
                            />
                        </div>
                    </div>

                    {/* Phone (Read Only) */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Numéro de téléphone
                            <span className="text-xs font-normal text-emerald-600 ml-2">(Vérifié)</span>
                        </label>
                        <div className="relative opacity-70">
                            <span className="absolute left-4 top-3.5 text-gray-400">
                                <Phone className="w-5 h-5" />
                            </span>
                            <input
                                type="tel"
                                name="phone"
                                value={formData.phone}
                                readOnly
                                className="w-full pl-12 pr-4 py-3 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-600 dark:text-gray-400 cursor-not-allowed"
                            />
                        </div>
                        <p className="text-xs text-gray-400 mt-1 ml-1">
                            Pour changer de numéro, contactez le support.
                        </p>
                    </div>

                    {/* Email */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email</label>
                        <div className="relative">
                            <span className="absolute left-4 top-3.5 text-gray-400">
                                <Mail className="w-5 h-5" />
                            </span>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition dark:text-white"
                                placeholder="votre@email.com"
                            />
                        </div>
                    </div>

                    {/* Address */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Adresse</label>
                        <div className="relative">
                            <span className="absolute left-4 top-3.5 text-gray-400">
                                <MapPin className="w-5 h-5" />
                            </span>
                            <input
                                type="text"
                                name="address"
                                value={formData.address}
                                onChange={handleChange}
                                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition dark:text-white"
                                placeholder="Quartier, Ville"
                            />
                        </div>
                    </div>
                </div>

                {/* Submit Button */}
                <div className="pt-4">
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg shadow-emerald-200 dark:shadow-emerald-900/20 active:scale-[0.98] transition flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <Save className="w-5 h-5" />
                                Enregistrer les modifications
                            </>
                        )}
                    </button>
                </div>

            </form>
        </div>
    );
}
