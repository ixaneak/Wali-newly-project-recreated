"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Phone, Mail, User, MapPin, Users, Plus, X, Check, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface EmergencyContact {
    id: string;
    name: string;
    phone: string;
    relationship: string;
}

interface Beneficiary {
    id: string;
    name: string;
    relationship: string;
    percentage: number;
}

export default function EditProfilePage() {
    const router = useRouter();

    // User info
    const [phone, setPhone] = useState('+225 07 12 34 56 78');
    const [email, setEmail] = useState('user@example.com');
    const [address, setAddress] = useState('Cocody, Abidjan');

    // Emergency contacts
    const [emergencyContacts, setEmergencyContacts] = useState<EmergencyContact[]>([
        { id: '1', name: 'Marie Kouassi', phone: '+225 07 98 76 54 32', relationship: 'Épouse' }
    ]);

    // Beneficiaries
    const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([
        { id: '1', name: 'Marie Kouassi', relationship: 'Épouse', percentage: 100 }
    ]);

    const [saving, setSaving] = useState(false);
    const [showAddContact, setShowAddContact] = useState(false);
    const [showAddBeneficiary, setShowAddBeneficiary] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        await new Promise(resolve => setTimeout(resolve, 1500));
        toast.success('Profil mis à jour avec succès!');
        setSaving(false);
        router.back();
    };

    const addEmergencyContact = (contact: Omit<EmergencyContact, 'id'>) => {
        setEmergencyContacts([...emergencyContacts, { ...contact, id: Date.now().toString() }]);
        setShowAddContact(false);
        toast.success('Contact ajouté');
    };

    const removeEmergencyContact = (id: string) => {
        setEmergencyContacts(emergencyContacts.filter(c => c.id !== id));
        toast.success('Contact supprimé');
    };

    const addBeneficiary = (beneficiary: Omit<Beneficiary, 'id'>) => {
        setBeneficiaries([...beneficiaries, { ...beneficiary, id: Date.now().toString() }]);
        setShowAddBeneficiary(false);
        toast.success('Bénéficiaire ajouté');
    };

    const removeBeneficiary = (id: string) => {
        setBeneficiaries(beneficiaries.filter(b => b.id !== id));
        toast.success('Bénéficiaire supprimé');
    };

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
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Modifier le profil
                </h1>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
                {/* Personal Info */}
                <Section title="Informations personnelles">
                    <InputField
                        icon={Phone}
                        label="Numéro de téléphone"
                        value={phone}
                        onChange={setPhone}
                        type="tel"
                    />
                    <InputField
                        icon={Mail}
                        label="Email"
                        value={email}
                        onChange={setEmail}
                        type="email"
                    />
                    <InputField
                        icon={MapPin}
                        label="Adresse"
                        value={address}
                        onChange={setAddress}
                    />
                </Section>

                {/* Emergency Contacts */}
                <Section
                    title="Contacts d'urgence"
                    action={
                        <button
                            onClick={() => setShowAddContact(true)}
                            className="text-emerald-600 hover:text-emerald-700 text-sm font-medium flex items-center gap-1"
                        >
                            <Plus className="w-4 h-4" />
                            Ajouter
                        </button>
                    }
                >
                    {emergencyContacts.map(contact => (
                        <ContactCard
                            key={contact.id}
                            name={contact.name}
                            phone={contact.phone}
                            relationship={contact.relationship}
                            onRemove={() => removeEmergencyContact(contact.id)}
                        />
                    ))}
                </Section>

                {/* Beneficiaries */}
                <Section
                    title="Bénéficiaires"
                    action={
                        <button
                            onClick={() => setShowAddBeneficiary(true)}
                            className="text-emerald-600 hover:text-emerald-700 text-sm font-medium flex items-center gap-1"
                        >
                            <Plus className="w-4 h-4" />
                            Ajouter
                        </button>
                    }
                >
                    {beneficiaries.map(beneficiary => (
                        <BeneficiaryCard
                            key={beneficiary.id}
                            name={beneficiary.name}
                            relationship={beneficiary.relationship}
                            percentage={beneficiary.percentage}
                            onRemove={() => removeBeneficiary(beneficiary.id)}
                        />
                    ))}
                </Section>
            </div>

            {/* Save Button */}
            <div className="fixed bottom-0 left-0 right-0 p-6 bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800">
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 dark:disabled:bg-slate-700 text-white py-3.5 rounded-xl font-medium transition flex items-center justify-center gap-2"
                >
                    {saving ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Enregistrement...
                        </>
                    ) : (
                        <>
                            <Check className="w-5 h-5" />
                            Enregistrer les modifications
                        </>
                    )}
                </button>
            </div>

            {/* Add Contact Modal */}
            {showAddContact && (
                <AddContactModal
                    onClose={() => setShowAddContact(false)}
                    onAdd={addEmergencyContact}
                />
            )}

            {/* Add Beneficiary Modal */}
            {showAddBeneficiary && (
                <AddBeneficiaryModal
                    onClose={() => setShowAddBeneficiary(false)}
                    onAdd={addBeneficiary}
                />
            )}
        </div>
    );
}

