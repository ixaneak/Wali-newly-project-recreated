"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    ArrowLeft,
    Download,
    Search,
    Filter,
    CheckCircle2,
    XCircle,
    Clock,
    Calendar,
    DollarSign,
    CreditCard
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

type TransactionType = 'recharge' | 'payment' | 'claim_payout' | 'refund';
type TransactionStatus = 'completed' | 'pending' | 'failed';

interface Transaction {
    id: string;
    type: TransactionType;
    status: TransactionStatus;
    amount: number;
    description: string;
    date: Date;
    method: string;
    reference: string;
}

const MOCK_TRANSACTIONS: Transaction[] = [
    {
        id: 'txn-001',
        type: 'payment',
        status: 'completed',
        amount: 15000,
        description: 'Paiement plan Classique - Janvier 2026',
        date: new Date('2026-01-15'),
        method: 'Orange Money',
        reference: 'OM-2026011500123'
    },
    {
        id: 'txn-002',
        type: 'claim_payout',
        status: 'completed',
        amount: 50000,
        description: 'Paiement claim #claim-003',
        date: new Date('2026-01-05'),
        method: 'Orange Money',
        reference: 'CL-2026010500456'
    },
    {
        id: 'txn-003',
        type: 'recharge',
        status: 'completed',
        amount: 25000,
        description: 'Recharge compte Wali',
        date: new Date('2025-12-28'),
        method: 'Wave',
        reference: 'WV-2025122800789'
    },
    {
        id: 'txn-004',
        type: 'payment',
        status: 'completed',
        amount: 15000,
        description: 'Paiement plan Classique - Décembre 2025',
        date: new Date('2025-12-15'),
        method: 'MTN Mobile Money',
        reference: 'MTN-2025121500234'
    },
    {
        id: 'txn-005',
        type: 'payment',
        status: 'pending',
        amount: 15000,
        description: 'Paiement plan Classique - Février 2026',
        date: new Date('2026-02-15'),
        method: 'Orange Money',
        reference: 'OM-2026021500567'
    }
];

const TYPE_CONFIG = {
    recharge: { label: 'Recharge', icon: DollarSign, color: 'text-blue-600', sign: '+' },
    payment: { label: 'Paiement', icon: CreditCard, color: 'text-red-600', sign: '-' },
    claim_payout: { label: 'Remboursement', icon: CheckCircle2, color: 'text-emerald-600', sign: '+' },
    refund: { label: 'Remboursement', icon: CheckCircle2, color: 'text-emerald-600', sign: '+' }
};

export default function PaymentHistoryPage() {
    const router = useRouter();
    const [transactions] = useState(MOCK_TRANSACTIONS);
    const [filterStatus, setFilterStatus] = useState<TransactionStatus | 'all'>('all');
    const [searchQuery, setSearchQuery] = useState('');

    // Filter transactions
    const filteredTransactions = transactions.filter(txn => {
        const matchesStatus = filterStatus === 'all' || txn.status === filterStatus;
        const matchesSearch = txn.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
            txn.reference.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesStatus && matchesSearch;
    });

    // Calculate totals
    const totalIn = transactions
        .filter(t => (t.type === 'recharge' || t.type === 'claim_payout') && t.status === 'completed')
        .reduce((sum, t) => sum + t.amount, 0);

    const totalOut = transactions
        .filter(t => t.type === 'payment' && t.status === 'completed')
        .reduce((sum, t) => sum + t.amount, 0);

    const handleExport = () => {
        toast.success('Export en cours...');
        // Simulate export
        setTimeout(() => {
            toast.success('Historique exporté en PDF');
        }, 1500);
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

                <div className="flex items-center justify-between mb-4">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Historique paiements
                    </h1>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 text-emerald-600 hover:text-emerald-700 text-sm font-medium"
                    >
                        <Download className="w-4 h-4" />
                        Exporter
                    </button>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4">
                        <div className="text-sm text-emerald-600 dark:text-emerald-400 mb-1">Entrées</div>
                        <div className="text-xl font-bold text-emerald-700 dark:text-emerald-300">
                            +{totalIn.toLocaleString()} F
                        </div>
                    </div>
                    <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-4">
                        <div className="text-sm text-red-600 dark:text-red-400 mb-1">Sorties</div>
                        <div className="text-xl font-bold text-red-700 dark:text-red-300">
                            -{totalOut.toLocaleString()} F
                        </div>
                    </div>
                </div>

                {/* Search */}
                <div className="relative mb-4">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Rechercher une transaction..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                </div>

                {/* Filters */}
                <div className="flex gap-2 overflow-x-auto pb-2 -mx-6 px-6 scrollbar-hide">
                    <FilterButton
                        label="Tous"
                        active={filterStatus === 'all'}
                        onClick={() => setFilterStatus('all')}
                    />
                    <FilterButton
                        label="Complétés"
                        active={filterStatus === 'completed'}
                        onClick={() => setFilterStatus('completed')}
                    />
                    <FilterButton
                        label="En attente"
                        active={filterStatus === 'pending'}
                        onClick={() => setFilterStatus('pending')}
                    />
                    <FilterButton
                        label="Échoués"
                        active={filterStatus === 'failed'}
                        onClick={() => setFilterStatus('failed')}
                    />
                </div>
            </div>

            {/* Transactions List */}
            <div className="p-6 space-y-3">
                {filteredTransactions.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="w-16 h-16 bg-gray-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Filter className="w-8 h-8 text-gray-400" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                            Aucune transaction trouvée
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400">
                            Essayez une autre recherche
                        </p>
                    </div>
                ) : (
                    filteredTransactions.map((transaction) => (
                        <TransactionCard key={transaction.id} transaction={transaction} />
                    ))
                )}
            </div>
        </div>
    );
}

function FilterButton({
    label,
    active,
    onClick
}: {
    label: string;
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
            {label}
        </button>
    );
}

function TransactionCard({ transaction }: { transaction: Transaction }) {
    const config = TYPE_CONFIG[transaction.type];
    const Icon = config.icon;

    const statusIcon = transaction.status === 'completed' ? CheckCircle2 :
        transaction.status === 'pending' ? Clock : XCircle;

    const statusColor = transaction.status === 'completed' ? 'text-emerald-600' :
        transaction.status === 'pending' ? 'text-yellow-600' : 'text-red-600';

    const StatusIcon = statusIcon;

    return (
        <div className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-2xl p-4">
            <div className="flex items-start gap-3 mb-3">
                <div className={`w-12 h-12 rounded-xl bg-gray-50 dark:bg-slate-800 flex items-center justify-center ${config.color}`}>
                    <Icon className="w-6 h-6" />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                        <h3 className="font-medium text-gray-900 dark:text-white">
                            {transaction.description}
                        </h3>
                        <div className={`text-lg font-bold ${config.color}`}>
                            {config.sign}{transaction.amount.toLocaleString()} F
                        </div>
                    </div>

                    <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            <span>{format(transaction.date, 'dd MMM yyyy', { locale: fr })}</span>
                        </div>
                        <span>•</span>
                        <span>{transaction.method}</span>
                    </div>

                    <div className="flex items-center gap-2 mt-2">
                        <StatusIcon className={`w-4 h-4 ${statusColor}`} />
                        <span className={`text-xs font-medium ${statusColor}`}>
                            {transaction.status === 'completed' ? 'Complété' :
                                transaction.status === 'pending' ? 'En attente' : 'Échoué'}
                        </span>
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs text-gray-400 font-mono">
                            {transaction.reference}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
