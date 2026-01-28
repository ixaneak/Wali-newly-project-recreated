"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    ArrowLeft,
    Phone,
    Mail,
    MessageCircle,
    ChevronDown,
    Send,
    HelpCircle,
    FileText,
    Shield,
    CreditCard
} from 'lucide-react';
import { toast } from 'sonner';

const FAQ_ITEMS = [
    {
        category: 'general',
        icon: HelpCircle,
        title: 'Questions générales',
        items: [
            {
                question: 'Comment fonctionne Wali ?',
                answer: 'Wali est une assurance santé accessible qui vous permet de vous protéger contre les frais médicaux imprévus. Rechargez votre compte, activez votre couverture, et soumettez vos claims en cas de besoin.'
            },
            {
                question: 'Quels sont les délais de traitement des claims ?',
                answer: 'Les claims sont généralement traités sous 48-72 heures. Vous recevrez une notification par SMS et email à chaque étape du processus.'
            },
            {
                question: 'Puis-je changer de plan ?',
                answer: 'Oui ! Vous pouvez upgrader votre plan à tout moment depuis la section "Mon plan" de votre profil. Le nouveau tarif sera appliqué immédiatement.'
            }
        ]
    },
    {
        category: 'coverage',
        icon: Shield,
        title: 'Couverture',
        items: [
            {
                question: 'Que couvre mon plan Classique ?',
                answer: 'Le plan Classique couvre jusqu\'à 500,000 XOF de frais médicaux incluant consultations, médicaments, analyses, et hospitalisations d\'urgence.'
            },
            {
                question: 'Les membres de ma famille sont-ils couverts ?',
                answer: 'Avec le plan Coopérative, vous pouvez ajouter jusqu\'à 5 dépendants. Contactez le support pour plus d\'informations sur la couverture familiale.'
            },
            {
                question: 'Y a-t-il une période de carence ?',
                answer: 'Non, votre couverture est active dès que votre paiement est validé. Vous pouvez soumettre des claims immédiatement.'
            }
        ]
    },
    {
        category: 'payments',
        icon: CreditCard,
        title: 'Paiements',
        items: [
            {
                question: 'Quels moyens de paiement acceptez-vous ?',
                answer: 'Nous acceptons Orange Money, MTN Mobile Money, et Wave. Le paiement est instantané et sécurisé.'
            },
            {
                question: 'Puis-je obtenir un remboursement ?',
                answer: 'Les paiements mensuels ne sont pas remboursables. Cependant, en cas de claim approuvé, le montant vous sera versé selon le mode de paiement choisi.'
            },
            {
                question: 'Comment renouveler mon abonnement ?',
                answer: 'Votre plan se renouvelle automatiquement chaque mois. Vous recevrez un rappel 3 jours avant la date de renouvellement.'
            }
        ]
    },
    {
        category: 'claims',
        icon: FileText,
        title: 'Claims',
        items: [
            {
                question: 'Comment soumettre un claim ?',
                answer: 'Allez dans l\'onglet "Mes Claims", cliquez sur "Nouveau claim", sélectionnez le type de sinistre, ajoutez les détails et les photos, puis soumettez.'
            },
            {
                question: 'Quels documents dois-je fournir ?',
                answer: 'Fournissez des photos des reçus médicaux, prescriptions, et tout document justifiant vos dépenses. Plus vous fournissez de preuves, plus le traitement sera rapide.'
            },
            {
                question: 'Pourquoi mon claim a-t-il été rejeté ?',
                answer: 'Les claims peuvent être rejetés si les dépenses ne sont pas couvertes par votre plan, si les documents sont insuffisants, ou si le montant dépasse votre plafond. Consultez les notes de révision pour plus de détails.'
            }
        ]
    }
];

