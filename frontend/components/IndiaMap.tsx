"use client";

import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

/**
 * India climate-risk map using Leaflet + OpenStreetMap tiles.
 *
 * OpenStreetMap does not need an API key/token: its map tiles are served by a
 * community-run free tile network. Mapbox, by contrast, is a commercial
 * product that requires a billed account and access token.
 *
 * We use CircleMarker (not the default blue pin icon) so we can color markers
 * by risk level and avoid Next.js/webpack breaking Leaflet's default icon paths.
 */

type Region = {
  id: number;
  name: string;
  state?: string | null;
  latitude: number | null;
  longitude: number | null;
  riskLevel?: string | null;
  lastUpdated?: string | null;
};

function riskColor(riskLevel?: string | null): string {
  const level = (riskLevel ?? "Low").toLowerCase();
  if (level === "high") return "#dc2626";
  if (level === "medium") return "#f59e0b";
  return "#16a34a";
}

function formatLastUpdated(value?: string | null): string {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function IndiaMap() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const baseUrl =
      process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ||
      "http://localhost:8080";

    let cancelled = false;

    async function loadRegions() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${baseUrl}/api/regions`);
        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }
        const data: Region[] = await response.json();
        if (!cancelled) {
          setRegions(data);
        }
      } catch {
        if (!cancelled) {
          setError(
            "Could not load regions from the backend. Is it running on port 8080?"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadRegions();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex h-full min-h-[24rem] w-full items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 backdrop-blur-md lg:min-h-[40rem]">
        Loading regions...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full min-h-[24rem] w-full items-center justify-center rounded-xl border border-red-400/30 bg-red-500/10 px-4 text-center text-red-200 backdrop-blur-md lg:min-h-[40rem]">
        {error}
      </div>
    );
  }

  const mappable = regions.filter(
    (r) =>
      typeof r.latitude === "number" &&
      typeof r.longitude === "number" &&
      !Number.isNaN(r.latitude) &&
      !Number.isNaN(r.longitude)
  );

  return (
    <div className="h-full min-h-[24rem] w-full overflow-hidden rounded-xl border border-white/10 bg-white/5 shadow-sm backdrop-blur-md lg:min-h-[40rem]">
      <MapContainer
        center={[20.5937, 78.9629]}
        zoom={4.5}
        scrollWheelZoom
        className="h-full min-h-[24rem] w-full lg:min-h-[40rem]"
      >
        {/* OSM community tiles — free, no Mapbox token required */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {mappable.map((region) => {
          const color = riskColor(region.riskLevel);
          return (
            <CircleMarker
              key={region.id}
              center={[region.latitude as number, region.longitude as number]}
              radius={10}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.85,
                weight: 2,
              }}
            >
              <Popup>
                <div className="min-w-[10rem] text-slate-900">
                  <p className="text-sm font-semibold">{region.name}</p>
                  <p className="mt-1 text-sm">
                    Risk: {region.riskLevel ?? "Low"}
                  </p>
                  <p className="mt-1 text-xs text-slate-600">
                    Updated: {formatLastUpdated(region.lastUpdated)}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
