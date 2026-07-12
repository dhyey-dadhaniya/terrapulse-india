import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-4 text-center text-slate-100">
      <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
        TerraPulse India
      </h1>
      <p className="mt-4 max-w-lg text-slate-400">
        Monitor regional climate risk, AQI forecasts, and live sensor alerts in
        one dashboard.
      </p>
      <Link
        href="/dashboard"
        className="mt-8 rounded-xl border border-white/15 bg-white/10 px-6 py-3 text-sm font-semibold text-white backdrop-blur-md transition hover:bg-white/15"
      >
        View Dashboard
      </Link>
    </main>
  );
}
