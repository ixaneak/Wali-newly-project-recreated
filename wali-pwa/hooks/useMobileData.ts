import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api-client';
import { DashboardData, Transaction, Pharmacy, ReimbursementStats } from '@/types/mobile-ui';

export function useDashboard() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const result = await apiService.fetchDashboard();
                setData(result as DashboardData);
            } catch (err) {
                setError('Erreur de chargement du tableau de bord');
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    return { data, loading, error };
}

export function useTransactions(filter: string = 'Tout') {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const result = await apiService.fetchTransactions(filter);
                setTransactions(result as Transaction[]);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [filter]);

    return { transactions, loading };
}

export function usePharmacies() {
    const [pharmacies, setPharmacies] = useState<Pharmacy[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            // Mock lat/lng
            const result = await apiService.fetchNearbyPharmacies(5.3, -4.0);
            setPharmacies(result as Pharmacy[]);
            setLoading(false);
        };
        load();
    }, []);

    return { pharmacies, loading };
}

export function useReimbursementStats() {
    const [stats, setStats] = useState<ReimbursementStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            const result = await apiService.fetchReimbursementStats();
            setStats(result as ReimbursementStats);
            setLoading(false);
        };
        load();
    }, []);

    return { stats, loading };
}
