"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, MessageCircle, Phone, Mail, ChevronDown, ChevronUp, Search, HelpCircle } from 'lucide-react';

interface FaqItem {
    question: string;
    answer: string;
}

const FAQS: FaqItem[] = [
    {
        question: "Comment signaler un incident ?",
        answer: "Allez dans l'onglet 'Mes Claims' et cliquez sur le bouton '+'. Suivez les étapes pour remplir les détails et ajouter des photos. Notre équipe examinera votre demande sous 24h."
    },
    {
        question: "Où trouver mes attestations ?",
        answer: "Vos attestations d'assurance sont disponibles dans la section Profil > Mes documents. Vous pouvez les télécharger au format PDF à tout moment."
    },
    {
        question: "Comment payer ma cotisation ?",
        answer: "Sur l'écran d'accueil, cliquez sur 'Recharger'. Nous acceptons Orange Money, MTN Mobile Money, Moov Money et Wave."
    },
    {
        question: "Quelle est la durée de validité de mon assurance ?",
        answer: "Votre assurance est valable tant que votre solde couvre la prime quotidienne/hebdomadaire. Vous recevrez une notification si votre solde est bas."
    },
    {
        question: "Puis-je changer de formule ?",
        answer: "Oui, vous pouvez passer à une formule supérieure (ex: de Basique à Confort) dans la section Profil > Mon plan. Le changement prendra effet le mois suivant."
    }
];

export default function SupportPage() {
    const router = useRouter();
    const [openIndex, setOpenIndex] = useState<number | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    const toggleFaq = (index: number) => {
        setOpenIndex(openIndex === index ? null : index);
    };

    const filteredFaqs = FAQS.filter(faq =>
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-20">
            {/* Header */}
            <div className="bg-emerald-600 pb-12 pt-4 px-4 rounded-b-[2.5rem] shadow-lg">
                <div className="flex items-center justify-between mb-6">
                    <button
                        onClick={() => router.back()}
                        className="p-2 bg-white/20 hover:bg-white/30 rounded-full text-white transition backdrop-blur-sm"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <h1 className="text-lg font-bold text-white">Aide & Support</h1>
                    <div className="w-10" />
                </div>

                <h2 className="text-2xl font-bold text-white mb-2 text-center">Comment pouvons-nous vous aider ?</h2>
                <p className="text-emerald-100 text-center text-sm mb-6">
                    Trouvez des réponses ou contactez notre équipe 24/7
                </p>

                {/* Search Bar */}
                <div className="relative max-w-md mx-auto">
                    <Search className="absolute left-4 top-3.5 text-gray-400 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Rechercher une question..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-3.5 bg-white text-gray-900 rounded-2xl shadow-lg border-0 focus:ring-2 focus:ring-emerald-400 outline-none placeholder-gray-400"
                    />
                </div>
            </div>

            <div className="px-6 -mt-6">
                {/* Contact Actions */}
                <div className="grid grid-cols-3 gap-3 mb-8">
                    <button className="flex flex-col items-center justify-center p-4 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 hover:shadow-md transition active:scale-95">
                        <div className="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-2">
                            <MessageCircle className="w-6 h-6" />
                        </div>
                        <span className="text-xs font-bold text-gray-700 dark:text-gray-300">WhatsApp</span>
                    </button>

                    <button className="flex flex-col items-center justify-center p-4 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 hover:shadow-md transition active:scale-95">
                        <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-2">
                            <Phone className="w-6 h-6" />
                        </div>
                        <span className="text-xs font-bold text-gray-700 dark:text-gray-300">Appeler</span>
                    </button>

                    <button className="flex flex-col items-center justify-center p-4 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 hover:shadow-md transition active:scale-95">
                        <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mb-2">
                            <Mail className="w-6 h-6" />
                        </div>
                        <span className="text-xs font-bold text-gray-700 dark:text-gray-300">Email</span>
                    </button>
                </div>

                {/* FAQ Section */}
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 ml-1 flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-emerald-600" />
                    Questions Fréquentes
                </h3>

                <div className="space-y-3">
                    {filteredFaqs.length > 0 ? (
                        filteredFaqs.map((faq, index) => (
                            <div
                                key={index}
                                className="bg-white dark:bg-slate-900 rounded-2xl border border-gray-100 dark:border-slate-800 overflow-hidden shadow-sm"
                            >
                                <button
                                    onClick={() => toggleFaq(index)}
                                    className="w-full p-4 flex items-center justify-between text-left"
                                >
                                    <span className="font-medium text-gray-800 dark:text-gray-200 pr-4">{faq.question}</span>
                                    {openIndex === index ? (
                                        <ChevronUp className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                                    ) : (
                                        <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                                    )}
                                </button>

                                {openIndex === index && (
                                    <div className="px-4 pb-4 text-sm text-gray-600 dark:text-gray-400 leading-relaxed border-t border-gray-50 dark:border-slate-800 pt-3">
                                        {faq.answer}
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            Aucune réponse trouvée pour "{searchQuery}"
                        </div>
                    )}
                </div>
            </div>

            <div className="mt-8 text-center px-8">
                <p className="text-xs text-gray-400">
                    Notre équipe de support est disponible du lundi au samedi, de 8h à 20h.
                </p>
            </div>
        </div >
    );
}
