"use client";

import { useState, useEffect, useCallback } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { apiRequest } from "@/lib/api";
import {
  Wallet,
  Target,
  ShieldCheck,
  TrendingUp,
  AlertCircle,
  Plus,
  Trash2,
  CheckCircle2,
  ArrowRight,
  Info,
} from "lucide-react";

interface ProfileData {
  age?: number | null;
  monthly_income?: string | number | null;
  monthly_expenses?: string | number | null;
  savings?: string | number | null;
  existing_investments?: string | number | null;
  monthly_investment_capacity?: string | number | null;
}

interface GoalItem {
  id: number;
  title: string;
  goal_type: string;
  target_amount: string | number;
  time_horizon_months: number;
  planned_monthly_investment?: string | number | null;
}

interface RiskAssessmentData {
  id: number;
  risk_score: number;
  risk_category: "conservative" | "moderate" | "aggressive";
  assessed_at: string;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData>({
    age: 28,
    monthly_income: 100000,
    monthly_expenses: 60000,
    savings: 300000,
    existing_investments: 1400000,
    monthly_investment_capacity: 40000,
  });

  const [goals, setGoals] = useState<GoalItem[]>([]);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentData | null>(null);

  // Risk questionnaire answers (0 to 4)
  const [riskAnswers, setRiskAnswers] = useState({
    investment_experience: 2,
    time_horizon: 3,
    loss_reaction: 2,
    growth_preference: 3,
    financial_stability: 3,
  });

