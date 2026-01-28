import { createClient, RedisClientType } from 'redis';
import { config } from '../config';
import { OTPData } from '../types';
import { logger } from '../utils/logger';
import { orangeSMSService } from './sms.service';
import { MockRedisClient } from './mock-redis';

export class OTPService {
    private redisClient: any; // Can be Real or Mock

    constructor() {
        this.initializeClient();
    }

    private async initializeClient() {
        // Try connecting to real Redis with a short timeout / limited retries
        const realClient = createClient({
            url: config.redisUrl,
            socket: {
                connectTimeout: 2000,
                reconnectStrategy: (retries) => {
                    if (retries > 2) {
                        return new Error('Max retries reached'); // Stop reconciling
                    }
                    return 500; // Retry after 500ms
                }
            }
        });

        realClient.on('error', (err: any) => {
            // Only log if we haven't switched to mock yet
            if (this.redisClient !== realClient) return;
            logger.warn(`Redis connection warning: ${err.message}`);
        });

        try {
            await realClient.connect();
            this.redisClient = realClient;
            logger.info('Connected to Real Redis');
        } catch (error) {
            logger.warn('Failed to connect to Redis (Max retries or timeout). Switching to Mock Redis.');
            try {
                await realClient.disconnect(); // Ensure it stops trying
            } catch (e) { /* ignore disconnect error */ }

            this.redisClient = new MockRedisClient();
            this.redisClient.isMock = true;
            await this.redisClient.connect();
        }
    }

    /**
     * Generate random 6-digit OTP code
     */
    private generateCode(): string {
        return Math.floor(100000 + Math.random() * 900000).toString();
    }

    /**
     * Generate and send OTP
     */
    async generateOTP(phone: string): Promise<{ success: boolean; message: string }> {
        try {
            // Ensure client is ready (mock fallback if needed)
            if (!this.redisClient) {
                this.redisClient = new MockRedisClient();
                this.redisClient.isMock = true;
                await this.redisClient.connect();
            }

            const client = this.redisClient;

            // Check rate limiting
            const rateLimitKey = `ratelimit:sms:${phone}`;
            const count = await client.get(rateLimitKey);

            if (count && parseInt(count) >= config.smsRateLimitPerPhone) {
                return {
                    success: false,
                    message: 'Trop de tentatives. Réessayez dans 1 heure.',
                };
            }

            // Generate OTP
            const code = this.generateCode();
            const otpData: OTPData = {
                code,
                phone,
                attempts: 0,
                createdAt: Date.now(),
            };

            // Store OTP in Redis with expiry
            const otpKey = `otp:${phone}`;
            await client.setEx(
                otpKey,
                config.otpExpiryMinutes * 60,
                JSON.stringify(otpData)
            );

            // Update rate limit counter
            const currentCount = count ? parseInt(count) : 0;
            await client.setEx(rateLimitKey, 3600, (currentCount + 1).toString());

            // Send SMS
            const smsSent = await orangeSMSService.sendOTP(phone, code);

            if (!smsSent) {
                // If real SMS fails, and we are in DEV, fallback to simulation
                if (process.env.NODE_ENV === 'development') {
                    logger.info(`[DEV FALLBACK] SMS failed, but returning success with code: ${code}`);
                    return { success: true, message: 'Code OTP (Simulé) envoyé.' };
                }

                return {
                    success: false,
                    message: 'Échec de l\'envoi du SMS. Réessayez.',
                };
            }

            logger.info(`OTP generated for ${phone}: ${code}`);

            return {
                success: true,
                message: 'Code OTP envoyé par SMS.',
            };
        } catch (error) {
            logger.error('Error generating OTP:', error);
            return {
                success: false,
                message: 'Erreur serveur. Réessayez plus tard.',
            };
        }
    }

    /**
     * Verify OTP code
     */
    async verifyOTP(phone: string, code: string): Promise<{ success: boolean; message: string }> {
        try {
            if (!this.redisClient) {
                this.redisClient = new MockRedisClient();
                this.redisClient.isMock = true;
                await this.redisClient.connect();
            }

            const client = this.redisClient;
            const otpKey = `otp:${phone}`;
            const otpDataStr = await client.get(otpKey);

            // Dev backdoor
            if (process.env.NODE_ENV === 'development' && code === '123456') {
                logger.info(`[DEV] Backdoor access granted for ${phone}`);
                return { success: true, message: 'Code développeur accepté.' };
            }

            if (!otpDataStr) {
                return {
                    success: false,
                    message: 'Code expiré ou invalide.',
                };
            }

            const otpData: OTPData = JSON.parse(otpDataStr);

            // Check max attempts
            if (otpData.attempts >= config.otpMaxAttempts) {
                await client.del(otpKey);
                return {
                    success: false,
                    message: 'Trop de tentatives incorrectes. Demandez un nouveau code.',
                };
            }

            // Verify code
            if (otpData.code !== code) {
                otpData.attempts += 1;
                await client.setEx(
                    otpKey,
                    config.otpExpiryMinutes * 60,
                    JSON.stringify(otpData)
                );

                return {
                    success: false,
                    message: `Code incorrect. ${config.otpMaxAttempts - otpData.attempts} tentatives restantes.`,
                };
            }

            // Success - delete OTP
            await client.del(otpKey);
            logger.info(`OTP verified successfully for ${phone}`);

            return {
                success: true,
                message: 'Code vérifié avec succès.',
            };
        } catch (error) {
            logger.error('Error verifying OTP:', error);
            // Dev backdoor logic repeated in catch just in case
            if (process.env.NODE_ENV === 'development' && code === '123456') {
                return { success: true, message: 'Code développeur accepté.' };
            }
            return {
                success: false,
                message: 'Erreur serveur. Réessayez plus tard.',
            };
        }
    }

    /**
     * Check if phone has active OTP
     */
    async hasActiveOTP(phone: string): Promise<boolean> {
        const client = this.redisClient || new MockRedisClient();
        const otpKey = `otp:${phone}`;
        const exists = await client.exists(otpKey);
        return exists === 1;
    }

    /**
     * Get remaining OTP expiry time in seconds
     */
    async getOTPExpiry(phone: string): Promise<number> {
        const client = this.redisClient || new MockRedisClient();
        const otpKey = `otp:${phone}`;
        return await client.ttl(otpKey);
    }
}

export const otpService = new OTPService();
