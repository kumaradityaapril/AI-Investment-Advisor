"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Lock, Mail, AlertCircle, ArrowRight, X } from "lucide-react";

interface AuthModalProps {
  isOpen: boolean;
  initialMode?: "login" | "register";
  onClose: () => void;
  onSuccess?: (email: string) => void;
}

export default function AuthModal({
  isOpen,
  initialMode = "login",
  onClose,
  onSuccess,
}: AuthModalProps) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (mode === "register") {
        if (password.length < 8) {
          throw new Error("Password must be at least 8 characters long.");
        }
        await register(email, password);
      } else {
        await login(email, password);
      }

      if (onSuccess) {
        onSuccess(email);
      }
      onClose();
    } catch (err: any) {
      setError(
        err.message ||
          (mode === "register"
            ? "Registration failed. An account with this email may already exist."
            : "Invalid email or password. Please verify your credentials or register.")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md rounded-3xl bg-white p-8 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-700 border border-indigo-100 mb-3 shadow-sm">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 font-display">
            {mode === "login" ? "Sign in to Advisor" : "Create Account"}
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            {mode === "login"
              ? "Access your personal wealth analysis & AI recommendations"
              : "Register to unlock automated financial planning"}
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex rounded-xl bg-slate-100 p-1 mb-6">
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              mode === "login"
                ? "bg-white text-indigo-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              mode === "register"
                ? "bg-white text-indigo-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-600" />
            <div className="flex-1 font-medium leading-relaxed">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="investor@example.com"
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-100 transition-all text-sm outline-none text-slate-900 bg-slate-50/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5">
              Password {mode === "register" && "(min 8 chars)"}
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-100 transition-all text-sm outline-none text-slate-900 bg-slate-50/50"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-5 rounded-xl bg-gradient-to-r from-indigo-700 to-indigo-600 hover:from-indigo-800 hover:to-indigo-700 text-white font-semibold text-sm shadow-md shadow-indigo-200 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70 mt-2"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                Processing...
              </span>
            ) : mode === "login" ? (
              <>
                Sign In to Dashboard <ArrowRight className="w-4 h-4" />
              </>
            ) : (
              <>
                Create & Continue <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-slate-400">
          Backend verified • Isolated per-investor tenant security
        </p>
      </div>
    </div>
  );
}