function Section({ title, action, children }: { title: string; action?: React.ReactNode; children: React.ReactNode }) {
    return (
        <div>
            <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h2>
                {action}
            </div>
            <div className="space-y-3">
                {children}
            </div>
        </div>
    );
}

function InputField({
    icon: Icon,
    label,
    value,
    onChange,
    type = 'text'
}: {
    icon: any;
    label: string;
    value: string;
    onChange: (value: string) => void;
    type?: string;
}) {
    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {label}
            </label>
            <div className="relative">
                <Icon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
            </div>
        </div>
    );
}

function ContactCard({ name, phone, relationship, onRemove }: { name: string; phone: string; relationship: string; onRemove: () => void }) {
    return (
        <div className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl p-4 flex items-start justify-between">
            <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600">
                    <User className="w-5 h-5" />
                </div>
                <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{name}</h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{phone}</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500">{relationship}</p>
                </div>
            </div>
            <button
                onClick={onRemove}
                className="w-8 h-8 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 flex items-center justify-center transition"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

function BeneficiaryCard({ name, relationship, percentage, onRemove }: { name: string; relationship: string; percentage: number; onRemove: () => void }) {
    return (
        <div className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl p-4 flex items-start justify-between">
            <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600">
                    <Users className="w-5 h-5" />
                </div>
                <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{name}</h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{relationship}</p>
                    <p className="text-xs font-medium text-emerald-600">{percentage}% des bénéfices</p>
                </div>
            </div>
            <button
                onClick={onRemove}
                className="w-8 h-8 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 flex items-center justify-center transition"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

function AddContactModal({ onClose, onAdd }: { onClose: () => void; onAdd: (contact: Omit<EmergencyContact, 'id'>) => void }) {
    const [name, setName] = useState('');
    const [phone, setPhone] = useState('');
    const [relationship, setRelationship] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onAdd({ name, phone, relationship });
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-6">
            <div className="bg-white dark:bg-slate-900 rounded-t-3xl sm:rounded-2xl w-full sm:max-w-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                    Ajouter un contact d'urgence
                </h3>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="text"
                        placeholder="Nom complet"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <input
                        type="tel"
                        placeholder="Numéro de téléphone"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        required
                        className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <input
                        type="text"
                        placeholder="Relation (ex: Épouse, Frère)"
                        value={relationship}
                        onChange={(e) => setRelationship(e.target.value)}
                        required
                        className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-3 bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-slate-700 transition"
                        >
                            Annuler
                        </button>
                        <button
                            type="submit"
                            className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium transition"
                        >
                            Ajouter
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

function AddBeneficiaryModal({ onClose, onAdd }: { onClose: () => void; onAdd: (beneficiary: Omit<Beneficiary, 'id'>) => void }) {
    const [name, setName] = useState('');
    const [relationship, setRelationship] = useState('');
    const [percentage, setPercentage] = useState(100);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onAdd({ name, relationship, percentage });
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-6">
            <div className="bg-white dark:bg-slate-900 rounded-t-3xl sm:rounded-2xl w-full sm:max-w-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                    Ajouter un bénéficiaire
                </h3>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="text"
                        placeholder="Nom complet"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <input
                        type="text"
                        placeholder="Relation (ex: Épouse, Enfant)"
                        value={relationship}
                        onChange={(e) => setRelationship(e.target.value)}
                        required
                        className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Pourcentage: {percentage}%
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            step="5"
                            value={percentage}
                            onChange={(e) => setPercentage(Number(e.target.value))}
                            className="w-full"
                        />
                    </div>
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-3 bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-slate-700 transition"
                        >
                            Annuler
                        </button>
                        <button
                            type="submit"
                            className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium transition"
                        >
                            Ajouter
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
