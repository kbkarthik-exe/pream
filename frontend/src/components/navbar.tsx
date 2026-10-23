"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function Navbar() {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-[#2B2F3D] bg-[#0B0C10]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#D4AF37]/40 bg-[#12141A] shadow-[0_0_12px_rgba(212,175,55,0.2)] transition-all group-hover:border-[#D4AF37]">
            <span className="font-mono text-sm font-bold text-[#D4AF37]">Ψ</span>
          </div>
          <div className="flex flex-col">
            <span className="font-mono text-sm font-bold tracking-wider text-white">
              AICF<span className="text-[#D4AF37]">.INTEL</span>
            </span>
            <span className="text-[10px] tracking-widest text-[#9FA6B2] uppercase">
              Content Forensics
            </span>
          </div>
        </Link>

        {/* Navigation Actions */}
        <nav className="flex items-center gap-3 sm:gap-4">
          <span className="hidden items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs text-emerald-400 sm:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Core Active
          </span>

          {isLoading ? (
            <span className="text-xs text-[#9FA6B2]">Verifying session...</span>
          ) : user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3 py-1.5 text-xs text-[#F8F9FA] transition-colors hover:border-[#D4AF37]/50"
              >
                <span className="h-2 w-2 rounded-full bg-[#D4AF37]" />
                <span className="font-mono font-medium text-[#F3E5AB]">
                  {user.username}
                </span>
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400 transition-colors hover:border-red-500/60 hover:bg-red-500/20"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 sm:gap-3">
              <Link
                href="/login"
                className="rounded-md border border-[#2B2F3D] bg-[#12141A] px-3.5 py-1.5 text-xs font-medium text-[#F8F9FA] transition-colors hover:border-[#D4AF37] hover:text-[#D4AF37]"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="rounded-md border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-3.5 py-1.5 text-xs font-semibold text-black transition-opacity hover:opacity-95"
              >
                Register
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
