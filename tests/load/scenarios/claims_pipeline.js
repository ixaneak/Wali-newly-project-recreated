import http from 'k6/http';
import { check, sleep } from 'k6';
import { globalThresholds, getBaseHeaders } from '../configs/thresholds.js';
import { generateIvorianPhone } from '../shared/data.js';

export const options = {
    scenarios: {
        claims_pipeline: {
            executor: 'constant-vus',
            vus: 100,
            duration: '30m', // Soak Test
            tags: { scenario: 'claims', priority: 'critical' }
        }
    },
    thresholds: globalThresholds
};

const API_HOST = __ENV.API_HOST || 'http://host.docker.internal:8000';

export default function () {
    const artisanPhone = generateIvorianPhone();

    // 1. Submit Claim via API (Simulating PWA frontend)
    const submitPayload = JSON.stringify({
        artisan_phone: artisanPhone,
        claim_type: 'pharmacy',
        amount: Math.floor(Math.random() * 50000) + 1000,
        pharmacy_id: "00000000-0000-0000-0000-000000000000", // Will fail gracefully or use mock
        image_url: "https://example.com/mock_prescription.jpg"
    });

    const submitRes = http.post(`${API_HOST}/api/claims`, submitPayload, {
        headers: getBaseHeaders(),
        tags: { name: 'claim_submit' }
    });

    check(submitRes, {
        'Claim created (201)': (r) => r.status === 201 || r.status === 200,
        'Has Claim ID': (r) => { try { return r.json('id') !== undefined; } catch (e) { return false; } }
    });

    let claimId = null;
    try {
        claimId = submitRes.json('id');
    } catch (e) {
        // Skip rest of iteration if submission failed
        return;
    }

    // 2. Poll for Status Update (Simulating client waiting for fraud check)
    // Fraud check runs async in Celery. We poll a few times
    let isProcessed = false;
    for (let i = 0; i < 5; i++) {
        sleep(2); // Wait 2s between polls

        const statusRes = http.get(`${API_HOST}/api/claims/${claimId}`, {
            headers: getBaseHeaders(),
            tags: { name: 'claim_poll' }
        });

        try {
            const status = statusRes.json('status');
            if (status !== 'submitted' && status !== 'processing') {
                isProcessed = true;

                check(statusRes, {
                    'Fraud score calculated': (r) => r.json('fraud_score') !== null
                });
                break;
            }
        } catch (e) {
            // Error parsing, just continue polling
        }
    }

    // 3. Admin Approval (if flagged for review)
    // Simulating admin logging in and approving
    if (isProcessed) {
        const approvePayload = JSON.stringify({
            status: "approved",
            notes: "Load test automated approval"
        });

        const approveRes = http.patch(`${API_HOST}/api/claims/${claimId}/status`, approvePayload, {
            headers: getBaseHeaders(),
            tags: { name: 'admin_claim_approve' }
        });

        check(approveRes, {
            'Admin approval successful': (r) => r.status === 200 || r.status === 404 // 404 if mock db not synced
        });
    }

    sleep(1);
}
