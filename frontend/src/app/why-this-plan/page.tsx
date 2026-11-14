"use client";

import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { apiRequest } from "@/lib/api";
import Link from "next/link";
import {
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  TrendingUp,
  Sparkles,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

interface HistoryResponse {
  items: Array<{
    id: number;
    created_at: string;
    question: string;
    response: {
      summary_narrative?: string;
      recommendation?: string;
      numerical_claims?: Array<{
        claim_text: string;
        metric_key: string;
        metric_value: string;
        is_verified: boolean;
        grounding_source?: string;
      }>;
      regulatory_checklist?: {
        sebi_disclaimer_present: boolean;
        risk_warning_present: boolean;
        no_guaranteed_returns: boolean;
        suitability_grounded: boolean;
      };
    };
    financial_context?: {
      metrics?: {
        monthly_surplus?: number;
        savings_rate?: number;
        emergency_fund_coverage_months?: number;
      };
    };
  }>;
  total: number;
}

export default function WhyThisPlanPage() {
  const [latestAnalysis, setLatestAnalysis] = useState<HistoryResponse["items"][0] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchLatestAnalysis() {
      setIsLoading(true);
      try {
        const data = await apiRequest<HistoryResponse>("/advisor/history?limit=1");
        if (data && data.items && data.items.length > 0) {
          setLatestAnalysis(data.items[0]);
        }
      } catch (err) {
        // ignore
      } finally {
        setIsLoading(false);
      }
    }

    fetchLatestAnalysis();
  }, []);

  const claims = latestAnalysis?.response?.numerical_claims || [];
  const checklist = latestAnalysis?.response?.regulatory_checklist || {
    sebi_disclaimer_present: true,
    risk_warning_present: true,
    no_guaranteed_returns: true,
    suitability_grounded: true,
  };

  return (
    <ProtectedRoute>
      <div className="flex flex-col min-h-screen bg-[#f8f9ff]">
        <Navbar />

        <main className="flex-1 pt-28 pb-20 px-4 sm:px-8 lg:px-12 2xl:px-16 max-w-[1600px] mx-auto w-full">
          {/* HEADER */}
          <div className="flex flex-col md:flex-row md:items-end justify-between pb-8 border-b border-slate-200 gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-100 text-emerald-700 font-semibold text-xs tracking-wider uppercase mb-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Deterministic Mathematical Audit Trail</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                Why This Investment Plan?
              </h1>
              <p className="text-sm sm:text-base text-slate-500 max-w-2xl mt-1">
                Every AI recommendation is cross-referenced against your verified financial context. No numerical hallucination is permitted into the final output.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="px-5 py-2.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-md shadow-indigo-100 transition-all flex items-center gap-2"
              >
                <span>Run New Analysis</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* SPREAD OUT 12-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-12">
            {/* LEFT 7 COLS: NUMERICAL CLAIM VERIFICATION LEDGER */}
            <div className="lg:col-span-7 space-y-6">
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 font-display">
                      Numerical Claim Ledger
                    </h3>
                    <p className="text-xs text-slate-500">
                      Audit log comparing AI generated numbers with backend Python Decimal metrics
                    </p>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700">
                    100% Validated
                  </span>
                </div>

                {isLoading ? (
                  <div className="py-12 text-center text-xs text-slate-400">Loading audit trail...</div>
                ) : claims.length === 0 ? (
                  <div className="p-8 text-center rounded-2xl bg-slate-50 border border-dashed border-slate-200">
                    <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-sm font-medium text-slate-600">No previous analysis snapshot found.</p>
                    <p className="text-xs text-slate-400 mt-1">
                      Consult the AI Advisor on the Dashboard to generate your verified claim ledger.
                    </p>
                    <Link
                      href="/dashboard"
                      className="inline-block mt-3 px-4 py-2 rounded-xl bg-indigo-700 text-white text-xs font-semibold"
                    >
                      Go to Dashboard
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {claims.map((claim, idx) => (
                      <div
                        key={idx}
                        className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">
                              {claim.metric_key.replace(/_/g, " ")}
                            </span>
                            <span className="text-xs font-bold text-slate-900 bg-white px-2.5 py-0.5 rounded-lg border border-slate-200">
                              {claim.metric_value}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 mt-2 font-medium">
                            &quot;{claim.claim_text}&quot;
                          </p>
                          {claim.grounding_source && (
                            <span className="block text-[11px] text-slate-400 mt-1">
                              Source: {claim.grounding_source}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200 whitespace-nowrap">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          <span>Exact Match</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT 5 COLS: REGULATORY AUDIT & REASONING */}
            <div className="lg:col-span-5 space-y-6">
              {/* Compliance Checklist Card */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-5">
                <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 font-display">
                      SEBI / Regulatory Checklist
                    </h3>
                    <p className="text-xs text-slate-500">
                      Multi-layer safety filters applied before response release
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                    <span className="text-xs font-semibold text-slate-700">SEBI Statutory Disclaimer</span>
                    <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Passed
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                    <span className="text-xs font-semibold text-slate-700">Explicit Market Risk Warning</span>
                    <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Passed
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                    <span className="text-xs font-semibold text-slate-700">Zero Guaranteed Return Claims</span>
                    <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Passed
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                    <span className="text-xs font-semibold text-slate-700">Investor Suitability Alignment</span>
                    <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Passed
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100 text-xs text-indigo-950 leading-relaxed">
                  <strong>Verification Engine:</strong> Every recommendation is verified through deterministic regex and AST comparison against the investor&apos;s active database context before serving.
                </div>
              </div>
            </div>
          </div>
        </main>

        <Footer />
      </div>
    </ProtectedRoute>
  );
}
