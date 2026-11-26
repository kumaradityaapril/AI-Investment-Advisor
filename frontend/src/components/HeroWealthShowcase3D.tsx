"use client";

import React, { useState } from "react";
import Link from "next/link";
import { TrendingUp, ShieldCheck, Flag, CheckCircle, Sliders } from "lucide-react";
import { CountUp, SpotlightCard } from "@/components/reactbits";

export default function HeroWealthShowcase3D() {
  const [simDeposit, setSimDeposit] = useState<number>(2500);
  const [showSimTray, setShowSimTray] = useState<boolean>(false);

  return (
    <div className="relative w-full max-w-[540px] xl:max-w-[580px] mx-auto py-2">
      {/* Ambient Glow behind glass showcase */}
      <div className="absolute -top-10 -right-10 w-72 h-72 bg-emerald-500/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute -bottom-10 -left-10 w-72 h-72 bg-emerald-500/15 rounded-full blur-[100px] pointer-events-none" />

      {/* Authentic Glassmorphism Spotlight Card */}
      <SpotlightCard
        className="relative rounded-[32px] glass-panel p-6 sm:p-8"
        spotlightColor="rgba(16, 185, 129, 0.16)"
        borderColor="rgba(16, 185, 129, 0.5)"
      >
        {/* Top Header (3D Markets toggle removed as requested) */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 gap-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-semibold shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>SEC &amp; SEBI Portfolio Grounding</span>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-black/40 border border-white/10 text-[11px] font-mono text-emerald-400 shadow-inner">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>Live Portfolio Calibration</span>
          </div>
        </div>

        {/* Hero Metric & Circular Indicator */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-5 items-center py-6 border-b border-white/10">
          {/* Left: Total Tracked Capital */}
          <div className="sm:col-span-7 flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Total Tracked Wealth
            </span>
            <div className="flex items-baseline gap-3">
              <span className="font-display font-extrabold text-3xl sm:text-4xl text-white tracking-tight">
                <CountUp to={142500} prefix="$" duration={1.8} />
              </span>
              <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 font-bold text-xs shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>+8.4% YTD</span>
              </div>
            </div>
            <p className="text-xs text-zinc-400 mt-1 leading-snug">
              Verified across 3 asset classes with Python Decimal precision. Zero drift.
            </p>
          </div>

          {/* Right: Health Gauge (Score 94) */}
          <div className="sm:col-span-5 flex flex-col items-center justify-center">
            <div className="relative w-28 h-28 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 120 120">
                <circle
                  className="text-zinc-800/80 stroke-current"
                  cx="60"
                  cy="60"
                  fill="none"
                  r="48"
                  strokeWidth="8"
                />
                <circle
                  className="text-emerald-500 stroke-current"
                  cx="60"
                  cy="60"
                  fill="none"
                  r="48"
                  strokeDasharray="301.6"
                  strokeDashoffset="35"
                  strokeLinecap="round"
                  strokeWidth="8"
                />
                <circle
                  className="text-emerald-400 stroke-current"
                  cx="60"
                  cy="60"
                  fill="none"
                  r="37"
                  strokeDasharray="232.5"
                  strokeDashoffset="25"
                  strokeLinecap="round"
                  strokeWidth="6"
                />
              </svg>

              <div className="absolute flex flex-col items-center justify-center bg-zinc-950/80 backdrop-blur-md rounded-2xl w-16 h-16 shadow-lg border border-white/10">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-display font-extrabold text-base text-white leading-none mt-0.5">
                  <CountUp to={94} duration={1.2} />
                </span>
                <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-tighter">
                  Health
                </span>
              </div>
            </div>
            <span className="text-[11px] font-bold text-emerald-400 mt-2 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              Optimal and Balanced
            </span>
          </div>
        </div>

        {/* Goal Milestone & Progress Bar */}
        <div className="py-5 flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-bold text-white">
              <Flag className="w-4 h-4 text-emerald-400" />
              <span>Target: $250,000 by 2030</span>
            </div>
            <span className="px-2.5 py-0.5 rounded-md bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 font-extrabold text-[11px]">
              57% Achieved
            </span>
          </div>

          <div className="w-full h-2.5 rounded-full bg-zinc-800/80 overflow-hidden border border-white/5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.5)] transition-all duration-1000"
              style={{ width: "57%" }}
            />
          </div>

          <div className="flex items-center justify-between text-xs text-zinc-400 pt-0.5">
            <span className="flex items-center gap-1.5 font-medium text-zinc-300">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              <strong className="text-white">$1,500/mo</strong> planned contribution
            </span>
            <span className="font-semibold text-zinc-400">$107,500 remaining</span>
          </div>
        </div>

        {/* Interactive Simulation Tray */}
        <div className="pt-3 border-t border-white/10 flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setShowSimTray(!showSimTray)}
              className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>{showSimTray ? "Hide Simulation Slider" : "Run Portfolio Deposit Simulation"}</span>
            </button>
            <span className="text-[10px] font-semibold text-zinc-400">Deterministic math</span>
          </div>

          {showSimTray && (
            <div className="p-4 rounded-2xl bg-black/40 backdrop-blur-md border border-white/10 flex flex-col gap-2.5 shadow-inner">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-300 font-medium">Extra Lump Sum Deposit:</span>
                <span className="font-bold font-mono text-emerald-400 bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800">
                  +${simDeposit.toLocaleString()}
                </span>
              </div>
              <input
                type="range"
                min="500"
                max="10000"
                step="500"
                value={simDeposit}
                onChange={(e) => setSimDeposit(Number(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
              <div className="text-[11px] text-zinc-300 flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>
                  Accelerates 2030 target by{" "}
                  <strong className="text-emerald-400 font-bold">
                    {(simDeposit / 600).toFixed(1)} months
                  </strong>{" "}
                  at 8.4% compounding yield.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Verified Regulatory Footer */}
        <div className="mt-4 pt-3 flex items-center justify-between text-[11px] text-zinc-400 border-t border-white/10">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>Real-time SEBI &amp; SEC Guardrails</span>
          </span>
          <Link
            href="/dashboard"
            className="font-bold text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1"
          >
            Go to Dashboard &rarr;
          </Link>
        </div>
      </SpotlightCard>
    </div>
  );
}
