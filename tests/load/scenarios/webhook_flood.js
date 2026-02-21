import http from 'k6/http';
import { check, sleep } from 'k6';
import { globalThresholds } from '../configs/thresholds.js';
import { generateWhatsAppSignature } from '../shared/signatures.js';
import { generateIvorianPhone } from '../shared/data.js';

export const options = {
    scenarios: {
        webhook_flood: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 1000 },
                { duration: '1m', target: 1000 },
                { duration: '30s', target: 0 }
            ],
            tags: { scenario: 'webhook', priority: 'high' }
        }
    },
    thresholds: {
        http_req_duration: ['p(95)<1000'], // Webhooks must be fast
        http_req_failed: ['rate<0.01']     // 1% error tolerance
    }
};

const API_HOST = __ENV.API_HOST || 'http://host.docker.internal:8000';
const APP_SECRET = __ENV.APP_SECRET || 'test_secret';

export default function () {
    const phone = generateIvorianPhone().replace('+', '');

    // 1. WhatsApp Webhook (Meta Format)
    const whatsappPayload = JSON.stringify({
        object: "whatsapp_business_account",
        entry: [{
            id: "1234567890",
            changes: [{
                value: {
                    messaging_product: "whatsapp",
                    metadata: {
                        display_phone_number: "16505551111",
                        phone_number_id: "1234567890"
                    },
                    messages: [{
                        from: phone,
                        id: `wamid.TEST${Math.floor(Date.now() / 1000)}`,
                        timestamp: Math.floor(Date.now() / 1000).toString(),
                        type: "text",
                        text: {
                            body: "Je veux declarer un sinistre"
                        }
                    }]
                }
            }]
        }]
    });

    const signature = generateWhatsAppSignature(whatsappPayload, APP_SECRET);

    const waRes = http.post(`${API_HOST}/api/webhooks/whatsapp`, whatsappPayload, {
        headers: {
            'Content-Type': 'application/json',
            'X-Hub-Signature-256': signature
        },
        tags: { name: 'whatsapp_webhook' }
    });

    check(waRes, {
        'WA status 200': (r) => r.status === 200,
        'WA immediate return': (r) => r.timings.duration < 500
    });

    // 2. USSD Webhook (Africa's Talking Format)
    const ussdPayload = {
        sessionId: `AT${Math.floor(Date.now() / 1000)}`,
        serviceCode: "*130#",
        phoneNumber: `+${phone}`,
        text: "1*2*3"
    };

    const ussdRes = http.post(`${API_HOST}/api/ussd/callback`, ussdPayload, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        tags: { name: 'ussd_webhook' }
    });

    check(ussdRes, {
        'USSD status 200': (r) => r.status === 200 || r.status === 201,
    });

    sleep(1);
}