export default function SupportPage() {
    const router = useRouter();
    const [expandedFaq, setExpandedFaq] = useState<string | null>(null);
    const [contactForm, setContactForm] = useState({
        subject: '',
        message: '',
        email: ''
    });
    const [sending, setSending] = useState(false);

    const handleSubmitContact = async (e: React.FormEvent) => {
        e.preventDefault();
        setSending(true);

        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));

        toast.success('Message envoyé ! Nous vous répondrons sous 24h.');
        setContactForm({ subject: '', message: '', email: '' });
        setSending(false);
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

                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    Aide & Support
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Comment pouvons-nous vous aider ?
                </p>
            </div>

            {/* Quick Actions */}
            <div className="p-6 grid grid-cols-3 gap-3">
                <QuickActionButton
                    icon={Phone}
                    label="Appeler"
                    color="emerald"
                    onClick={() => window.open('tel:+22527204050', '_self')}
                />
                <QuickActionButton
                    icon={MessageCircle}
                    label="WhatsApp"
                    color="green"
                    onClick={() => window.open('https://wa.me/22527204050', '_blank')}
                />
                <QuickActionButton
                    icon={Mail}
                    label="Email"
                    color="blue"
                    onClick={() => window.open('mailto:support@wali-ci.com', '_self')}
                />
            </div>

            {/* FAQ Sections */}
            <div className="px-6 pb-6">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                    Questions fréquentes
                </h2>

                <div className="space-y-6">
                    {FAQ_ITEMS.map((category) => (
                        <div key={category.category}>
                            <div className="flex items-center gap-2 mb-3">
                                <category.icon className="w-5 h-5 text-emerald-600" />
                                <h3 className="font-bold text-gray-900 dark:text-white">
                                    {category.title}
                                </h3>
                            </div>

                            <div className="space-y-2">
                                {category.items.map((item, index) => {
                                    const key = `${category.category}-${index}`;
                                    const isExpanded = expandedFaq === key;

                                    return (
                                        <button
                                            key={key}
                                            onClick={() => setExpandedFaq(isExpanded ? null : key)}
                                            className="w-full bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl p-4 text-left transition hover:shadow-sm"
                                        >
                                            <div className="flex items-start justify-between gap-3 mb-2">
                                                <h4 className="font-medium text-gray-900 dark:text-white flex-1">
                                                    {item.question}
                                                </h4>
                                                <ChevronDown
                                                    className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''
                                                        }`}
                                                />
                                            </div>

                                            {isExpanded && (
                                                <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed pr-8">
                                                    {item.answer}
                                                </p>
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Contact Form */}
            <div className="px-6 pb-6">
                <div className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-2xl p-6">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-4">
                        Vous ne trouvez pas de réponse ?
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                        Envoyez-nous un message et nous vous répondrons dans les 24 heures.
                    </p>

                    <form onSubmit={handleSubmitContact} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Email
                            </label>
                            <input
                                type="email"
                                value={contactForm.email}
                                onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                                required
                                placeholder="votre@email.com"
                                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Sujet
                            </label>
                            <input
                                type="text"
                                value={contactForm.subject}
                                onChange={(e) => setContactForm({ ...contactForm, subject: e.target.value })}
                                required
                                placeholder="Ex: Question sur mon claim"
                                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Message
                            </label>
                            <textarea
                                value={contactForm.message}
                                onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                                required
                                rows={4}
                                placeholder="Décrivez votre problème ou question..."
                                className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={sending}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 dark:disabled:bg-slate-700 text-white py-3 rounded-xl font-medium transition flex items-center justify-center gap-2"
                        >
                            {sending ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    Envoi...
                                </>
                            ) : (
                                <>
                                    <Send className="w-4 h-4" />
                                    Envoyer le message
                                </>
                            )}
                        </button>
                    </form>
                </div>
            </div>

            {/* Support Hours */}
            <div className="px-6 pb-6">
                <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4">
                    <h4 className="font-bold text-emerald-900 dark:text-emerald-400 mb-2">
                        Horaires du support
                    </h4>
                    <p className="text-sm text-emerald-700 dark:text-emerald-300">
                        Lun-Ven: 8h-20h | Sam: 9h-18h | Dim: 10h-16h
                    </p>
                    <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-2">
                        Support d'urgence 24/7 pour les claims approuvés
                    </p>
                </div>
            </div>
        </div>
    );
}

function QuickActionButton({
    icon: Icon,
    label,
    color,
    onClick
}: {
    icon: any;
    label: string;
    color: 'emerald' | 'green' | 'blue';
    onClick: () => void;
}) {
    const colorClasses = {
        emerald: 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600',
        green: 'bg-green-50 dark:bg-green-900/30 text-green-600',
        blue: 'bg-blue-50 dark:bg-blue-900/30 text-blue-600'
    };

    return (
        <button
            onClick={onClick}
            className={`p-4 rounded-xl ${colorClasses[color]} hover:scale-105 transition flex flex-col items-center gap-2`}
        >
            <Icon className="w-6 h-6" />
            <span className="text-xs font-medium">{label}</span>
        </button>
    );
}
