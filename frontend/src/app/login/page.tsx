"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Lock, Mail, ArrowRight, ShieldCheck, AlertCircle, Sparkles } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(
        err.message || "Failed to sign in. Please verify your email and password."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090a0f] text-[#f8fafc] relative overflow-hidden">
      {/* Ambient Emerald Glow Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[350px] h-[350px] bg-emerald-500/5 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute inset-0 dark-grid opacity-30 pointer-events-none" />

      <Navbar />

      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-16 md:py-24 relative z-10">
        <div className="w-full max-w-xl animate-popup">
          {/* Main Glassy 3D Card */}
          <div className="relative rounded-3xl p-8 sm:p-12 backdrop-blur-2xl bg-zinc-900/60 border border-white/10 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.95),0_0_50px_rgba(16,185,129,0.1)] transition-all duration-300 hover:border-emerald-500/30">
            {/* Top Glowing Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 mb-4 shadow-[0_0_25px_rgba(16,185,129,0.35)] transition-transform hover:scale-110 duration-300">
                <Lock className="w-8 h-8" />
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-display tracking-tight">
                Welcome Back
              </h1>
              <p className="text-sm text-zinc-400 mt-2">
                Sign in to your private AI Investment Advisor portfolio
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-300 flex items-start gap-3 text-sm shadow-[0_0_20px_rgba(244,63,94,0.15)]">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
                <div className="flex-1 font-medium">{error}</div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="investor@example.com"
                    className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-zinc-800 bg-zinc-950/80 text-white placeholder-zinc-500 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/20 transition-all text-sm outline-none"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    Password
                  </label>
                </div>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-zinc-800 bg-zinc-950/80 text-white placeholder-zinc-500 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/20 transition-all text-sm outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-400 hover:from-emerald-400 hover:to-emerald-300 text-zinc-950 font-bold text-sm shadow-[0_4px_25px_rgba(16,185,129,0.35)] hover:shadow-[0_8px_35px_rgba(16,185,129,0.55)] hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 mt-3"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-4 rounded-full border-2 border-zinc-950 border-t-transparent animate-spin"></span>
                    <span>Verifying Credentials...</span>
                  </div>
                ) : (
                  <>
                    <span>Sign In to Private Dashboard</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-8 pt-6 border-t border-white/10 text-center">
              <p className="text-sm text-zinc-400">
                Don't have an account yet?{" "}
                <Link
                  href="/register"
                  className="font-semibold text-emerald-400 hover:text-emerald-300 underline underline-offset-4 transition-colors"
                >
                  Create one now
                </Link>
              </p>
            </div>

            {/* Institutional Security Badge */}
            <div className="mt-6 flex items-center justify-center gap-2 text-xs text-zinc-400 bg-zinc-950/60 border border-zinc-800/80 py-2.5 px-4 rounded-xl">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>256-Bit Argon2id Encrypted • Tenant-Isolated Data</span>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
