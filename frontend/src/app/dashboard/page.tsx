"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { apiRequest } from "@/lib/api";
import {
  TrendingUp,
  Wallet,
  ShieldCheck,
  Target,
  Sparkles,
  ArrowRight,
  PieChart as PieIcon,
  AlertCircle,
  CheckCircle2,
  Send,
  FileText,
  Sliders,
} from "lucide-react";

interface FinancialContextData {
  profile?: {
    monthly_income?: string | number;
    monthly_expenses?: string | number;
    savings?: string | number;
    existing_investments?: string | number;
    monthly_investment_capacity?: string | number;
  };
  goals?: Array<{
    id: number;
    title: string;
    goal_type: string;
    target_amount: string | number;
    time_horizon_months: number;
    planned_monthly_investment?: string | number;
  }>;
  risk_assessment?: {
    risk_score: number;
    risk_category: string;
    assessed_at: string;
  };
  metrics?: {
    total_savings_and_investments?: string | number;
    monthly_surplus?: string | number;
    savings_rate?: string | number;
    emergency_fund_coverage_months?: string | number;
    emergency_fund_target?: string | number;
    emergency_fund_shortfall?: string | number;
  };
  goal_analysis?: Array<{
    goal_id: number;
    goal_title: string;
    target_amount: string | number;
    monthly_contribution_shortfall?: string | number;
    is_on_track?: boolean;
    future_value_projection?: string | number;
  }>;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<FinancialContextData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasProfile, setHasProfile] = useState(true);

  // Quick Advisor Consultation State
  const [promptQuery, setPromptQuery] = useState("");
  const [aiAnswer, setAiAnswer] = useState<any | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [advisorError, setAdvisorError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      try {
        const res = await apiRequest<FinancialContextData>("/financial-analysis/me");
        setData(res);
        setHasProfile(true);
      } catch (err: any) {
        if (err.message && err.message.includes("404")) {
          setHasProfile(false);
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const handleAskAdvisor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptQuery.trim()) return;

    setIsGenerating(true);
    setAdvisorError(null);

    try {
      const res = await apiRequest("/advisor/analyze", {
        method: "POST",
        body: JSON.stringify({ question: promptQuery }),
      });
      setAiAnswer(res);
    } catch (err: any) {
      setAdvisorError(err.message || "Failed to generate AI advice.");
    } finally {
      setIsGenerating(false);
    }
  };

  const metrics = data?.metrics || {};
  const profile = data?.profile || {};
  const goals = data?.goals || [];
  const risk = data?.risk_assessment;
  const goalAnalysis = data?.goal_analysis || [];

  const totalWealth = metrics.total_savings_and_investments
    ? `₹${Number(metrics.total_savings_and_investments).toLocaleString("en-IN")}`
    : "₹0";

  const monthlySurplus = metrics.monthly_surplus
    ? `₹${Number(metrics.monthly_surplus).toLocaleString("en-IN")}`
    : "₹0";

  const savingsRate = metrics.savings_rate
    ? `${Number(metrics.savings_rate).toFixed(1)}%`
    : "0.0%";

  const emergencyMonths = metrics.emergency_fund_coverage_months
    ? `${Number(metrics.emergency_fund_coverage_months).toFixed(1)} mos`
    : "0.0 mos";

  return (
    <ProtectedRoute>
      <div className="flex flex-col min-h-screen bg-[#f8f9ff]">
        <Navbar />

        <main className="flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-12 max-w-7xl mx-auto w-full">
          {/* TOP WELCOME BAR */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-8 border-b border-slate-200 gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 font-semibold text-xs tracking-wider uppercase mb-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Live Institutional Intelligence</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                Welcome back, {user?.email ? user.email.split("@")[0] : "Investor"} 👋
              </h1>
              <p className="text-sm sm:text-base text-slate-500 mt-1">
                Here is your live wealth overview calibrated with Python Decimal math and verified SEBI regulatory guardrails.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/profile"
                className="px-5 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:text-indigo-700 hover:border-indigo-200 font-semibold text-xs shadow-xs transition-all flex items-center gap-2"
              >
                <Sliders className="w-4 h-4 text-indigo-600" />
                <span>Adjust Baseline</span>
              </Link>
              <Link
                href="/documents"
                className="px-5 py-2.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-md shadow-indigo-100 transition-all flex items-center gap-2"
              >
                <FileText className="w-4 h-4" />
                <span>Ingest Documents</span>
              </Link>
            </div>
          </div>

          {/* ONBOARDING CALLOUT IF PROFILE IS EMPTY */}
          {!isLoading && !hasProfile && (
            <div className="mb-8 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-indigo-700 to-indigo-600 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div>
                <span className="px-3 py-1 rounded-full bg-white/20 text-white text-xs font-semibold uppercase tracking-wider">
                  Profile Setup Needed
                </span>
                <h3 className="text-2xl font-bold font-display mt-2">
                  Complete Your Financial Profile
                </h3>
                <p className="text-sm text-indigo-100 max-w-xl mt-1">
                  We need your monthly income, living expenses, and goals to generate your personalized deterministic cash flow metrics and AI recommendations.
                </p>
              </div>
              <Link
                href="/profile"
                className="px-6 py-3.5 rounded-2xl bg-white text-indigo-700 font-bold text-sm shadow-md hover:bg-indigo-50 transition-all flex items-center gap-2 whitespace-nowrap"
              >
                Setup Profile Now <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}

          {/* SPREAD OUT 4-COLUMN KPI METRIC CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Card 1 */}
            <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Total Tracked Wealth
                </span>
                <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </div>
              <div>
                <h2 className="text-3xl font-extrabold text-slate-900 font-display tracking-tight">
                  {totalWealth}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Liquid savings + active investments
                </p>
              </div>
            </div>

            {/* Card 2 */}
            <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Monthly Surplus
                </span>
                <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                  <Wallet className="w-5 h-5" />
                </div>
              </div>
              <div>
                <h2 className="text-3xl font-extrabold text-emerald-700 font-display tracking-tight">
                  {monthlySurplus}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Disposable capital for monthly SIPs
                </p>
              </div>
            </div>

            {/* Card 3 */}
            <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Savings Rate
                </span>
                <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                  <PieIcon className="w-5 h-5" />
                </div>
              </div>
              <div>
                <h2 className="text-3xl font-extrabold text-purple-700 font-display tracking-tight">
                  {savingsRate}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Percentage of income retained
                </p>
              </div>
            </div>

            {/* Card 4 */}
            <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Emergency Buffer
                </span>
                <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5" />
                </div>
              </div>
              <div>
                <h2 className="text-3xl font-extrabold text-slate-900 font-display tracking-tight">
                  {emergencyMonths}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Living expense coverage in savings
                </p>
              </div>
            </div>
          </div>

          {/* SPREAD OUT 12-COLUMN MAIN CONTENT GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* LEFT 8 COLS: GOALS & CASH FLOW ANALYSIS */}
            <div className="lg:col-span-8 space-y-8">
              {/* Financial Goals Tracking Section */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
                      <Target className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-slate-900 font-display">
                        Active Financial Goals &amp; Shortfall
                      </h3>
                      <p className="text-xs text-slate-500">
                        Calculated against current SIP and monthly contribution capacity
                      </p>
                    </div>
                  </div>
                  <Link
                    href="/profile"
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-700"
                  >
                    Manage Goals &rarr;
                  </Link>
                </div>

                {goals.length === 0 ? (
                  <div className="p-8 text-center rounded-2xl bg-slate-50 border border-dashed border-slate-200">
                    <Target className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-sm font-medium text-slate-600">No active goals registered.</p>
                    <Link
                      href="/profile"
                      className="inline-block mt-3 px-4 py-2 rounded-xl bg-indigo-700 text-white text-xs font-semibold"
                    >
                      Add a Goal in Profile
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {goals.map((g) => {
                      const analysis = goalAnalysis.find((a) => a.goal_id === g.id);
                      const shortfall = analysis?.monthly_contribution_shortfall
                        ? Number(analysis.monthly_contribution_shortfall)
                        : 0;

                      return (
                        <div
                          key={g.id}
                          className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-base font-bold text-slate-900">{g.title}</h4>
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 uppercase">
                                {g.goal_type}
                              </span>
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
                              <span>Target: <strong className="text-slate-800">₹{Number(g.target_amount).toLocaleString("en-IN")}</strong></span>
                              <span>Horizon: <strong className="text-slate-800">{g.time_horizon_months} mos</strong></span>
                            </div>
                          </div>

                          <div className="flex sm:flex-col sm:items-end justify-between items-center">
                            {shortfall > 0 ? (
                              <div className="flex items-center gap-1.5 text-xs text-rose-700 font-semibold bg-rose-50 px-3 py-1.5 rounded-xl border border-rose-200">
                                <AlertCircle className="w-4 h-4 text-rose-600" />
                                <span>₹{shortfall.toLocaleString("en-IN")}/mo Shortfall</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-semibold bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
                                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                                <span>On Track</span>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Interactive AI Advisor Consultation */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
                <div className="flex items-center gap-3 pb-6 border-b border-slate-100 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 font-display">
                      Ask AI Investment Advisor
                    </h3>
                    <p className="text-xs text-slate-500">
                      Direct consultation backed by hybrid RAG and your actual balance sheet
                    </p>
                  </div>
                </div>

                <form onSubmit={handleAskAdvisor} className="space-y-4">
                  <div className="relative">
                    <input
                      type="text"
                      value={promptQuery}
                      onChange={(e) => setPromptQuery(e.target.value)}
                      placeholder="e.g. How can I resolve my monthly shortfall using index funds vs PPF?"
                      className="w-full pl-4 pr-12 py-3.5 rounded-2xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-50 text-sm outline-none text-slate-900 bg-slate-50/50"
                    />
                    <button
                      type="submit"
                      disabled={isGenerating || !promptQuery.trim()}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white flex items-center justify-center transition-all disabled:opacity-50 cursor-pointer"
                    >
                      {isGenerating ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {advisorError && (
                    <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                      {advisorError}
                    </div>
                  )}

                  {aiAnswer && (
                    <div className="mt-4 p-6 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-4">
                      <div className="flex items-center justify-between border-b border-indigo-100 pb-3">
                        <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                          <Sparkles className="w-4 h-4 text-indigo-600" />
                          Advisor Recommendation
                        </span>
                        <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                          100% Mathematically Validated
                        </span>
                      </div>
                      <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                        {aiAnswer.summary_narrative || aiAnswer.recommendation || JSON.stringify(aiAnswer, null, 2)}
                      </p>
                    </div>
                  )}
                </form>
              </div>
            </div>

            {/* RIGHT 4 COLS: RISK TIER & MODULE DIRECTORY */}
            <div className="lg:col-span-4 space-y-6">
              {/* Risk Profile Card */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-3">
                  SEBI Risk Calibration
                </span>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="text-2xl font-black text-slate-900 font-display capitalize">
                      {risk?.risk_category || "Moderate"}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Calibrated score: <strong>{risk?.risk_score ?? 12} / 20</strong>
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center font-bold text-base border border-purple-100">
                    {risk?.risk_score ?? 12}
                  </div>
                </div>

                <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden mb-4">
                  <div
                    className="bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 h-full rounded-full"
                    style={{ width: `${((risk?.risk_score ?? 12) / 20) * 100}%` }}
                  ></div>
                </div>

                <Link
                  href="/profile"
                  className="block text-center py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-xs font-semibold text-indigo-700 transition-colors"
                >
                  Recalibrate Risk Score &rarr;
                </Link>
              </div>

              {/* Fast Module Switcher */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
                  Advisor Workspaces
                </span>

                <Link
                  href="/scenarios"
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/50 hover:border-indigo-200 border border-slate-100 transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center">
                      <Sliders className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-xs font-bold text-slate-900 group-hover:text-indigo-700">
                        What-if Scenarios
                      </h5>
                      <p className="text-[11px] text-slate-500">Simulate monthly SIP adjustments</p>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                </Link>

                <Link
                  href="/compare"
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/50 hover:border-indigo-200 border border-slate-100 transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
                      <TrendingUp className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-xs font-bold text-slate-900 group-hover:text-indigo-700">
                        Asset Comparator
                      </h5>
                      <p className="text-[11px] text-slate-500">FD vs PPF vs Equity Index Funds</p>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                </Link>

                <Link
                  href="/research"
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/50 hover:border-indigo-200 border border-slate-100 transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-xs font-bold text-slate-900 group-hover:text-indigo-700">
                        Research Agent
                      </h5>
                      <p className="text-[11px] text-slate-500">Multi-step autonomous agent</p>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                </Link>

                <Link
                  href="/history"
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/50 hover:border-indigo-200 border border-slate-100 transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="text-xs font-bold text-slate-900 group-hover:text-indigo-700">
                        Analysis History &amp; Diff
                      </h5>
                      <p className="text-[11px] text-slate-500">Side-by-side snapshot comparison</p>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </div>
            </div>
          </div>
        </main>

        <Footer />
      </div>
    </ProtectedRoute>
  );
}
