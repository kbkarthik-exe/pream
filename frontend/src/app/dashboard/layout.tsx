"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/lib/auth-context";

interface NavItem {
  name: string;
  href: string;
  icon: string;
  badge?: string;
}

const navItems: NavItem[] = [
  { name: "Overview", href: "/dashboard", icon: "⊞" },
  { name: "AI Text Detection", href: "/dashboard/text", icon: "¶", badge: "TXT" },
  { name: "AI Image Detection", href: "/dashboard/image", icon: "◩", badge: "IMG" },
  { name: "AI Video Detection", href: "/dashboard/video", icon: "▶", badge: "VID" },
  { name: "AI Audio Detection", href: "/dashboard/audio", icon: "♫", badge: "AUD" },
  { name: "Reports Section", href: "/dashboard/reports", icon: "📄" },
  { name: "Settings & Profile", href: "/dashboard/settings", icon: "⚙" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <AuthGuard>
      <div className="flex min-h-[calc(100vh-65px)] flex-col md:flex-row bg-[#0B0C10] text-[#F8F9FA]">
        {/* Mobile Top Header */}
        <div className="flex items-center justify-between border-b border-[#2B2F3D] bg-[#12141A] px-4 py-3 md:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md border border-[#D4AF37]/50 bg-[#191C24] font-mono text-xs font-bold text-[#D4AF37]">
              Ψ
            </div>
            <span className="font-mono text-xs font-bold tracking-wider text-white">
              AICF<span className="text-[#D4AF37]">.CONSOLE</span>
            </span>
          </div>

          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg border border-[#2B2F3D] bg-[#191C24] p-2 text-xs text-[#F3E5AB] focus:outline-none"
            aria-label="Toggle Navigation Drawer"
          >
            {mobileMenuOpen ? "✕ Close" : "☰ Menu"}
          </button>
        </div>

        {/* Sidebar Container */}
        <aside
          className={`${
            mobileMenuOpen ? "block" : "hidden"
          } md:block md:w-64 shrink-0 border-r border-[#2B2F3D] bg-[#12141A]/95 p-4 flex flex-col justify-between`}
        >
          <div>
            {/* Sidebar Brand Header */}
            <div className="hidden md:flex items-center gap-3 pb-6 border-b border-[#2B2F3D]">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#D4AF37]/50 bg-[#191C24] shadow-[0_0_12px_rgba(212,175,55,0.2)]">
                <span className="font-mono text-sm font-bold text-[#D4AF37]">Ψ</span>
              </div>
              <div className="flex flex-col">
                <span className="font-mono text-sm font-bold tracking-wider text-white">
                  AICF<span className="text-[#D4AF37]">.INTEL</span>
                </span>
                <span className="text-[10px] tracking-widest text-[#9FA6B2] uppercase">
                  Analyst Console
                </span>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="mt-6 space-y-1.5">
              <span className="block px-3 text-[10px] font-mono tracking-widest text-[#6B7280] uppercase">
                Forensics Navigation
              </span>
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center justify-between rounded-lg px-3 py-2.5 text-xs font-medium transition-all ${
                      isActive
                        ? "border border-[#D4AF37]/40 bg-[#191C24] text-[#F3E5AB] shadow-[0_0_12px_rgba(212,175,55,0.15)]"
                        : "text-[#9FA6B2] hover:bg-[#191C24]/60 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-[#D4AF37]">{item.icon}</span>
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className="rounded bg-[#0B0C10] px-1.5 py-0.5 font-mono text-[9px] text-[#6B7280] border border-[#2B2F3D]">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer: Analyst Profile & Logout */}
          <div className="mt-8 border-t border-[#2B2F3D] pt-4">
            <div className="rounded-lg border border-[#2B2F3D] bg-[#191C24]/80 p-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-[#F3E5AB] truncate max-w-[120px]">
                  {user?.username}
                </span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[9px] font-mono text-emerald-400">
                  ONLINE
                </span>
              </div>
              <p className="mt-1 text-[10px] text-[#6B7280] truncate">{user?.email}</p>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-red-500/40 bg-red-500/10 py-2 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/20"
            >
              <span>Sign Out</span>
            </button>
          </div>
        </aside>

        {/* Main Content Workspace */}
        <div className="flex-1 overflow-x-hidden p-4 sm:p-6 lg:p-8 forensic-grid">
          {children}
        </div>
      </div>
    </AuthGuard>
  );
}
