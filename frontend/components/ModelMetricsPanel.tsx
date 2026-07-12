"use client";

import { useEffect, useMemo, useState } from "react";

/**
 * Risk classifier quality panel.
 *
 * Accuracy = overall % of test rows predicted correctly.
 * F1-macro = balances precision and recall for Low/Medium/High equally, so a
 * rarer class is not ignored just because another class is more common.
 * Confusion matrix = rows are true labels, columns are predicted labels — shows
 * which classes get mixed up (e.g. how often true Medium is called High).
 */

type ModelMetrics = {
  accuracy: number;
  f1_macro: number;
  confusion_matrix: number[][];
  labels: string[];
};

function formatPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function cellBackground(value: number, max: number): string {
  if (max <= 0) return "rgba(37, 99, 235, 0.05)";
  const intensity = Math.min(1, value / max);
  // Light → darker blue as counts rise (simple heatmap).
  return `rgba(37, 99, 235, ${0.08 + intensity * 0.72})`;
}

export default function ModelMetricsPanel() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const baseUrl =
      process.env.NEXT_PUBLIC_ML_ENGINE_URL?.replace(/\/$/, "") ||
      "http://localhost:8000";

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${baseUrl}/api/climate/model-metrics`);
        if (!response.ok) {
          throw new Error(`ML engine returned ${response.status}`);
        }
        const data: ModelMetrics = await response.json();
        if (!cancelled) {
          setMetrics(data);
        }
      } catch {
        if (!cancelled) {
          setMetrics(null);
          setError(
            "Could not load model metrics. Is the ML engine running on port 8000?"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const maxCell = useMemo(() => {
    if (!metrics) return 0;
    return Math.max(0, ...metrics.confusion_matrix.flat());
  }, [metrics]);

  return (
    <section className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur-md sm:p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-white">
          Risk model metrics
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Test-set scores from the XGBoost Low / Medium / High classifier
          (computed at ML engine startup).
        </p>
      </div>

      {loading && (
        <div className="py-10 text-center text-slate-400">
          Loading model metrics...
        </div>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-red-400/30 bg-red-500/10 px-4 py-8 text-center text-red-200">
          {error}
        </div>
      )}

      {!loading && metrics && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-5 text-center">
              <p className="text-3xl font-bold tracking-tight text-white">
                {formatPct(metrics.accuracy)}
              </p>
              <p className="mt-1 text-sm text-slate-400">Accuracy</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-5 text-center">
              <p className="text-3xl font-bold tracking-tight text-white">
                {formatPct(metrics.f1_macro)}
              </p>
              <p className="mt-1 text-sm text-slate-400">F1-macro</p>
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium text-slate-200">
              Confusion matrix
            </h3>
            <p className="mb-3 text-xs text-slate-500">
              Rows = true label · Columns = predicted label
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-[18rem] border-collapse text-sm">
                <thead>
                  <tr>
                    <th className="px-2 py-1.5 text-left font-medium text-slate-500">
                      True \ Pred
                    </th>
                    {metrics.labels.map((label) => (
                      <th
                        key={`col-${label}`}
                        className="px-2 py-1.5 text-center font-medium text-slate-300"
                      >
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metrics.confusion_matrix.map((row, rowIndex) => (
                    <tr key={`row-${metrics.labels[rowIndex] ?? rowIndex}`}>
                      <th className="px-2 py-1.5 text-left font-medium text-slate-300">
                        {metrics.labels[rowIndex] ?? `Class ${rowIndex}`}
                      </th>
                      {row.map((value, colIndex) => (
                        <td
                          key={`cell-${rowIndex}-${colIndex}`}
                          className="px-2 py-2 text-center font-semibold text-white"
                          style={{
                            backgroundColor: cellBackground(value, maxCell),
                          }}
                        >
                          {value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
