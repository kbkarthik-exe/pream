"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/lib/auth-context";
import {
  ShieldCheck,
  LayoutDashboard,
  FileText,
  Image as ImageIcon,
  Film,
  FileSpreadsheet,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Activity,
  ChevronLeft,
  UserCheck,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeColor?: string;
}

const navItems: NavItem[] = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Text Forensics", href: "/dashboard/text", icon: FileText, badge: "VERIFIED", badgeColor: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  { name: "Image Forensics", href: "/dashboard/image", icon: ImageIcon, badge: "VERIFIED", badgeColor: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  { name: "Video Forensics", href: "/dashboard/video", icon: Film, badge: "PARTIAL", badgeColor: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
  { name: "Case Reports", href: "/dashboard/reports", icon: FileSpreadsheet },
  { name: "Model Evaluation", href: "/dashboard/evaluation", icon: BarChart3, badge: "BENCH", badgeColor: "text-[#D6B15E] border-[#D6B15E]/30 bg-[#D6B15E]/10" },
  { name: "Settings & Security", href: "/dashboard/settings", icon: Settings },
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
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  // Resolve current page title and breadcrumb
  const currentNav = navItems.find((item) => item.href === pathname) || {
    name: "Forensic Workspace",
  };

  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden bg-[#090A0D] text-[#F5F5F2]">
        {/* Mobile Backdrop */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/80 backdrop-blur-xs md:hidden"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Sidebar */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex flex-col justify-between border-r border-[#292D35] bg-[#0D0F13] transition-all duration-300 md:static md:translate-x-0 ${
            mobileMenuOpen ? "translate-x-0 w-64" : "-translate-x-full md:translate-x-0"
          } ${isCollapsed ? "md:w-20" : "md:w-64"}`}
        >
          {/* Sidebar Header */}
          <div>
            <div className="flex h-16 items-center justify-between border-b border-[#292D35] px-4">
              <Link
                href="/dashboard"
                className="flex items-center gap-3 overflow-hidden group focus:outline-hidden"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[#D6B15E]/40 bg-[#12151B] shadow-[0_0_12px_rgba(214,177,94,0.15)] group-hover:border-[#D6B15E] transition-all">
                  <ShieldCheck className="h-5 w-5 text-[#D6B15E]" />
                </div>
                {!isCollapsed && (
                  <div className="flex flex-col truncate">
                    <span className="font-mono text-sm font-bold tracking-wider text-[#F5F5F2]">
                      AICF<span className="text-[#D6B15E]">.INTEL</span>
                    </span>
                    <span className="text-[10px] tracking-widest text-[#737984] uppercase">
                      Forensic Console
                    </span>
                  </div>
                )}
              </Link>

              {/* Mobile Close Button */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="rounded-lg p-1.5 text-[#A3A7B0] hover:bg-[#181C23] hover:text-[#F5F5F2] md:hidden cursor-pointer"
                aria-label="Close navigation"
              >
                <X className="h-5 w-5" />
              </button>

              {/* Desktop Collapse Toggle */}
              <button
                type="button"
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="hidden rounded-lg p-1.5 text-[#737984] hover:bg-[#181C23] hover:text-[#F5F5F2] md:flex cursor-pointer transition-colors"
                title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
              </button>
            </div>

            {/* Navigation Section */}
            <nav className="mt-4 space-y-1 px-3">
              {!isCollapsed && (
                <div className="px-3 pb-2 pt-1 font-mono text-[10px] font-semibold tracking-wider text-[#737984] uppercase">
                  Forensic Modules
                </div>
              )}
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    title={isCollapsed ? item.name : undefined}
                    className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs transition-all ${
                      isActive
                        ? "border border-[#D6B15E]/40 bg-[#181C23] text-[#F0D58A] shadow-[0_0_12px_rgba(214,177,94,0.12)] font-semibold"
                        : "text-[#A3A7B0] hover:bg-[#12151B] hover:text-[#F5F5F2]"
                    } ${isCollapsed ? "justify-center px-0" : ""}`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 transition-colors ${isActive ? "text-[#D6B15E]" : "text-[#737984] group-hover:text-[#A3A7B0]"}`} />
                    {!isCollapsed && (
                      <div className="flex flex-1 items-center justify-between truncate">
                        <span className="truncate">{item.name}</span>
                        {item.badge && (
                          <span
                            className={`rounded px-1.5 py-0.5 font-mono text-[9px] font-bold border ${item.badgeColor || "text-[#737984] border-[#292D35] bg-[#090A0D]"}`}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer: Analyst Profile & Sign Out */}
          <div className="border-t border-[#292D35] p-3">
            {!isCollapsed ? (
              <div className="rounded-xl border border-[#292D35] bg-[#12151B] p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 truncate">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[#D6B15E]/40 bg-[#181C23] font-mono text-xs font-bold text-[#D6B15E]">
                      {user?.username?.charAt(0).toUpperCase() || "A"}
                    </div>
                    <div className="truncate">
                      <div className="font-mono text-xs font-semibold text-[#F0D58A] truncate">
                        {user?.username}
                      </div>
                      <div className="text-[10px] text-[#737984] truncate">
                        {user?.email}
                      </div>
                    </div>
                  </div>
                  <span className="flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(34,197,94,0.8)]" title="Session Active" />
                </div>

                <button
                  type="button"
                  onClick={handleLogout}
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 py-1.5 text-xs font-medium text-red-400 transition-colors hover:border-red-500/50 hover:bg-red-500/20 cursor-pointer"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-[#D6B15E]/40 bg-[#181C23] font-mono text-xs font-bold text-[#D6B15E]"
                  title={`${user?.username} (${user?.email})`}
                >
                  {user?.username?.charAt(0).toUpperCase() || "A"}
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20 cursor-pointer"
                  title="Sign Out"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </aside>

        {/* Main Application Area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Top Integrated Enterprise Header */}
          <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-[#292D35] bg-[#0D0F13]/90 px-4 sm:px-6 backdrop-blur-md">
            {/* Left: Mobile Toggle & Breadcrumb */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(true)}
                className="rounded-lg border border-[#292D35] bg-[#12151B] p-2 text-[#A3A7B0] hover:text-[#F5F5F2] md:hidden cursor-pointer"
                aria-label="Open navigation menu"
              >
                <Menu className="h-5 w-5" />
              </button>

              <div className="flex items-center gap-2 text-xs">
                <span className="font-mono text-[#737984]">AICF</span>
                <span className="text-[#3A404D]">/</span>
                <span className="font-medium text-[#F5F5F2] font-mono">{currentNav.name}</span>
              </div>
            </div>

            {/* Right: Engine Telemetry Status & User Action */}
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="hidden items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400 sm:inline-flex">
                <Activity className="h-3 w-3 animate-pulse" />
                <span className="font-mono text-[11px] font-medium tracking-wide">Inference Engine Active</span>
              </div>

              <div className="flex items-center gap-2 rounded-lg border border-[#292D35] bg-[#12151B] px-3 py-1.5 text-xs text-[#A3A7B0]">
                <UserCheck className="h-3.5 w-3.5 text-[#D6B15E]" />
                <span className="font-mono text-[#F0D58A] hidden sm:inline">{user?.username}</span>
                <span className="font-mono text-[10px] text-[#737984]">#{user?.id}</span>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-500/20 transition-colors cursor-pointer"
                title="End forensic session"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          </header>

          {/* Main Content Workspace */}
          <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 forensic-grid">
            <div className="mx-auto max-w-7xl">
              {children}
            </div>
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
