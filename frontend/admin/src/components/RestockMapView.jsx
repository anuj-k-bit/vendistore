import React, { useEffect, useRef } from 'react';
import { MapPin, Navigation, Truck, RefreshCw } from 'lucide-react';

export default function RestockMapView({ inventoryData }) {
  const mapRef = useRef(null);

  // Machine GIS Coordinates in San Francisco
  const machineLocations = [
    { id: 'VM-101', name: 'Financial District Node', lat: 37.789, lng: -122.401, status: 'Low Stock', fill: 20 },
    { id: 'VM-102', name: 'SoMa Tech Hub', lat: 37.776, lng: -122.417, status: 'Operational', fill: 85 },
    { id: 'VM-103', name: 'Union Square Retail', lat: 37.785, lng: -122.408, status: 'Operational', fill: 70 },
    { id: 'VM-104', name: 'Airport Transit Hub', lat: 37.808, lng: -122.415, status: 'Critical', fill: 13 },
    { id: 'VM-105', name: 'Haight Station', lat: 37.769, lng: -122.446, status: 'Operational', fill: 90 },
    { id: 'VM-106', name: 'Mission District Terminal', lat: 37.759, lng: -122.414, status: 'Low Stock', fill: 35 },
    { id: 'VM-107', name: 'Japantown Plaza', lat: 37.783, lng: -122.432, status: 'Critical', fill: 15 },
    { id: 'VM-108', name: 'Mission Bay Biotech', lat: 37.764, lng: -122.388, status: 'Operational', fill: 65 },
    { id: 'VM-109', name: 'Embarcadero Ferry Building', lat: 37.795, lng: -122.393, status: 'Operational', fill: 80 },
    { id: 'VM-110', name: 'Polk Street Terminal', lat: 37.788, lng: -122.422, status: 'Operational', fill: 75 }
  ];

  // Restock route path coordinates (connects VM-104 -> VM-107 -> VM-101 -> VM-106)
  const restockRoutePath = [
    [37.808, -122.415], // VM-104 (Critical)
    [37.783, -122.432], // VM-107 (Critical)
    [37.789, -122.401], // VM-101 (Low Stock)
    [37.759, -122.414]  // VM-106 (Low Stock)
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl font-sans relative overflow-hidden">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-cyan-950 border border-cyan-800 text-cyan-400">
            <Navigation className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white font-mono uppercase tracking-tight text-sm flex items-center gap-2">
              Fleet GIS & Restock Polyline Route Map
              <span className="bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-[10px] px-2 py-0.5 rounded-full font-mono">
                OpenStreetMap
              </span>
            </h3>
            <p className="text-xs text-slate-400">San Francisco Bay Area • Optimized Dispatch Route Overlay</p>
          </div>
        </div>
      </div>

      {/* Visual Simulated Interactive Leaflet GIS Map Container */}
      <div className="w-full h-72 bg-slate-950 rounded-xl border border-slate-800 relative overflow-hidden flex flex-col justify-between p-4 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]">
        {/* Route Line SVG Overlay */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-cyan-400/80 fill-none stroke-2 stroke-dasharray-4">
          <path d="M 520 40 L 320 90 L 480 100 L 420 210" className="animate-pulse" />
        </svg>

        {/* Map Header Overlay */}
        <div className="flex items-center justify-between z-10">
          <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 text-slate-300 px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-2">
            <Truck className="w-4 h-4 text-cyan-400" /> Restock Dispatch Route: <strong className="text-white">VM-104 &rarr; VM-107 &rarr; VM-101 &rarr; VM-106</strong>
          </div>
          <div className="bg-slate-900/90 text-emerald-400 border border-slate-800 text-[11px] font-mono px-2.5 py-1 rounded-lg">
            ● 4 Priority Stops
          </div>
        </div>

        {/* Map Markers Overlay Grid */}
        <div className="relative flex-1 my-2 z-10 grid grid-cols-5 gap-4 items-center">
          {machineLocations.map((loc) => (
            <div
              key={loc.id}
              className={`p-2 rounded-lg border backdrop-blur-md transition-all hover:scale-105 ${
                loc.fill <= 20
                  ? 'bg-rose-950/90 border-rose-700 text-rose-300 shadow-lg shadow-rose-950/50'
                  : loc.fill <= 50
                  ? 'bg-amber-950/90 border-amber-700 text-amber-300 shadow-lg shadow-amber-950/50'
                  : 'bg-slate-900/80 border-slate-800 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-black text-xs">{loc.id}</span>
                <MapPin className={`w-3.5 h-3.5 ${loc.fill <= 20 ? 'text-rose-400 animate-bounce' : loc.fill <= 50 ? 'text-amber-400' : 'text-emerald-400'}`} />
              </div>
              <div className="text-[10px] truncate opacity-90 mt-0.5">{loc.name}</div>
              <div className="text-[10px] font-mono font-bold mt-1">Stock: {loc.fill}%</div>
            </div>
          ))}
        </div>

        {/* Legend Footer Overlay */}
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 z-10 pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Critical (&le;20%)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Low Stock (20-50%)</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Nominal (&gt;50%)</span>
          </div>
          <div>Center: 37.7749° N, 122.4194° W</div>
        </div>
      </div>
    </div>
  );
}
