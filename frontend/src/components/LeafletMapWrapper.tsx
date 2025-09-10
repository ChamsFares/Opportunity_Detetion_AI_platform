import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import React, { useEffect, useRef } from 'react';

// Fix for default markers in react-leaflet
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface Region {
    name: string;
    opportunity: string;
    color: string;
    potential: string;
    coordinates: [number, number];
}

interface LeafletMapWrapperProps {
    regions: Record<string, Region>;
    onRegionSelect: (regionKey: string) => void;
}

const LeafletMapWrapper: React.FC<LeafletMapWrapperProps> = ({ regions, onRegionSelect }) => {
    const mapRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<L.Map | null>(null);

    useEffect(() => {
        if (!mapRef.current || mapInstanceRef.current) return;

        // Initialize the map
        const map = L.map(mapRef.current).setView([46.2276, 2.2137], 6);

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        mapInstanceRef.current = map;

        // Add markers for each region
        Object.entries(regions).forEach(([key, region]) => {
            // Create custom icon with region color
            const customIcon = L.divIcon({
                className: 'custom-marker',
                html: `
                    <div style="
                        width: 20px;
                        height: 20px;
                        background-color: ${region.color};
                        border: 2px solid white;
                        border-radius: 50%;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    "></div>
                `,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            const marker = L.marker(region.coordinates, { icon: customIcon })
                .addTo(map)
                .bindPopup(`
                    <div style="text-align: center; padding: 8px;">
                        <h4 style="margin: 0 0 4px 0; font-weight: 600; font-size: 16px;">${region.name}</h4>
                        <p style="margin: 2px 0; font-size: 12px; color: #666;">Opportunity: ${region.opportunity}</p>
                        <p style="margin: 2px 0; font-size: 12px; color: #666;">Potential: ${region.potential}</p>
                        <div style="
                            width: 16px; 
                            height: 16px; 
                            background-color: ${region.color}; 
                            border-radius: 50%; 
                            margin: 8px auto 0;
                        "></div>
                    </div>
                `);

            marker.on('click', () => {
                onRegionSelect(key);
            });
        });

        // Cleanup function
        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, [regions, onRegionSelect]);

    return (
        <div
            ref={mapRef}
            style={{
                height: '100%',
                width: '100%',
                borderRadius: '8px',
                minHeight: '300px'
            }}
        />
    );
};

export default LeafletMapWrapper;
