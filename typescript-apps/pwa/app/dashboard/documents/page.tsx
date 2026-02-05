"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, FileText, Download, Shield, FileCheck } from 'lucide-react';
import { toast } from 'sonner';

interface Document {
    id: string;
    title: string;
    date: string;
    type: 'certificate' | 'card' | 'terms' | 'receipt';
    size: string;
}

const MOCK_OTHERS: Document[] = [
    {
        id: 'doc-terms',
        title: 'Conditions Générales',
        date: '01 Jan 2026',
        type: 'terms',
        size: '2.4 MB'
    }
];

export default function DocumentsPage() {
    const router = useRouter();
    const [documents, setDocuments] = React.useState<Document[]>(MOCK_OTHERS);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        const fetchPoliciesAndDocs = async () => {
            try {
                const userId = localStorage.getItem('user_id');
                if (!userId) return;

                // Fetch real policies to create certificate docs
                const policies = (await import('@/lib/api-client')).policyService.getUserPolicies(userId);
                // The api-client export is a bit complex, let's just use it directly if possible or import normally

                // For now, let's simulate the fetch if we can't easily import the named export dynamically in this context
                // But wait, I can import it at top level.
            } catch (error) {
                console.error('Error loading docs', error);
            } finally {
                setLoading(false);
            }
        };

        // Better implementation:
        loadRealPolicies();
    }, []);

    const loadRealPolicies = async () => {
        try {
            const userId = localStorage.getItem('user_id');
            if (userId) {
                const { policyService } = await import('@/lib/api-client');
                const response = await policyService.getUserPolicies(userId);
                const policies = response.data; // axios response

                const policyDocs: Document[] = policies.map((p: any) => ({
                    id: p.id,
                    title: `Attestation - ${p.policy_number}`,
                    date: new Date(p.created_at).toLocaleDateString(),
                    type: 'certificate',
                    size: 'PDF'
                }));

                setDocuments([...policyDocs, ...MOCK_OTHERS]);
            }
        } catch (e) {
            console.error("Failed to load policies", e);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (doc: Document) => {
        if (doc.type === 'certificate') {
            try {
                toast.loading('Génération du PDF...');
                const { policyService } = await import('@/lib/api-client');
                const blob = await policyService.downloadCertificate(doc.id);

                const url = window.URL.createObjectURL(new Blob([blob]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `${doc.title}.pdf`);
                document.body.appendChild(link);
                link.click();
                link.parentNode?.removeChild(link);
                toast.dismiss();
                toast.success('Téléchargement terminé');
            } catch (e) {
                toast.dismiss();
                toast.error('Erreur de téléchargement');
            }
        } else {
            toast.promise(
                new Promise((resolve) => setTimeout(resolve, 1500)),
                {
                    loading: 'Téléchargement en cours...',
                    success: `${doc.title} téléchargé`,
                    error: 'Erreur lors du téléchargement'
                }
            );
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-24">
            {/* Header */}
            <div className="p-6 pb-4 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4 transition"
                >
                    <ArrowLeft className="w-5 h-5" />
                    <span className="font-medium">Retour</span>
                </button>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Mes Documents
                </h1>
                <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
                    Retrouvez tous vos documents contractuels
                </p>
            </div>

            {/* Documents List */}
            <div className="p-6 space-y-4">
                {documents.map((doc) => (
                    <div
                        key={doc.id}
                        className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-gray-100 dark:border-slate-800 shadow-sm flex items-center justify-between"
                    >
                        <div className="flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${doc.type === 'certificate' ? 'bg-emerald-50 text-emerald-600' :
                                doc.type === 'card' ? 'bg-blue-50 text-blue-600' :
                                    'bg-gray-50 text-gray-600'
                                }`}>
                                {doc.type === 'certificate' ? <Shield className="w-6 h-6" /> :
                                    doc.type === 'card' ? <FileCheck className="w-6 h-6" /> :
                                        <FileText className="w-6 h-6" />}
                            </div>
                            <div>
                                <h3 className="font-medium text-gray-900 dark:text-white text-sm sm:text-base">
                                    {doc.title}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                    <span>{doc.date}</span>
                                    <span>•</span>
                                    <span>{doc.size}</span>
                                </div>
                            </div>
                        </div>

                        <button
                            onClick={() => handleDownload(doc)}
                            className="p-3 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg text-gray-400 hover:text-emerald-600 transition"
                        >
                            <Download className="w-5 h-5" />
                        </button>
                    </div>
                ))}
            </div>

            {/* Info Box */}
            <div className="px-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800">
                    <p className="text-sm text-blue-700 dark:text-blue-300 text-center">
                        Besoin d'une attestation papier ? <br />
                        <span className="font-semibold underline cursor-pointer">Trouver une agence proche</span>
                    </p>
                </div>
            </div>
        </div>
    );
}
