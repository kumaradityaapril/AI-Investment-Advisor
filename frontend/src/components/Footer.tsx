import Link from "next/link";
import { Sparkles, ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full bg-[#07080b] border-t border-white/10 py-16 px-4 sm:px-8 lg:px-12 2xl:px-16 text-zinc-400">
      <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-start justify-between gap-10">
        <div className="flex flex-col gap-4 max-w-sm">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-950/70 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.25)]">
              <Sparkles className="w-5 h-5 text-emerald-400" />
            </div>
            <span className="font-display font-extrabold text-lg text-white tracking-tight">
              AI Investment Advisor
            </span>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Institutional-grade autonomous wealth intelligence powered by
            deterministic Python math, pgvector hybrid search, and strict
            SEBI/SEC regulatory guardrails.
          </p>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-950/50 border border-emerald-500/30 px-3.5 py-1.5 rounded-xl w-fit shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>SEC &amp; SEBI Disclaimers Grounded</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 text-xs">
          <div className="flex flex-col gap-2.5">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">
              Platform Modules
            </span>
            <Link href="/dashboard" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Wealth Overview
            </Link>
            <Link href="/profile" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Risk Calibration
            </Link>
            <Link href="/documents" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Read Documents (RAG)
            </Link>
            <Link href="/compare" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Compare Assets
            </Link>
          </div>

          <div className="flex flex-col gap-2.5">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">
              Intelligence Engines
            </span>
            <Link href="/scenarios" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              What-If Simulator
            </Link>
            <Link href="/research" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              LangGraph Research
            </Link>
            <Link href="/why-this-plan" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Safety Audits Trail
            </Link>
            <Link href="/history" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Memory Diff
            </Link>
          </div>

          <div className="flex flex-col gap-2.5">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">
              Guardrails
            </span>
            <span className="text-zinc-500">Zero LLM Hallucination</span>
            <span className="text-zinc-500">768-dim Vector Space</span>
            <span className="text-zinc-500">Deterministic Decimal Math</span>
            <span className="text-zinc-500">Audit Trail Verification</span>
          </div>

          <div className="flex flex-col gap-2.5">
            <span className="font-bold text-white uppercase tracking-wider text-[11px]">
              Legal &amp; Compliance
            </span>
            <Link href="/privacy" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-zinc-400 hover:text-emerald-400 transition-colors">
              Terms &amp; Conditions
            </Link>
            <span className="text-zinc-500">SEBI Grounding</span>
            <span className="text-zinc-500">Tenant Isolation</span>
          </div>
        </div>
      </div>

      <div className="max-w-[1600px] mx-auto mt-12 pt-6 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-zinc-500">
        <div className="flex items-center gap-4">
          <p>© 2026 AI Investment Advisor. For educational &amp; analytical guidance.</p>
          <span className="text-zinc-700">|</span>
          <Link href="/privacy" className="hover:text-emerald-400 underline underline-offset-4 transition-colors">Privacy Policy</Link>
          <span className="text-zinc-700">|</span>
          <Link href="/terms" className="hover:text-emerald-400 underline underline-offset-4 transition-colors">Terms of Service</Link>
        </div>
        <p className="max-w-md text-center sm:text-right">
          All projections are based on user assumptions and historical data. Not SEBI registered investment advice.
        </p>
      </div>
    </footer>
  );
}
