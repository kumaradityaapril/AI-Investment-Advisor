"use client";

import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Link from "next/link";
import { ShieldAlert, FileText, ArrowLeft, AlertTriangle } from "lucide-react";

export default function TermsAndConditionsPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#090a0f] text-[#f8fafc]">
      <Navbar />

      <main className="flex-1 pt-28 pb-20 px-4 sm:px-8 lg:px-12 2xl:px-16 max-w-[1200px] mx-auto w-full">
        {/* Breadcrumb Navigation */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-700 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </Link>
        </div>

        {/* Page Header */}
        <div className="bg-white rounded-2xl p-8 sm:p-10 border border-slate-200/80 shadow-xs mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-slate-100 text-slate-800 font-semibold text-xs uppercase tracking-wider mb-3">
            <FileText className="w-3.5 h-3.5 text-indigo-700" />
            <span>Statutory Legal Agreement</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
            Terms and Conditions
          </h1>
          <p className="text-sm text-slate-500 mt-2 max-w-2xl leading-relaxed">
            Effective Date: January 1, 2026. Please read these terms carefully before accessing or using AI Investment Advisor.
          </p>
        </div>

        {/* Terms Body */}
        <div className="bg-white rounded-2xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-10 text-slate-700 text-sm leading-relaxed">
          {/* Statutory Advisory Disclaimer Box */}
          <div className="p-5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-950 space-y-2">
            <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-amber-900">
              <AlertTriangle className="w-4 h-4 text-amber-700" />
              <span>Mandatory Statutory Disclaimer</span>
            </div>
            <p className="text-xs leading-relaxed">
              AI Investment Advisor is an educational and analytical decision-support workspace combining deterministic mathematical calculations with retrieval-augmented language models. The software does not provide formal individualized investment advice under the SEBI (Investment Advisers) Regulations, 2013 or SEC Investment Advisers Act of 1940. Outputs are generated for informational purposes only. Always consult a qualified, licensed financial professional before executing investment transactions.
            </p>
          </div>

          {/* Section 1 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">1</span>
              <span>Acceptance of Agreement</span>
            </h2>
            <p>
              By creating an account, accessing, or utilizing any portion of this application, you agree to be bound by these Terms and Conditions and our Privacy Policy. If you do not accept these terms, you must discontinue use of the platform immediately.
            </p>
          </section>

          {/* Section 2 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">2</span>
              <span>Nature of Service &amp; Non-Execution</span>
            </h2>
            <p>
              The platform provides computational tools including cash flow calculations, goal trajectory simulations, hybrid document search, and comparative analysis:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
              <li>
                <strong>No Brokerage or Order Execution:</strong> The platform does not hold custody of client assets, execute trades, route securities orders, or manage investment portfolios directly.
              </li>
              <li>
                <strong>No Performance Guarantees:</strong> Capital market instruments (including equities, mutual funds, ETFs, and foreign securities) fluctuate in value and involve risk of principal loss. Past performance, backtests, and deterministic mathematical projections do not guarantee future returns.
              </li>
              <li>
                <strong>Human-in-the-Loop Principle:</strong> All recommendations are intended to assist the user in evaluating scenarios. You retain sole discretion and legal responsibility for any financial decisions made.
              </li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">3</span>
              <span>User Obligations &amp; Profile Accuracy</span>
            </h2>
            <p>
              The precision of deterministic outputs relies directly upon the accuracy of user-provided information:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
              <li>
                <strong>True and Accurate Figures:</strong> You agree to provide accurate, honest financial data regarding income, liabilities, expenses, and investment goals.
              </li>
              <li>
                <strong>Authorized Documents:</strong> You may only upload documents (salary slips, bank statements, tax forms, or portfolio statements) that you have lawful authorization to possess and process.
              </li>
              <li>
                <strong>Credential Security:</strong> You are responsible for safeguarding your login credentials and preventing unauthorized access to your account.
              </li>
            </ul>
          </section>

          {/* Section 4 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">4</span>
              <span>Prohibited Activities</span>
            </h2>
            <p>
              When using the platform, you agree not to:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
              <li>Upload malicious files, viruses, or corrupted PDFs intended to compromise document extraction pipelines.</li>
              <li>Attempt to bypass rate limits, authentication boundaries, tenant isolation, or safety audit filters.</li>
              <li>Reverse engineer, decompile, or extract the underlying model weights, system prompts, or proprietary algorithms.</li>
              <li>Use automated scripts or scrapers to extract platform data without prior written authorization.</li>
            </ul>
          </section>

          {/* Section 5 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">5</span>
              <span>Limitation of Liability</span>
            </h2>
            <p>
              To the fullest extent permitted by applicable law, AI Investment Advisor, its creators, contributors, and hosting providers shall not be liable for any direct, indirect, incidental, consequential, or punitive damages, including financial loss, lost profits, portfolio depreciation, or tax penalties resulting from your use of or reliance upon platform calculations, simulations, or AI outputs.
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-3 border-t border-slate-100 pt-6">
            <h2 className="text-lg font-bold text-slate-900 font-display">
              Governing Law &amp; Inquiries
            </h2>
            <p className="text-xs text-slate-600">
              These terms are governed by the laws of India. For questions concerning these terms, contact our legal desk at: <span className="font-mono text-indigo-700">legal@aiinvestmentadvisor.com</span>.
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
