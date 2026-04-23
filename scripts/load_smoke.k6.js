// ──────────────────────────────────────────────────────────────────────────────
// AMAN ERP — k6 smoke load test (PH10-B7)
//
// Goal: 100 RPS sustained for 1 minute against the read-mostly health/list
// endpoints. Fails the run when p95 latency exceeds 800ms or the error rate
// exceeds 1%.
//
// Usage:
//   AMAN_BASE_URL=http://localhost:8000 \
//   AMAN_TOKEN=$ADMIN_BEARER_TOKEN \
//   k6 run scripts/load_smoke.k6.js
//
// CI integration:
//   - Run against a staging environment (never production).
//   - Export results: ``k6 run --out json=load.json scripts/load_smoke.k6.js``.
// ──────────────────────────────────────────────────────────────────────────────
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const baseUrl = __ENV.AMAN_BASE_URL || 'http://localhost:8000';
const token = __ENV.AMAN_TOKEN || '';

const errorRate = new Rate('errors');

export const options = {
    scenarios: {
        smoke: {
            executor: 'constant-arrival-rate',
            rate: 100,
            timeUnit: '1s',
            duration: '1m',
            preAllocatedVUs: 50,
            maxVUs: 200,
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<800'],
        errors: ['rate<0.01'],
    },
};

const headers = token ? { Authorization: `Bearer ${token}` } : {};

const READ_ENDPOINTS = [
    '/api/health',
    '/api/auth/me',
    '/api/dashboard/summary',
    '/api/inventory/products?limit=20',
    '/api/sales/invoices?limit=20',
    '/api/accounting/journal-entries?limit=20',
];

export default function () {
    const path = READ_ENDPOINTS[Math.floor(Math.random() * READ_ENDPOINTS.length)];
    const res = http.get(`${baseUrl}${path}`, { headers, tags: { endpoint: path } });
    const ok = check(res, {
        'status 2xx/3xx': (r) => r.status >= 200 && r.status < 400,
    });
    errorRate.add(!ok);
    sleep(0.05);
}

export function handleSummary(data) {
    return {
        stdout: JSON.stringify({
            metrics: {
                http_req_duration_p95: data.metrics.http_req_duration.values['p(95)'],
                http_req_duration_avg: data.metrics.http_req_duration.values.avg,
                http_reqs: data.metrics.http_reqs.values.count,
                error_rate: data.metrics.errors ? data.metrics.errors.values.rate : 0,
            },
        }, null, 2),
    };
}
