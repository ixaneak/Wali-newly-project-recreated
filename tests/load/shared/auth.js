import hmac from 'k6/crypto';
import encoding from 'k6/encoding';

/**
 * Generate a JWT token using HMAC-SHA256
 * @param {Object} payload The claims object
 * @param {string} secret The signing secret
 * @returns {string} The signed JWT token
 */
export function generateTestJWT(payload, secret) {
    const header = {
        alg: 'HS256',
        typ: 'JWT'
    };

    // Base64URL encode function (standard Base64 with + -> -, / -> _, and removing padding =)
    const base64UrlEncode = (obj) => {
        let str = encoding.b64encode(JSON.stringify(obj));
        return str.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    };

    const encodedHeader = base64UrlEncode(header);
    const encodedPayload = base64UrlEncode(payload);

    const signatureBytes = hmac('sha256', secret, `${encodedHeader}.${encodedPayload}`, 'base64');
    const signature = signatureBytes.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    return `${encodedHeader}.${encodedPayload}.${signature}`;
}

/**
 * Build a valid 2-minute Pharmacy QR Token for k6 iterations
 */
export function createPharmacyQRToken(policyId) {
    // 2 minutes expiry to match strict security standards
    const now = Math.floor(Date.now() / 1000);
    const payload = {
        sub: policyId,
        jti: `k6-test-${__ITER}-${Date.now()}`,
        exp: now + 120,
        type: 'pharmacy_qr'
    };

    const secret = __ENV.JWT_SECRET || 'your_super_secret_jwt_key';
    return generateTestJWT(payload, secret);
}
