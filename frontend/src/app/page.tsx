"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ThreeDHeroSphere from "@/components/ThreeDHeroSphere";
import AuthModal from "@/components/AuthModal";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const { user } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("register");
  const [activeTab, setActiveTab] = useState<"overview" | "rag" | "simulator" | "guardrails">("overview");

  return (
    <div className="flex flex-col min-h-screen bg-[#f8f9ff]">
      <Navbar />

      <main className="flex-1 pt-24">
        {/* HERO SECTION WITH 3D CANVAS */}
        <section className="relative overflow-hidden pt-12 pb-20 px-6 lg:px-12 max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Content */}
            <div className="lg:col-span-7 flex flex-col gap-6 z-10">
              <div className="inline-flex items-center gap-2 self-start px-3.5 py-1.5 rounded-full bg-[#e1e0ff] text-[#07006c] font-semibold text-xs tracking-wide">
                <span className="w-2 h-2 rounded-full bg-[#2a14b4] animate-ping"></span>
                <span>ENTERPRISE WEALTH INTELLIGENCE</span>
              </div>

              <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl text-[#0b1c30] tracking-tight leading-[1.12]">
                Private Wealth Clarity. <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#2a14b4] via-[#4648d4] to-[#10b981]">
                  Zero Hallucinations.
                </span>
              </h1>

              <p className="text-base sm:text-lg text-[#464554] max-w-2xl leading-relaxed">
                The first autonomous investment advisor backed by deterministic
                Python math, pgvector hybrid search, and multi-layer regulatory
                guardrails. Every financial recommendation is citation-grounded
                and mathematically verified.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-4 pt-2">
                {user ? (
                  <Link
                    href="/dashboard"
                    className="px-7 py-3.5 rounded-xl bg-[#2a14b4] hover:bg-[#4338ca] text-white font-semibold text-sm shadow-[0_4px_16px_rgba(42,20,180,0.25)] hover:shadow-[0_6px_20px_rgba(42,20,180,0.35)] hover:-translate-y-0.5 transition-all flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      dashboard
                    </span>
                    <span>Go to My Dashboard</span>
                  </Link>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setAuthMode("register");
                        setIsAuthOpen(true);
                      }}
                      className="px-7 py-3.5 rounded-xl bg-[#2a14b4] hover:bg-[#4338ca] text-white font-semibold text-sm shadow-[0_4px_16px_rgba(42,20,180,0.25)] hover:shadow-[0_6px_20px_rgba(42,20,180,0.35)] hover:-translate-y-0.5 transition-all flex items-center gap-2 cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[18px]">
                        rocket_launch
                      </span>
                      <span>Get Started Free</span>
                    </button>

                    <Link
                      href="/login"
                      className="px-6 py-3.5 rounded-xl bg-white hover:bg-[#eff4ff] text-[#0b1c30] font-semibold text-sm border border-[#e2e8f0] shadow-sm hover:-translate-y-0.5 transition-all flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-[18px] text-[#2a14b4]">
                        lock
                      </span>
                      <span>Sign In to Advisor</span>
                    </Link>
                  </>
                )}
              </div>

              {/* Key Platform Accreditations */}
              <div className="grid grid-cols-3 gap-4 pt-6 border-t border-[#e2e8f0]">
                <div>
                  <div className="font-display font-bold text-2xl text-[#0b1c30]">
                    100%
                  </div>
                  <div className="text-xs text-[#777586] font-medium">
                    Claim Ledger Grounding
                  </div>
                </div>
                <div>
                  <div className="font-display font-bold text-2xl text-[#2a14b4]">
                    768-dim
                  </div>
                  <div className="text-xs text-[#777586] font-medium">
                    HNSW Vector Embeddings
                  </div>
                </div>
                <div>
                  <div className="font-display font-bold text-2xl text-[#10b981]">
                    Python Decimal
                  </div>
                  <div className="text-xs text-[#777586] font-medium">
                    Exact Financial Math
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: 3D INTERACTIVE HERO SPHERE */}
            <div className="lg:col-span-5 flex items-center justify-center relative">
              <ThreeDHeroSphere />
            </div>
          </div>
        </section>

        {/* INTERACTIVE CAPABILITY TABS */}
        <section className="py-16 px-6 lg:px-12 bg-white border-y border-[#e2e8f0]">
          <div className="max-w-7xl mx-auto flex flex-col gap-10">
            <div className="flex flex-col items-center text-center max-w-2xl mx-auto">
              <span className="px-3 py-1 rounded-full bg-[#eff4ff] text-[#2a14b4] text-xs font-semibold mb-2">
                COMPLETE PRD PLATFORM CAPABILITIES
              </span>
              <h2 className="font-display font-bold text-3xl text-[#0b1c30]">
                Built for Precision, Backed by Code
              </h2>
              <p className="text-sm text-[#464554] mt-2">
                Toggle through the four core pillars that power our verified AI
                Investment Advisor engine.
              </p>
            </div>

            {/* Navigation Tabs */}
            <div className="flex justify-center">
              <div className="inline-flex p-1.5 rounded-2xl bg-[#eff4ff] border border-[#e2e8f0]">
                {[
                  { id: "overview", label: "Wealth Overview", icon: "wallet" },
                  { id: "rag", label: "Document RAG", icon: "menu_book" },
                  { id: "simulator", label: "Scenario Simulator", icon: "tune" },
                  { id: "guardrails", label: "Safety Audits", icon: "verified" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                      activeTab === tab.id
                        ? "bg-[#2a14b4] text-white shadow-md shadow-indigo-500/20"
                        : "text-[#464554] hover:text-[#0b1c30]"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {tab.icon}
                    </span>
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Interactive Preview Bento Card */}
            <div className="rounded-2xl border border-[#e2e8f0] bg-[#f8f9ff] p-6 lg:p-10 shadow-sm">
              {activeTab === "overview" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-2.5 py-1 rounded-full bg-[#85f8c4]/40 text-[#00442d] font-semibold text-xs">
                      Deterministic Metric Engine
                    </span>
                    <h3 className="font-display font-bold text-2xl text-[#0b1c30]">
                      Live Portfolio Health &amp; Surplus Gauges
                    </h3>
                    <p className="text-sm text-[#464554] leading-relaxed">
                      Income minus fixed expenses computes your exact monthly
                      surplus and savings rate with Python Decimal precision. No
                      LLM guesswork.
                    </p>
                    <Link
                      href="/dashboard"
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2a14b4] hover:underline"
                    >
                      Open Live Dashboard →
                    </Link>
                  </div>
                  <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-white p-5 rounded-xl border border-[#e2e8f0] shadow-sm">
                      <div className="text-xs text-[#777586] font-semibold uppercase">
                        Monthly Cash Surplus
                      </div>
                      <div className="text-3xl font-bold font-mono text-[#0b1c30] mt-1">
                        ₹40,000.00
                      </div>
                      <div className="text-xs text-[#10b981] font-semibold mt-2 flex items-center gap-1">
                        <span className="material-symbols-outlined text-[15px]">
                          trending_up
                        </span>
                        40.0% Savings Rate
                      </div>
                    </div>
                    <div className="bg-white p-5 rounded-xl border border-[#e2e8f0] shadow-sm">
                      <div className="text-xs text-[#777586] font-semibold uppercase">
                        Emergency Fund Runway
                      </div>
                      <div className="text-3xl font-bold font-mono text-[#0b1c30] mt-1">
                        5.0 Months
                      </div>
                      <div className="text-xs text-[#464554] mt-2">
                        Target: 6.0 Months Buffer
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "rag" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-2.5 py-1 rounded-full bg-[#e1e0ff] text-[#07006c] font-semibold text-xs">
                      Hybrid Vector + BM25 RAG
                    </span>
                    <h3 className="font-display font-bold text-2xl text-[#0b1c30]">
                      Deep Financial PDF Statement Ingestion
                    </h3>
                    <p className="text-sm text-[#464554] leading-relaxed">
                      Drop annual reports (10-Ks) or mutual fund statements.
                      Chunks are embedded into 768-dim vectors in pgvector and
                      contextually reranked by Gemini.
                    </p>
                    <Link
                      href="/documents"
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2a14b4] hover:underline"
                    >
                      Open Document Library →
                    </Link>
                  </div>
                  <div className="md:col-span-2 bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-3">
                    <div className="flex items-center justify-between border-b border-[#e2e8f0] pb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-[#eff4ff] flex items-center justify-center text-[#2a14b4]">
                          <span className="material-symbols-outlined text-[20px]">
                            description
                          </span>
                        </div>
                        <div>
                          <div className="text-sm font-bold text-[#0b1c30]">
                            Q3_Portfolio_Holdings.pdf
                          </div>
                          <div className="text-xs text-[#777586]">
                            Indexed into 18 chunks • 768d HNSW Vector
                          </div>
                        </div>
                      </div>
                      <span className="px-2.5 py-1 rounded-full bg-[#85f8c4]/40 text-[#00442d] font-semibold text-xs">
                        Verified Clean
                      </span>
                    </div>
                    <div className="p-3 bg-[#eff4ff] rounded-lg text-xs text-[#0b1c30]">
                      <span className="font-bold text-[#2a14b4]">
                        [Evidence Chunk #42]:
                      </span>{" "}
                      &quot;Domestic Equity allocation stands at 65.4% across
                      broad-market index funds and large-cap leaders.&quot;
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "simulator" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-2.5 py-1 rounded-full bg-[#85f8c4]/40 text-[#00442d] font-semibold text-xs">
                      What-If Compounding Engine
                    </span>
                    <h3 className="font-display font-bold text-2xl text-[#0b1c30]">
                      Financial Scenario Simulator
                    </h3>
                    <p className="text-sm text-[#464554] leading-relaxed">
                      Experiment with hypothetical life adjustments: step up SIP
                      by ₹5,000, deploy a lump sum bonus, or cut living costs.
                      See 10-year compounding trajectories.
                    </p>
                    <Link
                      href="/scenarios"
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2a14b4] hover:underline"
                    >
                      Launch Simulator →
                    </Link>
                  </div>
                  <div className="md:col-span-2 bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#0b1c30]">
                        Scenario: Step Up Monthly SIP +₹5,000
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-[#85f8c4] text-[#00442d] text-xs font-bold">
                        +₹18.4 Lakhs Compounded Gain
                      </span>
                    </div>
                    <div className="h-3 rounded-full bg-slate-100 overflow-hidden flex">
                      <div className="h-full bg-[#2a14b4] w-[45%]"></div>
                      <div className="h-full bg-[#10b981] w-[35%]"></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-[#464554]">
                      <span>Baseline Corpus: ₹42.5L</span>
                      <span className="font-bold text-[#00442d]">
                        Simulated Corpus: ₹60.9L
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "guardrails" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-2.5 py-1 rounded-full bg-[#ffdad6] text-[#ba1a1a] font-semibold text-xs">
                      Multi-Layer Safety Engine
                    </span>
                    <h3 className="font-display font-bold text-2xl text-[#0b1c30]">
                      Numerical Claim Ledger &amp; Legal Compliance
                    </h3>
                    <p className="text-sm text-[#464554] leading-relaxed">
                      Every currency and percentage value in AI advice is
                      cross-checked against verified financial context. No
                      guarantees or speculation allowed.
                    </p>
                    <Link
                      href="/why-this-plan"
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2a14b4] hover:underline"
                    >
                      View Safety Audit Trail →
                    </Link>
                  </div>
                  <div className="md:col-span-2 bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-[#00442d]">
                      <span className="material-symbols-outlined text-[16px] text-[#10b981]">
                        check_circle
                      </span>
                      <span>100% Numerical Claims Coverage Enforced</span>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg text-xs font-mono text-slate-700">
                      Claimed: monthly_surplus = ₹40,000.00 &lt;-- Verified
                      against context.metrics.monthly_surplus (Match: TRUE)
                    </div>
                    <div className="text-[11px] text-[#777586] italic">
                      Educational risk-tolerance indicator only. Not guaranteed
                      financial advice.
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* 9 MODULAR APP SCREENS CATALOG */}
        <section className="py-20 px-6 lg:px-12 max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="px-3 py-1 rounded-full bg-[#eff4ff] text-[#2a14b4] text-xs font-semibold">
              FULL SUITE EXPERIENCE
            </span>
            <h2 className="font-display font-bold text-3xl text-[#0b1c30] mt-2">
              Explore Every Feature In Depth
            </h2>
            <p className="text-sm text-[#464554] mt-2">
              Direct access to all 9 production modules designed to give you
              complete mastery over your financial future.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                title: "Personal Wealth Overview",
                path: "/dashboard",
                icon: "monitoring",
                desc: "Total net worth tracking, monthly surplus, and real-time 2030 goal progress bar.",
                tag: "Core Dashboard",
              },
              {
                title: "Profile & Risk Assessment",
                path: "/profile",
                icon: "tune",
                desc: "Calibrate cash baseline, income, expenses, and complete 5-question risk scoring.",
                tag: "Foundation",
              },
              {
                title: "Read Documents (Hybrid RAG)",
                path: "/documents",
                icon: "folder_managed",
                desc: "PDF statement ingestion, 768-dim embeddings, and grounded chunk-level Q&A.",
                tag: "Intelligence",
              },
              {
                title: "Compare Stocks & Funds",
                path: "/compare",
                icon: "balance",
                desc: "Side-by-side matrix comparing FD, Index Funds, PPF, and stocks with future values.",
                tag: "Comparison Engine",
              },
              {
                title: "Why This Plan? (Safety Audits)",
                path: "/why-this-plan",
                icon: "security",
                desc: "Full mathematical proof, numerical claims coverage ledger, and SEC compliance.",
                tag: "Guardrails",
              },
              {
                title: "Financial Scenario Simulator",
                path: "/scenarios",
                icon: "timeline",
                desc: "What-If sliders for step-up SIPs, bonus lump sums, and 10-year compounding trajectories.",
                tag: "Simulation",
              },
              {
                title: "LangGraph Research Agent",
                path: "/research",
                icon: "psychology",
                desc: "Autonomous multi-step agent executing bounded regulatory tools and facts.",
                tag: "Agentic AI",
              },
              {
                title: "Analysis History & Diff",
                path: "/history",
                icon: "history",
                desc: "Compare two snapshots to view automated net worth and goal delta progression.",
                tag: "Memory Diff",
              },
              {
                title: "Bank-Grade JWT Authentication",
                path: "/login",
                icon: "verified_user",
                desc: "Secure tenant-isolated authentication backed by FastAPI JWT tokens and bcrypt password hashing.",
                tag: "Security",
              },
            ].map((feature, i) => (
              <Link
                key={i}
                href={feature.path}
                className="group p-6 rounded-2xl bg-white border border-[#e2e8f0] shadow-sm hover:shadow-md hover:-translate-y-1 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-[#eff4ff] text-[#2a14b4] group-hover:bg-[#2a14b4] group-hover:text-white transition-colors flex items-center justify-center">
                      <span className="material-symbols-outlined text-[22px]">
                        {feature.icon}
                      </span>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#f1f5f9] text-[#475569] font-medium text-[11px]">
                      {feature.tag}
                    </span>
                  </div>
                  <h3 className="font-display font-bold text-lg text-[#0b1c30] group-hover:text-[#2a14b4] transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-xs text-[#464554] mt-2 leading-relaxed">
                    {feature.desc}
                  </p>
                </div>
                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center text-xs font-bold text-[#2a14b4] group-hover:underline">
                  Launch View →
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* CALL TO ACTION */}
        <section className="py-20 px-6 lg:px-12 bg-[#2a14b4] text-white text-center">
          <div className="max-w-3xl mx-auto space-y-6">
            <span className="px-3 py-1 rounded-full bg-white/20 text-white text-xs font-semibold">
              READY FOR PRODUCTION
            </span>
            <h2 className="font-display font-bold text-3xl sm:text-4xl">
              Start Your Grounded Financial Journey
            </h2>
            <p className="text-white/80 text-sm sm:text-base max-w-xl mx-auto">
              Join forward-thinking investors who trust deterministic mathematics
              over speculative promises.
            </p>
            <div className="pt-2">
              <button
                onClick={() => {
                  setAuthMode("register");
                  setIsAuthOpen(true);
                }}
                className="px-8 py-3.5 rounded-xl bg-white text-[#2a14b4] font-bold text-sm shadow-xl hover:bg-slate-100 hover:scale-105 transition-all"
              >
                Create Free Account
              </button>
            </div>
          </div>
        </section>
      </main>

      <Footer />

      <AuthModal
        isOpen={isAuthOpen}
        initialMode={authMode}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={() => {
          setIsAuthOpen(false);
          window.location.href = "/dashboard";
        }}
      />
    </div>
  );
}
