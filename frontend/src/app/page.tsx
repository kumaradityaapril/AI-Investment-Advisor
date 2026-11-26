"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import HeroWealthShowcase3D from "@/components/HeroWealthShowcase3D";
import AuthModal from "@/components/AuthModal";
import TiltCard from "@/components/TiltCard";
import { useAuth } from "@/context/AuthContext";
import { SpotlightCard, Particles, CountUp, DecryptedText } from "@/components/reactbits";

export default function HomePage() {
  const { user } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("register");
  const [activeTab, setActiveTab] = useState<"overview" | "rag" | "simulator" | "guardrails">("overview");

  return (
    <div className="flex flex-col min-h-screen bg-[#090a0f] text-[#f8fafc] relative overflow-hidden">
      {/* Global Background Ambient Glows */}
      <div className="absolute top-20 left-1/4 w-[700px] h-[700px] bg-emerald-500/8 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute top-1/2 right-10 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-40 left-10 w-[600px] h-[600px] bg-emerald-500/6 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute inset-0 dark-grid opacity-30 pointer-events-none" />

      <Navbar />

      <main className="flex-1 pt-20 relative z-10">
        {/* HERO SECTION WITH 3D CANVAS */}
        <section className="relative overflow-hidden pt-10 sm:pt-14 pb-16 sm:pb-24 px-4 sm:px-8 lg:px-12 2xl:px-16 max-w-[1600px] mx-auto w-full">
          {/* React Bits Interactive 3D Particle Constellation */}
          <Particles
            particleCount={42}
            speed={0.4}
            particleColor="rgba(16, 185, 129, 0.35)"
            lineColor="rgba(16, 185, 129, 0.12)"
          />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 xl:gap-14 items-center relative z-10">
            {/* Left Content */}
            <div className="lg:col-span-7 xl:col-span-7 flex flex-col gap-6 z-10">
              <div className="inline-flex items-center gap-2.5 self-start px-3.5 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 font-semibold text-xs tracking-wide shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <DecryptedText
                  text="ENTERPRISE WEALTH INTELLIGENCE • SEC & SEBI GROUNDED"
                  speed={35}
                  maxIterations={12}
                  className="font-semibold text-xs tracking-wide"
                  encryptedClassName="text-emerald-400 font-mono text-xs"
                />
              </div>

              <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl xl:text-7xl text-white tracking-tight leading-[1.08]">
                Private Wealth Clarity. <br />
                <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200 bg-clip-text text-transparent">
                  Zero Hallucinations.
                </span>
              </h1>

              <p className="text-base sm:text-lg lg:text-xl text-zinc-400 max-w-3xl leading-relaxed">
                The first autonomous investment advisor backed by deterministic
                Python Decimal math, pgvector hybrid search, and multi-layer regulatory
                guardrails. Every financial recommendation is citation-grounded
                and mathematically verified.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-4 pt-2">
                {user ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-400 hover:from-emerald-400 hover:to-emerald-300 text-zinc-950 font-bold text-sm shadow-[0_0_25px_rgba(16,185,129,0.35)] hover:shadow-[0_0_40px_rgba(16,185,129,0.55)] hover:-translate-y-1 hover:scale-105 transition-all flex items-center gap-2.5"
                    >
                      <span className="material-symbols-outlined text-[20px]">
                        dashboard
                      </span>
                      <span>Go to My Dashboard</span>
                    </Link>

                    <Link
                      href="/scenarios"
                      className="px-7 py-4 rounded-2xl bg-zinc-900/90 hover:bg-zinc-800 text-white font-semibold text-sm border border-white/10 hover:border-emerald-500/40 shadow-lg hover:-translate-y-1 hover:scale-105 transition-all flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-[20px] text-emerald-400">
                        tune
                      </span>
                      <span>Simulate Scenarios</span>
                    </Link>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setAuthMode("register");
                        setIsAuthOpen(true);
                      }}
                      className="px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-400 hover:from-emerald-400 hover:to-emerald-300 text-zinc-950 font-bold text-sm shadow-[0_0_25px_rgba(16,185,129,0.35)] hover:shadow-[0_0_40px_rgba(16,185,129,0.55)] hover:-translate-y-1 hover:scale-105 transition-all flex items-center gap-2.5 cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[20px]">
                        rocket_launch
                      </span>
                      <span>Get Started Free</span>
                    </button>

                    <Link
                      href="/login"
                      className="px-7 py-4 rounded-2xl bg-zinc-900/90 hover:bg-zinc-800 text-white font-semibold text-sm border border-white/10 hover:border-emerald-500/40 shadow-lg hover:-translate-y-1 hover:scale-105 transition-all flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-[20px] text-emerald-400">
                        lock
                      </span>
                      <span>Sign In to Advisor</span>
                    </Link>
                  </>
                )}
              </div>

              {/* Key Platform Accreditations - 3D Pop-up Tilt Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
                <TiltCard maxTilt={10}>
                  <SpotlightCard
                    className="h-full border border-white/10 bg-zinc-900/60 backdrop-blur-xl hover:border-emerald-500/50 shadow-lg"
                    spotlightColor="rgba(16, 185, 129, 0.15)"
                    borderColor="rgba(16, 185, 129, 0.45)"
                  >
                    <div className="p-5 rounded-2xl h-full flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-1.5 text-emerald-400 mb-1.5">
                          <span className="material-symbols-outlined text-[18px]">verified</span>
                          <span className="text-[10px] font-bold uppercase tracking-wider">Grounding</span>
                        </div>
                        <div className="font-display font-extrabold text-3xl text-white">
                          <CountUp to={100} suffix="%" duration={1.8} />
                        </div>
                        <div className="text-xs text-zinc-300 font-semibold mt-1">
                          Claim Ledger Grounding
                        </div>
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-2 leading-snug">
                        Every currency &amp; % cross-referenced against facts
                      </div>
                    </div>
                  </SpotlightCard>
                </TiltCard>

                <TiltCard maxTilt={10}>
                  <SpotlightCard
                    className="h-full border border-white/10 bg-zinc-900/60 backdrop-blur-xl hover:border-emerald-500/50 shadow-lg"
                    spotlightColor="rgba(16, 185, 129, 0.15)"
                    borderColor="rgba(16, 185, 129, 0.45)"
                  >
                    <div className="p-5 rounded-2xl h-full flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-1.5 text-teal-400 mb-1.5">
                          <span className="material-symbols-outlined text-[18px]">hub</span>
                          <span className="text-[10px] font-bold uppercase tracking-wider">Hybrid RAG</span>
                        </div>
                        <div className="font-display font-extrabold text-3xl text-emerald-400">
                          <CountUp to={768} suffix="-dim" duration={2.2} />
                        </div>
                        <div className="text-xs text-zinc-300 font-semibold mt-1">
                          HNSW Vector Embeddings
                        </div>
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-2 leading-snug">
                        SEC 10-K &amp; statement ingestion in pgvector
                      </div>
                    </div>
                  </SpotlightCard>
                </TiltCard>

                <TiltCard maxTilt={10}>
                  <SpotlightCard
                    className="h-full border border-white/10 bg-zinc-900/60 backdrop-blur-xl hover:border-emerald-500/50 shadow-lg"
                    spotlightColor="rgba(16, 185, 129, 0.15)"
                    borderColor="rgba(16, 185, 129, 0.45)"
                  >
                    <div className="p-5 rounded-2xl h-full flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-1.5 text-emerald-400 mb-1.5">
                          <span className="material-symbols-outlined text-[18px]">calculate</span>
                          <span className="text-[10px] font-bold uppercase tracking-wider">Exact Math</span>
                        </div>
                        <div className="font-display font-extrabold text-3xl text-white">
                          Python Decimal
                        </div>
                        <div className="text-xs text-zinc-300 font-semibold mt-1">
                          Exact Financial Math
                        </div>
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-2 leading-snug">
                        Zero floating point drift or LLM hallucination
                      </div>
                    </div>
                  </SpotlightCard>
                </TiltCard>
              </div>

              {/* Live Institutional Signal Ribbon */}
              <div className="p-4 rounded-2xl bg-zinc-900/80 border border-emerald-500/25 flex items-center justify-between text-xs text-zinc-300 shadow-[0_0_20px_rgba(0,0,0,0.6)]">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="font-bold text-white">Deterministic Guardrails:</span>
                  <span className="hidden sm:inline text-zinc-400">SEBI Risk Score • Compound Interest Engine • Tenant Isolation</span>
                </div>
                <span className="font-mono text-[11px] text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
                  SHA-256 Verified
                </span>
              </div>
            </div>

            {/* Right Column: INTERACTIVE 3D WEALTH SHOWCASE COMPONENT */}
            <div className="lg:col-span-5 xl:col-span-5 flex items-center justify-center relative w-full">
              <TiltCard maxTilt={6}>
                <HeroWealthShowcase3D />
              </TiltCard>
            </div>
          </div>
        </section>

        {/* INTERACTIVE CAPABILITY TABS */}
        <section className="py-20 px-4 sm:px-8 lg:px-12 2xl:px-16 bg-[#0c0d13] border-y border-white/10 relative overflow-hidden">
          {/* Ambient Refraction Glow Orb behind Bento section */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-emerald-500/15 rounded-full blur-[140px] pointer-events-none" />

          <div className="max-w-[1600px] mx-auto flex flex-col gap-12 relative z-10">
            <div className="flex flex-col items-center text-center max-w-2xl mx-auto">
              <span className="px-3.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-semibold mb-3 shadow-[0_0_12px_rgba(16,185,129,0.2)]">
                COMPLETE PLATFORM ARCHITECTURE
              </span>
              <h2 className="font-display font-extrabold text-3xl sm:text-4xl text-white tracking-tight">
                Built for Precision, Backed by Code
              </h2>
              <p className="text-sm text-zinc-400 mt-2.5">
                Toggle through the four core pillars that power our verified AI
                Investment Advisor engine.
              </p>
            </div>

            {/* Navigation Tabs */}
            <div className="flex justify-center">
              <div className="inline-flex p-1.5 rounded-2xl bg-black/40 backdrop-blur-md border border-white/10 shadow-xl">
                {[
                  { id: "overview", label: "Wealth Overview", icon: "wallet" },
                  { id: "rag", label: "Document RAG", icon: "menu_book" },
                  { id: "simulator", label: "Scenario Simulator", icon: "tune" },
                  { id: "guardrails", label: "Safety Audits", icon: "verified" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                      activeTab === tab.id
                        ? "bg-emerald-500 text-zinc-950 font-bold shadow-[0_0_15px_rgba(16,185,129,0.4)] scale-[1.02]"
                        : "text-zinc-400 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[17px]">
                      {tab.icon}
                    </span>
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Interactive Preview Bento Card (Authentic Glassmorphism Object) */}
            <div className="rounded-[32px] glass-panel p-6 lg:p-12">
              {activeTab === "overview" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-3 py-1 rounded-md bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 font-semibold text-xs">
                      Deterministic Metric Engine
                    </span>
                    <h3 className="font-display font-extrabold text-2xl text-white">
                      Live Portfolio Health &amp; Surplus Gauges
                    </h3>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                      Income minus fixed expenses computes your exact monthly
                      surplus and savings rate with Python Decimal precision. No
                      LLM guesswork.
                    </p>
                    <Link
                      href="/dashboard"
                      className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 hover:text-emerald-300 group"
                    >
                      <span>Open Live Dashboard</span>
                      <span className="group-hover:translate-x-1 transition-transform">→</span>
                    </Link>
                  </div>
                  <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div className="bg-zinc-950/80 p-6 rounded-2xl border border-zinc-800 shadow-lg hover:border-emerald-500/40 transition-all">
                      <div className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">
                        Monthly Cash Surplus
                      </div>
                      <div className="text-3xl font-extrabold font-mono text-white mt-1.5">
                        ₹40,000.00
                      </div>
                      <div className="text-xs text-emerald-400 font-semibold mt-3 flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[16px]">
                          trending_up
                        </span>
                        40.0% Savings Rate
                      </div>
                    </div>
                    <div className="bg-zinc-950/80 p-6 rounded-2xl border border-zinc-800 shadow-lg hover:border-emerald-500/40 transition-all">
                      <div className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">
                        Emergency Fund Runway
                      </div>
                      <div className="text-3xl font-extrabold font-mono text-white mt-1.5">
                        5.0 Months
                      </div>
                      <div className="text-xs text-zinc-400 mt-3">
                        Target: 6.0 Months Buffer
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "rag" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-3 py-1 rounded-md bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 font-semibold text-xs">
                      Hybrid Vector + BM25 RAG
                    </span>
                    <h3 className="font-display font-extrabold text-2xl text-white">
                      Deep Financial PDF Statement Ingestion
                    </h3>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                      Drop annual reports (10-Ks) or mutual fund statements.
                      Chunks are embedded into 768-dim vectors in pgvector and
                      contextually reranked with Reciprocal Rank Fusion.
                    </p>
                    <Link
                      href="/documents"
                      className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 hover:text-emerald-300 group"
                    >
                      <span>Open Document Library</span>
                      <span className="group-hover:translate-x-1 transition-transform">→</span>
                    </Link>
                  </div>
                  <div className="md:col-span-2 bg-zinc-950/80 p-6 rounded-2xl border border-zinc-800 shadow-lg space-y-4">
                    <div className="flex items-center justify-between border-b border-zinc-800 pb-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                          <span className="material-symbols-outlined text-[20px]">
                            description
                          </span>
                        </div>
                        <div>
                          <div className="text-sm font-bold text-white">
                            Q3_Portfolio_Holdings.pdf
                          </div>
                          <div className="text-xs text-zinc-400">
                            Indexed into 18 chunks • 768d HNSW Vector
                          </div>
                        </div>
                      </div>
                      <span className="px-3 py-1 rounded-md bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 font-semibold text-xs">
                        Verified Clean
                      </span>
                    </div>
                    <div className="p-3.5 bg-zinc-900 rounded-xl text-xs text-zinc-300 border border-zinc-800/80">
                      <span className="font-bold text-emerald-400">
                        [Evidence Chunk #42]:
                      </span>{" "}
                      &quot;Domestic Equity allocation stands at 65.4% across
                      broad-market index funds and large-cap leaders.&quot;
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "simulator" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-3 py-1 rounded-md bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 font-semibold text-xs">
                      What-If Compounding Engine
                    </span>
                    <h3 className="font-display font-extrabold text-2xl text-white">
                      Financial Scenario Simulator
                    </h3>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                      Experiment with hypothetical life adjustments: step up SIP
                      by ₹5,000, deploy a lump sum bonus, or cut living costs.
                      See 10-year compounding trajectories.
                    </p>
                    <Link
                      href="/scenarios"
                      className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 hover:text-emerald-300 group"
                    >
                      <span>Launch Simulator</span>
                      <span className="group-hover:translate-x-1 transition-transform">→</span>
                    </Link>
                  </div>
                  <div className="md:col-span-2 bg-zinc-950/80 p-6 rounded-2xl border border-zinc-800 shadow-lg space-y-5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">
                        Scenario: Step Up Monthly SIP +₹5,000
                      </span>
                      <span className="px-3 py-1 rounded-md bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-bold">
                        +₹18.4 Lakhs Compounded Gain
                      </span>
                    </div>
                    <div className="h-3 rounded-full bg-zinc-800 overflow-hidden flex border border-white/5">
                      <div className="h-full bg-zinc-600 w-[45%]"></div>
                      <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 w-[35%] shadow-[0_0_12px_rgba(16,185,129,0.5)]"></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span>Baseline Corpus: ₹42.5L</span>
                      <span className="font-bold text-emerald-400">
                        Simulated Corpus: ₹60.9L
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "guardrails" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                  <div className="md:col-span-1 space-y-4">
                    <span className="px-3 py-1 rounded-md bg-rose-950/60 border border-rose-500/30 text-rose-300 font-semibold text-xs">
                      Multi-Layer Safety Engine
                    </span>
                    <h3 className="font-display font-extrabold text-2xl text-white">
                      Numerical Claim Ledger &amp; Legal Compliance
                    </h3>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                      Every currency and percentage value in AI advice is
                      cross-checked against verified financial context. No
                      guarantees or speculation allowed.
                    </p>
                    <Link
                      href="/why-this-plan"
                      className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 hover:text-emerald-300 group"
                    >
                      <span>View Safety Audit Trail</span>
                      <span className="group-hover:translate-x-1 transition-transform">→</span>
                    </Link>
                  </div>
                  <div className="md:col-span-2 bg-zinc-950/80 p-6 rounded-2xl border border-zinc-800 shadow-lg space-y-3.5">
                    <div className="flex items-center gap-2 text-xs font-bold text-emerald-400">
                      <span className="material-symbols-outlined text-[18px]">
                        check_circle
                      </span>
                      <span>100% Numerical Claims Coverage Enforced</span>
                    </div>
                    <div className="p-3.5 bg-zinc-900 rounded-xl text-xs font-mono text-zinc-300 border border-zinc-800/80">
                      Claimed: monthly_surplus = ₹40,000.00 &lt;-- Verified
                      against context.metrics.monthly_surplus (Match: TRUE)
                    </div>
                    <div className="text-[11px] text-zinc-500 italic">
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
        <section className="py-24 px-4 sm:px-8 lg:px-12 2xl:px-16 max-w-[1600px] mx-auto w-full">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="px-3.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
              FULL SUITE EXPERIENCE
            </span>
            <h2 className="font-display font-extrabold text-3xl sm:text-4xl text-white mt-3 tracking-tight">
              Explore Every Feature In Depth
            </h2>
            <p className="text-sm text-zinc-400 mt-2.5">
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
              <TiltCard key={i} maxTilt={7}>
                <SpotlightCard
                  className="h-full border border-white/10 bg-zinc-900/50 backdrop-blur-xl hover:border-emerald-500/50 transition-all rounded-3xl"
                  spotlightColor="rgba(16, 185, 129, 0.15)"
                  borderColor="rgba(16, 185, 129, 0.45)"
                >
                  <Link
                    href={feature.path}
                    className="group p-7 rounded-3xl flex flex-col justify-between h-full"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-5">
                        <div className="w-11 h-11 rounded-2xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 group-hover:bg-emerald-500 group-hover:text-zinc-950 transition-all flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                          <span className="material-symbols-outlined text-[24px]">
                            {feature.icon}
                          </span>
                        </div>
                        <span className="px-3 py-1 rounded-full bg-zinc-800/80 border border-zinc-700/60 text-zinc-300 font-medium text-[11px]">
                          {feature.tag}
                        </span>
                      </div>
                      <h3 className="font-display font-bold text-lg text-white group-hover:text-emerald-400 transition-colors">
                        {feature.title}
                      </h3>
                      <p className="text-xs text-zinc-400 mt-2.5 leading-relaxed">
                        {feature.desc}
                      </p>
                    </div>
                    <div className="mt-6 pt-3.5 border-t border-white/10 flex items-center text-xs font-bold text-emerald-400 group-hover:translate-x-1 transition-transform">
                      <span>Launch View →</span>
                    </div>
                  </Link>
                </SpotlightCard>
              </TiltCard>
            ))}
          </div>
        </section>

        {/* CALL TO ACTION */}
        <section className="py-24 px-6 lg:px-12 bg-gradient-to-b from-zinc-950 via-[#0a1410] to-[#090a0f] text-white text-center border-t border-white/10 relative overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none" />

          <div className="max-w-3xl mx-auto space-y-6 relative z-10">
            <span className="px-3.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-500/30 text-emerald-400 text-xs font-semibold shadow-[0_0_15px_rgba(16,185,129,0.25)]">
              READY FOR PRODUCTION
            </span>
            <h2 className="font-display font-extrabold text-3xl sm:text-5xl text-white tracking-tight">
              Start Your Grounded Financial Journey
            </h2>
            <p className="text-zinc-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Join forward-thinking investors who trust deterministic mathematics
              over speculative promises.
            </p>
            <div className="pt-3">
              <button
                onClick={() => {
                  setAuthMode("register");
                  setIsAuthOpen(true);
                }}
                className="px-9 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-400 hover:from-emerald-400 hover:to-emerald-300 text-zinc-950 font-bold text-sm shadow-[0_0_30px_rgba(16,185,129,0.4)] hover:shadow-[0_0_45px_rgba(16,185,129,0.6)] hover:scale-105 transition-all cursor-pointer"
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
