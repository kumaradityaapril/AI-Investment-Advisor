"use client";

import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { apiRequest } from "@/lib/api";
import {
  Sliders,
  TrendingUp,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Zap,
} from "lucide-react";

interface ScenarioTemplate {
  name: string;
  description: string;
  monthly_investment_delta?: number;
  monthly_income_delta?: number;
  monthly_expenses_delta?: number;
  lump_sum_investment?: number;
  time_horizon_years?: number;
  expected_annual_return_percent?: number;
}

interface ScenarioSimulationResult {
  scenario_name: string;
  baseline_projection: {
    final_future_value: number;
    total_invested: number;
    total_interest: number;
    annual_breakdown?: Array<{
      year: number;
      beginning_balance: number;
      annual_contribution: number;
      interest_earned: number;
      ending_balance: number;
    }>;
  };
  scenario_projection: {
    final_future_value: number;
    total_invested: number;
    total_interest: number;
    annual_breakdown?: Array<{
      year: number;
      beginning_balance: number;
      annual_contribution: number;
      interest_earned: number;
      ending_balance: number;
    }>;
  };
  difference: {
    future_value_delta: number;
    total_invested_delta: number;
    total_interest_delta: number;
    percentage_increase?: number;
  };
  ai_explanation: {
    summary_narrative: string;
    key_takeaways: string[];
    risk_considerations: string[];
    goal_impact_analysis: string;
  };
  disclaimer: string;
}

