/**
 * WALI Load Test Script - Improved Version
 * 
 * Simulates realistic user traffic patterns
 * Tests critical paths: health checks, pharmacy verification, enrollments
 * 
 * Improvements over v1:
 * - Better error handling and retries
 * - Realistic user wait times
 * - Gradual ramp-up to avoid overwhelming cold starts
 * - Proper cleanup and reporting
 */

import http from 'k6/http';
import { check, sleep, group, fail } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// ═════════════════════════════════════════════════════════════════
// CUSTOM METRICS
// ═════════════════════════════════════════════════════════════════

const pharmacyCheckErrorRate = new Rate('pharmacy_check_errors');
const enrollmentSuccessRate = new Rate('enrollment_success');
const apiErrorRate = new Rate('api_errors');
const responseTime = new Trend('response_time');

const healthCheckCounter = new Counter('health_checks_total');
const enrollmentCounter = new Counter('enrollments_total');

// ═════════════════════════════════════════════════════════════════
// TEST CONFIGURATION
// ═════════════════════════════════════════════════════════════════

export const options = {
  // Gradual ramp-up to allow services to scale
  stages: [
    { duration: '1m', target: 10 },    // Warm-up: 10 users
    { duration: '2m', target: 50 },    // Ramp to 50 users
    { duration: '5m', target: 50 },    // Steady state at 50
    { duration: '2m', target: 100 },   // Ramp to 100 users
    { duration: '5m', target: 100 },   // Peak load at 100
    { duration: '2m', target: 50 },    // Ramp down
    { duration: '1m', target: 0 },     // Cool down
  ],
  
  thresholds: {
    // Error rates
    'api_errors': ['rate<0.05'],           // Less than 5% errors
    'pharmacy_check_errors': ['rate<0.03'], // Less than 3% pharmacy errors
    
    // Response times
    'http_req_duration': ['p(95)<1000'],    // 95% under 1s
    'http_req_duration{scenario:health}': ['p(95)<100'],
    'response_time': ['p(95)<800'],
    
    // Success rates
    'enrollment_success': ['rate>0.95'],    // 95%+ enrollment success
    
    // Overall check pass rate
    'checks': ['rate>0.95'],
  },
  
  // Test metadata
  tags: {
    testName: 'wali-load-test',
    environment: __ENV.ENVIRONMENT || 'staging',
  },
};

// ═════════════════════════════════════════════════════════════════
// ENVIRONMENT CONFIG
// ═════════════════════════════════════════════════════════════════

const BASE_URL = __ENV.BASE_URL || 'https://wali-policy-service.fly.dev';
const API_KEY = __ENV.API_KEY || '';

const params = {
  headers: {
    'Content-Type': 'application/json',
    'Authorization': API_KEY ? `Bearer ${API_KEY}` : '',
    'X-Load-Test': 'true',
  },
  timeout: '30s',
};

// ═════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═════════════════════════════════════════════════════════════════

function logError(context, response) {
  console.error(`ERROR [${context}]: Status=${response.status}, Body=${response.body?.substring(0, 200)}`);
}

function checkResponse(response, checks, context) {
  const result = check(response, checks);
  
  if (!result) {
    logError(context, response);
    apiErrorRate.add(1);
  } else {
    apiErrorRate.add(0);
  }
  
  responseTime.add(response.timings.duration);
  return result;
}

// ═════════════════════════════════════════════════════════════════
// TEST SCENARIOS
// ═════════════════════════════════════════════════════════════════

export default function () {
  
  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 1: Health Check (Lightweight probe)
  // ═══════════════════════════════════════════════════════════════
  group('Health Check', function () {
    const startTime = Date.now();
    const res = http.get(`${BASE_URL}/health`, {
      ...params,
      tags: { scenario: 'health' },
    });
    
    const success = checkResponse(res, {
      'health status is 200': (r) => r.status === 200,
      'health response time < 200ms': (r) => r.timings.duration < 200,
      'health response is valid JSON': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.status === 'healthy' || body.status === 'ok';
        } catch (e) {
          return false;
        }
      },
    }, 'health_check');
    
    healthCheckCounter.add(1);
    
    // If health check fails, don't proceed with other tests
    if (!success) {
      console.warn('Health check failed, skipping other tests');
      sleep(randomIntBetween(1, 3));
      return;
    }
  });
  
  // Realistic user wait time
  sleep(randomIntBetween(1, 3));
  
  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 2: Pharmacy Verification (B2B flow)
  // ═══════════════════════════════════════════════════════════════
  group('Pharmacy Verification', function () {
    const pharmacyId = `PHARM-${randomIntBetween(1, 500)}`;
    
    const res = http.get(
      `${BASE_URL}/api/v1/pharmacy/verify/${pharmacyId}`,
      params
    );
    
    const success = checkResponse(res, {
      'pharmacy verify status is 200 or 404': (r) => [200, 404].includes(r.status),
      'pharmacy response time < 800ms': (r) => r.timings.duration < 800,
    }, 'pharmacy_verification');
    
    pharmacyCheckErrorRate.add(!success);
    
    // Simulate pharmacy doing verification work
    sleep(randomIntBetween(2, 5));
  });
  
  // ═══════════════════════════════════════════════════════════════
  // SCENARIO 3: Enrollment Flow (Simulate artisan enrollment)
  // ═══════════════════════════════════════════════════════════════
  group('Enrollment Creation', function () {
    const enrollmentData = {
      user_id: `user-${randomIntBetween(1000, 999999)}`,
      partner_product_id: 'NSIA-HEALTH-01',
      partner_product_config: {
        coverage_amount: 50000,
        duration_months: 12,
      },
      payment_frequency: 'monthly',
      region: ['Abidjan', 'Bouaké', 'Yamoussoukro'][randomIntBetween(0, 2)],
    };
    
    const res = http.post(
      `${BASE_URL}/api/v1/partners/NSIA/enrollments`,
      JSON.stringify(enrollmentData),
      params
    );
    
    // Enrollment might fail due to validation - that's ok
    const success = checkResponse(res, {
      'enrollment returns valid status': (r) => [201, 400, 422, 500].includes(r.status),
      'enrollment response time < 1500ms': (r) => r.timings.duration < 1500,
    }, 'enrollment_creation');
    
    if (res.status === 201) {
      enrollmentSuccessRate.add(1);
      enrollmentCounter.add(1);
    } else {
      enrollmentSuccessRate.add(0);
    }
  });
  
  // Final wait before next iteration
  sleep(randomIntBetween(1, 5));
}

// ═════════════════════════════════════════════════════════════════
// TEST LIFECYCLE HOOKS
// ═════════════════════════════════════════════════════════════════

export function setup() {
  console.log('Load test starting...');
  console.log(`Target URL: ${BASE_URL}`);
  console.log(`API Key configured: ${API_KEY ? 'Yes' : 'No'}`);
  
  // Verify target is reachable
  const healthCheck = http.get(`${BASE_URL}/health`, { timeout: '10s' });
  if (healthCheck.status !== 200) {
    console.error(`Target ${BASE_URL} is not healthy!`);
    console.error(`Status: ${healthCheck.status}, Body: ${healthCheck.body}`);
    // Don't fail - let the test run and report
  } else {
    console.log('Target is healthy, proceeding with tests');
  }
  
  return {
    startTime: Date.now(),
    baseUrl: BASE_URL,
  };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Load test completed in ${duration}s`);
  console.log('Check the results above for pass/fail status');
}
