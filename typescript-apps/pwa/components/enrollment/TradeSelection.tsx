'use client';

import React from 'react';
import { Hammer, Scissors, Wrench, Briefcase } from 'lucide-react';

interface Trade {
    code: string;
    name: string;
    icon: any;
}

interface TradeSelectionProps {
    onSelect: (trade: string) => void;
    trades?: Trade[];
}

export const TradeSelection: React.FC<TradeSelectionProps> = ({ onSelect, trades }) => {
    const defaultTrades: Trade[] = [
        { code: 'WOOD', name: 'Menuisier', icon: Hammer },
        { code: 'TAIL', name: 'Couturier', icon: Scissors },
        { code: 'MECH', name: 'Mécanicien', icon: Wrench },
        { code: 'COMM', name: 'Commerçant', icon: Briefcase }
    ];

    const displayTrades = trades || defaultTrades;

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white text-center">
                Quelle est votre activité?
            </h2>

            <div className="grid grid-cols-2 gap-4">
                {displayTrades.map((trade) => (
                    <button
                        key={trade.code}
                        onClick={() => onSelect(trade.code)}
                        className="flex flex-col items-center justify-center p-6 bg-white dark:bg-slate-800 rounded-2xl border-2 border-transparent hover:border-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-all shadow-sm group"
                    >
                        <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                            <trade.icon className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                        </div>
                        <span className="font-medium text-gray-900 dark:text-white">{trade.name}</span>
                    </button>
                ))}
            </div>
        </div>
    );
};
