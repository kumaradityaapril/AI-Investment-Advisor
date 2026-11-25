"use client";

import React, { useState } from "react";
import Link from "next/link";
import { TrendingUp, ShieldCheck, Flag, CheckCircle, Sliders } from "lucide-react";

export default function HeroWealthShowcase3D() {
  const [simDeposit, setSimDeposit] = useState<number>(2500);
  const [showSimTray, setShowSimTray] = useState<boolean>(false);

  return (
    <div className="relative w-full max-w-[540px] xl:max-w-[580px] mx-auto py-2">
      {/* Institutional Card Shell */}
      <div className="relative rounded-2xl bg-white border border-slate-200/90 shadow-sm p-6 sm:p-8">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>SEC &amp; SEBI Portfolio Grounding</span>
          </div>

          <span className="text-[11px] font-semibold text-slate-500">
            Institutional Portfolio Preview
          </span>
        </div>

        {/* Hero Metric & Circular Indicator */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-5 items-center py-6 border-b border-slate-100">
          {/* Left: Total Tracked Capital */}
          <div className="sm:col-span-7 flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Total Tracked Wealth
            </span>
            <div className="flex items-baseline gap-3">
              <span className="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
                $142,500
              </span>
              <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-100 font-bold text-xs">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>+8.4% YTD</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-1 leading-snug">
              Verified across 3 asset classes with Python Decimal precision. Zero drift.
            </p>
          </div>

          {/* Right: Health Gauge (Score 94) */}
          <div className="sm:col-span-5 flex flex-col items-center justify-center">
            <div className="relative w-28 h-28 flex items-center justify-center">
              {/* Concentric SVG Rings */}
              <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 120 120">
                <circle
                  className="text-slate-100 stroke-current"
                  cx="60"
                  cy="60"
                  fill="none"
                  r="48"
                  strokeWidth="8"
                />
                <circle
                  className="text-indigo-600 stroke-current"
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
                  className="text-emerald-500 stroke-current"
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

              <div className="absolute flex flex-col items-center justify-center bg-white rounded-xl w-16 h-16 shadow-xs border border-slate-100">
                <ShieldCheck className="w-4 h-4 text-indigo-700" />
                <span className="font-display font-extrabold text-base text-slate-900 leading-none mt-0.5">
                  94
                </span>
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-tighter">
                  Health
                </span>
              </div>
            </div>
            <span className="text-[11px] font-bold text-emerald-700 mt-2 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Optimal and Balanced
            </span>
          </div>
        </div>

        {/* Goal Milestone & Progress Bar */}
        <div className="py-5 flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-bold text-slate-900">
              <Flag className="w-4 h-4 text-indigo-600" />
              <span>Target: $250,000 by 2030</span>
            </div>
            <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-extrabold text-[11px]">
              57% Achieved
            </span>
          </div>

          <div className="w-full h-2.5 rounded-md bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-md bg-indigo-700"
              style={{ width: "57%" }}
            />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 pt-0.5">
            <span className="flex items-center gap-1 font-medium text-slate-700">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
              <strong>$1,500/mo</strong> planned contribution
            </span>
            <span className="font-semibold text-slate-400">$107,500 remaining</span>
          </div>
        </div>

        {/* Interactive Simulation Tray */}
        <div className="pt-3 border-t border-slate-100 flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setShowSimTray(!showSimTray)}
              className="text-xs font-bold text-indigo-700 hover:text-indigo-900 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>{showSimTray ? "Hide Simulation Slider" : "Run Portfolio Deposit Simulation"}</span>
            </button>
            <span className="text-[10px] font-semibold text-slate-400">Deterministic math</span>
          </div>

          {showSimTray && (
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col gap-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600 font-medium">Extra Lump Sum Deposit:</span>
                <span className="font-bold font-mono text-indigo-700 bg-white px-2 py-0.5 rounded border border-slate-200">
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
                className="w-full accent-indigo-700 cursor-pointer"
              />
              <div className="text-[11px] text-slate-600 flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>
                  Accelerates 2030 target by{" "}
                  <strong className="text-emerald-700 font-bold">
                    {(simDeposit / 600).toFixed(1)} months
                  </strong>{" "}
                  at 8.4% compounding yield.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Verified Regulatory Footer */}
        <div className="mt-4 pt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>Real-time SEBI &amp; SEC Guardrails</span>
          </span>
          <Link
            href="/dashboard"
            className="font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            Go to Dashboard &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
