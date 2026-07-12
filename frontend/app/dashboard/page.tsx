import dynamic from "next/dynamic";
import AqiForecastChart from "@/components/AqiForecastChart";
import LiveAlertFeed from "@/components/LiveAlertFeed";
import ModelMetricsPanel from "@/components/ModelMetricsPanel";

const IndiaMap = dynamic(() => import("@/components/IndiaMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[min(80vh,40rem)] w-full items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 backdrop-blur-md">
      Loading map...
    </div>
  ),
});

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-5 sm:px-6">
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            TerraPulse India
          </h1>
          <p className="text-sm text-slate-400 sm:text-base">
            Climate risk, air quality forecasts, and live IoT fire alerts across
            Indian regions.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
        {/* Desktop: ~60% map / ~40% side panels. Mobile: single column stack. */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5 lg:gap-6">
          <section className="min-h-[24rem] lg:col-span-3 lg:min-h-[40rem]">
            <IndiaMap />
          </section>

          <aside className="flex flex-col gap-6 lg:col-span-2">
            <AqiForecastChart />
            <LiveAlertFeed />
            <ModelMetricsPanel />
          </aside>
        </div>
      </div>
    </main>
  );
}
