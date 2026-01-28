"use client";

import React from 'react';
import { ClaimStatus, CLAIM_STATUS_CONFIG } from '@/types/claims';
import { CheckCircle2, Clock, Eye, XCircle, DollarSign, FileText } from 'lucide-react';

interface ClaimStatusBadgeProps {
    status: ClaimStatus;
    showIcon?: boolean;
}

const StatusIcons = {
    draft: FileText,
    submitted: Clock,
    under_review: Eye,
    approved: CheckCircle2,
    rejected: XCircle,
    paid: DollarSign,
};

export default function ClaimStatusBadge({ status, showIcon = true }: ClaimStatusBadgeProps) {
    const config = CLAIM_STATUS_CONFIG[status];
    const Icon = StatusIcons[status];

    return (
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.color}`}>
            {showIcon && <Icon className="w-3.5 h-3.5" />}
            <span>{config.label}</span>
        </div>
    );
}
