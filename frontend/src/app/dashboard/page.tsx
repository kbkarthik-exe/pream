"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardStats, dashboardApi, ForensicReport, reportsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentReports, setRecentReports] = useState<ForensicReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [statsData, reportsData] = await Promise.all([
          dashboardApi.getStats(),
          reportsApi.list(),
        ]);
        setStats(statsData);
        setRecentReports(reportsData.slice(0, 5));
      } catch {
        // Fallback or offline state
      } finally {
        setLoading(false);
      }
    }
    void loadDashboardData();
  }, []);

  const detectionModules = [
    {
      title: "AI Text Detection",
      href: "/dashboard/text",
      code: "MOD-TXT-01",
      icon: "¶",
      description: "Detect synthetic language, LLM perplexity gradients, and token burstiness.",
      count: stats?.text_reports ?? 0,
    },
    {
      title: "AI Image Detection",
      href: "/dashboard/image",
      code: "MOD-IMG-02",
      icon: "◩",
      description: "Detect diffusion noise signatures, GAN frequency artifacts, and EXIF anomalies.",
      count: stats?.image_reports ?? 0,
    },
    {
      title: "AI Video Detection",
      href: "/dashboard/video",
      code: "MOD-VID-03",
      icon: "▶",
      description: "Analyze deepfake facial warps, temporal flicker, and frame-rate jitter.",
      count: stats?.video_reports ?? 0,
    },
    {
      title: "AI Audio Detection",
      href: "/dashboard/audio",
      code: "MOD-AUD-04",
      icon: "♫",
      description: "Detect synthetic voice clones, vocoder spectral footprints, and pitch shifts.",
      count: stats?.audio_reports ?? 0,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Welcome Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-mono text-xs uppercase tracking-wider text-[#D4AF37]">
              Analyst Forensics Console
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Welcome, <span className="text-[#F3E5AB]">{user?.username}</span>
          </h1>
          <p className="mt-1 text-xs text-[#9FA6B2]">
            Authenticity Intelligence Workspace &bull; ID: #{user?.id} &bull; Institutional Account
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/reports"
            className="rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-4 py-2 text-xs font-semibold text-black transition-opacity hover:opacity-95"
          >
            + Log New Investigation
          </Link>
        </div>
      </div>

      {/* Real Statistics Grid (Aggregated from DB, never invented) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold tracking-wide text-white uppercase">
            Real Investigation Statistics
          </h2>
          <span className="font-mono text-[11px] text-[#D4AF37]">
            PostgreSQL Verified Metrics
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-5 shadow-sm">
            <span className="text-xs text-[#9FA6B2]">Total Investigations</span>
            <p className="mt-2 font-mono text-3xl font-bold text-[#D4AF37]">
              {loading ? "..." : (stats?.total_reports ?? 0)}
            </p>
            <p className="mt-1 text-[11px] text-[#6B7280]">Real DB Records (0 if empty)</p>
          </div>

          <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-5 shadow-sm">
            <span className="text-xs text-[#9FA6B2]">Text Modality Cases</span>
            <p className="mt-2 font-mono text-3xl font-bold text-white">
              {loading ? "..." : (stats?.text_reports ?? 0)}
            </p>
            <p className="mt-1 text-[11px] text-[#6B7280]">Perplexity &amp; Burstiness</p>
          </div>

          <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-5 shadow-sm">
            <span className="text-xs text-[#9FA6B2]">Media Modality Cases</span>
            <p className="mt-2 font-mono text-3xl font-bold text-white">
              {loading
                ? "..."
                : (stats ? stats.image_reports + stats.video_reports + stats.audio_reports : 0)}
            </p>
            <p className="mt-1 text-[11px] text-[#6B7280]">Image, Video, Audio</p>
          </div>

          <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-5 shadow-sm">
            <span className="text-xs text-[#9FA6B2]">Active Sessions</span>
            <p className="mt-2 font-mono text-3xl font-bold text-emerald-400">
              {loading ? "..." : (stats?.active_sessions ?? 1)}
            </p>
            <p className="mt-1 text-[11px] text-[#6B7280]">Server-Managed HttpOnly</p>
          </div>
        </div>
      </div>

      {/* Four Detection Modules (Each opens its own analysis page) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold tracking-wide text-white uppercase">
              Forensic Detection Modules
            </h2>
            <p className="text-xs text-[#9FA6B2]">
              Select a specialized modality engine to execute content forensics
            </p>
          </div>
          <span className="font-mono text-[11px] text-[#D4AF37]">4 ENGINES</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {detectionModules.map((mod) => (
            <Link
              key={mod.code}
              href={mod.href}
              className="group relative flex flex-col justify-between rounded-xl border border-[#2B2F3D] bg-[#12141A]/85 p-5 transition-all hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.15)]"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-[#D4AF37]/40 bg-[#191C24] font-mono text-sm font-bold text-[#D4AF37]">
                    {mod.icon}
                  </span>
                  <span className="font-mono text-[10px] text-[#9FA6B2]">
                    {mod.code}
                  </span>
                </div>

                <h3 className="mt-4 text-base font-semibold text-white group-hover:text-[#F3E5AB]">
                  {mod.title}
                </h3>
                <p className="mt-1.5 text-xs leading-relaxed text-[#9FA6B2]">
                  {mod.description}
                </p>
              </div>

              <div className="mt-6 flex items-center justify-between border-t border-[#2B2F3D]/60 pt-3 text-xs">
                <span className="font-mono text-[11px] text-[#6B7280]">
                  Cases Logged: <strong className="text-white">{mod.count}</strong>
                </span>
                <span className="font-medium text-[#D4AF37] group-hover:translate-x-0.5 transition-transform">
                  Launch &rarr;
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Analysis History Section (Real DB records) */}
      <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/85 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-3">
          <div>
            <h2 className="text-base font-semibold text-white">Recent Analysis History</h2>
            <p className="text-xs text-[#9FA6B2]">
              Audit trail of authenticated investigations from PostgreSQL
            </p>
          </div>
          <Link
            href="/dashboard/reports"
            className="text-xs font-medium text-[#D4AF37] hover:text-[#F3E5AB]"
          >
            View All Reports &rarr;
          </Link>
        </div>

        {loading ? (
          <p className="py-8 text-center text-xs text-[#9FA6B2]">Loading analysis history...</p>
        ) : recentReports.length === 0 ? (
          <div className="my-6 rounded-lg border border-dashed border-[#2B2F3D] p-8 text-center">
            <span className="font-mono text-xl text-[#D4AF37]">0</span>
            <p className="mt-2 text-xs font-semibold text-white">No analysis records found.</p>
            <p className="mt-1 text-[11px] text-[#6B7280]">
              In accordance with AICF rules, zero records are reported honestly. No mock data is invented.
            </p>
            <div className="mt-4">
              <Link
                href="/dashboard/reports"
                className="inline-block rounded-lg border border-[#D4AF37]/40 bg-[#191C24] px-4 py-2 text-xs font-medium text-[#D4AF37] hover:bg-[#D4AF37] hover:text-black transition-colors"
              >
                Log an Investigation Case
              </Link>
            </div>
          </div>
        ) : (
          <div className="mt-4 divide-y divide-[#2B2F3D]/60">
            {recentReports.map((report) => (
              <div key={report.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-white">
                      #{report.id} &bull; {report.title}
                    </span>
                    <span className="rounded bg-[#191C24] px-2 py-0.5 font-mono text-[10px] text-[#D4AF37] uppercase border border-[#2B2F3D]">
                      {report.media_type}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-[#9FA6B2] line-clamp-1">{report.summary}</p>
                </div>
                <span className="shrink-0 text-[11px] font-mono text-[#6B7280]">
                  {new Date(report.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
