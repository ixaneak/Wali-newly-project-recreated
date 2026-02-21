import http from 'k6/http';
import { check, sleep } from 'k6';
import { globalThresholds, getBaseHeaders } from '../configs/thresholds.js';
import { generateIvorianPhone, generateFakeTransactionId } from '../shared/data.js';

export const options = {
    scenarios: {
        mobile_money_chaos: {
            executor: 'constant-vus',
            vus: 50,
            duration: '15m',
            tags: { scenario: 'payments', priority: 'high' }
        }
    },
    thresholds: globalThresholds
};

const API_HOST = __ENV.API_HOST || 'http://host.docker.internal:8000';

export default function () {
    const phone = generateIvorianPhone();
    const transactionId = generateFakeTransactionId();
    const amount = Math.floor(Math.random() * 50000) + 1000;

    // Simulate Chaos / Instability
    const r = Math.random();
    let timeout = 10000; // default 10s timeout
    let injectLatency = false;

    if (r < 0.20) {
        // 20% of requests have 5s latency injected (simulated at load generator level or expecting backend to handle slow clients)
        injectLatency = true;
    } else if (r < 0.30) {
        // 10% of requests timeout completely (simulating dropped packets)
        timeout = 10; // 10ms timeout will almost certainly fail
    }

    // 1. Orange Money Callback Simulation
    const orangePayload = JSON.stringify({
        status: 'SUCCESS',
        txnid: transactionId,
        amount: amount,
        customer_msisdn: phone.replace('+225', '')
    });

    const startTime = Date.now();

    // Simulating the external operator calling our backend Webhook
    const orangeRes = http.post(`${API_HOST}/api/payments/orange/callback`, orangePayload, {
        headers: getBaseHeaders(),
        timeout: timeout,
        tags: { name: 'orange_money_callback', chaos: injectLatency ? 'latency' : (timeout === 10 ? 'timeout' : 'none') }
    });

    if (injectLatency) {
        // Hold the connection open to simulate slow 3G on the client side
        sleep(5);
    }

    check(orangeRes, {
        'Orange status 200 (if no timeout)': (r) => {
            if (timeout === 10) return true; // Ignore timeout failures for this check
            return r.status === 200 || r.status === 202;
        }
    });

    // 2. Wave Callback Simulation
    const wavePayload = JSON.stringify({
        id: transactionId,
        type: "checkout.session.completed",
        data: {
            amount: amount,
            currency: "XOF",
            payment_status: "succeeded",
            client_reference: `WALI-${Math.floor(Math.random() * 10000)}`
        }
    });

    const waveRes = http.post(`${API_HOST}/api/payments/wave/webhook`, wavePayload, {
        headers: {
            'Content-Type': 'application/json',
            'wave-signature': `v1,${Math.floor(Date.now() / 1000)},dummy_signature`
        },
        timeout: timeout,
        tags: { name: 'wave_webhook' }
    });

    // 3. Test Idempotency (Send same Wave payload again)
    const waveIdempotencyRes = http.post(`${API_HOST}/api/payments/wave/webhook`, wavePayload, {
        headers: {
            'Content-Type': 'application/json',
            'wave-signature': `v1,${Math.floor(Date.now() / 1000)},dummy_signature`
        },
        tags: { name: 'wave_idempotency_check' }
    });

    check(waveIdempotencyRes, {
        'Idempotency respected (200 success or 409 conflict)': (r) => r.status === 200 || r.status === 409
    });

    sleep(1);
}
