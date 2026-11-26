"use client";

import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Link from "next/link";
import { ShieldCheck, Lock, FileText, ArrowLeft, CheckCircle2 } from "lucide-react";

export default function PrivacyPolicyPage() {
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
            <Lock className="w-3.5 h-3.5 text-indigo-700" />
            <span>Institutional Data Protection Policy</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
            Privacy Policy
          </h1>
          <p className="text-sm text-slate-500 mt-2 max-w-2xl leading-relaxed">
            Effective Date: January 1, 2026. This policy describes how AI Investment Advisor collects, processes, and safeguards investor financial information, uploaded documents, and analytical data.
          </p>
        </div>

        {/* Policy Body */}
        <div className="bg-white rounded-2xl p-8 sm:p-10 border border-slate-200/80 shadow-xs space-y-10 text-slate-700 text-sm leading-relaxed">
          {/* Section 1 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">1</span>
              <span>Information We Collect</span>
            </h2>
            <p>
              We collect information strictly necessary to provide deterministic portfolio analysis, cash flow calculations, and risk-calibrated recommendations:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
              <li>
                <strong>Account Credentials:</strong> Email address and encrypted password credentials (hashed using bcrypt with salt).
              </li>
              <li>
                <strong>Financial Profile Data:</strong> Self-reported figures including monthly income, living expenses, liquid savings, active investments, and monthly investment capacity.
              </li>
              <li>
                <strong>Financial Objectives:</strong> Defined investment goals, target corpus amounts, and target investment horizons.
              </li>
              <li>
                <strong>Risk Assessment Responses:</strong> Responses to our standardized risk tolerance and financial capacity questionnaire.
              </li>
              <li>
                <strong>Uploaded Financial Documents:</strong> PDF financial statements, portfolio summaries, or salary slips uploaded voluntarily by the user for text extraction and hybrid RAG indexing.
              </li>
            </ul>
          </section>

          {/* Section 2 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">2</span>
              <span>How We Process Your Financial Information</span>
            </h2>
            <p>
              Your data is processed strictly for analytical and educational decision-support:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
              <li>
                <strong>Deterministic Calculations:</strong> Calculating financial metrics (monthly surplus, savings rate, emergency fund coverage, and required monthly contributions) using precision Python Decimal math.
              </li>
              <li>
                <strong>Document Search (Hybrid RAG):</strong> Extracting text from uploaded PDF documents and generating 768-dimensional vector embeddings stored in an isolated PostgreSQL pgvector database schema.
              </li>
              <li>
                <strong>Grounded AI Analysis:</strong> Providing contextual financial information to language models through structured prompts to generate explainable advice with citations.
              </li>
              <li>
                <strong>Compliance Audits:</strong> Validating AI outputs against database ground truth to prevent numerical hallucinations and enforce regulatory disclaimers.
              </li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">3</span>
              <span>Zero Model Training & Third-Party Non-Disclosure</span>
            </h2>
            <p>
              We maintain a strict boundary between user data and foundation models:
            </p>
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>No Public Model Training</span>
              </div>
              <p className="text-xs text-slate-600">
                Your uploaded documents, balance sheet entries, and chat queries are never used to train, retrain, or improve public foundation models. API interactions with inference providers (Groq and Google Gemini) are conducted under enterprise non-persistence terms.
              </p>
            </div>
            <p>
              We do not sell, rent, monetize, or disclose your personal or financial records to brokers, marketing agencies, lending partners, or data aggregators.
            </p>
          </section>

          {/* Section 4 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">4</span>
              <span>Data Storage, Security, and Tenant Isolation</span>
            </h2>
            <p>
              We apply defense-in-depth security measures to protect stored records:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
              <li>
                <strong>Multi-Tenant Isolation:</strong> Every database query is strictly scoped to the authenticated user ID. Cross-tenant data leakage is prohibited at the database query level.
              </li>
              <li>
                <strong>Authentication Security:</strong> Industry-standard JSON Web Tokens (JWT) signed with HMAC-SHA256 and secure cookie/header transmission.
              </li>
              <li>
                <strong>Encrypted In-Transit & At-Rest:</strong> Data transmissions are encrypted using Transport Layer Security (TLS 1.3). Database storage and backups are encrypted at rest.
              </li>
            </ul>
          </section>

          {/* Section 5 */}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold">5</span>
              <span>User Data Rights & Deletion</span>
            </h2>
            <p>
              You maintain complete ownership of your financial records:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
              <li>
                <strong>Update & Rectification:</strong> You can modify your income, expenses, goals, and risk profile at any time via the Profile &amp; Risk dashboard.
              </li>
              <li>
                <strong>Document Removal:</strong> You can delete any uploaded PDF document, which immediately purges the file and its corresponding pgvector embedding chunks.
              </li>
              <li>
                <strong>Account Deletion:</strong> Upon request, your account and all associated immutable history snapshots will be permanently removed from our active databases.
              </li>
            </ul>
          </section>

          {/* Section 6 */}
          <section className="space-y-3 border-t border-slate-100 pt-6">
            <h2 className="text-lg font-bold text-slate-900 font-display">
              Contact Privacy Compliance
            </h2>
            <p className="text-xs text-slate-600">
              For inquiries regarding data protection practices, or to exercise your privacy rights, contact our compliance office at: <span className="font-mono text-indigo-700">privacy@aiinvestmentadvisor.com</span>.
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
