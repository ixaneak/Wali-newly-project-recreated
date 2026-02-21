import hmac from 'k6/crypto';

/**
 * Calculate HMAC-SHA256 signature for Meta/WhatsApp Webhooks
 * @param {string} payload Raw JSON string body
 * @param {string} secret The APP_SECRET used for verification
 * @returns {string} The sha256 formatted signature
 */
export function generateWhatsAppSignature(payload, secret) {
    const signature = hmac('sha256', secret, payload, 'hex');
    return `sha256=${signature}`;
}

/**
 * Calculate Africa's Talking USSD Sandbox signature format (if needed)
 * Most AT setups use standard form-data locally, but HMAC is provided for completeness.
 */
export function generateATSignature(payload, secret) {
    return hmac('sha256', secret, payload, 'base64');
}
