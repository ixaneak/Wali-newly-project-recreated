import dotenv from 'dotenv';

dotenv.config();

export const config = {
    // Server
    port: parseInt(process.env.PORT || '8003', 10),
    nodeEnv: process.env.NODE_ENV || 'development',

    // Redis
    redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',

    // Orange SMS API
    orangeSmsClientId: process.env.ORANGE_SMS_CLIENT_ID || '',
    orangeSmsClientSecret: process.env.ORANGE_SMS_CLIENT_SECRET || '',
    orangeSmsBaseUrl: process.env.ORANGE_SMS_BASE_URL || 'https://api.orange.com/smsmessaging/v1',
    orangeSenderName: process.env.ORANGE_SENDER_NAME || 'Wali',

    // OTP Configuration
    otpLength: 6,
    otpExpiryMinutes: 5,
    otpMaxAttempts: 3,

    // Rate Limiting
    smsRateLimitPerPhone: 3, // Max SMS per phone per hour

    // CORS
    allowedOrigins: (process.env.ALLOWED_ORIGINS || 'http://localhost:3000').split(','),
};
