"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import AuthModal from "./AuthModal";
import { Sparkles, LogOut, Menu, X, ShieldCheck } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: "Dashboard", href: "/dashboard" },
    { name: "Profile & Risk", href: "/profile" },
    { name: "Documents", href: "/documents" },
    { name: "Compare", href: "/compare" },
    { name: "Scenarios", href: "/scenarios" },
    { name: "Research", href: "/research" },
    { name: "Safety Audits", href: "/why-this-plan" },
    { name: "History", href: "/history" },
  ];

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-40 bg-[#090a0f]/85 backdrop-blur-xl border-b border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.6)]">
        <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-8 lg:px-12 2xl:px-16 h-20 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group flex-shrink-0">
            <div className="w-9 h-9 rounded-xl bg-emerald-950/70 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.25)] group-hover:scale-110 group-hover:shadow-[0_0_25px_rgba(16,185,129,0.45)] transition-all flex-shrink-0">
              <Sparkles className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="flex flex-col">
              <span className="font-display font-extrabold text-base sm:text-lg text-white tracking-tight leading-none whitespace-nowrap group-hover:text-emerald-300 transition-colors">
                AI Investment Advisor
              </span>
              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider mt-0.5 whitespace-nowrap">
                Wealth Intelligence
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 bg-zinc-900/80 p-1.5 rounded-2xl border border-zinc-800 flex-shrink-0">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 whitespace-nowrap ${
                pathname === "/"
                  ? "bg-emerald-500 text-zinc-950 font-bold shadow-[0_0_15px_rgba(16,185,129,0.4)] scale-[1.02]"
                  : "text-zinc-400 hover:text-emerald-300 hover:bg-white/5"
              }`}
            >
              Home
            </Link>
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? "bg-emerald-500 text-zinc-950 font-bold shadow-[0_0_15px_rgba(16,185,129,0.4)] scale-[1.02]"
                      : "text-zinc-400 hover:text-emerald-300 hover:bg-white/5"
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Right Action Tools */}
          <div className="flex items-center gap-3.5 flex-shrink-0">
            {/* Live Data Badge */}
            <div className="hidden xl:flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-zinc-900/80 border border-zinc-800 text-zinc-300 text-xs font-medium whitespace-nowrap flex-shrink-0">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse flex-shrink-0"></span>
              <span>SEC / SEBI Grounded</span>
            </div>

            {/* User Account / Auth Actions */}
            {user ? (
              <div className="flex items-center gap-2.5 flex-shrink-0">
                <Link
                  href="/profile"
                  className="flex items-center gap-2 py-1 px-2.5 rounded-xl bg-zinc-900/80 border border-zinc-800 hover:border-emerald-500/50 hover:bg-zinc-800/80 transition-all flex-shrink-0"
                >
                  <div className="w-6 h-6 rounded-lg bg-emerald-500 flex items-center justify-center text-zinc-950 text-[11px] font-bold flex-shrink-0 shadow-[0_0_10px_rgba(16,185,129,0.3)]">
                    {user.name
                      ? user.name.trim().substring(0, 2).toUpperCase()
                      : user.email.substring(0, 2).toUpperCase()}
                  </div>
                  <span className="text-xs font-semibold text-zinc-200 max-w-[140px] truncate hidden sm:inline">
                    {user.name || user.email.split("@")[0]}
                  </span>
                </Link>

                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-2 rounded-xl text-zinc-400 hover:text-rose-400 hover:bg-rose-950/40 border border-transparent hover:border-rose-500/30 transition-all cursor-pointer flex-shrink-0"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2.5 flex-shrink-0">
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-zinc-300 hover:text-emerald-400 hover:bg-white/5 transition-colors whitespace-nowrap"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-400 hover:from-emerald-400 hover:to-emerald-300 text-zinc-950 text-xs font-bold shadow-[0_0_20px_rgba(16,185,129,0.35)] hover:shadow-[0_0_30px_rgba(16,185,129,0.55)] hover:scale-105 transition-all whitespace-nowrap"
                >
                  Register
                </Link>
              </div>
            )}

            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl text-zinc-300 hover:text-white hover:bg-white/10 flex-shrink-0"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {isMobileMenuOpen && (
          <div className="lg:hidden bg-[#090a0f]/95 backdrop-blur-2xl border-b border-white/10 px-4 py-4 space-y-2 animate-in fade-in slide-in-from-top-2 duration-150">
            <div className="grid grid-cols-2 gap-2 pb-3 border-b border-white/10">
              <Link
                href="/"
                onClick={() => setIsMobileMenuOpen(false)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold text-center transition-all ${
                  pathname === "/" ? "bg-emerald-500 text-zinc-950 font-bold" : "text-zinc-400 hover:bg-white/5"
                }`}
              >
                Home
              </Link>
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`px-3 py-2 rounded-xl text-xs font-semibold text-center transition-all ${
                      isActive ? "bg-emerald-500 text-zinc-950 font-bold" : "text-zinc-400 hover:bg-white/5"
                    }`}
                  >
                    {link.name}
                  </Link>
                );
              })}
            </div>
            {!user ? (
              <div className="flex gap-2 pt-2">
                <Link
                  href="/login"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex-1 text-center py-2.5 rounded-xl border border-zinc-800 text-xs font-semibold text-zinc-300 hover:bg-white/5"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex-1 text-center py-2.5 rounded-xl bg-emerald-500 text-zinc-950 font-bold text-xs shadow-[0_0_15px_rgba(16,185,129,0.35)]"
                >
                  Register
                </Link>
              </div>
            ) : (
              <div className="pt-2">
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false);
                    logout();
                  }}
                  className="w-full text-center py-2.5 rounded-xl border border-rose-500/30 text-rose-400 text-xs font-semibold bg-rose-950/30"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        )}
      </header>

      <AuthModal
        isOpen={isAuthOpen}
        initialMode={authMode}
        onClose={() => setIsAuthOpen(false)}
      />
    </>
  );
}
