import { Pharmacy } from './mock-pharmacies';

export interface UserLocation {
    lat: number;
    lng: number;
}

/**
 * Get user's current location using browser geolocation API
 */
export const getUserLocation = (): Promise<UserLocation> => {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by your browser'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                });
            },
            (error) => {
                reject(error);
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0,
            }
        );
    });
};

/**
 * Calculate distance between two points using Haversine formula
 * Returns distance in kilometers
 */
export const calculateDistance = (
    lat1: number,
    lng1: number,
    lat2: number,
    lng2: number
): number => {
    const R = 6371; // Earth's radius in kilometers
    const dLat = toRad(lat2 - lat1);
    const dLng = toRad(lng2 - lng1);

    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) *
        Math.cos(toRad(lat2)) *
        Math.sin(dLng / 2) *
        Math.sin(dLng / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;

    return Math.round(distance * 10) / 10; // Round to 1 decimal
};

const toRad = (degrees: number): number => {
    return (degrees * Math.PI) / 180;
};

/**
 * Sort pharmacies by distance from user location
 */
export const sortByDistance = (
    pharmacies: Pharmacy[],
    userLocation: UserLocation
): (Pharmacy & { distance: number })[] => {
    return pharmacies
        .map((pharmacy) => ({
            ...pharmacy,
            distance: calculateDistance(
                userLocation.lat,
                userLocation.lng,
                pharmacy.coordinates.lat,
                pharmacy.coordinates.lng
            ),
        }))
        .sort((a, b) => a.distance - b.distance);
};

/**
 * Default center for Abidjan (Plateau area)
 */
export const ABIDJAN_CENTER: UserLocation = {
    lat: 5.3197,
    lng: -4.0081,
};
