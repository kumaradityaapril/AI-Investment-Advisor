
"use client";

import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  service: string;
};

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkBackend() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;

        if (!apiUrl) {
          throw new Error("Backend API URL is not configured.");
        }

        const response = await fetch(`${apiUrl}/health`);

        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }

        const data: HealthResponse = await response.json();
        setHealth(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to connect to backend."
        );
      } finally {
        setLoading(false);
      }
    }

    checkBackend();
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-white">
      <section className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
        <p className="text-sm font-medium text-cyan-400">
          AI INVESTMENT ADVISOR
        </p>

        <h1 className="mt-3 text-3xl font-bold">
          Backend Connection
        </h1>

        <p className="mt-3 text-slate-400">
          Checking communication between Next.js and FastAPI.
        </p>

        <div className="mt-8 rounded-xl bg-slate-800 p-5">
          {loading ? (
            <p className="text-slate-300">Checking connection...</p>
          ) : error ? (
            <div>
              <p className="font-semibold text-red-400">
                Connection failed
              </p>
              <p className="mt-2 break-words text-sm text-slate-300">
                {error}
              </p>
            </div>
          ) : (
            <div>
              <p className="font-semibold text-emerald-400">
                Backend connected successfully
              </p>
              <p className="mt-2 text-sm text-slate-300">
                Status: {health?.status}
              </p>
              <p className="text-sm text-slate-300">
                Service: {health?.service}
              </p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
