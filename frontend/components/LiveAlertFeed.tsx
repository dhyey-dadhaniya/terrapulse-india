"use client";

import { Client, IMessage } from "@stomp/stompjs";
import { useEffect, useRef, useState } from "react";
import SockJS from "sockjs-client";

// Webpack/browser bundles may not define Node's `global`; SockJS expects it.
if (typeof window !== "undefined") {
  const g = window as typeof window & { global?: typeof window };
  if (!g.global) {
    g.global = window;
  }
}
/**
 * Live alert feed over WebSocket + STOMP.
 *
 * Unlike a normal API fetch (where we ask "anything new?" on a timer), this
 * keeps an open connection so the backend can *push* a new AlertLog the
 * instant it is created — no polling loop needed.
 */

type AlertNotification = {
  id: number;
  regionId: number;
  regionName?: string | null;
  message: string;
  severity: string;
  createdAt?: string | null;
};

type ConnectionStatus = "connecting" | "connected" | "disconnected";

const MAX_ALERTS = 50;

function formatTimestamp(value?: string | null): string {
  if (!value) return "Just now";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(date);
}

function severityStyles(severity: string): string {
  const level = severity.toUpperCase();
  if (level === "HIGH") return "bg-red-100 text-red-800 ring-red-200";
  if (level === "MEDIUM") return "bg-amber-100 text-amber-800 ring-amber-200";
  return "bg-emerald-100 text-emerald-800 ring-emerald-200";
}

export default function LiveAlertFeed() {
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [newestId, setNewestId] = useState<number | null>(null);
  const clientRef = useRef<Client | null>(null);

  useEffect(() => {
    const baseUrl =
      process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ||
      "http://localhost:8080";

    const client = new Client({
      webSocketFactory: () => new SockJS(`${baseUrl}/ws`),
      reconnectDelay: 5000,
      heartbeatIncoming: 10000,
      heartbeatOutgoing: 10000,
      onConnect: () => {
        setStatus("connected");
        client.subscribe("/topic/alerts", (message: IMessage) => {
          try {
            const payload = JSON.parse(message.body) as AlertNotification;
            setAlerts((prev) => {
              const next = [payload, ...prev.filter((a) => a.id !== payload.id)];
              return next.slice(0, MAX_ALERTS);
            });
            setNewestId(payload.id);
          } catch (err) {
            console.error("Failed to parse alert message", err);
          }
        });
      },
      onDisconnect: () => {
        setStatus("disconnected");
      },
      onStompError: () => {
        setStatus("disconnected");
      },
      onWebSocketClose: () => {
        setStatus("disconnected");
      },
    });

    clientRef.current = client;
    setStatus("connecting");
    client.activate();

    return () => {
      clientRef.current = null;
      void client.deactivate();
    };
  }, []);

  useEffect(() => {
    if (newestId == null) return;
    const timer = window.setTimeout(() => setNewestId(null), 1100);
    return () => window.clearTimeout(timer);
  }, [newestId]);

  const statusColor =
    status === "connected"
      ? "bg-emerald-500"
      : status === "connecting"
        ? "bg-amber-400"
        : "bg-red-500";

  const statusLabel =
    status === "connected"
      ? "Connected"
      : status === "connecting"
        ? "Connecting…"
        : "Disconnected — reconnecting…";

  return (
    <section className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur-md sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Live alerts</h2>
          <p className="mt-1 text-sm text-slate-400">
            Pushed from the backend over WebSocket as fire-like events arrive.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${statusColor}`}
            aria-hidden
          />
          <span>{statusLabel}</span>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="rounded-lg border border-dashed border-white/15 bg-white/5 px-4 py-10 text-center text-sm text-slate-400">
          No alerts yet. Run the IoT simulator to generate fire events.
        </div>
      ) : (
        <ul className="max-h-[22rem] space-y-3 overflow-y-auto pr-1 lg:max-h-[18rem]">
          {alerts.map((alert) => {
            const isNewest = alert.id === newestId;
            return (
              <li
                key={alert.id}
                className={`rounded-lg border border-white/10 px-3 py-3 ${
                  isNewest ? "alert-flash" : "bg-white/5"
                }`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${severityStyles(
                      alert.severity
                    )}`}
                  >
                    {alert.severity}
                  </span>
                  <span className="text-sm font-semibold text-slate-100">
                    {alert.regionName ?? `Region #${alert.regionId}`}
                  </span>
                  <span className="ml-auto text-xs text-slate-400">
                    {formatTimestamp(alert.createdAt)}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-300">{alert.message}</p>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
