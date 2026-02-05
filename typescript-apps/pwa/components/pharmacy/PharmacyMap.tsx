"use client";

import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Pharmacy } from '@/lib/mock-pharmacies';
import { UserLocation } from '@/lib/geolocation';
import { Navigation, Phone, MapPin } from 'lucide-react';

// Fix for default marker icons in Leaflet
const createIcon = (color: string) => {
    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                background-color: ${color};
                width: 32px;
                height: 32px;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                border: 3px solid white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            ">
                <div style="
                    width: 10px;
                    height: 10px;
                    background-color: white;
                    border-radius: 50%;
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                "></div>
            </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32],
    });
};

const pharmacyIcon = createIcon('#10b981'); // emerald-500
const userIcon = createIcon('#3b82f6'); // blue-500

interface PharmacyMapProps {
    pharmacies: (Pharmacy & { distance?: number })[];
    userLocation: UserLocation;
    selectedPharmacy: Pharmacy | null;
    onSelectPharmacy: (pharmacy: Pharmacy | null) => void;
    onGetDirections: (pharmacy: Pharmacy) => void;
    onMapMove?: (center: UserLocation) => void;
}

// Component to handle map events
function MapEvents({ onMapMove }: { onMapMove?: (center: UserLocation) => void }) {
    useMapEvents({
        moveend: (e) => {
            if (onMapMove) {
                const center = e.target.getCenter();
                onMapMove({ lat: center.lat, lng: center.lng });
            }
        },
    });
    return null;
}

export default function PharmacyMap({
    pharmacies,
    userLocation,
    selectedPharmacy,
    onSelectPharmacy,
    onGetDirections,
    onMapMove,
}: PharmacyMapProps) {
    const mapCenter = useMemo<[number, number]>(
        () => [userLocation.lat, userLocation.lng],
        [userLocation]
    );

    return (
        <MapContainer
            center={mapCenter}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
            className="z-0"
        >
            <MapEvents onMapMove={onMapMove} />

            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* User Location Marker */}
            <Marker position={mapCenter} icon={userIcon}>
                <Popup>
                    <div className="text-center p-2">
                        <p className="font-bold text-blue-600">Votre position</p>
                    </div>
                </Popup>
            </Marker>

            {/* User Location Radius */}
            <Circle
                center={mapCenter}
                radius={2000}
                pathOptions={{
                    color: '#3b82f6',
                    fillColor: '#3b82f6',
                    fillOpacity: 0.1,
                    weight: 2,
                }}
            />

            {/* Pharmacy Markers */}
            {pharmacies.map((pharmacy) => (
                <Marker
                    key={pharmacy.id}
                    position={[pharmacy.coordinates.lat, pharmacy.coordinates.lng]}
                    icon={pharmacyIcon}
                    eventHandlers={{
                        click: () => onSelectPharmacy(pharmacy),
                    }}
                >
                    <Popup>
                        <div className="p-2 min-w-[200px]">
                            <h3 className="font-bold text-gray-900 mb-2">{pharmacy.name}</h3>
                            <p className="text-sm text-gray-600 mb-2 flex items-start gap-1">
                                <MapPin className="w-4 h-4 flex-shrink-0 mt-0.5" />
                                <span>{pharmacy.address}</span>
                            </p>
                            {pharmacy.distance !== undefined && (
                                <p className="text-xs text-emerald-600 font-bold mb-2">
                                    📍 {pharmacy.distance} km
                                </p>
                            )}
                            <p className="text-xs text-gray-500 mb-3">
                                ⏰ {pharmacy.hours}
                            </p>
                            <button
                                onClick={() => onGetDirections(pharmacy)}
                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium py-2 px-3 rounded-lg transition flex items-center justify-center gap-2"
                            >
                                <Navigation className="w-4 h-4" />
                                Itinéraire
                            </button>
                        </div>
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    );
}
