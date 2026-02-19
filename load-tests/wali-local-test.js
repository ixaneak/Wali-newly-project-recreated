/**
 * WALI Local Load Test — Policy Service Only
 * 
 * Tests the running policy service including SAR compliance endpoints.
 * Claims/payment services skipped (require DB/module deps not available locally).
 * 
 * Usage:
 *   k6 run load-tests/wali-local-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom Metrics
const sarScanTime = new Trend('sar_scan_time');
const sarDashboardTime = new Trend('sar_dashboard_time');
const healthCheckTime = new Trend('health_check_time');
const riskEventTime = new Trend('risk_event_time');
const errorRate = new Rate('errors');
const sarTriggered = new Counter('sar_detections');

// Config — moderate load for a dev laptop
export const options = {
    stages: [
        { duration: '10s', target: 10 },   // Warm up
        { duration: '30s', target: 10 },   // Baseline
        { duration: '10s', target: 30 },   // Ramp up
        { duration: '30s', target: 30 },   // Sustained
        { duration: '10s', target: 50 },   // Stress
        { duration: '30s', target: 50 },   // Sustained high
        { duration: '10s', target: 0 },    // Cool down
    ],
    thresholds: {
        http_req_duration: ['p(95)<1000'],
        http_req_failed: ['rate<0.15'],
        sar_scan_time: ['p(95)<500'],
        sar_dashboard_time: ['p(95)<300'],
        health_check_time: ['p(95)<200'],
    },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const ADMIN_TOKEN = __ENV.ADMIN_TOKEN || '';

const jsonParams = { headers: { 'Content-Type': 'application/json' } };
const adminParams = {
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ADMIN_TOKEN}`,
    },
};

export default function () {

    // 1. Health Check
    group('Health Check', function () {
        const res = http.get(`${BASE}/health`);
        healthCheckTime.add(res.timings.duration);
        const ok = check(res, {
            'health 200': (r) => r.status === 200,
            'health < 200ms': (r) => r.timings.duration < 200,
        });
        errorRate.add(!ok);
    });

    // 2. SAR Scan Transaction (core compliance)
    group('SAR Scan', function () {
        const amounts = [50000, 100000, 200000, 500000, 600000, 1000000];
        const payload = JSON.stringify({
            user_id: `user_${randomIntBetween(1, 5000)}`,
            amount: amounts[randomIntBetween(0, amounts.length - 1)],
            phone: `+22507${randomIntBetween(1000000, 9999999)}`,
            payer_phone: Math.random() > 0.7
                ? `+22505${randomIntBetween(1000000, 9999999)}`
                : undefined,
            policyholder_phone: `+22507${randomIntBetween(1000000, 9999999)}`,
        });

        const res = http.post(
            `${BASE}/api/v1/compliance/sar/scan-transaction`, payload, adminParams
        );
        sarScanTime.add(res.timings.duration);

        const ok = check(res, {
            'scan 200': (r) => r.status === 200,
        });
        errorRate.add(!ok);

        try {
            if (res.json('scoring_result').risk_score > 40) sarTriggered.add(1);
        } catch { }
    });

    // 3. Risk Events List
    group('Risk Events', function () {
        const res = http.get(
            `${BASE}/api/v1/compliance/sar/risk-events?limit=20`, adminParams
        );
        riskEventTime.add(res.timings.duration);
        const ok = check(res, { 'events 200': (r) => r.status === 200 });
        errorRate.add(!ok);
    });

    // 4. SAR Dashboard
    group('SAR Dashboard', function () {
        const res = http.get(
            `${BASE}/api/v1/compliance/sar/dashboard`, adminParams
        );
        sarDashboardTime.add(res.timings.duration);
        const ok = check(res, { 'dashboard 200': (r) => r.status === 200 });
        errorRate.add(!ok);
    });

    // 5. SAR Reports List
    group('SAR Reports', function () {
        const res = http.get(
            `${BASE}/api/v1/compliance/sar/reports?limit=10`, adminParams
        );
        check(res, { 'reports 200': (r) => r.status === 200 });
    });

    // 6. Policy Enrollment (may return 400/500 without full DB, still tests throughput)
    group('Enrollment', function () {
        const payload = JSON.stringify({
            user_id: `user_+22501${randomIntBetween(1000000, 9999999)}`,
            partner_product_id: 'NSIA-HEALTH-01',
            partner_product_config: { coverage_type: 'health', family_size: randomIntBetween(1, 5) },
            payment_frequency: 'monthly',
        });

        const res = http.post(
            `${BASE}/api/v1/partners/NSIA/enrollments`, payload, jsonParams
        );
        check(res, {
            'enrollment not 500': (r) => r.status !== 500,
        });
    });

    sleep(randomIntBetween(1, 2));
}

export function setup() {
    console.log(`WALI Local Load Test targeting ${BASE}`);
    console.log('Max 50 VUs over ~2.5 minutes');

    const res = http.get(`${BASE}/health`);
    if (res.status !== 200) {
        throw new Error(`Policy service not responding! Status: ${res.status}`);
    }
    console.log('Policy service is UP');
    return { startTime: Date.now() };
}

export function teardown(data) {
    const secs = ((Date.now() - data.startTime) / 1000).toFixed(1);
    console.log(`Completed in ${secs}s`);
}
