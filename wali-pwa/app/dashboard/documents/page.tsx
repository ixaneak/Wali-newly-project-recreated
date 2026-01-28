"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    ArrowLeft,
    FileText,
    Download,
    Search,
    Shield,
    Receipt,
    FileCheck,
    Calendar,
    Filter
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

type DocumentType = 'policy' | 'receipt' | 'claim' | 'certificate';

interface Document {
    id: string;
    type: DocumentType;
    title: string;
    date: Date;
    size: string;
    url: string;
}

const MOCK_DOCUMENTS: Document[] = [
    {
        id: 'doc-001',
        type: 'certificate',
        title: 'Certificat d\'assurance Wali Classique',
        date: new Date('2026-01-01'),
        size: '245 KB',
        url: '#'
    },
    {
        id: 'doc-002',
        type: 'receipt',
        title: 'Reçu paiement - Janvier 2026',
        date: new Date('2026-01-15'),
        size: '128 KB',
        url: '#'
    },
    {
        id: 'doc-003',
        type: 'receipt',
        title: 'Reçu paiement - Décembre 2025',
        date: new Date('2025-12-15'),
        size: '132 KB',
        url: '#'
    },
    {
        id: 'doc-004',
        type: 'claim',
        title: 'Claim #claim-001 - Documents',
        date: new Date('2026-01-21'),
        size: '1.2 MB',
        url: '#'
    },
    {
        id: 'doc-005',
        type: 'claim',
        title: 'Claim #claim-002 - Documents',
        date: new Date('2026-01-11'),
        size: '856 KB',
        url: '#'
    },
    {
        id: 'doc-006',
        type: 'policy',
        title: 'Conditions générales Wali',
        date: new Date('2025-12-01'),
        size: '2.4 MB',
        url: '#'
    },
    {
        id: 'doc-007',
        type: 'certificate',
        title: 'Attestation de couverture',
        date: new Date('2026-01-01'),
        size: '180 KB',
        url: '#'
    }
];

const DOCUMENT_CONFIG = {
    policy: {
        label: 'Polices',
        icon: Shield,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50 dark:bg-blue-900/20'
    },
    receipt: {
        label: 'Reçus',
        icon: Receipt,
        color: 'text-emerald-600',
        bgColor: 'bg-emerald-50 dark:bg-emerald-900/20'
    },
    claim: {
        label: 'Claims',
        icon: FileCheck,
        color: 'text-purple-600',
        bgColor: 'bg-purple-50 dark:bg-purple-900/20'
    },
    certificate: {
        label: 'Certificats',
        icon: FileText,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50 dark:bg-orange-900/20'
    }
};

export default function DocumentsPage() {
    const router = useRouter();
    const [documents] = useState(MOCK_DOCUMENTS);
    const [filterType, setFilterType] = useState<DocumentType | 'all'>('all');
    const [searchQuery, setSearchQuery] = useState('');

    // Filter documents
    const filteredDocuments = documents.filter(doc => {
        const matchesType = filterType === 'all' || doc.type === filterType;
        const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesType && matchesSearch;
    });

    const handleDownload = (doc: Document) => {
        toast.success(`Téléchargement de ${doc.title}`);
        // Simulate download
        console.log('Downloading:', doc.url);
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

                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Mes documents
                </h1>

                {/* Search */}
                <div className="relative mb-4">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Rechercher un document..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                </div>

                {/* Filters */}
                <div className="flex gap-2 overflow-x-auto pb-2 -mx-6 px-6 scrollbar-hide">
                    <FilterButton
                        label="Tous"
                        count={documents.length}
                        active={filterType === 'all'}
                        onClick={() => setFilterType('all')}
                    />
                    <FilterButton
                        label="Polices"
                        count={documents.filter(d => d.type === 'policy').length}
                        active={filterType === 'policy'}
                        onClick={() => setFilterType('policy')}
                    />
                    <FilterButton
                        label="Reçus"
                        count={documents.filter(d => d.type === 'receipt').length}
                        active={filterType === 'receipt'}
                        onClick={() => setFilterType('receipt')}
                    />
                    <FilterButton
                        label="Certificats"
                        count={documents.filter(d => d.type === 'certificate').length}
                        active={filterType === 'certificate'}
                        onClick={() => setFilterType('certificate')}
                    />
                    <FilterButton
                        label="Claims"
                        count={documents.filter(d => d.type === 'claim').length}
                        active={filterType === 'claim'}
                        onClick={() => setFilterType('claim')}
                    />
                </div>
            </div>

            {/* Documents List */}
            <div className="p-6 space-y-3">
                {filteredDocuments.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="w-16 h-16 bg-gray-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Filter className="w-8 h-8 text-gray-400" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                            Aucun document trouvé
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400">
                            {searchQuery ? 'Essayez une autre recherche' : 'Aucun document disponible'}
                        </p>
                    </div>
                ) : (
                    filteredDocuments.map((doc) => (
                        <DocumentCard
                            key={doc.id}
                            document={doc}
                            onDownload={() => handleDownload(doc)}
                        />
                    ))
                )}
            </div>
        </div>
    );
}

function FilterButton({
    label,
    count,
    active,
    onClick
}: {
    label: string;
    count: number;
    active: boolean;
    onClick: () => void
}) {
    return (
        <button
            onClick={onClick}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition ${active
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-700'
                }`}
        >
            {label} ({count})
        </button>
    );
}

function DocumentCard({
    document,
    onDownload
}: {
    document: Document;
    onDownload: () => void
}) {
    const config = DOCUMENT_CONFIG[document.type];
    const Icon = config.icon;

    return (
        <div className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-2xl p-4">
            <div className="flex items-start gap-3">
                <div className={`w-12 h-12 rounded-xl ${config.bgColor} flex items-center justify-center ${config.color} flex-shrink-0`}>
                    <Icon className="w-6 h-6" />
                </div>

                <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-1">
                        {document.title}
                    </h3>
                    <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            <span>{format(document.date, 'dd MMM yyyy', { locale: fr })}</span>
                        </div>
                        <span>•</span>
                        <span>{document.size}</span>
                    </div>
                </div>

                <button
                    onClick={onDownload}
                    className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 flex items-center justify-center transition flex-shrink-0"
                >
                    <Download className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
