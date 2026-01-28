"use client";

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { MapPin, List, Navigation, Phone, Clock, Loader2 } from 'lucide-react';
import { MOCK_PHARMACIES, Pharmacy } from '@/lib/mock-pharmacies';
import { getUserLocation, sortByDistance, calculateDistance, ABIDJAN_CENTER, UserLocation } from '@/lib/geolocation';
import { toast } from 'sonner';

// Dynamically import map to avoid SSR issues
const PharmacyMap = dynamic(() => import('@/components/pharmacy/PharmacyMap'), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-900">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
        </div>
    ),
});

type ViewMode = 'map' | 'list';

export default function PharmacyFinder() {
    const [viewMode, setViewMode] = useState<ViewMode>('map');
    const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
    const [pharmacies, setPharmacies] = useState<(Pharmacy & { distance?: number })[]>(MOCK_PHARMACIES);
    const [selectedPharmacy, setSelectedPharmacy] = useState<Pharmacy | null>(null);
    const [loading, setLoading] = useState(true);
    const [mapCenter, setMapCenter] = useState<UserLocation | null>(null);
    const [showSearchArea, setShowSearchArea] = useState(false);

    const [showNavigationModal, setShowNavigationModal] = useState(false);
    const [selectedNavPharmacy, setSelectedNavPharmacy] = useState<Pharmacy | null>(null);

    useEffect(() => {
        // Request user location
        getUserLocation()
            .then((location) => {
                setUserLocation(location);
                setMapCenter(location);
                const sorted = sortByDistance(MOCK_PHARMACIES, location);
                setPharmacies(sorted);
                toast.success('Localisation activée');
            })
            .catch((error) => {
                console.error('Geolocation error:', error);
                setUserLocation(ABIDJAN_CENTER);
                setMapCenter(ABIDJAN_CENTER);
                toast.info('Utilisation de la position par défaut');
            })
            .finally(() => {
                setLoading(false);
            });
    }, []);

    const handleMapMove = (newCenter: UserLocation) => {
        setMapCenter(newCenter);
        // Show "Search this area" button if map moved significantly from user location
        const originalCenter = userLocation || ABIDJAN_CENTER;
        const distance = Math.abs(newCenter.lat - originalCenter.lat) + Math.abs(newCenter.lng - originalCenter.lng);
        setShowSearchArea(distance > 0.01); // ~1km threshold
    };

    const handleSearchArea = () => {
        if (mapCenter) {
            // Filter pharmacies within 50km radius of map center
            const nearbyPharmacies = MOCK_PHARMACIES.filter(pharmacy => {
                const distance = calculateDistance(
                    mapCenter.lat,
                    mapCenter.lng,
                    pharmacy.coordinates.lat,
                    pharmacy.coordinates.lng
                );
                return distance <= 50; // 50km radius
            });

            if (nearbyPharmacies.length === 0) {
                toast.error('Aucune pharmacie trouvée dans cette zone');
                return;
            }

            const sorted = sortByDistance(nearbyPharmacies, mapCenter);
            setPharmacies(sorted);
            setShowSearchArea(false);
            toast.success(`${sorted.length} pharmacie${sorted.length > 1 ? 's' : ''} trouvée${sorted.length > 1 ? 's' : ''}`);
        }
    };

    const handleGetDirections = (pharmacy: Pharmacy) => {
        setSelectedNavPharmacy(pharmacy);
        setShowNavigationModal(true);
    };

    const openNavigation = (app: 'google' | 'yango') => {
        if (!selectedNavPharmacy) return;

        const destination = `${selectedNavPharmacy.coordinates.lat},${selectedNavPharmacy.coordinates.lng}`;
        const origin = userLocation
            ? `${userLocation.lat},${userLocation.lng}`
            : `${ABIDJAN_CENTER.lat},${ABIDJAN_CENTER.lng}`;

        let url = '';
        if (app === 'google') {
            // Google Maps
            url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=driving`;
        } else if (app === 'yango') {
            // Yango Maps (deep link)
            url = `yandexnavi://build_route_on_map?lat_to=${selectedNavPharmacy.coordinates.lat}&lon_to=${selectedNavPharmacy.coordinates.lng}`;
            // Fallback to web if app not installed
            setTimeout(() => {
                window.open(`https://yandex.com/maps/?rtext=${origin.replace(',', '%2C')}~${destination.replace(',', '%2C')}&rtt=auto`, '_blank');
            }, 500);
        }

        window.open(url, '_blank');
        setShowNavigationModal(false);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen bg-gray-50 dark:bg-slate-950">
            {/* Header */}
            <div className="p-6 pb-4 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Pharmacies partenaires</h1>

                {/* View Toggle */}
                <div className="flex gap-2">
                    <button
                        onClick={() => setViewMode('map')}
                        className={`flex-1 py-2.5 px-4 rounded-xl font-medium text-sm transition flex items-center justify-center gap-2 ${viewMode === 'map'
                            ? 'bg-emerald-600 text-white'
                            : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400'
                            }`}
                    >
                        <MapPin className="w-4 h-4" />
                        Carte
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={`flex-1 py-2.5 px-4 rounded-xl font-medium text-sm transition flex items-center justify-center gap-2 ${viewMode === 'list'
                            ? 'bg-emerald-600 text-white'
                            : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400'
                            }`}
                    >
                        <List className="w-4 h-4" />
                        Liste
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden relative">
                {viewMode === 'map' ? (
                    <>
                        <PharmacyMap
                            pharmacies={pharmacies}
                            userLocation={userLocation || ABIDJAN_CENTER}
                            selectedPharmacy={selectedPharmacy}
                            onSelectPharmacy={setSelectedPharmacy}
                            onGetDirections={handleGetDirections}
                            onMapMove={handleMapMove}
                        />

                        {/* Search This Area Button */}
                        {showSearchArea && (
                            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000]">
                                <button
                                    onClick={handleSearchArea}
                                    className="bg-white dark:bg-slate-900 text-gray-900 dark:text-white px-4 py-2.5 rounded-full shadow-lg border border-gray-200 dark:border-slate-700 font-medium text-sm hover:bg-gray-50 dark:hover:bg-slate-800 transition flex items-center gap-2"
                                >
                                    <MapPin className="w-4 h-4" />
                                    Rechercher dans cette zone
                                </button>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="h-full overflow-y-auto p-6 pb-24 space-y-3">
                        {pharmacies.map((pharmacy) => (
                            <PharmacyCard
                                key={pharmacy.id}
                                pharmacy={pharmacy}
                                onGetDirections={() => handleGetDirections(pharmacy)}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Navigation Modal */}
            {showNavigationModal && selectedNavPharmacy && (
                <div className="fixed inset-0 bg-black/50 z-[2000] flex items-end sm:items-center justify-center p-6">
                    <div className="bg-white dark:bg-slate-900 rounded-t-3xl sm:rounded-2xl w-full sm:max-w-md p-6">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                            Choisir l'application
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                            {selectedNavPharmacy.name}
                        </p>

                        <div className="space-y-3">
                            <button
                                onClick={() => openNavigation('google')}
                                className="w-full bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 hover:border-emerald-500 dark:hover:border-emerald-500 text-gray-900 dark:text-white font-medium py-4 px-4 rounded-xl transition flex items-center gap-3"
                            >
                                <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center">
                                    <Navigation className="w-5 h-5 text-emerald-600" />
                                </div>
                                <div className="flex-1 text-left">
                                    <div className="font-bold">Google Maps</div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400">Navigation recommandée</div>
                                </div>
                            </button>

                            <button
                                onClick={() => openNavigation('yango')}
                                className="w-full bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 hover:border-emerald-500 dark:hover:border-emerald-500 text-gray-900 dark:text-white font-medium py-4 px-4 rounded-xl transition flex items-center gap-3"
                            >
                                <div className="w-10 h-10 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg flex items-center justify-center">
                                    <MapPin className="w-5 h-5 text-yellow-600" />
                                </div>
                                <div className="flex-1 text-left">
                                    <div className="font-bold">Yango Maps</div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400">Navigation locale</div>
                                </div>
                            </button>
                        </div>

                        <button
                            onClick={() => setShowNavigationModal(false)}
                            className="w-full mt-4 text-gray-600 dark:text-gray-400 font-medium py-3 hover:text-gray-900 dark:hover:text-white transition"
                        >
                            Annuler
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

function PharmacyCard({ pharmacy, onGetDirections }: { pharmacy: Pharmacy & { distance?: number }, onGetDirections: () => void }) {
    return (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-gray-100 dark:border-slate-800 shadow-sm">
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-1">{pharmacy.name}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        {pharmacy.address}
                    </p>
                </div>
                {pharmacy.distance !== undefined && (
                    <div className="bg-emerald-50 dark:bg-emerald-900/20 px-2.5 py-1 rounded-lg">
                        <span className="text-xs font-bold text-emerald-700 dark:text-emerald-500">
                            {pharmacy.distance} km
                        </span>
                    </div>
                )}
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {pharmacy.hours}
                </div>
                <div className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5" />
                    <a href={`tel:${pharmacy.phone}`} className="hover:text-emerald-600">
                        {pharmacy.phone}
                    </a>
                </div>
            </div>

            <button
                onClick={onGetDirections}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 rounded-xl transition flex items-center justify-center gap-2"
            >
                <Navigation className="w-4 h-4" />
                Obtenir l'itinéraire
            </button>
        </div>
    );
}
