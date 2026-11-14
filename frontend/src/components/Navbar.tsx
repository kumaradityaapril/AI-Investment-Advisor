"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import AuthModal from "./AuthModal";
import { Sparkles, Shield, LogOut, User, Menu, X } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: "Home", href: "/" },
    { name: "Dashboard", href: "/dashboard", protected: true },
    { name: "Profile & Risk", href: "/profile", protected: true },
    { name: "Documents (RAG)", href: "/documents", protected: true },
    { name: "Compare Assets", href: "/compare", protected: true },
    { name: "Why This Plan", href: "/why-this-plan", protected: true },
    { name: "Scenarios", href: "/scenarios", protected: true },
    { name: "Research Agent", href: "/research", protected: true },
    { name: "History & Diff", href: "/history", protected: true },
  ];

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-40 bg-white/90 backdrop-blur-xl border-b border-slate-200/80 shadow-xs">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group flex-shrink-0">
            <div className="w-10 h-10 rounded-2xl bg-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-200 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 text-indigo-100" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-display font-black text-xl text-indigo-900 tracking-tight">
                  Aura AI
                </span>
                <span className="hidden sm:inline-block px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 font-bold text-[10px] tracking-wide uppercase">
                  Wealth Advisor
                </span>
              </div>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden xl:flex items-center gap-1 bg-slate-100/80 p-1.5 rounded-full border border-slate-200/60">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-150 whitespace-nowrap ${
                    isActive
                      ? "bg-indigo-700 text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/70"
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Right Action Tools */}
          <div className="flex items-center gap-3">
            {/* Live Data Badge */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200/80 text-slate-600 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="hidden 2xl:inline">Verified SEC / SEBI Data</span>
              <span className="2xl:hidden">Verified</span>
            </div>

            {/* User Account / Auth Actions */}
            {user ? (
              <div className="flex items-center gap-3">
                <Link
                  href="/profile"
                  className="flex items-center gap-2.5 py-1.5 px-3 rounded-full bg-slate-50 border border-slate-200/80 hover:bg-indigo-50/50 transition-colors"
                >
                  <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold">
                    {user.email.substring(0, 2).toUpperCase()}
                  </div>
                  <span className="text-xs font-semibold text-slate-800 max-w-[130px] truncate hidden sm:inline">
                    {user.email}
                  </span>
                </Link>

                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-2 rounded-full text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-full text-xs font-semibold text-slate-700 hover:text-indigo-700 hover:bg-slate-100 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 rounded-full bg-indigo-700 hover:bg-indigo-800 text-white text-xs font-semibold shadow-sm transition-all shadow-indigo-200"
                >
                  Get Started
                </Link>
              </div>
            )}

            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="xl:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100"
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
          <div className="xl:hidden bg-white border-b border-slate-200 px-4 py-4 space-y-2">
            <div className="grid grid-cols-2 gap-2 pb-3 border-b border-slate-100">
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`px-3 py-2 rounded-xl text-xs font-semibold text-center transition-all ${
                      isActive
                        ? "bg-indigo-700 text-white"
                        : "text-slate-600 hover:bg-slate-100"
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
                  className="flex-1 text-center py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex-1 text-center py-2.5 rounded-xl bg-indigo-700 text-xs font-semibold text-white"
                >
                  Register
                </Link>
              </div>
            ) : (
              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs text-slate-500 truncate">
                  Logged in as <strong className="text-slate-800">{user.email}</strong>
                </span>
                <button
                  onClick={() => {
                    logout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="text-xs font-semibold text-rose-600 px-3 py-1.5 rounded-lg bg-rose-50"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        )}
      </header>

      {/* Auth Modal Container if triggered elsewhere */}
      <AuthModal
        isOpen={isAuthOpen}
        initialMode={authMode}
        onClose={() => setIsAuthOpen(false)}
      />
    </>
  );
}
