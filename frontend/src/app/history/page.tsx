"use client";

import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { apiRequest } from "@/lib/api";
import Link from "next/link";
import {
  History,
  TrendingUp,
  TrendingDown,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  Clock,
  ArrowLeftRight,
} from "lucide-react";

interface HistoryItem {
  id: number;
  created_at: string;
  question: string;
  response: {
    summary_narrative?: string;
    recommendation?: string;
  };
  financial_context?: {
    metrics?: {
      total_savings_and_investments?: number;
      monthly_surplus?: number;
      savings_rate?: number;
    };
    risk_assessment?: {
      risk_category?: string;
      risk_score?: number;
    };
  };
}

interface DiffResponse {
  baseline_id: number;
  current_id: number;
  metric_deltas: Array<{
    metric_name: string;
    metric_key: string;
    baseline_value: string;
    current_value: string;
    delta_value: string;
    percentage_change?: string;
    trend: "improved" | "declined" | "neutral" | "unchanged";
  }>;
  risk_shift: {
    baseline_category?: string;
    current_category?: string;
    baseline_score?: number;
    current_score?: number;
    score_delta?: number;
    category_changed?: boolean;
  };
  ai_explanation: {
    summary_narrative: string;
    key_improvements: string[];
    areas_of_concern: string[];
    obsolete_advice: string[];
  };
}

