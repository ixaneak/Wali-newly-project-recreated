'use client';

import React, { useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

/**
 * PayDunya Payment Page
 *
 * Allows users to initiate a mobile money payment via PayDunya.
 * In test mode, displays sandbox test numbers and PIN.
 */

const PROVIDERS = [
    { id: 'orange_money', label: 'Orange Money', prefix: '07/08', color: '#FF6600' },
    { id: 'mtn_momo', label: 'MTN MoMo', prefix: '05/06', color: '#FFCC00' },
    { id: 'wave', label: 'Wave', prefix: '09', color: '#1DC4E9' },
    { id: 'moov', label: 'Moov Money', prefix: '01', color: '#0066CC' },
];

const TEST_NUMBERS: Record<string, { number: string; pin: string }> = {
    orange_money: { number: '+225 77777777', pin: '1234' },
    mtn_momo: { number: '+225 55555555', pin: '1234' },
    wave: { number: '+225 99999999', pin: '1234' },
    moov: { number: '+225 66666666', pin: '1234' },
};

type PaymentStatus = 'idle' | 'loading' | 'redirecting' | 'verifying' | 'success' | 'error';

export default function PaydunyaPaymentPage() {
    const searchParams = useSearchParams();
    const router = useRouter();

    const policyId = searchParams.get('policyId') || '';
    const amount = parseInt(searchParams.get('amount') || '4500', 10);

    const [phoneNumber, setPhoneNumber] = useState('');
    const [selectedProvider, setSelectedProvider] = useState('');
    const [status, setStatus] = useState<PaymentStatus>('idle');
    const [error, setError] = useState('');
    const [paymentRef, setPaymentRef] = useState('');
    const [paymentUrl, setPaymentUrl] = useState('');
    const [instructions, setInstructions] = useState('');

    const detectProvider = (phone: string) => {
        const clean = phone.replace(/\s/g, '').replace('+225', '');
        if (clean.startsWith('07') || clean.startsWith('08')) return 'orange_money';
        if (clean.startsWith('05') || clean.startsWith('06')) return 'mtn_momo';
        if (clean.startsWith('01')) return 'moov';
        if (clean.startsWith('09')) return 'wave';
        return '';
    };

    const handlePhoneChange = (value: string) => {
        setPhoneNumber(value);
        const provider = detectProvider(value);
        if (provider) setSelectedProvider(provider);
    };

    const validatePhone = (phone: string): boolean => {
        const clean = phone.replace(/\s/g, '');
        return /^\+225(07|08|05|06|01|09)\d{8}$/.test(clean);
    };

    const initiatePayment = async () => {
        if (!policyId) {
            setError('ID de police manquant');
            return;
        }

        if (!validatePhone(phoneNumber)) {
            setError('Numéro invalide. Format: +225 07 XX XX XX XX');
            return;
        }

        setStatus('loading');
        setError('');

        try {
            const token = localStorage.getItem('authToken') || '';
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payments/paydunya/initiate`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        policy_id: policyId,
                        phone_number: phoneNumber.replace(/\s/g, ''),
                    }),
                }
            );

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || `Erreur ${res.status}`);
            }

            const data = await res.json();
            setPaymentRef(data.internal_ref);
            setPaymentUrl(data.payment_url);
            setInstructions(data.instructions);
            setStatus('redirecting');

            // In production, redirect to PayDunya checkout
            // window.location.href = data.payment_url;
        } catch (err: any) {
            setError(err.message || 'Erreur de paiement');
            setStatus('error');
        }
    };

    const verifyPayment = async () => {
        if (!paymentRef) return;

        setStatus('verifying');
        try {
            const token = localStorage.getItem('authToken') || '';
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payments/paydunya/verify/${paymentRef}`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );

            if (!res.ok) throw new Error(`Erreur ${res.status}`);

            const data = await res.json();
            if (data.status === 'completed') {
                setStatus('success');
            } else {
                setStatus('redirecting'); // Still pending
                setError(`Statut: ${data.status} — en attente de confirmation`);
            }
        } catch (err: any) {
            setError(err.message);
            setStatus('error');
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                {/* Header */}
                <div style={styles.header}>
                    <h1 style={styles.title}>Paiement PayDunya</h1>
                    <div style={styles.testBadge}>MODE TEST</div>
                </div>

                {/* Amount display */}
                <div style={styles.amountBox}>
                    <span style={styles.amountLabel}>Montant à payer</span>
                    <span style={styles.amountValue}>
                        {amount.toLocaleString('fr-FR')} <small>XOF</small>
                    </span>
                </div>

                {status === 'idle' || status === 'loading' || status === 'error' ? (
                    <>
                        {/* Provider selection */}
                        <div style={styles.providersGrid}>
                            {PROVIDERS.map((p) => (
                                <button
                                    key={p.id}
                                    onClick={() => setSelectedProvider(p.id)}
                                    style={{
                                        ...styles.providerBtn,
                                        borderColor: selectedProvider === p.id ? p.color : '#E5E7EB',
                                        backgroundColor: selectedProvider === p.id ? `${p.color}15` : '#FFF',
                                    }}
                                >
                                    <span style={{ fontWeight: 600, color: p.color }}>{p.label}</span>
                                    <span style={styles.providerPrefix}>Préfixe: {p.prefix}</span>
                                </button>
                            ))}
                        </div>

                        {/* Phone input */}
                        <div style={styles.inputGroup}>
                            <label style={styles.label}>Numéro de téléphone</label>
                            <input
                                type="tel"
                                placeholder="+225 07 XX XX XX XX"
                                value={phoneNumber}
                                onChange={(e) => handlePhoneChange(e.target.value)}
                                style={styles.input}
                            />
                            <span style={styles.hint}>
                                Numéro Orange, MTN, Wave ou Moov
                            </span>
                        </div>

                        {/* Test numbers info */}
                        {selectedProvider && TEST_NUMBERS[selectedProvider] && (
                            <div style={styles.testInfo}>
                                <strong>🧪 Numéro test:</strong> {TEST_NUMBERS[selectedProvider].number}
                                <br />
                                <strong>🔑 PIN:</strong> {TEST_NUMBERS[selectedProvider].pin}
                            </div>
                        )}

                        {/* Error */}
                        {error && <div style={styles.errorBox}>{error}</div>}

                        {/* Pay button */}
                        <button
                            onClick={initiatePayment}
                            disabled={status === 'loading'}
                            style={{
                                ...styles.payBtn,
                                opacity: status === 'loading' ? 0.6 : 1,
                            }}
                        >
                            {status === 'loading' ? 'Traitement...' : 'Payer maintenant'}
                        </button>
                    </>
                ) : status === 'redirecting' ? (
                    <div style={styles.resultBox}>
                        <h2 style={{ color: '#059669' }}>✅ Facture créée</h2>
                        <p>Référence: <strong>{paymentRef}</strong></p>
                        {instructions && <p style={styles.testInfo}>{instructions}</p>}
                        {paymentUrl && (
                            <a
                                href={paymentUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={styles.paydunyaLink}
                            >
                                Ouvrir PayDunya Checkout →
                            </a>
                        )}
                        <button onClick={verifyPayment} style={styles.verifyBtn}>
                            Vérifier le paiement
                        </button>
                        {error && <p style={{ color: '#D97706', marginTop: 8 }}>{error}</p>}
                    </div>
                ) : status === 'verifying' ? (
                    <div style={styles.resultBox}>
                        <p>⏳ Vérification en cours...</p>
                    </div>
                ) : status === 'success' ? (
                    <div style={styles.resultBox}>
                        <h2 style={{ color: '#059669' }}>🎉 Paiement confirmé!</h2>
                        <p>Votre assurance Wali est maintenant <strong>active</strong>.</p>
                        <button
                            onClick={() => router.push('/dashboard')}
                            style={styles.payBtn}
                        >
                            Retour au tableau de bord
                        </button>
                    </div>
                ) : null}
            </div>
        </div>
    );
}

// ==================== Styles ====================

const styles: Record<string, React.CSSProperties> = {
    container: {
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
        fontFamily: "'Inter', -apple-system, sans-serif",
    },
    card: {
        background: '#FFFFFF',
        borderRadius: 16,
        padding: 32,
        maxWidth: 480,
        width: '100%',
        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24,
    },
    title: {
        fontSize: 22,
        fontWeight: 700,
        color: '#1E293B',
        margin: 0,
    },
    testBadge: {
        background: '#FEF3C7',
        color: '#D97706',
        fontSize: 11,
        fontWeight: 700,
        padding: '4px 10px',
        borderRadius: 12,
        letterSpacing: 0.5,
    },
    amountBox: {
        background: 'linear-gradient(135deg, #059669, #047857)',
        borderRadius: 12,
        padding: '16px 20px',
        color: '#FFF',
        marginBottom: 24,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    amountLabel: {
        fontSize: 14,
        opacity: 0.9,
    },
    amountValue: {
        fontSize: 28,
        fontWeight: 800,
    },
    providersGrid: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 10,
        marginBottom: 20,
    },
    providerBtn: {
        border: '2px solid #E5E7EB',
        borderRadius: 10,
        padding: '12px 10px',
        cursor: 'pointer',
        textAlign: 'center' as const,
        background: '#FFF',
        transition: 'all 0.2s',
        display: 'flex',
        flexDirection: 'column' as const,
        gap: 4,
    },
    providerPrefix: {
        fontSize: 11,
        color: '#9CA3AF',
    },
    inputGroup: {
        marginBottom: 16,
    },
    label: {
        display: 'block',
        fontSize: 13,
        fontWeight: 600,
        color: '#374151',
        marginBottom: 6,
    },
    input: {
        width: '100%',
        padding: '12px 14px',
        borderRadius: 8,
        border: '1.5px solid #D1D5DB',
        fontSize: 16,
        outline: 'none',
        boxSizing: 'border-box' as const,
    },
    hint: {
        fontSize: 12,
        color: '#9CA3AF',
        marginTop: 4,
        display: 'block',
    },
    testInfo: {
        background: '#EFF6FF',
        border: '1px solid #BFDBFE',
        borderRadius: 8,
        padding: 12,
        fontSize: 13,
        color: '#1E40AF',
        marginBottom: 16,
        lineHeight: 1.6,
    },
    errorBox: {
        background: '#FEF2F2',
        border: '1px solid #FECACA',
        borderRadius: 8,
        padding: 12,
        fontSize: 13,
        color: '#DC2626',
        marginBottom: 16,
    },
    payBtn: {
        width: '100%',
        padding: '14px 20px',
        borderRadius: 10,
        background: 'linear-gradient(135deg, #059669, #047857)',
        color: '#FFF',
        fontSize: 16,
        fontWeight: 700,
        border: 'none',
        cursor: 'pointer',
        transition: 'opacity 0.2s',
    },
    resultBox: {
        textAlign: 'center' as const,
        padding: '20px 0',
    },
    paydunyaLink: {
        display: 'block',
        background: '#2563EB',
        color: '#FFF',
        padding: '12px 20px',
        borderRadius: 8,
        textDecoration: 'none',
        fontWeight: 600,
        marginTop: 16,
        marginBottom: 12,
    },
    verifyBtn: {
        background: '#F3F4F6',
        color: '#374151',
        border: '1px solid #D1D5DB',
        borderRadius: 8,
        padding: '10px 20px',
        cursor: 'pointer',
        fontWeight: 600,
        marginTop: 8,
    },
};
