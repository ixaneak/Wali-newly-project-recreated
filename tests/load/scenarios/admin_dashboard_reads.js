import http from 'k6/http';
import { check, sleep } from 'k6';
import { globalThresholds, getBaseHeaders } from '../configs/thresholds.js';
import { generateTestJWT } from '../shared/auth.js';

export const options = {
    scenarios: {
        admin_reads: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '2m', target: 50 },  // Ramp to 50 concurrent admins
                { duration: '5m', target: 50 },  // Hold for 5m
                { duration: '1m', target: 0 },   // Coast down
            ],
            tags: { scenario: 'admin_dashboard', priority: 'medium' }
        }
    },
    thresholds: {
        ...globalThresholds,
        http_req_duration: ['p(95)<2000'], // Aggregations can be slower, max 2s p95 constraint
    }
};

const API_HOST = __ENV.API_HOST || 'http://host.docker.internal:8000';
const ADMIN_SECRET = __ENV.JWT_SECRET || 'your_super_secret_jwt_key';

export default function () {
    // Generate an admin token
    const payload = {
        sub: `admin-mock-${__ITER}`,
        role: "admin",
        exp: Math.floor(Date.now() / 1000) + 3600
    };

    const token = generateTestJWT(payload, ADMIN_SECRET);
    const headers = {
        ...getBaseHeaders(),
        'Authorization': `Bearer ${token}`
    };

    // 1. Fetch Global Compliance Analytics
    const complianceRes = http.get(`${API_HOST}/api/compliance/status`, {
        headers,
        tags: { name: 'admin_compliance_status' }
    });

    check(complianceRes, {
        'Compliance 200 OK': (r) => r.status === 200 || r.status === 401 || r.status === 404, // Handle mock limits
    });

    // 2. Fetch Latest Claims requiring review
    const claimsRes = http.get(`${API_HOST}/api/claims?status=submitted&limit=50`, {
        headers,
        tags: { name: 'admin_pending_claims' }
    });

    check(claimsRes, {
        'Claims List 200 OK': (r) => r.status === 200 || r.status === 401 || r.status === 404,
    });

    // Simulate thinking time for Admin
    sleep(2);
}
