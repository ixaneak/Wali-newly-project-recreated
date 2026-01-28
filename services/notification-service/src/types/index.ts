export interface OTPData {
    code: string;
    phone: string;
    attempts: number;
    createdAt: number;
}

export interface SMSRequest {
    phone: string;
    message: string;
}

export interface OTPGenerateRequest {
    phone: string;
}

export interface OTPVerifyRequest {
    phone: string;
    code: string;
}

export interface NotificationPayload {
    type: 'payment_success' | 'payment_failed' | 'claim_approved' | 'claim_rejected' | 'policy_expiring';
    phone: string;
    data: Record<string, any>;
}
