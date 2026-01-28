import axios, { AxiosInstance, AxiosError } from 'axios';

// Base URLs for microservices
const API_BASE_URLS = {
    policy: process.env.NEXT_PUBLIC_POLICY_SERVICE_URL || 'http://localhost:8000',
    payment: process.env.NEXT_PUBLIC_PAYMENT_SERVICE_URL || 'http://localhost:8080',
    claims: process.env.NEXT_PUBLIC_CLAIMS_SERVICE_URL || 'http://localhost:8001',
    compliance: process.env.NEXT_PUBLIC_COMPLIANCE_SERVICE_URL || 'http://localhost:8002',
    notification: process.env.NEXT_PUBLIC_NOTIFICATION_SERVICE_URL || 'http://localhost:8003',
};

// Create axios instances for each service
const createApiClient = (baseURL: string): AxiosInstance => {
    const client = axios.create({
        baseURL,
        timeout: 30000,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    // Request interceptor - add auth token
    client.interceptors.request.use(
        (config) => {
            const token = localStorage.getItem('auth_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        },
        (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    client.interceptors.response.use(
        (response) => response,
        (error: AxiosError) => {
            if (error.response?.status === 401) {
                // Unauthorized - clear token and redirect to login
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_id');
                window.location.href = '/login';
            }
            return Promise.reject(error);
        }
    );

    return client;
};

// API clients for each service
export const policyApi = createApiClient(API_BASE_URLS.policy);
export const paymentApi = createApiClient(API_BASE_URLS.payment);
export const claimsApi = createApiClient(API_BASE_URLS.claims);
export const complianceApi = createApiClient(API_BASE_URLS.compliance);
export const notificationApi = createApiClient(API_BASE_URLS.notification);

// Notification API methods
export const notificationService = {
    generateOTP: (phone: string) =>
        notificationApi.post('/api/v1/notifications/otp/generate', { phone }),

    verifyOTP: (phone: string, code: string) =>
        notificationApi.post('/api/v1/notifications/otp/verify', { phone, code }),

    getOTPStatus: (phone: string) =>
        notificationApi.get(`/api/v1/notifications/otp/status/${phone}`),
};

// Policy API methods
export const policyService = {
    createPolicy: (data: any) =>
        policyApi.post('/api/v1/policies', data),

    getUserPolicies: (userId: string) =>
        policyApi.get(`/api/v1/policies/user/${userId}`),

    getPolicy: (policyId: string) =>
        policyApi.get(`/api/v1/policies/${policyId}`),

    activatePolicy: (policyId: string) =>
        policyApi.post(`/api/v1/policies/${policyId}/activate`),
};

// Payment API methods
export const paymentService = {
    initiatePayment: (data: any) =>
        paymentApi.post('/api/v1/payments/initiate', data),

    verifyPayment: (ref: string, provider: string) =>
        paymentApi.get(`/api/v1/payments/verify/${ref}?provider=${provider}`),
};

// Claims API methods
export const claimsService = {
    submitClaim: (formData: FormData) =>
        claimsApi.post('/api/v1/claims', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        }),

    getUserClaims: (userId: string) =>
        claimsApi.get(`/api/v1/claims/user/${userId}`),

    getClaim: (claimId: string) =>
        claimsApi.get(`/api/v1/claims/${claimId}`),

    getPendingClaims: () =>
        claimsApi.get('/api/v1/claims/admin/pending'),

    reviewClaim: (claimId: string, data: any) =>
        claimsApi.post(`/api/v1/claims/${claimId}/review`, data),
};

// Compliance API methods
export const complianceService = {
    getMonthlyReport: (year: number, month: number) =>
        complianceApi.get(`/api/v1/compliance/reports/monthly/${year}/${month}`, {
            responseType: 'blob',
        }),

    getTaxExemptionStatus: () =>
        complianceApi.get('/api/v1/compliance/tax-exemption-status'),

    getRevenueSegregation: () =>
        complianceApi.get('/api/v1/compliance/revenue-segregation'),
};
