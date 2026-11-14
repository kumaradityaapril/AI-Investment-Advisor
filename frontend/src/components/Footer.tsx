import Link from "next/link";

export default function Footer() {
  return (
    <footer className="w-full bg-white border-t border-[#e2e8f0] py-12 px-4 sm:px-8 lg:px-12 2xl:px-16 text-[#464554]">
      <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-start justify-between gap-8">
        <div className="flex flex-col gap-3 max-w-sm">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#2a14b4] flex items-center justify-center text-white">
              <span className="material-symbols-outlined text-[18px]">
                auto_awesome
              </span>
            </div>
            <span className="font-display font-bold text-lg text-[#2a14b4]">
              AI Investment Advisor
            </span>
          </div>
          <p className="text-xs text-[#777586] leading-relaxed">
            Institutional-grade autonomous wealth intelligence powered by
            deterministic Python math, pgvector hybrid search, and strict
            regulatory guardrails.
          </p>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#00442d] bg-[#85f8c4]/40 px-3 py-1 rounded-full w-fit">
            <span className="w-2 h-2 rounded-full bg-[#10b981]"></span>
            <span>SEC &amp; SEBI Disclaimers Grounded</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-8 text-xs">
          <div className="flex flex-col gap-2">
            <span className="font-bold text-[#0b1c30] uppercase tracking-wider text-[11px]">
              Platform Modules
            </span>
            <Link href="/dashboard" className="hover:text-[#2a14b4] transition-colors">
              Wealth Overview
            </Link>
            <Link href="/profile" className="hover:text-[#2a14b4] transition-colors">
              Risk Calibration
            </Link>
            <Link href="/documents" className="hover:text-[#2a14b4] transition-colors">
              Read Documents (RAG)
            </Link>
            <Link href="/compare" className="hover:text-[#2a14b4] transition-colors">
              Compare Assets
            </Link>
          </div>

          <div className="flex flex-col gap-2">
            <span className="font-bold text-[#0b1c30] uppercase tracking-wider text-[11px]">
              Intelligence Engines
            </span>
            <Link href="/scenarios" className="hover:text-[#2a14b4] transition-colors">
              What-If Simulator
            </Link>
            <Link href="/research" className="hover:text-[#2a14b4] transition-colors">
              LangGraph Research
            </Link>
            <Link href="/why-this-plan" className="hover:text-[#2a14b4] transition-colors">
              Safety Audits Trail
            </Link>
            <Link href="/history" className="hover:text-[#2a14b4] transition-colors">
              Memory Diff
            </Link>
          </div>

          <div className="flex flex-col gap-2">
            <span className="font-bold text-[#0b1c30] uppercase tracking-wider text-[11px]">
              Guardrails
            </span>
            <span className="text-[#777586]">Zero LLM Hallucination</span>
            <span className="text-[#777586]">768-dim Vector Space</span>
            <span className="text-[#777586]">Deterministic Decimal Math</span>
            <span className="text-[#777586]">Audit Trail Verification</span>
          </div>
        </div>
      </div>

      <div className="max-w-[1600px] mx-auto mt-10 pt-6 border-t border-[#e2e8f0]/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#777586]">
        <p>© 2026 AI Investment Advisor. For educational &amp; analytical guidance.</p>
        <p className="max-w-md text-center sm:text-right">
          Investments carry market risk. Past performance does not guarantee future results.
        </p>
      </div>
    </footer>
  );
}

