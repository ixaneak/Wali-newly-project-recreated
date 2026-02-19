/**
 * WALI Load Test Script
 * 
 * Simulates 10,000 concurrent users across Ivory Coast
 * Tests QR generation, pharmacy verification, AI concierge, and payment webhooks
 * 
 * Usage:
 *   k6 run --vus 1 --iterations 1 load-tests/wali-load-test.js  # Dry run
 *   k6 run load-tests/wali-load-test.js                          # Full test
 *   k6 cloud run load-tests/wali-load-test.js                    # Distributed
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// ═════════════════════════════════════════════════════════════════
// CUSTOM METRICS
// ═════════════════════════════════════════════════════════════════

const pharmacyCheckErrorRate = new Rate('pharmacy_check_errors');
const qrGenerationTime = new Trend('qr_generation_time');
const claimSubmissionTime = new Trend('claim_submission_time');
const aiResponseTime = new Trend('ai_response_time');
const webhookProcessingTime = new Trend('webhook_processing_time');
const sarDetectionCounter = new Counter('sar_detections_triggered');

// ═════════════════════════════════════════════════════════════════
// TEST CONFIGURATION
// ═════════════════════════════════════════════════════════════════

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100 users
    { duration: '5m', target: 100 },   // Stay at 100 users (baseline)
    { duration: '2m', target: 400 },   // Ramp up to 400 users
    { duration: '5m', target: 400 },   // Stay at 400 users (peak)
    { duration: '2m', target: 1000 },  // Stress test: 1000 users
    { duration: '5m', target: 1000 },  // Sustained high load
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],      // 95% of requests <500ms
    http_req_failed: ['rate<0.01'],        // Error rate <1%
    pharmacy_check_errors: ['rate<0.05'],  // Pharmacy checks <5% errors
    qr_generation_time: ['p(95)<200'],     // QR generation <200ms
    ai_response_time: ['p(95)<3000'],      // AI responses <3s
  },
};

// ═════════════════════════════════════════════════════════════════
// ENVIRONMENT CONFIG
// ═════════════════════════════════════════════════════════════════

const BASE_URL = __ENV.BASE_URL || 'https://wali-policy-service.fly.dev';
const CLAIMS_URL = __ENV.CLAIMS_URL || 'https://wali-claims-service.fly.dev';
const AI_URL = __ENV.AI_URL || 'https://wali-ai-concierge.fly.dev';
const PAYMENT_URL = __ENV.PAYMENT_URL || 'https://payment-gateway-service.fly.dev';
const API_KEY = __ENV.API_KEY || '';

const params = {
  headers: {
    'Content-Type': 'application/json',
    'Authorization': API_KEY ? `Bearer ${API_KEY}` : '',
  },
};

// ═════════════════════════════════════════════════════════════════
// TEST SCENARIOS
// ═════════════════════════════════════════════════════════════════

export default function () {
  
  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 1: Health Check (Lightweight probe)
  // ═══════════════════════════════════════════════════════════════
  group('Health Check', function () {
    const res = http.get(`${BASE_URL}/health`);
    check(res, {
      'health status is 200': (r) => r.status === 200,
      'health response time <200ms': (r) => r.timings.duration < 200,
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 2: QR Generation (High Traffic - Insurance Cards)
  // ═══════════════════════════════════════════════════════════════
  group('QR Generation', function () {
    const policyId = `POL-TEST-${randomIntBetween(1, 10000)}`;
    const startTime = Date.now();
    
    const res = http.get(`${BASE_URL}/api/v1/partners/NSIA/enrollments/${policyId}/qr`, params);
    
    qrGenerationTime.add(Date.now() - startTime);
    
    check(res, {
      'qr status is 200 or 404': (r) => r.status === 200 || r.status === 404,
      'qr response time <500ms': (r) => r.timings.duration < 500,
    });
    
    sleep(randomIntBetween(1, 3)); // User looks at QR for 1-3 seconds
  });

  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 3: Policy Enrollment (New subscriptions)
  // ═══════════════════════════════════════════════════════════════
  group('Policy Enrollment', function () {
    const phone = `+22501${randomIntBetween(1000000, 9999999)}`;
    const payload = JSON.stringify({
      user_id: `user_${phone}`,
      partner_product_id: 'NSIA-HEALTH-01',
      partner_product_config: {
        coverage_type: 'health',
        family_size: randomIntBetween(1, 5),
      },
      payment_frequency: 'monthly',
    });

    const res = http.post(
      `${BASE_URL}/api/v1/partners/NSIA/enrollments`,
      payload,
      params
    );
    
    check(res, {
      'enrollment accepted': (r) => r.status === 201 || r.status === 200 || r.status === 409,
      'enrollment response time <800ms': (r) => r.timings.duration < 800,
    });
    
    // Check if SAR was triggered (rapid enrollment)
    if (res.json('fraud_score') > 40) {
      sarDetectionCounter.add(1);
    }
  });

  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 4: Pharmacy Verification (Critical Path)
  // ═══════════════════════════════════════════════════════════════
  group('Pharmacy Verification', function () {
    const payload = JSON.stringify({
      qr_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test',
      pharmacy_id: `PHARM-${randomIntBetween(1, 500)}`,
      medicine_code: ['PARA_500', 'AMOX_500', 'IBU_400', 'METFORMIN_500'][randomIntBetween(0, 3)],
      amount: randomIntBetween(1000, 50000),
    });

    const startTime = Date.now();
    const res = http.post(
      `${CLAIMS_URL}/api/v1/pharmacy/verify`,
      payload,
      params
    );
    
    const success = check(res, {
      'pharmacy verify status is 200': (r) => r.status === 200,
      'pharmacy response time <800ms': (r) => r.timings.duration < 800,
    });
    
    pharmacyCheckErrorRate.add(!success);
    sleep(randomIntBetween(2, 5)); // Pharmacist takes 2-5 seconds per patient
  });

  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 5: Incident Report Submission (Claims)
  // ═══════════════════════════════════════════════════════════════
  group('Incident Report', function () {
    const payload = JSON.stringify({
      user_id: `user_${randomIntBetween(1, 10000)}`,
      subscription_id: `sub_${randomIntBetween(1, 10000)}`,
      partner_id: 'NSIA',
      incident_type: 'ACCIDENT',
      description: 'Test incident report for load testing',
      reported_amount: randomIntBetween(50000, 500000),
      photos: ['https://cdn.wali.ci/photos/test1.jpg'],
    });

    const startTime = Date.now();
    const res = http.post(
      `${CLAIMS_URL}/api/v1/partners/NSIA/incidents/submit-json`,
      payload,
      params
    );
    
    claimSubmissionTime.add(Date.now() - startTime);
    
    check(res, {
      'incident submitted': (r) => r.status === 201 || r.status === 200,
      'incident response time <1000ms': (r) => r.timings.duration < 1000,
    });
    
    // Track SAR detection for rapid claims
    if (res.json('fraud_score') > 40) {
      sarDetectionCounter.add(1);
    }
  });

  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 6: AI Concierge (WhatsApp/Chat)
  // ═══════════════════════════════════════════════════════════════
  group('AI Concierge', function () {
    const messages = [
      'Bonjour',
      'Comment ça marche?',
      'J\'ai un accident',
      'Pharmacie proche?',
      'Combien ça coûte?',
      'Je veux m\'inscrire',
    ];
    
    const payload = JSON.stringify({
      phone_number: `+22501${randomIntBetween(1000000, 9999999)}`,
      message: messages[randomIntBetween(0, messages.length - 1)],
      context: 'whatsapp',
    });

    const startTime = Date.now();
    const res = http.post(
      `${AI_URL}/api/chat`,
      payload,
      params
    );
    
    aiResponseTime.add(Date.now() - startTime);
    
    check(res, {
      'chat status is 200': (r) => r.status === 200,
      'chat response time <3000ms': (r) => r.timings.duration < 3000,
    });
    
    sleep(randomIntBetween(5, 10)); // User reads response
  });

  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 7: Payment Webhook (Orange Money)
  // ═══════════════════════════════════════════════════════════════
  group('Payment Webhook', function () {
    const payload = JSON.stringify({
      transaction_id: `TXN-${randomIntBetween(100000, 999999)}`,
      status: ['SUCCESS', 'PENDING', 'FAILED'][randomIntBetween(0, 2)],
      amount: randomIntBetween(500, 5000),
      phone_number: `+22501${randomIntBetween(1000000, 9999999)}`,
      partner_response: {},
    });

    const startTime = Date.now();
    const res = http.post(
      `${PAYMENT_URL}/webhooks/orange-money`,
      payload,
      params
    );
    
    webhookProcessingTime.add(Date.now() - startTime);
    
    check(res, {
      'webhook accepted': (r) => r.status === 200,
      'webhook processed quickly': (r) => r.timings.duration < 100,
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 8: SAR Compliance Dashboard (Admin)
  // ═══════════════════════════════════════════════════════════════
  group('Compliance Dashboard', function () {
    // Get dashboard stats
    const statsRes = http.get(
      `${BASE_URL}/api/v1/compliance/sar/dashboard/stats`,
      params
    );
    
    check(statsRes, {
      'dashboard stats loaded': (r) => r.status === 200,
      'dashboard response time <500ms': (r) => r.timings.duration < 500,
    });

    // Get recent alerts
    const alertsRes = http.get(
      `${BASE_URL}/api/v1/compliance/sar/dashboard/alerts?limit=20`,
      params
    );
    
    check(alertsRes, {
      'alerts loaded': (r) => r.status === 200,
    });
  });

  // Think time between user actions
  sleep(randomIntBetween(1, 3));
}

// ═════════════════════════════════════════════════════════════════
// TEST LIFECYCLE HOOKS
// ═════════════════════════════════════════════════════════════════

export function setup() {
  console.log(`Starting WALI load test against: ${BASE_URL}`);
  console.log('Test configuration:');
  console.log('  - Max VUs: 1000');
  console.log('  - Duration: ~21 minutes');
  console.log('  - Thresholds: p95 <500ms, error rate <1%');
  
  // Verify target is accessible
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error(`Target ${BASE_URL} is not accessible. Status: ${res.status}`);
  }
  
  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`\nTest completed in ${duration}s`);
  console.log('Check the k6 output above for detailed metrics.');
}
