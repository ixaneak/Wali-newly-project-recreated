"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Filter, Search, Loader2, RefreshCw } from 'lucide-react';
import { ClaimStatus } from '@/types/claims';
import { claimsService, ClaimData } from '@/lib/api-client';
import { IncidentReport, IncidentStatus } from '@/types/app'; // New Import
import ClaimCard from '@/components/claims/ClaimCard';
import { toast } from 'sonner';

export default function ClaimsPage() {
    const router = useRouter();
    // Update state type to IncidentReport
    const [claims, setClaims] = useState<IncidentReport[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    // Map IncidentStatus to FilterStatus (loosely)
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState('');

    // Fetch incidents from API
    const fetchClaims = async (showLoader = true) => {
        try {
            if (showLoader) setLoading(true);
            const data = await claimsService.getUserClaims();
            setClaims(data);
        } catch (error: any) {
            console.error('Error fetching incidents:', error);
            const errorMsg = error?.response?.data?.detail || 'Impossible de charger les incidents';
            toast.error(errorMsg);
            setClaims([]);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    // Load claims on mount
    useEffect(() => {
        fetchClaims();
    }, []);

    // Refresh handler
    const handleRefresh = () => {
        setRefreshing(true);
        fetchClaims(false);
    };

    // Filter claims
    const filteredClaims = claims.filter(claim => {
        let matchesStatus = false;

        if (filterStatus === 'all') {
            matchesStatus = true;
        } else if (filterStatus === 'under_review') {
            // Map SaaS statuses to "under review"
            matchesStatus = ['submitted_to_wali', 'forwarded_to_partner', 'partner_reviewing'].includes(claim.status);
        } else if (filterStatus === 'approved') {
            matchesStatus = claim.status === 'partner_resolved'; // Assume resolved = approved for now
        } else {
            // Exact match fallback
            matchesStatus = claim.status === filterStatus;
        }

        const matchesSearch = claim.description.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesStatus && matchesSearch;
    });

    // Count by status
    const statusCounts = {
        all: claims.length,
        submitted: claims.filter(c => c.status === 'submitted_to_wali').length,
        under_review: claims.filter(c => ['submitted_to_wali', 'forwarded_to_partner', 'partner_reviewing'].includes(c.status)).length,
        approved: claims.filter(c => c.status === 'partner_resolved').length, // Mock mapping
        paid: 0, // No paid status in IncidentReport yet, logic differs
    };

    console.log('Incidents array:', claims);
    console.log('Status counts:', statusCounts);

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 pb-32">
            {/* Header */}
            <div className="p-6 pb-4 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Mes incidents</h1>
                        <button
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition"
                            title="Actualiser"
                        >
                            <RefreshCw className={`w-4 h-4 text-gray-600 dark:text-gray-400 ${refreshing ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                    <button
                        onClick={() => router.push('/dashboard/claims/new')}
                        className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-xl font-medium transition"
                    >
                        <Plus className="w-4 h-4" />
                        Nouveau
                    </button>
                </div>

                {/* Search */}
                <div className="relative mb-4">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Rechercher un incident..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                </div>

                {/* Filters */}
                <div className="flex gap-2 overflow-x-auto pb-2 -mx-6 px-6 scrollbar-hide">
                    <FilterButton
                        label={`Tous (${statusCounts.all})`}
                        active={filterStatus === 'all'}
                        onClick={() => setFilterStatus('all')}
                    />
                    <FilterButton
                        label={`En cours (${statusCounts.under_review})`}
                        active={filterStatus === 'under_review'}
                        onClick={() => setFilterStatus('under_review')}
                    />
                    <FilterButton
                        label={`Pris en charge (${statusCounts.approved})`}
                        active={filterStatus === 'approved'}
                        onClick={() => setFilterStatus('approved')}
                    />
                    {/* Temporarily remove "Payés" filter or map it to something else if needed */}
                </div>
            </div>

            {/* Claims List */}
            <div className="p-6 space-y-3">
                {loading ? (
                    // Loading skeleton
                    <div className="space-y-3">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-2xl p-4 animate-pulse">
                                <div className="flex items-start gap-3">
                                    <div className="w-12 h-12 bg-gray-200 dark:bg-slate-800 rounded-xl"></div>
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 bg-gray-200 dark:bg-slate-800 rounded w-3/4"></div>
                                        <div className="h-3 bg-gray-200 dark:bg-slate-800 rounded w-1/2"></div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : filteredClaims.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="w-16 h-16 bg-gray-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Filter className="w-8 h-8 text-gray-400" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                            Aucun incident trouvé
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400 mb-6">
                            {searchQuery ? 'Essayez une autre recherche' : 'Signalez votre premier incident'}
                        </p>
                        {!searchQuery && (
                            <button
                                onClick={() => router.push('/dashboard/claims/new')}
                                className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-xl font-medium transition"
                            >
                                <Plus className="w-5 h-5" />
                                Signaler un incident
                            </button>
                        )}
                    </div>
                ) : (
                    filteredClaims.map((claim) => {
                        // Map IncidentReport to component's expected Claim type
                        // This adapter allows us to reuse ClaimCard without rewriting it
                        const mappedClaim = {
                            id: claim.id,
                            userId: claim.user_id,
                            policyId: claim.subscription_id,
                            tier: claim.partner?.name || 'Partner',
                            type: claim.type,
                            // Map SaaS status to Legacy ClaimStatus for UI Badge
                            status: (
                                claim.status === 'partner_resolved' ? 'approved' :
                                    claim.status === 'partner_reviewing' ? 'under_review' :
                                        'submitted'
                            ) as ClaimStatus,
                            amount: claim.reported_amount,
                            description: claim.description,
                            incidentDate: new Date(claim.incident_date),
                            photos: claim.photos || [],
                            createdAt: new Date(claim.created_at),
                            updatedAt: new Date(claim.created_at), // fallback
                            reviewNotes: claim.partner_notes,
                            reviewedBy: claim.partner?.name,
                            reviewedAt: claim.resolved_at ? new Date(claim.resolved_at) : undefined,
                        };

                        return (
                            <ClaimCard
                                key={claim.id}
                                claim={mappedClaim}
                                onClick={() => router.push(`/dashboard/claims/${claim.id}`)}
                            />
                        );
                    })
                )}
            </div>
        </div>
    );
}

function FilterButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
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
