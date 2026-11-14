"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { Lock, ArrowRight, ShieldCheck } from "lucide-react";

export default function ProtectedRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      // Allow a brief moment or redirect
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8f9ff]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">
            Verifying secure session...
          </p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4 py-16 bg-[#f8f9ff]">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 border border-indigo-100 shadow-xl text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-6 shadow-sm">
            <Lock className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            Authentication Required
          </h2>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            Please register or sign in to access your private wealth dashboard, portfolio analytics, and AI advisory tools.
          </p>

          <div className="flex flex-col gap-3">
            <Link
              href="/login"
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-indigo-700 to-indigo-600 hover:from-indigo-800 hover:to-indigo-700 text-white font-semibold text-sm shadow-md shadow-indigo-200 transition-all flex items-center justify-center gap-2"
            >
              Sign In to Your Account <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/register"
              className="w-full py-3.5 px-6 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm transition-all"
            >
              Create New Account
            </Link>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-100 flex items-center justify-center gap-2 text-xs text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Bank-grade 256-bit JWT authentication</span>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

