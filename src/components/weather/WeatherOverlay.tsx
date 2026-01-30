"use client";

import { useEffect, useState } from "react";
import { Cloud, Wind, ThermometerSun, Eye, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";

export type WeatherCurrent = {
  temperature_c: number | null;
  temperature_f: number | null;
  relative_humidity: number | null;
  weather_code: number;
  conditions: string;
  wind_speed_kmh: number | null;
  wind_speed_mph: number | null;
  wind_direction: number | null;
  cloud_cover: number | null;
  visibility_km: number | null;
  latitude: number;
  longitude: number;
};

interface WeatherOverlayProps {
  /** Default center when no coords from map/incident (e.g. org HQ). */
  defaultLat?: number;
  defaultLng?: number;
  /** Override with current map/incident center. */
  lat?: number;
  lng?: number;
  /** Compact layout for sidebar. */
  compact?: boolean;
  className?: string;
}

export function WeatherOverlay({
  defaultLat = 43.07,
  defaultLng = -89.38,
  lat,
  lng,
  compact = false,
  className = "",
}: WeatherOverlayProps) {
  const [weather, setWeather] = useState<WeatherCurrent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const latitude = lat ?? defaultLat;
  const longitude = lng ?? defaultLng;

  const fetchWeather = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<WeatherCurrent>(
        `/api/weather/current?lat=${latitude}&lng=${longitude}`
      );
      setWeather(data);
    } catch (e) {
      setError("Weather unavailable");
      setWeather(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, [latitude, longitude]);

  if (loading && !weather) {
    return (
      <div
        className={`rounded-lg border border-zinc-700/80 bg-zinc-900/80 p-4 ${className}`}
      >
        <div className="flex items-center gap-2 text-zinc-400">
          <Cloud className="w-5 h-5 animate-pulse" />
          <span className="text-sm">Loading weather…</span>
        </div>
      </div>
    );
  }

  if (error && !weather) {
    return (
      <div
        className={`rounded-lg border border-zinc-700/80 bg-zinc-900/80 p-4 ${className}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-sm text-zinc-500">{error}</span>
          <button
            type="button"
            onClick={fetchWeather}
            className="text-xs text-orange-400 hover:text-orange-300"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!weather) return null;

  if (compact) {
    return (
      <div
        className={`rounded-lg border border-zinc-700/80 bg-zinc-900/80 p-3 ${className}`}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ThermometerSun className="w-4 h-4 text-orange-400" />
            <span className="font-semibold text-zinc-100">
              {weather.temperature_f != null ? `${weather.temperature_f}°F` : "—"}
            </span>
          </div>
          <span className="text-xs text-zinc-400">{weather.conditions}</span>
          <button
            type="button"
            onClick={fetchWeather}
            className="p-1 rounded hover:bg-zinc-800 text-zinc-500"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="flex gap-3 mt-1.5 text-xs text-zinc-500">
          <span className="flex items-center gap-1">
            <Wind className="w-3 h-3" />
            {weather.wind_speed_mph != null ? `${weather.wind_speed_mph} mph` : "—"}
          </span>
          {weather.visibility_km != null && (
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              {weather.visibility_km} km
            </span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`rounded-lg border border-zinc-700/80 bg-zinc-900/80 p-4 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
          <Cloud className="w-4 h-4 text-sky-400" />
          Weather
        </h3>
        <button
          type="button"
          onClick={fetchWeather}
          className="p-1.5 rounded hover:bg-zinc-800 text-zinc-500"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="flex items-center gap-2">
          <ThermometerSun className="w-4 h-4 text-orange-400" />
          <span className="text-zinc-100 font-medium">
            {weather.temperature_f != null ? `${weather.temperature_f}°F` : "—"}
          </span>
          <span className="text-zinc-500">{weather.conditions}</span>
        </div>
        <div className="flex items-center gap-2 text-zinc-400">
          <Wind className="w-4 h-4" />
          {weather.wind_speed_mph != null ? `${weather.wind_speed_mph} mph` : "—"}
          {weather.wind_direction != null && (
            <span className="text-xs">({weather.wind_direction}°)</span>
          )}
        </div>
        {weather.relative_humidity != null && (
          <div className="col-span-2 text-zinc-500 text-xs">
            Humidity {weather.relative_humidity}%
            {weather.visibility_km != null && ` · Visibility ${weather.visibility_km} km`}
          </div>
        )}
      </div>
    </div>
  );
}