  // Goal Form State
  const [newGoalTitle, setNewGoalTitle] = useState("");
  const [newGoalType, setNewGoalType] = useState("Retirement");
  const [newGoalTarget, setNewGoalTarget] = useState("");
  const [newGoalHorizonMonths, setNewGoalHorizonMonths] = useState("60");
  const [newGoalMonthlySip, setNewGoalMonthlySip] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isAddingGoal, setIsAddingGoal] = useState(false);
  const [isSubmittingRisk, setIsSubmittingRisk] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchProfileAndGoals = useCallback(async () => {
    setIsLoading(true);
    try {
      // 1. Fetch Profile
      try {
        const pData = await apiRequest<ProfileData>("/profile/me");
        if (pData) {
          setProfile({
            age: pData.age ?? 28,
            monthly_income: pData.monthly_income ?? 0,
            monthly_expenses: pData.monthly_expenses ?? 0,
            savings: pData.savings ?? 0,
            existing_investments: pData.existing_investments ?? 0,
            monthly_investment_capacity: pData.monthly_investment_capacity ?? 0,
          });
        }
      } catch (err: any) {
        // If 404, user hasn't created profile yet
      }

      // 2. Fetch Goals
      try {
        const gData = await apiRequest<GoalItem[]>("/goals");
        setGoals(gData || []);
      } catch (err) {
        // ignore
      }

      // 3. Fetch Risk Assessment
      try {
        const rData = await apiRequest<RiskAssessmentData>("/risk-assessments/latest");
        if (rData) {
          setRiskAssessment(rData);
        }
      } catch (err) {
        // ignore
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfileAndGoals();
  }, [fetchProfileAndGoals]);

  // Derived live metrics
  const incomeNum = Number(profile.monthly_income) || 0;
  const expenseNum = Number(profile.monthly_expenses) || 0;
  const savingsNum = Number(profile.savings) || 0;
  const surplus = Math.max(0, incomeNum - expenseNum);
  const savingsRate = incomeNum > 0 ? ((surplus / incomeNum) * 100).toFixed(1) : "0.0";
  const emergencyCoverage = expenseNum > 0 ? (savingsNum / expenseNum).toFixed(1) : "0.0";

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingProfile(true);
    setStatusMessage(null);

    try {
      const updated = await apiRequest<ProfileData>("/profile/me", {
        method: "PUT",
        body: JSON.stringify({
          age: Number(profile.age) || null,
          monthly_income: Number(profile.monthly_income) || 0,
          monthly_expenses: Number(profile.monthly_expenses) || 0,
          savings: Number(profile.savings) || 0,
          existing_investments: Number(profile.existing_investments) || 0,
          monthly_investment_capacity: Number(profile.monthly_investment_capacity) || surplus,
        }),
      });
      setProfile(updated);
      setStatusMessage({ type: "success", text: "Profile baseline saved successfully to backend." });
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to update profile." });
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGoalTitle || !newGoalTarget) return;

    setIsAddingGoal(true);
    setStatusMessage(null);

    try {
      const created = await apiRequest<GoalItem>("/goals", {
        method: "POST",
        body: JSON.stringify({
          title: newGoalTitle,
          goal_type: newGoalType,
          target_amount: parseFloat(newGoalTarget),
          time_horizon_months: parseInt(newGoalHorizonMonths) || 60,
          planned_monthly_investment: newGoalMonthlySip ? parseFloat(newGoalMonthlySip) : null,
        }),
      });

      setGoals((prev) => [...prev, created]);
      setNewGoalTitle("");
      setNewGoalTarget("");
      setNewGoalMonthlySip("");
      setStatusMessage({ type: "success", text: `Goal "${created.title}" registered.` });
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to create goal." });
    } finally {
      setIsAddingGoal(false);
    }
  };

  const handleDeleteGoal = async (goalId: number) => {
    try {
      await apiRequest(`/goals/${goalId}`, { method: "DELETE" });
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
      setStatusMessage({ type: "success", text: "Goal removed." });
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Could not delete goal." });
    }
  };

  const handleSubmitRisk = async () => {
    setIsSubmittingRisk(true);
    setStatusMessage(null);

    try {
      const res = await apiRequest<RiskAssessmentData>("/risk-assessments", {
        method: "POST",
        body: JSON.stringify(riskAnswers),
      });
      setRiskAssessment(res);
      setStatusMessage({
        type: "success",
        text: `Risk Assessment updated: Tier set to ${res.risk_category.toUpperCase()} (Score: ${res.risk_score}/20).`,
      });
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to evaluate risk." });
    } finally {
      setIsSubmittingRisk(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="flex flex-col min-h-screen bg-[#f8f9ff]">
        <Navbar />

        <main className="flex-1 pt-28 pb-20 px-4 sm:px-8 lg:px-12 2xl:px-16 max-w-[1600px] mx-auto w-full">
          {/* HEADER CONTEXT */}
          <div className="flex flex-col md:flex-row md:items-end justify-between pb-8 border-b border-slate-200 gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 font-semibold text-xs tracking-wider uppercase mb-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span>Deterministic Financial Profile Engine</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                Investor Profile &amp; Risk Blueprint
              </h1>
              <p className="text-sm sm:text-base text-slate-500 max-w-2xl mt-1">
                Calibrate your income, expenses, liquid buffers, and risk score. Every figure is saved to the database and used for deterministic shortfall calculation and AI advice.
              </p>
            </div>

            {statusMessage && (
              <div
                className={`p-4 rounded-2xl flex items-center gap-3 text-sm font-medium ${
                  statusMessage.type === "success"
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-rose-50 text-rose-800 border border-rose-200"
                }`}
              >
                {statusMessage.type === "success" ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
                )}
                <span>{statusMessage.text}</span>
              </div>
            )}
          </div>

          {/* SPREAD OUT 12-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* COLUMN 1: FINANCIAL BASELINE (7 COLS) */}
            <div className="lg:col-span-7 space-y-8">
              {/* Cash Flow Form Card */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
                      <Wallet className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-slate-900 font-display">
                        Cash Flow &amp; Balance Sheet
                      </h2>
                      <p className="text-xs text-slate-500">
                        Monthly inflows, living costs, and accumulated capital
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
                    Live Sync
                  </span>
                </div>

                <form onSubmit={handleUpdateProfile} className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                        Monthly Income (₹)
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={profile.monthly_income ?? ""}
                        onChange={(e) =>
                          setProfile({ ...profile, monthly_income: e.target.value })
                        }
                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-50 text-sm font-semibold text-slate-900 outline-none transition-all"
                        placeholder="e.g. 100000"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                        Monthly Expenses (₹)
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={profile.monthly_expenses ?? ""}
                        onChange={(e) =>
                          setProfile({ ...profile, monthly_expenses: e.target.value })
                        }
                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-50 text-sm font-semibold text-slate-900 outline-none transition-all"
                        placeholder="e.g. 60000"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                        Emergency Savings (₹)
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={profile.savings ?? ""}
                        onChange={(e) =>
                          setProfile({ ...profile, savings: e.target.value })
                        }
                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-50 text-sm font-semibold text-slate-900 outline-none transition-all"
                        placeholder="e.g. 300000"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                        Existing Investments (₹)
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={profile.existing_investments ?? ""}
                        onChange={(e) =>
                          setProfile({ ...profile, existing_investments: e.target.value })
                        }
                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-50 text-sm font-semibold text-slate-900 outline-none transition-all"
                        placeholder="e.g. 1400000"
                      />
                    </div>
                  </div>

                  {/* Derived Metrics Preview Banner */}
                  <div className="grid grid-cols-3 gap-4 p-5 rounded-2xl bg-indigo-50/50 border border-indigo-100">
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium">Monthly Surplus</span>
                      <p className="text-lg font-bold text-slate-900 font-display">
                        ₹{surplus.toLocaleString("en-IN")}
                      </p>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium">Savings Rate</span>
                      <p className="text-lg font-bold text-indigo-700 font-display">
                        {savingsRate}%
                      </p>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium">Emergency Buffer</span>
                      <p className="text-lg font-bold text-emerald-700 font-display">
                        {emergencyCoverage} mos
                      </p>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSavingProfile}
                    className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-semibold text-sm shadow-md shadow-indigo-100 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
                  >
                    {isSavingProfile ? "Saving to Backend..." : "Save Financial Baseline"}
                  </button>
                </form>
              </div>

              {/* Goals Management Card */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                      <Target className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-slate-900 font-display">
                        Financial Goals Ledger
                      </h2>
                      <p className="text-xs text-slate-500">
                        Grounded target targets used for deterministic shortfall calculations
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700">
                    {goals.length} Registered
                  </span>
                </div>

                {/* Goals List */}
                <div className="space-y-3 mb-6">
                  {goals.length === 0 ? (
                    <div className="p-8 text-center rounded-2xl bg-slate-50 border border-dashed border-slate-200">
                      <Target className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                      <p className="text-sm font-medium text-slate-600">No financial goals added yet.</p>
                      <p className="text-xs text-slate-400 mt-1">Add your first target below to calibrate shortfall analysis.</p>
                    </div>
                  ) : (
                    goals.map((g) => (
                      <div
                        key={g.id}
                        className="flex items-center justify-between p-4 rounded-2xl bg-slate-50/70 border border-slate-200/70 hover:bg-white hover:shadow-xs transition-all"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-bold text-slate-900">{g.title}</h4>
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                              {g.goal_type}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
                            <span>Target: <strong className="text-slate-800">₹{Number(g.target_amount).toLocaleString("en-IN")}</strong></span>
                            <span>Horizon: <strong className="text-slate-800">{g.time_horizon_months} mos</strong></span>
                            {g.planned_monthly_investment && (
                              <span>SIP: <strong className="text-slate-800">₹{Number(g.planned_monthly_investment).toLocaleString("en-IN")}/mo</strong></span>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => handleDeleteGoal(g.id)}
                          className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
                          title="Delete Goal"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* Add Goal Form */}
                <form onSubmit={handleCreateGoal} className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/70 space-y-4">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Plus className="w-4 h-4 text-indigo-600" /> Add New Goal Target
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">Goal Title</label>
                      <input
                        type="text"
                        required
                        value={newGoalTitle}
                        onChange={(e) => setNewGoalTitle(e.target.value)}
                        placeholder="e.g. Buy Family Home"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium bg-white outline-none focus:border-indigo-600"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">Goal Type</label>
                      <select
                        value={newGoalType}
                        onChange={(e) => setNewGoalType(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium bg-white outline-none focus:border-indigo-600"
                      >
                        <option value="Retirement">Retirement</option>
                        <option value="Real Estate">Real Estate</option>
                        <option value="Education">Education</option>
                        <option value="Wealth Accumulation">Wealth Accumulation</option>
                        <option value="Emergency Fund">Emergency Fund</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">Target Amount (₹)</label>
                      <input
                        type="number"
                        required
                        min="1000"
                        value={newGoalTarget}
                        onChange={(e) => setNewGoalTarget(e.target.value)}
                        placeholder="e.g. 5000000"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium bg-white outline-none focus:border-indigo-600"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-600 mb-1">Horizon (Months)</label>
                      <input
                        type="number"
                        required
                        min="1"
                        value={newGoalHorizonMonths}
                        onChange={(e) => setNewGoalHorizonMonths(e.target.value)}
                        placeholder="e.g. 60"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-medium bg-white outline-none focus:border-indigo-600"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isAddingGoal}
                    className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-70"
                  >
                    {isAddingGoal ? "Adding Goal..." : "Add Goal Target"}
                  </button>
                </form>
              </div>
            </div>

            {/* COLUMN 2: RISK ASSESSMENT QUESTIONNAIRE (5 COLS) */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-slate-900 font-display">
                        Risk Calibration
                      </h2>
                      <p className="text-xs text-slate-500">
                        SEBI-standard risk tolerance questionnaire
                      </p>
                    </div>
                  </div>
                  {riskAssessment && (
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-100 text-purple-800 uppercase tracking-wide">
                      {riskAssessment.risk_category}
                    </span>
                  )}
                </div>

                {/* Active Risk Score Display */}
                {riskAssessment && (
                  <div className="p-5 rounded-2xl bg-purple-50/60 border border-purple-100 mb-6 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-purple-800 font-medium">Assessed Risk Score</span>
                      <h3 className="text-2xl font-black text-purple-900 font-display">
                        {riskAssessment.risk_score} / 20
                      </h3>
                      <p className="text-[11px] text-purple-700 mt-0.5">
                        Tier: <strong className="capitalize">{riskAssessment.risk_category}</strong>
                      </p>
                    </div>
                    <div className="w-12 h-12 rounded-full border-4 border-purple-300 border-t-purple-700 flex items-center justify-center font-bold text-sm text-purple-900">
                      {riskAssessment.risk_score}
                    </div>
                  </div>
                )}

                <div className="space-y-6">
                  {/* Q1 */}
                  <div>
                    <label className="block text-xs font-bold text-slate-800 mb-2">
                      1. Investment Experience
                    </label>
                    <select
                      value={riskAnswers.investment_experience}
                      onChange={(e) =>
                        setRiskAnswers({ ...riskAnswers, investment_experience: parseInt(e.target.value) })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50/50 outline-none focus:border-indigo-600 font-medium"
                    >
                      <option value={0}>Novice (FDs &amp; Savings only) [0 pts]</option>
                      <option value={1}>Beginner (Mutual Funds for &lt; 2 yrs) [1 pt]</option>
                      <option value={2}>Intermediate (Stocks &amp; Mutual Funds 2-5 yrs) [2 pts]</option>
                      <option value={3}>Advanced (Active portfolio management &gt; 5 yrs) [3 pts]</option>
                      <option value={4}>Expert (Derivatives, Private Equity, Real Estate) [4 pts]</option>
                    </select>
                  </div>

                  {/* Q2 */}
                  <div>
                    <label className="block text-xs font-bold text-slate-800 mb-2">
                      2. Primary Horizon
                    </label>
                    <select
                      value={riskAnswers.time_horizon}
                      onChange={(e) =>
                        setRiskAnswers({ ...riskAnswers, time_horizon: parseInt(e.target.value) })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50/50 outline-none focus:border-indigo-600 font-medium"
                    >
                      <option value={0}>Less than 1 year (High liquidity needed) [0 pts]</option>
                      <option value={1}>1 to 3 years [1 pt]</option>
                      <option value={2}>3 to 5 years [2 pts]</option>
                      <option value={3}>5 to 10 years [3 pts]</option>
                      <option value={4}>More than 10 years (Long compounding) [4 pts]</option>
                    </select>
                  </div>

                  {/* Q3 */}
                  <div>
                    <label className="block text-xs font-bold text-slate-800 mb-2">
                      3. Reaction to 20% Portfolio Drop
                    </label>
                    <select
                      value={riskAnswers.loss_reaction}
                      onChange={(e) =>
                        setRiskAnswers({ ...riskAnswers, loss_reaction: parseInt(e.target.value) })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50/50 outline-none focus:border-indigo-600 font-medium"
                    >
                      <option value={0}>Panic and liquidate everything immediately [0 pts]</option>
                      <option value={1}>Move part to fixed deposits to stop bleeding [1 pt]</option>
                      <option value={2}>Do nothing and wait for recovery [2 pts]</option>
                      <option value={3}>Invest moderately more at discounted valuations [3 pts]</option>
                      <option value={4}>Aggressively buy more with all spare liquidity [4 pts]</option>
                    </select>
                  </div>

                  {/* Q4 */}
                  <div>
                    <label className="block text-xs font-bold text-slate-800 mb-2">
                      4. Growth Preference
                    </label>
                    <select
                      value={riskAnswers.growth_preference}
                      onChange={(e) =>
                        setRiskAnswers({ ...riskAnswers, growth_preference: parseInt(e.target.value) })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50/50 outline-none focus:border-indigo-600 font-medium"
                    >
                      <option value={0}>Preserve capital strictly (Accept ~5-6% returns) [0 pts]</option>
                      <option value={1}>Modest capital growth with minimal drawdowns [1 pt]</option>
                      <option value={2}>Balanced return matching inflation + 4% [2 pts]</option>
                      <option value={3}>High growth (Accept moderate volatility) [3 pts]</option>
                      <option value={4}>Maximum long-term wealth compounding [4 pts]</option>
                    </select>
                  </div>

                  {/* Q5 */}
                  <div>
                    <label className="block text-xs font-bold text-slate-800 mb-2">
                      5. Income Stability
                    </label>
                    <select
                      value={riskAnswers.financial_stability}
                      onChange={(e) =>
                        setRiskAnswers({ ...riskAnswers, financial_stability: parseInt(e.target.value) })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50/50 outline-none focus:border-indigo-600 font-medium"
                    >
                      <option value={0}>Unpredictable or commission-dependent [0 pts]</option>
                      <option value={1}>Freelance / Project-based contracts [1 pt]</option>
                      <option value={2}>Private sector salary with moderate stability [2 pts]</option>
                      <option value={3}>Established professional or stable corporate [3 pts]</option>
                      <option value={4}>Government / Tenured / Multiple passive streams [4 pts]</option>
                    </select>
                  </div>

                  <button
                    type="button"
                    onClick={handleSubmitRisk}
                    disabled={isSubmittingRisk}
                    className="w-full py-3.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-semibold text-xs shadow-md shadow-purple-100 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
                  >
                    {isSubmittingRisk ? "Evaluating Score..." : "Calibrate & Save Risk Tier"}
                  </button>
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
