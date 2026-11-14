"use client";

import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { apiRequest } from "@/lib/api";
import {
  TrendingUp,
  Sliders,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from "lucide-react";

interface ComparisonResult {
  comparison_table: Array<{
    name: string;
    category: string;
    expected_annual_return_percent: number;
    risk_level: string;
    liquidity: string;
    lock_in_period_months: number;
    tax_implications: string;
    capital_protection: string;
    advantages: string[];
    disadvantages: string[];
    projected_future_value?: number;
    projected_total_investment?: number;
    projected_total_earnings?: number;
  }>;
  ai_explanation: {
    summary: string;
    key_differences: string[];
    suitability_analysis: Array<{
      option_name: string;
      suitable_for: string;
      unsuitable_for: string;
      key_tradeoff: string;
    }>;
    risk_tradeoffs: string[];
  };
  disclaimer: string;
}

const PRESET_OPTIONS = [
  {
    name: "Bank Fixed Deposit (FD)",
    category: "fixed_income",
    expected_annual_return_percent: 7.0,
    risk_level: "low",
    liquidity: "moderate",
    lock_in_period_months: 12,
    recommended_horizon_months: 36,
    tax_implications: "Interest taxed at investor's marginal slab rate",
    capital_protection: "DICGC insured up to ₹5,00,000 per bank",
    advantages: ["Guaranteed returns", "Capital safety", "High predictability"],
    disadvantages: ["Low real returns post-tax and inflation", "TDS deduction"],
  },
  {
    name: "Nifty 50 Index Fund",
    category: "equity_mutual_fund",
    expected_annual_return_percent: 12.0,
    risk_level: "high",
    liquidity: "high",
    lock_in_period_months: 0,
    recommended_horizon_months: 60,
    tax_implications: "12.5% LTCG on profits exceeding ₹1.25L/yr; 20% STCG",
    capital_protection: "No capital guarantee; subject to equity market volatility",
    advantages: ["High long-term inflation-beating compounding", "Low expense ratio", "T+2 liquidity"],
    disadvantages: ["Short-term market drawdowns", "Requires emotional discipline"],
  },
  {
    name: "Public Provident Fund (PPF)",
    category: "ppf",
    expected_annual_return_percent: 7.1,
    risk_level: "low",
    liquidity: "locked",
    lock_in_period_months: 180,
    recommended_horizon_months: 180,
    tax_implications: "EEE status (Exempt on investment, interest, and maturity)",
    capital_protection: "Sovereign Government of India backed",
    advantages: ["Triple tax exemption", "Zero credit risk", "Disciplined savings"],
    disadvantages: ["15-year lock-in period", "₹1.5 Lakh annual cap"],
  },
  {
    name: "Sovereign Gold Bonds (SGB)",
    category: "gold",
    expected_annual_return_percent: 9.5,
    risk_level: "moderate",
    liquidity: "moderate",
    lock_in_period_months: 96,
    recommended_horizon_months: 96,
    tax_implications: "Capital gains completely tax-free if held to maturity",
    capital_protection: "RBI guaranteed redemption linked to market gold prices",
    advantages: ["2.5% annual coupon interest", "Tax-free redemption", "No storage risk"],
    disadvantages: ["8-year maturity duration", "Gold market price cycles"],
  },
];

export default function ComparePage() {
  const [selectedPresetNames, setSelectedPresetNames] = useState<string[]>([
    "Bank Fixed Deposit (FD)",
    "Nifty 50 Index Fund",
    "Public Provident Fund (PPF)",
  ]);
  const [invType, setInvType] = useState<"monthly_sip" | "lump_sum">("monthly_sip");
  const [amount, setAmount] = useState<number>(10000);
  const [horizonYears, setHorizonYears] = useState<number>(5);
  const [question, setQuestion] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const toggleOption = (name: string) => {
    if (selectedPresetNames.includes(name)) {
      if (selectedPresetNames.length <= 2) {
        setError("At least 2 options are required for comparison.");
        return;
      }
      setSelectedPresetNames(selectedPresetNames.filter((n) => n !== name));
    } else {
      if (selectedPresetNames.length >= 5) {
        setError("You can compare a maximum of 5 options at once.");
        return;
      }
      setSelectedPresetNames([...selectedPresetNames, name]);
    }
    setError(null);
  };

  const handleRunComparison = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const chosenOptions = PRESET_OPTIONS.filter((opt) =>
      selectedPresetNames.includes(opt.name)
    );

    try {
      const data = await apiRequest<ComparisonResult>("/investment-comparison/compare", {
        method: "POST",
        body: JSON.stringify({
          options: chosenOptions,
          investment_amount: amount,
          investment_type: invType,
          time_horizon_months: horizonYears * 12,
          investor_question: question || null,
        }),
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to run investment comparison.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="flex flex-col min-h-screen bg-[#f8f9ff]">
        <Navbar />

        <main className="flex-1 pt-28 pb-20 px-4 sm:px-8 lg:px-12 2xl:px-16 max-w-[1600px] mx-auto w-full">
          {/* HEADER */}
          <div className="flex flex-col md:flex-row md:items-end justify-between pb-8 border-b border-slate-200 gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 font-semibold text-xs tracking-wider uppercase mb-2">
                <TrendingUp className="w-4 h-4 text-indigo-600" />
                <span>Deterministic Future Value Projections</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                Multi-Asset Investment Comparator
              </h1>
              <p className="text-sm sm:text-base text-slate-500 max-w-2xl mt-1">
                Compare Fixed Income, Mutual Funds, PPF, and Gold side-by-side. The advisor uses exact compound interest formulas and unbiased AI suitability trade-offs without declaring false winners.
              </p>
            </div>
          </div>

          {/* SPREAD OUT 12-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-12">
            {/* CONTROLS (5 COLS) */}
            <div className="lg:col-span-5 space-y-6">
              <form onSubmit={handleRunComparison} className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900 font-display mb-1">
                    1. Select Assets to Compare (2 to 5)
                  </h3>
                  <p className="text-xs text-slate-500 mb-3">
                    Click to toggle options into your comparison matrix
                  </p>
                  <div className="space-y-2">
                    {PRESET_OPTIONS.map((opt) => {
                      const isSelected = selectedPresetNames.includes(opt.name);
                      return (
                        <div
                          key={opt.name}
                          onClick={() => toggleOption(opt.name)}
                          className={`p-3.5 rounded-2xl border text-xs font-semibold cursor-pointer transition-all flex items-center justify-between ${
                            isSelected
                              ? "bg-indigo-50/70 border-indigo-300 text-indigo-950 shadow-xs"
                              : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                          }`}
                        >
                          <div>
                            <span>{opt.name}</span>
                            <span className="block text-[11px] font-normal text-slate-500 mt-0.5">
                              Exp. Return: <strong>{opt.expected_annual_return_percent}% p.a.</strong> • Risk: {opt.risk_level}
                            </span>
                          </div>
                          <div
                            className={`w-5 h-5 rounded-md flex items-center justify-center text-xs ${
                              isSelected ? "bg-indigo-700 text-white" : "border border-slate-300"
                            }`}
                          >
                            {isSelected && "✓"}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Investment Type & Amount */}
                <div className="pt-4 border-t border-slate-100 space-y-4">
                  <h3 className="text-base font-bold text-slate-900 font-display mb-1">
                    2. Projection Parameters
                  </h3>

                  <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
                    <button
                      type="button"
                      onClick={() => setInvType("monthly_sip")}
                      className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                        invType === "monthly_sip" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600"
                      }`}
                    >
                      Monthly SIP
                    </button>
                    <button
                      type="button"
                      onClick={() => setInvType("lump_sum")}
                      className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                        invType === "lump_sum" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600"
                      }`}
                    >
                      Lump Sum
                    </button>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">
                      {invType === "monthly_sip" ? "Monthly Contribution (₹)" : "Initial Capital (₹)"}
                    </label>
                    <input
                      type="number"
                      min="500"
                      value={amount}
                      onChange={(e) => setAmount(Number(e.target.value))}
                      className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold outline-none focus:border-indigo-600"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                      <span>Time Horizon</span>
                      <strong className="text-indigo-700">{horizonYears} Years ({horizonYears * 12} mos)</strong>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="25"
                      value={horizonYears}
                      onChange={(e) => setHorizonYears(Number(e.target.value))}
                      className="w-full accent-indigo-700 cursor-pointer"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">
                      Specific Question (Optional)
                    </label>
                    <input
                      type="text"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="e.g. Which option has better tax treatment for a 30% slab?"
                      className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs outline-none focus:border-indigo-600"
                    />
                  </div>
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
                  {isLoading ? "Running Mathematical Projections..." : "Run Side-by-Side Comparison"}
                </button>
              </form>
            </div>

            {/* RESULTS (7 COLS) */}
            <div className="lg:col-span-7 space-y-6">
              {!result && !isLoading && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs">
                  <Sliders className="w-12 h-12 text-indigo-300 mx-auto mb-4" />
                  <h3 className="text-lg font-bold text-slate-900 font-display">
                    Configure and Run Comparison
                  </h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
                    Select your asset options and parameters on the left to see deterministic future values and AI-generated risk trade-offs.
                  </p>
                </div>
              )}

              {isLoading && (
                <div className="bg-white rounded-3xl p-12 border border-slate-200/80 text-center shadow-xs">
                  <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
                  <h4 className="text-sm font-bold text-slate-800">Calculating Compounding Curves...</h4>
                  <p className="text-xs text-slate-400 mt-1">Applying Python Decimal compound interest algorithms</p>
                </div>
              )}

              {result && (
                <div className="space-y-6">
                  {/* Future Value Projection Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {result.comparison_table.map((item) => (
                      <div
                        key={item.name}
                        className="bg-white rounded-3xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between"
                      >
                        <div>
                          <span className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider block mb-1">
                            {item.category.replace("_", " ")}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900">{item.name}</h4>
                          <div className="mt-3">
                            <span className="text-xs text-slate-400">Projected Future Value</span>
                            <p className="text-2xl font-black text-slate-900 font-display">
                              ₹{Number(item.projected_future_value || 0).toLocaleString("en-IN")}
                            </p>
                          </div>
                        </div>

                        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                          <span>Return: <strong>{item.expected_annual_return_percent}%</strong></span>
                          <span>Risk: <strong className="capitalize">{item.risk_level}</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* AI Explanation & Trade-offs */}
                  <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
                    <div className="flex items-center gap-2 pb-4 border-b border-slate-100">
                      <Sparkles className="w-5 h-5 text-indigo-600" />
                      <h4 className="text-base font-bold text-slate-900 font-display">
                        Objective Comparative Analysis
                      </h4>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {result.ai_explanation.summary}
                    </p>

                    {result.ai_explanation.key_differences?.length > 0 && (
                      <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-2">
                        <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider block">
                          Key Structural Differences
                        </span>
                        <ul className="space-y-1.5 text-xs text-slate-700 list-disc list-inside">
                          {result.ai_explanation.key_differences.map((diff, idx) => (
                            <li key={idx}>{diff}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Disclaimer */}
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
