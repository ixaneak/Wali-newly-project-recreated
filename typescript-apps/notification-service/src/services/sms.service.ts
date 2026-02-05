import axios from 'axios';
import { config } from '../config';
import { logger } from '../utils/logger';

interface OrangeAuthResponse {
    token_type: string;
    access_token: string;
    expires_in: number;
}

export class OrangeSMSService {
    private accessToken: string | null = null;
    private tokenExpiry: number = 0;

    /**
     * Get OAuth2 access token for Orange SMS API
     */
    private async getAccessToken(): Promise<string> {
        // Check if token is still valid
        if (this.accessToken && Date.now() < this.tokenExpiry) {
            return this.accessToken;
        }

        try {
            const auth = Buffer.from(
                `${config.orangeSmsClientId}:${config.orangeSmsClientSecret}`
            ).toString('base64');

            const response = await axios.post<OrangeAuthResponse>(
                'https://api.orange.com/oauth/v3/token',
                'grant_type=client_credentials',
                {
                    headers: {
                        'Authorization': `Basic ${auth}`,
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                }
            );

            this.accessToken = response.data.access_token;
            this.tokenExpiry = Date.now() + (response.data.expires_in * 1000) - 60000; // 1 min buffer

            logger.info('Orange SMS: Access token obtained');
            return this.accessToken;
        } catch (error) {
            logger.error('Orange SMS: Failed to get access token', error);
            throw new Error('Failed to authenticate with Orange SMS API');
        }
    }

    /**
     * Send SMS via Orange SMS API
     */
    async sendSMS(phone: string, message: string): Promise<boolean> {
        try {
            const token = await this.getAccessToken();

            // Format phone number for Côte d'Ivoire (+225)
            const formattedPhone = phone.startsWith('+225') ? phone : `+225${phone}`;

            const payload = {
                outboundSMSMessageRequest: {
                    address: `tel:${formattedPhone}`,
                    senderAddress: `tel:${config.orangeSenderName}`,
                    outboundSMSTextMessage: {
                        message: message,
                    },
                },
            };

            const response = await axios.post(
                `${config.orangeSmsBaseUrl}/outbound/${encodeURIComponent(config.orangeSenderName)}/requests`,
                payload,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            logger.info(`SMS sent to ${formattedPhone}: ${response.data.outboundSMSMessageRequest.resourceURL}`);
            return true;
        } catch (error: any) {
            logger.error(`Failed to send SMS to ${phone}:`, error.response?.data || error.message);
            return false;
        }
    }

    /**
     * Send OTP code via SMS
     */
    async sendOTP(phone: string, code: string): Promise<boolean> {
        const message = `Votre code Wali est: ${code}. Valide pour 5 minutes. Ne partagez pas ce code.`;
        return this.sendSMS(phone, message);
    }

    /**
     * Send payment confirmation SMS
     */
    async sendPaymentConfirmation(phone: string, amount: number, policyNumber: string): Promise<boolean> {
        const message = `Paiement de ${amount} XOF reçu pour la police ${policyNumber}. Merci d'utiliser Wali!`;
        return this.sendSMS(phone, message);
    }

    /**
     * Send claim approved SMS
     */
    async sendClaimApproved(phone: string, claimNumber: string, amount: number): Promise<boolean> {
        const message = `Votre réclamation ${claimNumber} a été approuvée. Montant: ${amount} XOF. Le paiement sera traité sous peu.`;
        return this.sendSMS(phone, message);
    }

    /**
     * Send claim rejected SMS
     */
    async sendClaimRejected(phone: string, claimNumber: string, reason: string): Promise<boolean> {
        const message = `Votre réclamation ${claimNumber} a été rejetée. Raison: ${reason}. Contactez le support pour plus d'infos.`;
        return this.sendSMS(phone, message);
    }

    /**
     * Send policy expiring warning
     */
    async sendPolicyExpiring(phone: string, policyNumber: string, daysRemaining: number): Promise<boolean> {
        const message = `Attention! Votre police ${policyNumber} expire dans ${daysRemaining} jours. Renouvelez maintenant pour rester protégé.`;
        return this.sendSMS(phone, message);
    }
}

export const orangeSMSService = new OrangeSMSService();