export default function HistoryPage() {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [baselineId, setBaselineId] = useState<number | null>(null);
  const [comparisonId, setComparisonId] = useState<number | null>(null);

  const [isDiffing, setIsDiffing] = useState(false);
  const [diffResult, setDiffResult] = useState<DiffResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      setIsLoading(true);
      try {
        const data = await apiRequest<{ items: HistoryItem[]; total: number }>("/advisor/history?limit=20");
        if (data && data.items) {
          setHistoryItems(data.items);
          if (data.items.length >= 2) {
            setBaselineId(data.items[data.items.length - 1].id);
            setComparisonId(data.items[0].id);
          } else if (data.items.length === 1) {
            setBaselineId(data.items[0].id);
          }
        }
      } catch (err) {
        // ignore
      } finally {
        setIsLoading(false);
      }
    }

    fetchHistory();
  }, []);

  const handleComputeDiff = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!baselineId || !comparisonId) return;
    if (baselineId === comparisonId) {
      setError("Please choose two different historical analyses to compare.");
      return;
    }

    setIsDiffing(true);
    setError(null);

    try {
      const data = await apiRequest<DiffResponse>("/advisor/history/diff", {
        method: "POST",
        body: JSON.stringify({
          baseline_analysis_id: baselineId,
          comparison_analysis_id: comparisonId,
        }),
      });
      setDiffResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to compute analysis diff.");
    } finally {
      setIsDiffing(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="flex flex-col min-h-screen bg-[#f8f9ff]">
        <Navbar />

        <main className="flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-12 max-w-7xl mx-auto w-full">
          {/* HEADER */}
          <div className="flex flex-col md:flex-row md:items-end justify-between pb-8 border-b border-slate-200 gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 font-semibold text-xs tracking-wider uppercase mb-2">
                <History className="w-4 h-4 text-indigo-600" />
                <span>Deterministic Memory Diff &amp; Advice Evolution</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                Analysis History &amp; Snapshot Diff
              </h1>
              <p className="text-sm sm:text-base text-slate-500 max-w-2xl mt-1">
                Inspect your previous AI consultations and compute exact delta differences between two point-in-time financial snapshots. Track net worth changes, risk shifts, and superseded advice.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="px-5 py-2.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-md shadow-indigo-100 transition-all flex items-center gap-2"
              >
                <span>New Consultation</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* SPREAD OUT 12-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-12">
            {/* TIMELINE (5 COLS) */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                  <h3 className="text-base font-bold text-slate-900 font-display">
                    Consultation Timeline
                  </h3>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
                    {historyItems.length} Snapshots
                  </span>
                </div>

                {isLoading ? (
                  <div className="py-12 text-center text-xs text-slate-400">Loading history...</div>
                ) : historyItems.length === 0 ? (
                  <div className="p-8 text-center rounded-2xl bg-slate-50 border border-dashed border-slate-200">
                    <History className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-sm font-medium text-slate-600">No consultation snapshots yet.</p>
                    <p className="text-xs text-slate-400 mt-1">
                      Run an analysis on the Dashboard to save your first snapshot to history.
                    </p>
                    <Link
                      href="/dashboard"
                      className="inline-block mt-3 px-4 py-2 rounded-xl bg-indigo-700 text-white text-xs font-semibold"
                    >
                      Go to Dashboard
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {historyItems.map((item) => (
                      <div
                        key={item.id}
                        className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:bg-white hover:shadow-xs transition-all"
                      >
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                          <span className="font-semibold text-indigo-700">#Snapshot {item.id}</span>
                          <span>{new Date(item.created_at).toLocaleDateString()}</span>
                        </div>
                        <h4 className="text-xs font-bold text-slate-800 line-clamp-2">
                          &quot;{item.question}&quot;
                        </h4>
                        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                          <span>
                            Surplus: <strong>₹{Number(item.financial_context?.metrics?.monthly_surplus || 0).toLocaleString("en-IN")}</strong>
                          </span>
                          <span className="capitalize">
                            Risk: <strong>{item.financial_context?.risk_assessment?.risk_category || "Moderate"}</strong>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Diff Selector Form */}
              {historyItems.length >= 2 && (
                <form onSubmit={handleComputeDiff} className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
                  <h4 className="text-sm font-bold text-slate-900 font-display flex items-center gap-2">
                    <ArrowLeftRight className="w-4 h-4 text-indigo-600" />
                    Compare Two Snapshots
                  </h4>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                        Baseline (Earlier)
                      </label>
                      <select
                        value={baselineId || ""}
                        onChange={(e) => setBaselineId(Number(e.target.value))}
                        className="w-full p-2.5 rounded-xl border border-slate-200 text-xs font-medium outline-none focus:border-indigo-600 bg-white"
                      >
                        {historyItems.map((item) => (
                          <option key={item.id} value={item.id}>
                            #{item.id} ({new Date(item.created_at).toLocaleDateString()})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                        Current (Later)
                      </label>
                      <select
                        value={comparisonId || ""}
                        onChange={(e) => setComparisonId(Number(e.target.value))}
                        className="w-full p-2.5 rounded-xl border border-slate-200 text-xs font-medium outline-none focus:border-indigo-600 bg-white"
                      >
                        {historyItems.map((item) => (
                          <option key={item.id} value={item.id}>
                            #{item.id} ({new Date(item.created_at).toLocaleDateString()})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {error && (
                    <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isDiffing}
                    className="w-full py-3 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
                  >
                    {isDiffing ? "Computing Mathematical Deltas..." : "Compute Snapshot Diff"}
                  </button>
                </form>
              )}
            </div>

            {/* RESULTS (7 COLS) */}
            <div className="lg:col-span-7 space-y-6">
              {!diffResult && !isDiffing && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs">
                  <ArrowLeftRight className="w-12 h-12 text-indigo-300 mx-auto mb-4" />
                  <h3 className="text-lg font-bold text-slate-900 font-display">
                    Select Snapshots to Compare
                  </h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
                    Compare your baseline financial context against a newer analysis to calculate wealth growth deltas and detect outdated advice.
                  </p>
                </div>
              )}

              {isDiffing && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs space-y-4">
                  <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto"></div>
                  <h4 className="text-sm font-bold text-slate-800">Diffing Point-in-Time Contexts...</h4>
                  <p className="text-xs text-slate-400">Comparing numerical matrices and detecting obsolete recommendations</p>
                </div>
              )}

              {diffResult && (
                <div className="space-y-6">
                  {/* Metric Deltas Table */}
                  <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                      <h4 className="text-base font-bold text-slate-900 font-display">
                        Deterministic Metric Deltas
                      </h4>
                      <span className="text-xs text-indigo-700 font-semibold">
                        #{diffResult.baseline_id} &rarr; #{diffResult.current_id}
                      </span>
                    </div>

                    <div className="space-y-3">
                      {diffResult.metric_deltas.map((m, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/80 flex items-center justify-between text-xs"
                        >
                          <div>
                            <span className="font-bold text-slate-800 block">{m.metric_name}</span>
                            <span className="text-[11px] text-slate-500">
                              Baseline: ₹{Number(m.baseline_value || 0).toLocaleString("en-IN")} &rarr; Current: ₹{Number(m.current_value || 0).toLocaleString("en-IN")}
                            </span>
                          </div>

                          <div
                            className={`flex items-center gap-1 font-bold px-2.5 py-1 rounded-xl text-xs ${
                              m.trend === "improved"
                                ? "bg-emerald-100 text-emerald-800"
                                : m.trend === "declined"
                                ? "bg-rose-100 text-rose-800"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {m.trend === "improved" && <TrendingUp className="w-3.5 h-3.5" />}
                            {m.trend === "declined" && <TrendingDown className="w-3.5 h-3.5" />}
                            <span>Δ {m.delta_value}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* AI Narrative Diff Card */}
                  <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
                    <div className="flex items-center gap-2 pb-4 border-b border-slate-100">
                      <Sparkles className="w-5 h-5 text-indigo-600" />
                      <h4 className="text-base font-bold text-slate-900 font-display">
                        AI Advice Evolution &amp; Obsolete Guidance
                      </h4>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {diffResult.ai_explanation.summary_narrative}
                    </p>

                    {diffResult.ai_explanation.obsolete_advice?.length > 0 && (
                      <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 space-y-2">
                        <span className="text-xs font-bold text-rose-800 uppercase tracking-wider block">
                          Superseded / Obsolete Advice
                        </span>
                        <ul className="space-y-1 text-xs text-rose-700 list-disc list-inside">
                          {diffResult.ai_explanation.obsolete_advice.map((obs, idx) => (
                            <li key={idx}>{obs}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>

        <Footer />
      </div>
    </ProtectedRoute>
  );
}
