"use client";

import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { apiRequest } from "@/lib/api";
import {
  Sparkles,
  Search,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
  Send,
  Clock,
  Layers,
  ArrowRight,
} from "lucide-react";

interface ResearchStep {
  step_number: number;
  tool_name: string;
  description: string;
  output_summary?: string;
}

interface ResearchReport {
  query: string;
  executive_summary: string;
  key_findings: string[];
  synthesis: string;
  risk_factors: string[];
  execution_steps?: ResearchStep[];
  regulatory_disclaimer: string;
}

export default function ResearchPage() {
  const [query, setQuery] = useState(
    "What are the tax implications and lock-in differences between PPF and Sovereign Gold Bonds?"
  );
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await apiRequest<ResearchReport>("/research", {
        method: "POST",
        body: JSON.stringify({ query }),
      });
      setReport(data);
    } catch (err: any) {
      setError(err.message || "Autonomous research agent encountered an error.");
    } finally {
      setIsLoading(false);
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
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <span>Autonomous LangGraph Research Agent</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                AI Deep Research Dossier
              </h1>
              <p className="text-sm sm:text-base text-slate-500 max-w-2xl mt-1">
                Dispatch an autonomous multi-step research agent. It plans sub-tasks, queries your indexed pgvector documents, runs deterministic calculations, and synthesizes institutional-grade research dossiers.
              </p>
            </div>
          </div>

          {/* SPREAD OUT 12-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-12">
            {/* CONTROLS (5 COLS) */}
            <div className="lg:col-span-5 space-y-6">
              <form onSubmit={handleRunResearch} className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-5">
                <h3 className="text-base font-bold text-slate-900 font-display">
                  Research Mission Prompt
                </h3>
                <p className="text-xs text-slate-500">
                  Ask complex financial questions requiring multi-source analysis
                </p>

                <div>
                  <textarea
                    rows={4}
                    required
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter research topic..."
                    className="w-full p-4 rounded-2xl border border-slate-200 text-xs sm:text-sm font-medium outline-none focus:border-indigo-600 focus:ring-4 focus:ring-indigo-50 leading-relaxed bg-slate-50/50"
                  />
                </div>

                {error && (
                  <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isLoading || !query.trim()}
                  className="w-full py-3.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-md shadow-indigo-100 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                      Executing LangGraph Workflow...
                    </span>
                  ) : (
                    <>
                      Execute Autonomous Research <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Sample Mission Presets */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-3">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Recommended Missions
                </h4>
                <button
                  type="button"
                  onClick={() =>
                    setQuery(
                      "What are the LTCG tax rules on equity mutual funds after the 2024 Budget and how does it compare to debt funds?"
                    )
                  }
                  className="w-full text-left p-3 rounded-2xl bg-slate-50 hover:bg-indigo-50/50 border border-slate-200 text-xs font-semibold text-slate-700 transition-all block cursor-pointer"
                >
                  2024 Budget LTCG Tax Changes on Mutual Funds
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setQuery(
                      "Compare emergency fund requirements for salaried individuals vs freelancers with fluctuating incomes."
                    )
                  }
                  className="w-full text-left p-3 rounded-2xl bg-slate-50 hover:bg-indigo-50/50 border border-slate-200 text-xs font-semibold text-slate-700 transition-all block cursor-pointer"
                >
                  Emergency Fund Calibration: Salaried vs Freelance
                </button>
              </div>
            </div>

            {/* RESULTS (7 COLS) */}
            <div className="lg:col-span-7 space-y-6">
              {!report && !isLoading && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs">
                  <Sparkles className="w-12 h-12 text-indigo-300 mx-auto mb-4" />
                  <h3 className="text-lg font-bold text-slate-900 font-display">
                    Dispatch Research Agent
                  </h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
                    Provide a query on the left to see autonomous tool execution steps, verified citations, and an executive research report.
                  </p>
                </div>
              )}

              {isLoading && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs space-y-4">
                  <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto"></div>
                  <h4 className="text-sm font-bold text-slate-800">Agent Running Autonomous Loops...</h4>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Retrieving document chunks from pgvector, validating statutory facts, and synthesizing findings.
                  </p>
                </div>
              )}

              {report && (
                <div className="space-y-6">
                  {/* Executive Summary Card */}
                  <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-5">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                      <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider flex items-center gap-1.5">
                        <FileText className="w-4 h-4" /> Research Dossier
                      </span>
                      <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                        Evidence Grounded
                      </span>
                    </div>

                    <div>
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                        Executive Summary
                      </h4>
                      <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                        {report.executive_summary}
                      </p>
                    </div>

                    {report.key_findings?.length > 0 && (
                      <div className="p-5 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-2.5">
                        <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider">
                          Key Findings
                        </h4>
                        <ul className="space-y-1.5 text-xs text-slate-700 list-disc list-inside">
                          {report.key_findings.map((f, i) => (
                            <li key={i}>{f}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {report.synthesis && (
                      <div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                          Detailed Synthesis
                        </h4>
                        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                          {report.synthesis}
                        </p>
                      </div>
                    )}

                    {report.risk_factors?.length > 0 && (
                      <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-2">
                        <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                          Risk Factors &amp; Regulatory Caveats
                        </h4>
                        <ul className="space-y-1 text-xs text-amber-800 list-disc list-inside">
                          {report.risk_factors.map((rf, i) => (
                            <li key={i}>{rf}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {report.regulatory_disclaimer && (
                      <div className="p-4 rounded-2xl bg-slate-50 text-[11px] text-slate-500 border border-slate-200 leading-relaxed">
                        {report.regulatory_disclaimer}
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
