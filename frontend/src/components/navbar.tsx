"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ShieldCheck, LogIn, UserPlus, LayoutDashboard, LogOut, Activity } from "lucide-react";

export function Navbar() {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Dashboard pages have their own integrated enterprise top-navigation and sidebar shell
  if (pathname?.startsWith("/dashboard")) {
    return null;
  }

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-[#292D35] bg-[#090A0D]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group focus:outline-hidden focus:ring-2 focus:ring-[#D6B15E]/50 rounded-lg p-1">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#D6B15E]/40 bg-[#12151B] shadow-[0_0_12px_rgba(214,177,94,0.15)] transition-all group-hover:border-[#D6B15E]">
            <ShieldCheck className="h-5 w-5 text-[#D6B15E]" />
          </div>
          <div className="flex flex-col">
            <span className="font-mono text-xs font-bold tracking-wider text-[#F5F5F2]">
              SYNTHETIC MEDIA <span className="text-[#D6B15E]">DETECTION</span>
            </span>
            <span className="text-[10px] tracking-widest text-[#A3A7B0] uppercase font-mono">
              Deep Learning Framework
            </span>
          </div>
        </Link>

        {/* Navigation Actions */}
        <nav className="flex items-center gap-3 sm:gap-4">
          <div className="hidden items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400 sm:inline-flex">
            <Activity className="h-3.5 w-3.5 animate-pulse" />
            <span className="font-mono text-[11px] font-medium tracking-wide">Core Engine Online</span>
          </div>

          {isLoading ? (
            <span className="text-xs text-[#A3A7B0] font-mono">Verifying session...</span>
          ) : user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 rounded-lg border border-[#292D35] bg-[#12151B] px-3.5 py-1.5 text-xs text-[#F5F5F2] transition-colors hover:border-[#D6B15E]/50 hover:bg-[#181C23]"
              >
                <LayoutDashboard className="h-3.5 w-3.5 text-[#D6B15E]" />
                <span className="font-mono font-medium text-[#F0D58A]">
                  {user.username}
                </span>
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400 transition-colors hover:border-red-500/60 hover:bg-red-500/20 cursor-pointer"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 sm:gap-3">
              <Link
                href="/login"
                className="flex items-center gap-1.5 rounded-lg border border-[#292D35] bg-[#12151B] px-3.5 py-1.5 text-xs font-medium text-[#F5F5F2] transition-all hover:border-[#D6B15E] hover:text-[#D6B15E]"
              >
                <LogIn className="h-3.5 w-3.5" />
                <span>Analyst Portal</span>
              </Link>
              <Link
                href="/register"
                className="flex items-center gap-1.5 rounded-lg border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-3.5 py-1.5 text-xs font-semibold text-[#090A0D] transition-opacity hover:opacity-95 shadow-[0_0_12px_rgba(214,177,94,0.2)]"
              >
                <UserPlus className="h-3.5 w-3.5" />
                <span>Register</span>
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
