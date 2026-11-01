import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { MapPin, ShieldCheck, AlertTriangle, Camera, CheckCircle2, Navigation, Layers } from 'lucide-react';

interface GeoPhoto {
  id: string;
  title: string;
  lat: number;
  lng: number;
  isInside: boolean;
  timestamp: string;
  device: string;
  phash: string;
  notes: string;
  thumbnailUrl: string;
}

export const GeotagMap: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const [selectedPhoto, setSelectedPhoto] = useState<GeoPhoto | null>(null);

  // Campus polygon boundary (Delhi Tech Campus example)
  const campusCenter: [number, number] = [28.545, 77.192];
  const campusPolygonCoords: [number, number][] = [
    [28.548, 77.189],
    [28.549, 77.195],
    [28.544, 77.196],
    [28.542, 77.191],
    [28.545, 77.189],
  ];

  // Geotagged evidence photos
  const photos: GeoPhoto[] = [
    {
      id: 'photo-1',
      title: 'Advanced Computer Lab 101',
      lat: 28.546,
      lng: 77.193,
      isInside: true,
      timestamp: '2026-10-25 14:22:10 IST',
      device: 'Samsung Galaxy Tab S9 (GNSS Valid)',
      phash: '0x9fa84b12c771',
      notes: 'Contains 60 Core i7 workstations. Perceptual hash verified unique.',
      thumbnailUrl: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&auto=format&fit=crop&q=60',
    },
    {
      id: 'photo-2',
      title: 'Central Engineering Library & Digital Portal',
      lat: 28.5445,
      lng: 77.1925,
      isInside: true,
      timestamp: '2026-10-25 15:05:44 IST',
      device: 'Samsung Galaxy Tab S9 (GNSS Valid)',
      phash: '0x3ec891a45b90',
      notes: 'Carpet area 620 sqm. Physical seating capacity verified.',
      thumbnailUrl: 'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=400&auto=format&fit=crop&q=60',
    },
    {
      id: 'photo-3',
      title: 'Electrical Machines Laboratory (WARNING: Off-Site)',
      lat: 28.572,
      lng: 77.218,
      isInside: false,
      timestamp: '2026-10-25 16:48:02 IST',
      device: 'Apple iPhone 14 (EXIF Spoofed / Modified)',
      phash: '0xb8a2f90119e3',
      notes: 'ALERT: Photo geotag is located 3.8 km outside declared campus land boundary. Suspected photo reuse or off-site inspection.',
      thumbnailUrl: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=400&auto=format&fit=crop&q=60',
    },
  ];

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: campusCenter,
        zoom: 14,
        attributionControl: false,
      });

      // CartoDB Dark Matter tiles for ultra-clean sleek dark styling
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
      }).addTo(map);

      // Campus Polygon boundary with high-visibility stroke & fill
      const polygon = L.polygon(campusPolygonCoords, {
        color: '#38bdf8',
        weight: 3,
        fillColor: '#0284c7',
        fillOpacity: 0.25,
        dashArray: '6, 6',
      }).addTo(map);

      polygon.bindPopup(
        `<div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 12px; padding: 4px;">
          <b style="color: #0369a1;">AICTE Approved Campus Boundary</b><br/>
          <span>Survey Plot 44/A • 5.50 Contiguous Acres</span><br/>
          <span style="color: #10b981; font-weight: bold;">✔ Certified Geofence</span>
        </div>`
      );

      // Add Custom Markers for Photos
      photos.forEach((photo) => {
        const isInside = photo.isInside;

        const customIcon = L.divIcon({
          className: 'custom-geo-marker',
          html: `
            <div style="
              width: 32px;
              height: 32px;
              border-radius: 50%;
              background: ${isInside ? '#10b981' : '#f43f5e'};
              border: 3px solid #ffffff;
              box-shadow: 0 0 12px ${isInside ? 'rgba(16, 185, 129, 0.8)' : 'rgba(244, 63, 94, 0.9)'};
              display: flex;
              align-items: center;
              justify-content: center;
              color: #ffffff;
              cursor: pointer;
              ${!isInside ? 'animation: pulse 1.5s infinite;' : ''}
            ">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                ${
                  isInside
                    ? '<polyline points="20 6 9 17 4 12"></polyline>'
                    : '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>'
                }
              </svg>
            </div>
          `,
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        });

        const marker = L.marker([photo.lat, photo.lng], { icon: customIcon }).addTo(map);

        marker.on('click', () => {
          setSelectedPhoto(photo);
        });
      });

      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Map Canvas */}
      <div className="lg:col-span-8 glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Geotag Physical Verification Map (Leaflet)
                <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-500/30 font-mono">
                  GPS & EXIF Geofence
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Audits photo GPS coordinates against statutory registered cadastral campus polygon boundaries.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              2 Photos Inside Campus
            </span>
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-rose-950/60 text-rose-300 border border-rose-500/30 font-semibold">
              <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping"></span>
              1 Photo Outside (Anomaly)
            </span>
          </div>
        </div>

        {/* Map Container */}
        <div
          ref={mapContainerRef}
          className="w-full h-[520px] rounded-xl border border-slate-800/80 overflow-hidden relative z-0"
        />

        {/* Footnote */}
        <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80 font-mono text-[11px]">
          <span>Polygon: WGS84 Geodetic Coordinates • Tolerancing: ±5 meters RTK</span>
          <span className="text-sky-400">Click marker to inspect EXIF metadata</span>
        </div>
      </div>

      {/* Selected Photo Inspection Panel */}
      <div className="lg:col-span-4 glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Camera className="w-4 h-4 text-sky-400" />
          <span>Physical Evidence Geotag Audit</span>
        </h4>

        {selectedPhoto ? (
          <div className="space-y-4 animate-in fade-in duration-200">
            {/* Thumbnail */}
            <div className="relative rounded-xl overflow-hidden border border-slate-800 aspect-video bg-slate-950">
              <img
                src={selectedPhoto.thumbnailUrl}
                alt={selectedPhoto.title}
                className="w-full h-full object-cover"
              />
              <div
                className={`absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                  selectedPhoto.isInside
                    ? 'bg-emerald-600 text-white'
                    : 'bg-rose-600 text-white animate-pulse'
                }`}
              >
                {selectedPhoto.isInside ? 'INSIDE CAMPUS' : 'OUTSIDE GEOFENCE'}
              </div>
            </div>

            {/* Photo Title */}
            <div>
              <h5 className="text-sm font-bold text-white">{selectedPhoto.title}</h5>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">{selectedPhoto.timestamp}</p>
            </div>

            {/* Metadata Grid */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500">Coordinates:</span>
                <span className="text-slate-200">{selectedPhoto.lat.toFixed(5)}, {selectedPhoto.lng.toFixed(5)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Camera / Sensor:</span>
                <span className="text-slate-200 truncate max-w-[170px]">{selectedPhoto.device}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Perceptual Hash:</span>
                <span className="text-sky-300">{selectedPhoto.phash}</span>
              </div>
            </div>

            {/* Verdict Box */}
            <div
              className={`p-3.5 rounded-xl border text-xs leading-relaxed ${
                selectedPhoto.isInside
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-200'
                  : 'bg-rose-950/30 border-rose-500/50 text-rose-200'
              }`}
            >
              <div className="flex items-center gap-1.5 font-bold mb-1">
                {selectedPhoto.isInside ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Geofence Compliant</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    <span>Spatial Violation Detected</span>
                  </>
                )}
              </div>
              <p className="text-[11px] text-slate-300 font-sans">{selectedPhoto.notes}</p>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl space-y-2">
            <MapPin className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-xs font-medium text-slate-300">No Photo Marker Selected</div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Click any green or red pin on the campus satellite map to verify physical lab photos, coordinate accuracy, and perceptual photo uniqueness.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
