// k6 Threshold Definitions
export const globalThresholds = {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests must complete below 0.5s
    http_req_failed: ['rate<0.001'],                // Less than 0.1% error rate
    checks: ['rate>0.99'],                          // 99% of assertions check(res, ...) must pass
    iteration_duration: ['p(95)<30000']             // Overall VUs iteration < 30s
};

export const loadImpactOptions = {
    distribution: {
        'amazon:fr:paris': { loadZone: 'amazon:fr:paris', percent: 100 }
    }
};

export const getBaseHeaders = () => {
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };
};
