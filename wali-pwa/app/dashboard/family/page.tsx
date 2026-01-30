"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Users, User, Heart, ShieldCheck, ChevronRight, X } from 'lucide-react';
import { toast } from 'sonner';

interface FamilyMember {
    id: string;
    name: string;
    relation: 'conjoint' | 'enfant' | 'parent';
    age: number;
    coverage: 'active' | 'inactive';
    avatar_color: string;
}

const MOCK_FAMILY: FamilyMember[] = [
    {
        id: 'fam-001',
        name: 'Fatou Koné',
        relation: 'conjoint',
        age: 28,
        coverage: 'active',
        avatar_color: 'bg-pink-100 text-pink-600'
    },
    {
        id: 'fam-002',
        name: 'Moussa Koné',
        relation: 'enfant',
        age: 5,
        coverage: 'active',
        avatar_color: 'bg-blue-100 text-blue-600'
    }
];

export default function FamilyPage() {
    const router = useRouter();
    const [members, setMembers] = useState<FamilyMember[]>(MOCK_FAMILY);
    const [showAddModal, setShowAddModal] = useState(false);

    // New Member Form State
    const [newMember, setNewMember] = useState({
        name: '',
        relation: 'enfant',
        age: ''
    });

    const handleAddMember = (e: React.FormEvent) => {
        e.preventDefault();

        // Validation
        if (!newMember.name || !newMember.age) {
            toast.error('Veuillez remplir tous les champs');
            return;
        }

        const member: FamilyMember = {
            id: `fam-${Date.now()}`,
            name: newMember.name,
            relation: newMember.relation as any,
            age: parseInt(newMember.age),
            coverage: 'inactive', // Default inactive until paid
            avatar_color: 'bg-emerald-100 text-emerald-600'
        };

        setMembers([...members, member]);
        setShowAddModal(false);
        setNewMember({ name: '', relation: 'enfant', age: '' });
        toast.success('Membre ajouté avec succès');

        // Show upgrade prompt
        setTimeout(() => {
            toast('N\'oubliez pas d\'activer sa couverture', {
                action: {
                    label: 'Activer',
                    onClick: () => console.log('Upgrade flow')
                }
            });
        }, 1000);
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
                    <h1 className="text-lg font-bold text-gray-900 dark:text-white">Ma Famille</h1>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="p-2 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 rounded-full transition"
                    >
                        <Plus className="w-6 h-6" />
                    </button>
                </div>
            </div>

            <div className="p-6">
                {/* Family Summary Card */}
                <div className="bg-gradient-to-br from-emerald-600 to-teal-700 rounded-3xl p-6 text-white shadow-lg mb-8 relative overflow-hidden">
                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-2 opacity-90">
                            <Users className="w-5 h-5" />
                            <span className="text-sm font-medium">Couverture Familiale</span>
                        </div>
                        <h2 className="text-3xl font-bold mb-1">{members.length + 1} Membres</h2>
                        <p className="opacity-80 text-sm">Vous + {members.length} dépendants</p>
                    </div>
                    {/* Background decoration */}
                    <div className="absolute right-0 bottom-0 opacity-10 transform translate-x-1/4 translate-y-1/4">
                        <Heart className="w-40 h-40" />
                    </div>
                </div>

                {/* Members List */}
                <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-4 ml-1">Dépendants</h3>

                <div className="space-y-4">
                    {members.map((member) => (
                        <div
                            key={member.id}
                            className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-gray-100 dark:border-slate-800 shadow-sm flex items-center justify-between"
                        >
                            <div className="flex items-center gap-4">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${member.avatar_color}`}>
                                    <User className="w-6 h-6" />
                                </div>
                                <div>
                                    <h4 className="font-bold text-gray-900 dark:text-white">{member.name}</h4>
                                    <div className="flex items-center gap-2 text-xs text-gray-500">
                                        <span className="capitalize">{member.relation}</span>
                                        <span>•</span>
                                        <span>{member.age} ans</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-col items-end gap-1">
                                {member.coverage === 'active' ? (
                                    <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 px-2 py-1 rounded-lg text-xs font-bold">
                                        <ShieldCheck className="w-3 h-3" />
                                        Couvert
                                    </span>
                                ) : (
                                    <button className="bg-gray-100 text-gray-600 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-emerald-600 hover:text-white transition">
                                        Activer
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Empty State Hint */}
                {members.length === 0 && (
                    <div className="text-center py-8 px-8 bg-gray-50 dark:bg-slate-800/50 rounded-2xl border border-dashed border-gray-200 dark:border-slate-700">
                        <User className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                        <p className="text-sm text-gray-500">
                            Ajoutez votre conjoint(e) ou vos enfants pour étendre votre couverture santé.
                        </p>
                    </div>
                )}
            </div>

            {/* Add Member Modal */}
            {showAddModal && (
                <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div className="w-full max-w-sm bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-2xl animate-in slide-in-from-bottom duration-300">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Ajouter un membre</h3>
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="p-2 bg-gray-100 dark:bg-slate-800 rounded-full hover:bg-gray-200"
                            >
                                <X className="w-5 h-5 text-gray-600" />
                            </button>
                        </div>

                        <form onSubmit={handleAddMember} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nom complet</label>
                                <input
                                    type="text"
                                    required
                                    value={newMember.name}
                                    onChange={(e) => setNewMember({ ...newMember, name: e.target.value })}
                                    className="w-full p-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
                                    placeholder="Ex: Fatou Koné"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Relation</label>
                                    <select
                                        value={newMember.relation}
                                        onChange={(e) => setNewMember({ ...newMember, relation: e.target.value })}
                                        className="w-full p-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
                                    >
                                        <option value="enfant">Enfant</option>
                                        <option value="conjoint">Conjoint(e)</option>
                                        <option value="parent">Parent</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Âge</label>
                                    <input
                                        type="number"
                                        required
                                        min="0"
                                        max="100"
                                        value={newMember.age}
                                        onChange={(e) => setNewMember({ ...newMember, age: e.target.value })}
                                        className="w-full p-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
                                        placeholder="Ex: 5"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg shadow-emerald-200 dark:shadow-emerald-900/20 active:scale-[0.98] transition mt-2"
                            >
                                Ajouter
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
