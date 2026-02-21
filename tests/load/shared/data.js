/**
 * Shared Data generators specifically tailored for Côte d'Ivoire.
 */

// Format: +225 07 XX XX XX XX or 07 XX XX XX XX
export function generateIvorianPhone() {
    const min = 10000000;
    const max = 99999999;
    const number = Math.floor(Math.random() * (max - min + 1)) + min;
    // Prefix with Orange ranges for testing (07)
    return `+22507${number}`;
}

// Ensure coordinates hit inside Abidjan to bypass the anti-fraud "outside country bounds" check
export function randomAbidjanCoordinates() {
    // Abidjan rough bounds: Lat (5.2 to 5.4), Lng (-4.1 to -3.9)
    const lat = 5.2 + (Math.random() * 0.2);
    const lng = -4.1 + (Math.random() * 0.2);

    return {
        latitude: parseFloat(lat.toFixed(4)),
        longitude: parseFloat(lng.toFixed(4))
    };
}

export function generateFakeTransactionId() {
    return `CI-TEST-${Math.floor(Date.now() / 1000)}-${Math.floor(Math.random() * 10000)}`;
}
