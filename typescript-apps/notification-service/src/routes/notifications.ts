import { Router, Request, Response } from 'express';
import { otpService } from '../services/otp.service';
import { orangeSMSService } from '../services/sms.service';
import { OTPGenerateRequest, OTPVerifyRequest, NotificationPayload } from '../types';
import { logger } from '../utils/logger';

const router = Router();

/**
 * POST /api/v1/notifications/otp/generate
 * Generate and send OTP code
 */
router.post('/otp/generate', async (req: Request, res: Response) => {
    try {
        const { phone }: OTPGenerateRequest = req.body;

        if (!phone) {
            return res.status(400).json({
                success: false,
                message: 'Numéro de téléphone requis',
            });
        }

        // Validate phone format (+225XXXXXXXX)
        const phoneRegex = /^\+?225[0-9]{10}$/;
        if (!phoneRegex.test(phone.replace(/\s/g, ''))) {
            return res.status(400).json({
                success: false,
                message: 'Format de téléphone invalide. Utilisez +225XXXXXXXXXX',
            });
        }

        const result = await otpService.generateOTP(phone);

        return res.status(result.success ? 200 : 400).json(result);
    } catch (error) {
        logger.error('Error in OTP generate endpoint:', error);
        return res.status(500).json({
            success: false,
            message: 'Erreur serveur',
        });
    }
});

/**
 * POST /api/v1/notifications/otp/verify
 * Verify OTP code
 */
router.post('/otp/verify', async (req: Request, res: Response) => {
    try {
        const { phone, code }: OTPVerifyRequest = req.body;

        if (!phone || !code) {
            return res.status(400).json({
                success: false,
                message: 'Téléphone et code requis',
            });
        }

        const result = await otpService.verifyOTP(phone, code);

        return res.status(result.success ? 200 : 400).json(result);
    } catch (error) {
        logger.error('Error in OTP verify endpoint:', error);
        return res.status(500).json({
            success: false,
            message: 'Erreur serveur',
        });
    }
});

/**
 * GET /api/v1/notifications/otp/status/:phone
 * Check OTP status for a phone number
 */
router.get('/otp/status/:phone', async (req: Request, res: Response) => {
    try {
        const { phone } = req.params;

        const hasActive = await otpService.hasActiveOTP(phone);
        const expiry = await otpService.getOTPExpiry(phone);

        return res.json({
            hasActiveOTP: hasActive,
            expiresIn: expiry > 0 ? expiry : 0,
        });
    } catch (error) {
        logger.error('Error in OTP status endpoint:', error);
        return res.status(500).json({
            success: false,
            message: 'Erreur serveur',
        });
    }
});

/**
 * POST /api/v1/notifications/send
 * Send notification (payment, claim status, etc.)
 */
router.post('/send', async (req: Request, res: Response) => {
    try {
        const { type, phone, data }: NotificationPayload = req.body;

        if (!type || !phone) {
            return res.status(400).json({
                success: false,
                message: 'Type et téléphone requis',
            });
        }

        let sent = false;

        switch (type) {
            case 'payment_success':
                sent = await orangeSMSService.sendPaymentConfirmation(
                    phone,
                    data.amount,
                    data.policyNumber
                );
                break;

            case 'claim_approved':
                sent = await orangeSMSService.sendClaimApproved(
                    phone,
                    data.claimNumber,
                    data.amount
                );
                break;

            case 'claim_rejected':
                sent = await orangeSMSService.sendClaimRejected(
                    phone,
                    data.claimNumber,
                    data.reason || 'Voir l\'application pour plus de détails'
                );
                break;

            case 'policy_expiring':
                sent = await orangeSMSService.sendPolicyExpiring(
                    phone,
                    data.policyNumber,
                    data.daysRemaining
                );
                break;

            default:
                return res.status(400).json({
                    success: false,
                    message: 'Type de notification invalide',
                });
        }

        return res.json({
            success: sent,
            message: sent ? 'Notification envoyée' : 'Échec de l\'envoi',
        });
    } catch (error) {
        logger.error('Error in send notification endpoint:', error);
        return res.status(500).json({
            success: false,
            message: 'Erreur serveur',
        });
    }
});

export default router;
