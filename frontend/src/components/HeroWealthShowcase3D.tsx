"use client";

import React, { useState, useRef, MouseEvent } from "react";
import Link from "next/link";
import { TrendingUp, ShieldCheck, Flag, CheckCircle, Sparkles, Sliders } from "lucide-react";

export default function HeroWealthShowcase3D() {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const [glarePos, setGlarePos] = useState({ x: 50, y: 50, opacity: 0 });
  const [simDeposit, setSimDeposit] = useState<number>(2500);
  const [showSimTray, setShowSimTray] = useState<boolean>(false);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -9; // Max 9 degrees
    const rotateY = ((x - centerX) / centerX) * 9;

    setTilt({ x: rotateX, y: rotateY });

    const glareX = (x / rect.width) * 100;
    const glareY = (y / rect.height) * 100;
    setGlarePos({ x: glareX, y: glareY, opacity: 0.18 });
  };

  const handleMouseEnter = () => setIsHovered(true);
  const handleMouseLeave = () => {
    setIsHovered(false);
    setTilt({ x: 0, y: 0 });
    setGlarePos((prev) => ({ ...prev, opacity: 0 }));
  };

  return (
    <div className="relative w-full max-w-[540px] xl:max-w-[580px] mx-auto py-4">
      {/* 3D Ambient Atmospheric Backdrops */}
      <div className="absolute -top-10 -right-10 w-72 h-72 rounded-full bg-gradient-to-br from-indigo-500/20 via-purple-500/10 to-transparent blur-3xl pointer-events-none animate-pulse"></div>
      <div className="absolute -bottom-10 -left-10 w-64 h-64 rounded-full bg-emerald-500/15 blur-2xl pointer-events-none"></div>

      {/* Main 3D Card Shell */}
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="relative rounded-3xl bg-white border border-slate-200/90 shadow-[0_16px_40px_-12px_rgba(99,102,241,0.12),0_4px_16px_-4px_rgba(15,23,42,0.06)] p-6 sm:p-8 transition-transform duration-200 ease-out will-change-transform cursor-pointer"
        style={{
          transformStyle: "preserve-3d",
          perspective: "1200px",
          transform: isHovered
            ? `perspective(1200px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) scale3d(1.02, 1.02, 1.02)`
            : "perspective(1200px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)",
        }}
      >
        {/* Dynamic Specular Sheen */}
        <div
          className="absolute inset-0 rounded-3xl pointer-events-none transition-opacity duration-300 z-30"
          style={{
            opacity: glarePos.opacity,
            background: `radial-gradient(circle 350px at ${glarePos.x}% ${glarePos.y}%, rgba(255, 255, 255, 0.9), transparent 75%)`,
          }}
        />

        {/* 3D Layer 1: Floating Top Badge (Z: 40px) */}
        <div
          className="flex items-center justify-between pb-4 border-b border-slate-100 transition-transform duration-300"
          style={{ transform: "translateZ(40px)" }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
            <span>SEC &amp; SEBI Portfolio Sync</span>
          </div>

          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Interactive 3D Preview</span>
          </span>
        </div>

        {/* 3D Layer 2: Glowing Concentric Tech Gauge & Hero Metric (Z: 32px) */}
        <div
          className="grid grid-cols-1 sm:grid-cols-12 gap-5 items-center py-6 border-b border-slate-100 transition-transform duration-300"
          style={{ transform: "translateZ(32px)" }}
        >
          {/* Left: Total Tracked Capital */}
          <div className="sm:col-span-7 flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Total Tracked Wealth
            </span>
            <div className="flex items-baseline gap-3">
              <span className="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
                $142,500
              </span>
              <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100 font-bold text-xs shadow-xs">
                <TrendingUp className="w-3.5 h-3.5" />
                <span>+8.4% YTD</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-1 leading-snug">
              Verified across 3 asset classes with Python Decimal precision. Zero drift.
            </p>
          </div>

          {/* Right: Concentric Tech Gauge (Score 94) */}
          <div className="sm:col-span-5 flex flex-col items-center justify-center">
            <div className="relative w-28 h-28 flex items-center justify-center">
              {/* Pulsing Ambient Glow behind the Gauge */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-indigo-500/25 via-emerald-400/25 to-purple-500/20 blur-lg animate-pulse"></div>

              {/* Concentric SVG Rings */}
              <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 120 120">
                {/* Background Ring */}
                <circle
                  className="text-slate-100 stroke-current"
                  cx="60"
                  cy="60"
                  fill="none"
                  r="48"
                  strokeWidth="8"
                />
                {/* Outer Indigo Ring */}
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
                {/* Inner Emerald Ring */}
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

              {/* Central Badge in the Tech Ring */}
              <div className="absolute flex flex-col items-center justify-center bg-white rounded-full w-16 h-16 shadow-md border border-slate-100">
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
              Optimal &amp; Balanced
            </span>
          </div>
        </div>

        {/* 3D Layer 3: Goal Milestone & Progress Bar (Z: 24px) */}
        <div
          className="py-5 flex flex-col gap-3 transition-transform duration-300"
          style={{ transform: "translateZ(24px)" }}
        >
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-bold text-slate-900">
              <Flag className="w-4 h-4 text-indigo-600" />
              <span>Target: $250,000 by 2030</span>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-extrabold text-[11px]">
              57% Achieved
            </span>
          </div>

          {/* Animated 3D Gradient Progress Bar */}
          <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden p-0.5 shadow-inner">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-700 via-indigo-500 to-emerald-500 transition-all duration-700 shadow-sm"
              style={{ width: "57%" }}
            />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 pt-0.5">
            <span className="flex items-center gap-1 font-medium text-slate-700">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
              <strong>$1,500/mo</strong> auto-deposit is on track
            </span>
            <span className="font-semibold text-slate-400">$107,500 to go</span>
          </div>
        </div>

        {/* 3D Layer 4: Interactive Micro Simulation Slider (Z: 20px) */}
        <div
          className="pt-3 border-t border-slate-100 flex flex-col gap-2.5 transition-transform duration-300"
          style={{ transform: "translateZ(20px)" }}
        >
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setShowSimTray(!showSimTray)}
              className="text-xs font-bold text-indigo-700 hover:text-indigo-900 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>{showSimTray ? "Hide Simulation Slider" : "⚡ Try Live Deposit Simulation"}</span>
            </button>
            <span className="text-[10px] font-semibold text-slate-400">Deterministic math</span>
          </div>

          {showSimTray && (
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col gap-2 animate-in fade-in slide-in-from-top-1 duration-200">
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

        {/* 3D Layer 5: Verified Regulatory Footer (Z: 14px) */}
        <div
          className="mt-4 pt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 transition-transform duration-300"
          style={{ transform: "translateZ(14px)" }}
        >
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>Real-time SEBI &amp; SEC Guardrails</span>
          </span>
          <Link
            href="/dashboard"
            className="font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            Launch Full Studio →
          </Link>
        </div>
      </div>
    </div>
  );
}

