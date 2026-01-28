"use client";

import React from 'react';
import { Claim, CLAIM_TYPE_CONFIG } from '@/types/claims';
import ClaimStatusBadge from './ClaimStatusBadge';
import { Heart, AlertTriangle, Home, FileText, ChevronRight, Calendar } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

interface ClaimCardProps {
    claim: Claim;
    onClick: () => void;
}

const TypeIcons = {
    medical: Heart,
    accident: AlertTriangle,
    property: Home,
    other: FileText,
};

export default function ClaimCard({ claim, onClick }: ClaimCardProps) {
    const typeConfig = CLAIM_TYPE_CONFIG[claim.type];
    const Icon = TypeIcons[claim.type];

    return (
        <button
            onClick={onClick}
            className="w-full bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-2xl p-4 hover:shadow-lg transition text-left group"
        >
            <div className="flex items-start gap-3 mb-3">
                <div className={`w-12 h-12 rounded-xl ${typeConfig.bgColor} flex items-center justify-center ${typeConfig.color} flex-shrink-0`}>
                    <Icon className="w-6 h-6" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                        <h3 className="font-bold text-gray-900 dark:text-white">
                            {typeConfig.label}
                        </h3>
                        <ClaimStatusBadge status={claim.status} />
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                        {claim.description}
                    </p>
                </div>
            </div>

            <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-4">
                    <div>
                        <span className="text-gray-500 dark:text-gray-400">Montant: </span>
                        <span className="font-bold text-gray-900 dark:text-white">
                            {claim.amount.toLocaleString()} XOF
                        </span>
                    </div>
                    <div className="flex items-center gap-1 text-gray-400">
                        <Calendar className="w-3.5 h-3.5" />
                        <span className="text-xs">
                            {formatDistanceToNow(new Date(claim.createdAt), {
                                addSuffix: true,
                                locale: fr
                            })}
                        </span>
                    </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-emerald-600 transition" />
            </div>
        </button>
    );
}
