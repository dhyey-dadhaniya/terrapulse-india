"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/**
 * AQI history + Prophet forecast chart.
 *
 * Solid line = historical AQI (what already happened).
 * Dashed line = model forecast (yhat) — the predicted path ahead.
 * Shaded band = uncertainty range between yhat_lower and yhat_upper: the model
 * is not saying AQI will land exactly on the dashed line, only that it is likely
 * somewhere inside that band.
 */

type HistoricalPoint = { date: string; aqi: number };
type ForecastPoint = {
  date: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
};

type ForecastResponse = {
  city: string;
  generated_at: string;
  historical: HistoricalPoint[];
  forecast: ForecastPoint[];
};

type ChartRow = {
  date: string;
  historical?: number;
  forecast?: number;
  bandBase?: number;
  bandHeight?: number;
};

const CITIES = ["Delhi", "Mumbai", "Chennai", "Bengaluru", "Kolkata"] as const;

function formatAxisDate(isoDate: string): string {
  const d = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(d.getTime())) return isoDate;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "2-digit",
  }).format(d);
}

export default function AqiForecastChart() {
  const [city, setCity] = useState<(typeof CITIES)[number]>("Delhi");
  const [rows, setRows] = useState<ChartRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadForecast = useCallback(async (selectedCity: string) => {
    const baseUrl =
      process.env.NEXT_PUBLIC_ML_ENGINE_URL?.replace(/\/$/, "") ||
      "http://localhost:8000";

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${baseUrl}/api/aqi/forecast/${encodeURIComponent(selectedCity.toLowerCase())}?days=90`
      );
      if (!response.ok) {
        throw new Error(`ML engine returned ${response.status}`);
      }
      const data: ForecastResponse = await response.json();

      const historicalRows: ChartRow[] = data.historical.map((point) => ({
        date: point.date,
        historical: point.aqi,
      }));

      const forecastRows: ChartRow[] = data.forecast.map((point) => ({
        date: point.date,
        forecast: point.yhat,
        // Stacked transparent base + height = confidence band between lower/upper.
        bandBase: point.yhat_lower,
        bandHeight: Math.max(0, point.yhat_upper - point.yhat_lower),
      }));

      // Bridge: last historical point also carries forecast start visually if needed.
      setRows([...historicalRows, ...forecastRows]);
    } catch {
      setRows([]);
      setError(
        "Could not load AQI forecast. Is the ML engine running on port 8000?"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadForecast(city);
  }, [city, loadForecast]);

  const xTicks = useMemo(() => {
    if (rows.length === 0) return [];
    const step = Math.max(1, Math.floor(rows.length / 12));
    const ticks: string[] = [];
    for (let i = 0; i < rows.length; i += step) {
      ticks.push(rows[i].date);
    }
    const last = rows[rows.length - 1].date;
    if (ticks[ticks.length - 1] !== last) {
      ticks.push(last);
    }
    return ticks;
  }, [rows]);

  return (
    <section className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur-md sm:p-6">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">
            AQI forecast (90 days)
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Solid = past AQI · Dashed = predicted AQI · Shaded band = uncertainty
            range
          </p>
          <p
            className="mt-1 text-xs text-amber-300/90"
            title="The ML forecast endpoint currently trains on Delhi-seasonal synthetic history for every city."
          >
            Demo data: seasonal pattern currently modeled on Delhi
          </p>
        </div>
        <label className="flex flex-col text-sm text-slate-300">
          City
          <select
            className="mt-1 rounded-md border border-white/15 bg-slate-900/80 px-3 py-2 text-slate-100"
            value={city}
            onChange={(e) =>
              setCity(e.target.value as (typeof CITIES)[number])
            }
            disabled={loading}
          >
            {CITIES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && (
        <div className="flex h-72 items-center justify-center text-slate-400 sm:h-80">
          Loading forecast...
        </div>
      )}

      {!loading && error && (
        <div className="flex h-72 items-center justify-center px-4 text-center text-red-300 sm:h-80">
          {error}
        </div>
      )}

      {!loading && !error && rows.length > 0 && (
        <div className="h-72 w-full sm:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={rows}
              margin={{ top: 8, right: 12, left: 0, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="date"
                ticks={xTicks}
                tickFormatter={formatAxisDate}
                minTickGap={24}
                angle={-30}
                textAnchor="end"
                height={60}
                tick={{ fontSize: 11, fill: "#94a3b8" }}
              />
              <YAxis
                label={{
                  value: "AQI",
                  angle: -90,
                  position: "insideLeft",
                  style: { fill: "#94a3b8", fontSize: 12 },
                }}
                tick={{ fontSize: 11, fill: "#94a3b8" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: "0.5rem",
                }}
                labelStyle={{ color: "#e2e8f0" }}
                labelFormatter={(label) => `Date: ${label}`}
                formatter={(value, name) => {
                  if (value == null || name === "bandBase") return [null, null];
                  if (name === "bandHeight") return [null, null];
                  const label =
                    name === "historical"
                      ? "Historical AQI"
                      : name === "forecast"
                        ? "Forecast (yhat)"
                        : String(name);
                  return [Number(value).toFixed(1), label];
                }}
              />
              <Legend wrapperStyle={{ color: "#cbd5e1" }} />
              {/* Confidence band: transparent lower stack + visible upper-lower height */}
              <Area
                type="monotone"
                dataKey="bandBase"
                stackId="confidence"
                stroke="none"
                fill="transparent"
                legendType="none"
                tooltipType="none"
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="bandHeight"
                name="Uncertainty band"
                stackId="confidence"
                stroke="none"
                fill="#fb923c"
                fillOpacity={0.25}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="historical"
                name="Historical AQI"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                name="Forecast (yhat)"
                stroke="#ea580c"
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
