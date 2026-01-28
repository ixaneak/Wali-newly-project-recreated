import { Transaction } from '@/types/mobile-ui';
import { ArrowUpRight, ArrowDownLeft, RefreshCcw } from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

interface TransactionListProps {
    transactions: Transaction[];
    limit?: number;
}

export default function TransactionList({ transactions, limit }: TransactionListProps) {
    const items = limit ? transactions.slice(0, limit) : transactions;

    const getIcon = (type: Transaction['type']) => {
        switch (type) {
            case 'cotisation': return <ArrowDownLeft className="w-5 h-5 text-emerald-600" />; // Money In (to account balance logic? Or payment?) Actually cotisation is payment OUT usually... but in insurance context, paying premium allows coverage. Let's assume Cotisation = Payment.
            // Wait, for Balance Card "Used" vs "Total".
            // Cotisation = Payment of Premium (Money out of user pocket, into system).
            // Utilisation = Usage of coverage (Money consumed from coverage).
            // Remboursement = Money back to user.

            // Let's stick to the prompt description:
            // "Green arrow for income/cotisations" -> implies adding to balance/validity?
            // "Red arrow for expenses/utilisations"

            case 'cotisation': return <ArrowUpRight className="w-5 h-5 text-emerald-600" />;
            case 'utilisation': return <ArrowDownLeft className="w-5 h-5 text-red-500" />;
            case 'remboursement': return <RefreshCcw className="w-5 h-5 text-blue-500" />;
        }
    };

    const getColor = (type: Transaction['type']) => {
        switch (type) {
            case 'cotisation': return 'bg-emerald-50 text-emerald-700';
            case 'utilisation': return 'bg-red-50 text-red-700';
            case 'remboursement': return 'bg-blue-50 text-blue-700';
        }
    };

    const getAmountColor = (type: Transaction['type']) => {
        switch (type) {
            case 'cotisation': return 'text-emerald-600'; // +
            case 'utilisation': return 'text-red-500'; // -
            case 'remboursement': return 'text-blue-500'; // +
        }
    };

    const getSign = (type: Transaction['type']) => {
        switch (type) {
            case 'cotisation': return '+';
            case 'utilisation': return '-';
            case 'remboursement': return '+';
        }
    };

    if (items.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500 text-sm bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                Aucune transaction récente
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {items.map((tx) => (
                <div key={tx.id} className="bg-white dark:bg-slate-900 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-800 transition cursor-pointer">
                    <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getColor(tx.type)}`}>
                            {getIcon(tx.type)}
                        </div>
                        <div>
                            <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{tx.title}</h4>
                            <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                                {format(new Date(tx.date), "d MMM, HH:mm", { locale: fr })}
                            </p>
                        </div>
                    </div>
                    <div className={`font-bold text-sm ${getAmountColor(tx.type)}`}>
                        {getSign(tx.type)} {tx.amount.toLocaleString('fr-FR')} F
                    </div>
                </div>
            ))}
        </div>
    );
}
