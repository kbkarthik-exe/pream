"use client";

import React, { useEffect, useState, useCallback } from "react";
import { reportsApi, type ForensicReport } from "@/lib/api";
import {
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Film,
  Download,
  Plus,
  Search,
  Lock,
  Globe,
  X,
  AlertTriangle,
} from "lucide-react";

type ModalityFilter = "all" | "text" | "image" | "video";

export default function ReportsPage() {
  const [reports, setReports] = useState<ForensicReport[]>([]);
  const [filter, setFilter] = useState<ModalityFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  // New report creation modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newMediaType, setNewMediaType] = useState<"text" | "image" | "video">("text");
  const [newSummary, setNewSummary] = useState("");
  const [newIsPrivate, setNewIsPrivate] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const handleDownloadPdf = async (reportId: number) => {
    setDownloadingId(reportId);
    setError(null);
    try {
      await reportsApi.downloadPdf(reportId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to download PDF report.";
      setError(msg);
    } finally {
      setDownloadingId(null);
    }
  };

  const refreshReports = useCallback(async () => {
    try {
      const data = await reportsApi.list(filter === "all" ? undefined : filter);
      setReports(data);
    } catch {
      setError("Failed to fetch forensic records from the database. Please verify your connection.");
    }
  }, [filter]);

  useEffect(() => {
    let isMounted = true;
    async function fetchReports() {
      try {
        const data = await reportsApi.list(filter === "all" ? undefined : filter);
        if (isMounted) {
          setReports(data);
        }
      } catch {
        if (isMounted) {
          setError("Failed to fetch forensic records from the database. Please verify your connection.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }
    void fetchReports();
    return () => {
      isMounted = false;
    };
  }, [filter]);

  const handleCreateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      setCreateError("Case title is required.");
      return;
    }
    setIsSubmitting(true);
    setCreateError(null);
    try {
      await reportsApi.create({
        title: newTitle.trim(),
        media_type: newMediaType,
        summary: newSummary.trim() || "Manual forensic investigation entry.",
        is_private: newIsPrivate,
      });
      setShowCreateModal(false);
      setNewTitle("");
      setNewSummary("");
      await refreshReports();
    } catch {
      setCreateError("Failed to record forensic case in database.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getModalityIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "text":
        return <FileText className="h-3.5 w-3.5 text-amber-400" />;
      case "image":
        return <ImageIcon className="h-3.5 w-3.5 text-sky-400" />;
      case "video":
        return <Film className="h-3.5 w-3.5 text-purple-400" />;
      default:
        return <FileSpreadsheet className="h-3.5 w-3.5 text-[#D6B15E]" />;
    }
  };

  // Filter reports by search query (title and summary)
  const filteredReports = reports.filter((report) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      report.title.toLowerCase().includes(query) ||
      report.summary.toLowerCase().includes(query) ||
      `#${report.id}`.includes(query)
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D6B15E] font-bold">CASE ARCHIVE</span>
            <span className="text-[#3A404D]">&bull;</span>
            <span className="text-xs text-[#A3A7B0]">Authenticated Forensic Ledger</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#F5F5F2]">
            Forensic Case Reports
          </h1>
          <p className="mt-1 text-xs text-[#A3A7B0]">
            Review authenticated forensic investigations, inspect evidentiary summaries, and download signed ReportLab PDF certificates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-4 py-2 font-mono text-xs font-bold text-[#090A0D] shadow-[0_0_15px_rgba(214,177,94,0.2)] hover:opacity-95 transition-opacity cursor-pointer"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Log Investigation Case</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-3.5 text-xs text-red-300 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          {/* Modality Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
            {(["all", "text", "image", "video"] as ModalityFilter[]).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setFilter(tab)}
                className={`rounded-lg px-3 py-1.5 transition-all cursor-pointer capitalize font-semibold ${
                  filter === tab
                    ? "border border-[#D6B15E]/40 bg-[#181C23] text-[#F0D58A] shadow-[0_0_10px_rgba(214,177,94,0.1)]"
                    : "text-[#737984] hover:text-[#F5F5F2] hover:bg-[#181C23]/60"
                }`}
              >
                {tab === "all" ? "All Modalities" : tab}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#737984]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by title or case #..."
              className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] pl-9 pr-3.5 py-1.5 text-xs text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden font-mono"
            />
          </div>
        </div>
      </div>

      {/* Reports Table Container */}
      <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-6 shadow-sm">
        {isLoading ? (
          <div className="py-16 text-center text-xs text-[#737984] font-mono">
            Loading investigation records...
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="py-16 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-[#292D35] bg-[#181C23] text-[#737984]">
              <FileSpreadsheet className="h-6 w-6" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-[#F5F5F2]">No matching cases found</h3>
            <p className="mt-1 text-xs text-[#737984] max-w-sm mx-auto">
              {searchQuery
                ? `No records match the filter query "${searchQuery}".`
                : "No forensic investigations logged for this modality filter yet."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#292D35] text-[11px] font-mono text-[#737984]">
                  <th className="pb-3 font-semibold">CASE REF</th>
                  <th className="pb-3 font-semibold">MODALITY</th>
                  <th className="pb-3 font-semibold">INVESTIGATION TITLE &amp; FINDINGS</th>
                  <th className="pb-3 font-semibold">PRIVACY</th>
                  <th className="pb-3 font-semibold">TIMESTAMP</th>
                  <th className="pb-3 font-semibold text-right">AUDIT REPORT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#292D35]">
                {filteredReports.map((report) => (
                  <tr key={report.id} className="hover:bg-[#181C23]/60 transition-colors">
                    <td className="py-3.5 font-mono font-medium text-[#F0D58A]">
                      #{report.id}
                    </td>
                    <td className="py-3.5">
                      <span className="inline-flex items-center gap-1.5 rounded-md border border-[#292D35] bg-[#181C23] px-2.5 py-1 font-mono text-[10px] text-[#F5F5F2] uppercase">
                        {getModalityIcon(report.media_type)}
                        {report.media_type}
                      </span>
                    </td>
                    <td className="py-3.5 max-w-lg">
                      <div className="font-semibold text-[#F5F5F2] truncate">{report.title}</div>
                      <div className="text-[11px] text-[#A3A7B0] line-clamp-1">{report.summary}</div>
                    </td>
                    <td className="py-3.5">
                      {report.is_private ? (
                        <span className="inline-flex items-center gap-1 rounded-md border border-[#292D35] bg-[#090A0D] px-2 py-0.5 font-mono text-[10px] text-[#737984]">
                          <Lock className="h-2.5 w-2.5 text-[#D6B15E]" />
                          Private
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-md border border-[#292D35] bg-[#090A0D] px-2 py-0.5 font-mono text-[10px] text-emerald-400">
                          <Globe className="h-2.5 w-2.5" />
                          Institutional
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 font-mono text-[11px] text-[#737984] whitespace-nowrap">
                      {new Date(report.created_at).toLocaleString([], {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3.5 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => handleDownloadPdf(report.id)}
                        disabled={downloadingId === report.id}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[#D6B15E]/40 bg-[#D6B15E]/10 px-3 py-1.5 font-mono text-[11px] font-semibold text-[#D6B15E] hover:bg-[#D6B15E]/20 disabled:opacity-50 transition-all cursor-pointer"
                        title="Download official PDF report certificate"
                      >
                        {downloadingId === report.id ? (
                          <>
                            <span className="h-3 w-3 animate-spin rounded-full border-2 border-[#D6B15E] border-t-transparent" />
                            <span>Generating...</span>
                          </>
                        ) : (
                          <>
                            <Download className="h-3.5 w-3.5" />
                            <span>Download PDF</span>
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Manual Case Entry Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl border border-[#292D35] bg-[#12151B] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#292D35] pb-4">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-[#D6B15E]" />
                <h3 className="text-sm font-bold text-[#F5F5F2] uppercase font-mono">
                  Log New Investigation Case
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="rounded-lg p-1 text-[#737984] hover:text-[#F5F5F2] transition-colors cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateReport} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-mono text-[#A3A7B0] uppercase">
                  Investigation Title *
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Audit Case: Suspected GAN Synthetic Portrait"
                  className="mt-1.5 w-full rounded-xl border border-[#292D35] bg-[#090A0D] px-3.5 py-2 text-xs text-[#F5F5F2] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-[#A3A7B0] uppercase">
                  Modality Engine
                </label>
                <select
                  value={newMediaType}
                  onChange={(e) =>
                    setNewMediaType(e.target.value as "text" | "image" | "video")
                  }
                  className="mt-1.5 w-full rounded-xl border border-[#292D35] bg-[#090A0D] px-3.5 py-2 text-xs text-[#F5F5F2] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                >
                  <option value="text">Text (MOD-TXT-01)</option>
                  <option value="image">Image (MOD-IMG-02)</option>
                  <option value="video">Video (MOD-VID-03)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-[#A3A7B0] uppercase">
                  Findings Summary
                </label>
                <textarea
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  placeholder="Summarize forensic findings, spectral anomalies, or contextual corroboration..."
                  rows={4}
                  className="mt-1.5 w-full rounded-xl border border-[#292D35] bg-[#090A0D] p-3 text-xs text-[#F5F5F2] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="modalIsPrivate"
                  checked={newIsPrivate}
                  onChange={(e) => setNewIsPrivate(e.target.checked)}
                  className="rounded border-[#292D35] bg-[#181C23] text-[#D6B15E] focus:ring-[#D6B15E]"
                />
                <label htmlFor="modalIsPrivate" className="text-xs text-[#A3A7B0] cursor-pointer">
                  Confidential case (Scoped strictly to this analyst ID)
                </label>
              </div>

              {createError && (
                <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-2.5 text-xs text-red-300">
                  {createError}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 border-t border-[#292D35] pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-[#292D35] bg-[#181C23] px-4 py-2 text-xs font-mono text-[#A3A7B0] hover:text-[#F5F5F2] transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-5 py-2 font-mono text-xs font-bold text-[#090A0D] hover:opacity-95 disabled:opacity-50 transition-opacity cursor-pointer"
                >
                  {isSubmitting ? "Saving Case..." : "Record in Database"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
