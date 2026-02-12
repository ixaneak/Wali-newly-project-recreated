'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { enrollmentService } from '@/lib/api-client';
import PartnerDisclosure from '@/components/auth/PartnerDisclosure';
import { TradeSelection } from '@/components/enrollment/TradeSelection';
import { QuoteDisplay } from '@/components/enrollment/QuoteDisplay';
import { PaymentConfirmation } from '@/components/enrollment/PaymentConfirmation';
import { ArrowLeft } from 'lucide-react';
import { auth } from '@/lib/firebase'; // Assuming auth is available

export default function EnrollmentPage() {
    const router = useRouter();
    const [step, setStep] = useState<'disclosure' | 'trade' | 'quote' | 'payment'>('disclosure');
    const [selectedTrade, setSelectedTrade] = useState<string>('');
    const [quote, setQuote] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [enrollmentId, setEnrollmentId] = useState<string | null>(null);
    const [paymentUrl, setPaymentUrl] = useState<string | null>(null);

    const partnerId = 'NSIA'; // Default partner for MVP

    const handleTradeSelect = async (trade: string) => {
        setSelectedTrade(trade);
        setLoading(true);
        try {
            // NEW: Fetch quote from partner API
            const partnerQuote = await enrollmentService.getPartnerQuote(partnerId, trade, 'ABIDJAN');
            setQuote(partnerQuote);
            setStep('quote');
        } catch (error) {
            console.error(error);
            alert('Erreur: Impossible de contacter NSIA pour le tarif.');
        } finally {
            setLoading(false);
        }
    };

    const handleEnroll = async () => {
        if (!auth.currentUser) {
            alert("Veuillez vous connecter pour souscrire.");
            return;
        }

        setLoading(true);
        try {
            // NEW: Create enrollment via partner endpoint
            const enrollment = await enrollmentService.createEnrollment(partnerId, {
                trade: selectedTrade,
                productId: quote.productId,
                phone: '22500000000', // TODO: Get REAL phone from user profile
                partnerId: partnerId,
                userId: auth.currentUser.uid
            });

            setEnrollmentId(enrollment.id);

            // NEW: Route payment to partner (not Wali)
            const payment = await enrollmentService.initiatePartnerPayment(partnerId, enrollment.id);
            setPaymentUrl(payment.paymentUrl);

            // In Web, we might redirect to payment URL, or show button. 
            // Here we show confirmation step with button.
            setStep('payment');

            if (payment.paymentUrl) {
                window.open(payment.paymentUrl, '_blank');
            }

        } catch (error) {
            console.error(error);
            alert('Erreur: Échec de la souscription. Veuillez réessayer.');
        } finally {
            setLoading(false);
        }
    };

    const checkEnrollmentStatus = async () => {
        if (!enrollmentId) return;
        try {
            const status = await enrollmentService.checkStatus(partnerId, enrollmentId);
            if (status.status === 'active') {
                alert('Félicitations! Votre couverture est active.');
                router.push('/dashboard');
            } else {
                alert('Statut actuel: ' + status.status + '. Veuillez vérifier le paiement.');
            }
        } catch (e) {
            alert('Erreur lors de la vérification du statut.');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex flex-col">
            <div className="p-4 bg-white dark:bg-slate-900 shadow-sm flex items-center sticky top-0 z-10">
                {step !== 'disclosure' && (
                    <button onClick={() => {
                        if (step === 'payment') router.push('/dashboard');
                        else if (step === 'quote') setStep('trade');
                        else if (step === 'trade') setStep('disclosure');
                    }} className="mr-4 text-gray-600 dark:text-gray-300">
                        <ArrowLeft size={24} />
                    </button>
                )}
                <h1 className="text-lg font-bold text-gray-900 dark:text-white flex-1 text-center">
                    Souscription
                </h1>
                <div className="w-8" />
            </div>

            <div className="flex-1 p-6 max-w-md mx-auto w-full">
                {step === 'disclosure' && (
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm">
                        <PartnerDisclosure
                            onAccept={() => setStep('trade')}
                            onDecline={() => router.back()}
                        />
                    </div>
                )}

                {step === 'trade' && (
                    <TradeSelection
                        onSelect={handleTradeSelect}
                    />
                )}

                {step === 'quote' && quote && (
                    <QuoteDisplay
                        partner="NSIA"
                        amount={quote.amount}
                        productName={quote.productId}
                        onConfirm={handleEnroll}
                        onCancel={() => setStep('trade')}
                        loading={loading}
                    />
                )}

                {step === 'payment' && (
                    <PaymentConfirmation
                        message="Vous allez être redirigé vers le paiement sécurisé de NSIA via Orange Money..."
                        onCheckStatus={checkEnrollmentStatus}
                        paymentUrl={paymentUrl || undefined}
                    />
                )}
            </div>
        </div>
    );
}