export default function ScenariosPage() {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [scenarioName, setScenarioName] = useState("Increase SIP by ₹5,000");
  const [sipDelta, setSipDelta] = useState<number>(5000);
  const [lumpSum, setLumpSum] = useState<number>(0);
  const [horizonYears, setHorizonYears] = useState<number>(10);
  const [returnRate, setReturnRate] = useState<number>(11);

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ScenarioSimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTemplates() {
      try {
        const data = await apiRequest<ScenarioTemplate[]>("/scenarios/templates");
        if (data && data.length > 0) {
          setTemplates(data);
        }
      } catch (err) {
        // ignore
      }
    }
    fetchTemplates();
  }, []);

  const applyTemplate = (tpl: ScenarioTemplate) => {
    setScenarioName(tpl.name);
    if (tpl.monthly_investment_delta !== undefined) setSipDelta(tpl.monthly_investment_delta);
    if (tpl.lump_sum_investment !== undefined) setLumpSum(tpl.lump_sum_investment);
    if (tpl.time_horizon_years !== undefined) setHorizonYears(tpl.time_horizon_years);
    if (tpl.expected_annual_return_percent !== undefined) setReturnRate(tpl.expected_annual_return_percent);
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiRequest<ScenarioSimulationResult>("/scenarios/simulate", {
        method: "POST",
        body: JSON.stringify({
          scenario_name: scenarioName,
          monthly_investment_delta: sipDelta,
          lump_sum_investment: lumpSum,
          time_horizon_years: horizonYears,
          expected_annual_return_percent: returnRate,
        }),
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Simulation failed. Please verify your profile baseline.");
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
                <Sliders className="w-4 h-4 text-indigo-600" />
                <span>Deterministic Scenario Simulator</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                Financial &quot;What-If&quot; Simulator
              </h1>
              <p className="text-sm sm:text-base text-slate-500 max-w-2xl mt-1">
                Test hypothetical financial decisions before committing capital. Calculate how increasing your monthly SIP by ₹5,000 or deploying a bonus affects your wealth compounding over 10+ years.
              </p>
            </div>
          </div>

          {/* SPREAD OUT 12-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-12">
            {/* CONTROLS (5 COLS) */}
            <div className="lg:col-span-5 space-y-6">
              {/* Quick Template Picker */}
              {templates.length > 0 && (
                <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                    Quick Scenario Presets
                  </h3>
                  <div className="space-y-2">
                    {templates.map((tpl) => (
                      <button
                        key={tpl.name}
                        type="button"
                        onClick={() => applyTemplate(tpl)}
                        className={`w-full p-3 rounded-2xl text-left text-xs font-semibold border transition-all flex items-center justify-between cursor-pointer ${
                          scenarioName === tpl.name
                            ? "bg-indigo-50 border-indigo-300 text-indigo-900 shadow-xs"
                            : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        <div className="pr-2">
                          <span>{tpl.name}</span>
                          <span className="block text-[11px] font-normal text-slate-400 mt-0.5">
                            {tpl.description}
                          </span>
                        </div>
                        <Zap className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Simulation Form */}
              <form onSubmit={handleSimulate} className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-5">
                <h3 className="text-base font-bold text-slate-900 font-display">
                  Hypothetical Parameters
                </h3>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    Scenario Title
                  </label>
                  <input
                    type="text"
                    required
                    value={scenarioName}
                    onChange={(e) => setScenarioName(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium outline-none focus:border-indigo-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                    <span>Monthly SIP Change (Δ ₹)</span>
                    <strong className="text-indigo-700">
                      {sipDelta >= 0 ? `+₹${sipDelta.toLocaleString("en-IN")}` : `-₹${Math.abs(sipDelta).toLocaleString("en-IN")}`}
                    </strong>
                  </div>
                  <input
                    type="range"
                    min="-15000"
                    max="50000"
                    step="1000"
                    value={sipDelta}
                    onChange={(e) => setSipDelta(Number(e.target.value))}
                    className="w-full accent-indigo-700 cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">
                    One-time Lump Sum Addition (₹)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="10000"
                    value={lumpSum}
                    onChange={(e) => setLumpSum(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium outline-none focus:border-indigo-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                    <span>Compounding Duration</span>
                    <strong className="text-indigo-700">{horizonYears} Years</strong>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="30"
                    value={horizonYears}
                    onChange={(e) => setHorizonYears(Number(e.target.value))}
                    className="w-full accent-indigo-700 cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                    <span>Assumed Annual Return Rate</span>
                    <strong className="text-indigo-700">{returnRate}% p.a.</strong>
                  </div>
                  <input
                    type="range"
                    min="4"
                    max="18"
                    step="0.5"
                    value={returnRate}
                    onChange={(e) => setReturnRate(Number(e.target.value))}
                    className="w-full accent-indigo-700 cursor-pointer"
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
                  disabled={isLoading}
                  className="w-full py-3.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-xs shadow-md shadow-indigo-100 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
                >
                  {isLoading ? "Running Simulation Engine..." : "Run Scenario Simulation"}
                </button>
              </form>
            </div>

            {/* RESULTS (7 COLS) */}
            <div className="lg:col-span-7 space-y-6">
              {!result && !isLoading && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs">
                  <Sliders className="w-12 h-12 text-indigo-300 mx-auto mb-4" />
                  <h3 className="text-lg font-bold text-slate-900 font-display">
                    Ready to Simulate
                  </h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
                    Choose a preset or adjust the parameters on the left to project baseline vs. hypothetical wealth outcomes over time.
                  </p>
                </div>
              )}

              {isLoading && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs">
                  <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
                  <h4 className="text-sm font-bold text-slate-800">Calculating Compounding Deltas...</h4>
                  <p className="text-xs text-slate-400 mt-1">Generating mathematical baseline and scenario curves</p>
                </div>
              )}

              {result && (
                <div className="space-y-6">
                  {/* Top Comparison KPI Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
                      <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">
                        Baseline Projection
                      </span>
                      <h4 className="text-2xl font-black text-slate-900 font-display mt-2">
                        ₹{Number(result.baseline_projection.final_future_value).toLocaleString("en-IN")}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1">
                        Invested: ₹{Number(result.baseline_projection.total_invested).toLocaleString("en-IN")}
                      </p>
                    </div>

                    <div className="bg-white rounded-3xl p-6 border border-indigo-200 shadow-xs relative overflow-hidden">
                      <span className="text-xs text-indigo-700 font-bold uppercase tracking-wider block">
                        Hypothetical Outcome
                      </span>
                      <h4 className="text-2xl font-black text-indigo-900 font-display mt-2">
                        ₹{Number(result.scenario_projection.final_future_value).toLocaleString("en-IN")}
                      </h4>
                      <div className="mt-1 flex items-center gap-1.5 text-xs text-emerald-700 font-bold">
                        <TrendingUp className="w-3.5 h-3.5" />
                        <span>
                          +₹{Number(result.difference.future_value_delta).toLocaleString("en-IN")} difference
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* AI Explanation Card */}
                  <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
                    <div className="flex items-center gap-2 pb-4 border-b border-slate-100">
                      <Sparkles className="w-5 h-5 text-indigo-600" />
                      <h4 className="text-base font-bold text-slate-900 font-display">
                        AI Scenario Breakdown &amp; Trade-Offs
                      </h4>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {result.ai_explanation.summary_narrative}
                    </p>

                    {result.ai_explanation.key_takeaways?.length > 0 && (
                      <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-2">
                        <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider block">
                          Key Advantages
                        </span>
                        <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside">
                          {result.ai_explanation.key_takeaways.map((point, idx) => (
                            <li key={idx}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.ai_explanation.risk_considerations?.length > 0 && (
                      <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-2">
                        <span className="text-xs font-bold text-amber-900 uppercase tracking-wider block flex items-center gap-1">
                          <ShieldAlert className="w-3.5 h-3.5 text-amber-600" /> Risks &amp; Liquidity Constraints
                        </span>
                        <ul className="space-y-1 text-xs text-amber-800 list-disc list-inside">
                          {result.ai_explanation.risk_considerations.map((risk, idx) => (
                            <li key={idx}>{risk}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="p-4 rounded-2xl bg-slate-50 text-[11px] text-slate-500 border border-slate-200 leading-relaxed">
                      {result.disclaimer}
                    </div>
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
