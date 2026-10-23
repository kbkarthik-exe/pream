"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { reportsApi, type ForensicReport } from "@/lib/api";

type ModalityFilter = "all" | "text" | "image" | "video" | "audio";

export default function ReportsPage() {
  const [reports, setReports] = useState<ForensicReport[]>([]);
  const [filter, setFilter] = useState<ModalityFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New report creation modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newMediaType, setNewMediaType] = useState<"text" | "image" | "video" | "audio">("text");
  const [newSummary, setNewSummary] = useState("");
  const [newIsPrivate, setNewIsPrivate] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

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

  const getModalityBadge = (type: string) => {
    const badges: Record<string, { label: string; color: string; border: string }> = {
      text: { label: "TEXT", color: "text-amber-400", border: "border-amber-400/30" },
      image: { label: "IMAGE", color: "text-cyan-400", border: "border-cyan-400/30" },
      video: { label: "VIDEO", color: "text-purple-400", border: "border-purple-400/30" },
      audio: { label: "AUDIO", color: "text-emerald-400", border: "border-emerald-400/30" },
    };
    const config = badges[type] || { label: type.toUpperCase(), color: "text-gray-400", border: "border-gray-500/30" };
    return (
      <span className={`rounded border px-2 py-0.5 font-mono text-[10px] font-semibold ${config.color} ${config.border} bg-[#191C24]`}>
        {config.label}
      </span>
    );
  };



  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D4AF37]">FORENSIC ARCHIVE</span>
            <span className="text-[#6B7280]">&bull;</span>
            <span className="text-xs text-[#9FA6B2]">PostgreSQL Evidence Log</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            Forensic Case Reports
          </h1>
          <p className="mt-1 text-xs text-[#9FA6B2]">
            Complete chronological audit trail of all registered content analyses and verification records.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-4 py-2 text-xs font-semibold text-black transition-opacity hover:opacity-95"
          >
            + Record New Case
          </button>
          <Link
            href="/dashboard"
            className="rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3.5 py-2 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37]"
          >
            &larr; Overview
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#2B2F3D] pb-3">
        {(["all", "text", "image", "video", "audio"] as ModalityFilter[]).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setFilter(tab)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === tab
                ? "border border-[#D4AF37] bg-[#191C24] text-[#D4AF37]"
                : "border border-transparent text-[#9FA6B2] hover:text-white hover:bg-[#191C24]/50"
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)} {tab === "all" ? `(${reports.length})` : ""}
          </button>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/20 p-4 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Reports Table / List */}
      <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 overflow-hidden">
        <div className="p-4 border-b border-[#2B2F3D] flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Database Records</h2>
          <span className="font-mono text-xs text-[#9FA6B2]">
            Total Found: <span className="text-[#D4AF37] font-bold">{reports.length}</span>
          </span>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-xs text-[#9FA6B2]">
            <div className="mx-auto mb-2 h-5 w-5 animate-spin rounded-full border-2 border-[#D4AF37] border-t-transparent"></div>
            Querying PostgreSQL forensic ledger...
          </div>
        ) : reports.length === 0 ? (
          <div className="p-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-[#2B2F3D] bg-[#191C24] text-xl text-[#6B7280]">
              ∅
            </div>
            <h3 className="mt-3 text-sm font-medium text-white">No forensic records found</h3>
            <p className="mt-1 text-xs text-[#9FA6B2]">
              {filter === "all"
                ? "No investigation cases have been committed to the database yet. Run an analysis module or record a new case."
                : `No records exist under the ${filter} modality.`}
            </p>
            <div className="mt-4 flex justify-center gap-3">
              <Link
                href={`/dashboard/${filter === "all" ? "text" : filter}`}
                className="rounded-lg border border-[#D4AF37]/50 bg-[#191C24] px-4 py-2 text-xs font-semibold text-[#D4AF37] hover:border-[#D4AF37]"
              >
                Go to Detection Module
              </Link>
              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                className="rounded-lg border border-[#2B2F3D] bg-[#12141A] px-4 py-2 text-xs text-white hover:border-[#6B7280]"
              >
                + Record Case
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[#2B2F3D] bg-[#191C24]/60 font-mono text-[11px] text-[#9FA6B2]">
                <tr>
                  <th className="py-3 px-4">CASE ID</th>
                  <th className="py-3 px-4">MODALITY</th>
                  <th className="py-3 px-4">INVESTIGATION TITLE</th>
                  <th className="py-3 px-4">STATUS</th>
                  <th className="py-3 px-4">ACCESS</th>
                  <th className="py-3 px-4">TIMESTAMP (UTC)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2B2F3D]/60 text-[#D1D5DB]">
                {reports.map((r) => (
                  <tr key={r.id} className="hover:bg-[#191C24]/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-[11px] text-[#6B7280]">
                      #{r.id}
                    </td>
                    <td className="py-3.5 px-4">
                      {getModalityBadge(r.media_type)}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-white">{r.title}</div>
                      {r.summary && (
                        <div className="mt-0.5 line-clamp-1 text-[11px] text-[#9FA6B2]">
                          {r.summary}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="rounded border border-emerald-500/30 bg-emerald-950/40 px-2 py-0.5 font-mono text-[10px] text-emerald-400">
                        VERIFIED
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-[#9FA6B2]">
                      {r.is_private ? "Confidential" : "Public"}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-[#6B7280]">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Record Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-[#2B2F3D] bg-[#12141A] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-3">
              <h2 className="text-sm font-bold text-white">Record Investigation Case</h2>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-[#9FA6B2] hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateReport} className="mt-4 space-y-4">
              {createError && (
                <div className="rounded-lg border border-rose-500/40 bg-rose-950/20 p-2.5 text-xs text-rose-300">
                  {createError}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-[#9FA6B2]">Case Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Audit of Statement #402"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3 py-2 text-xs text-white focus:border-[#D4AF37] focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#9FA6B2]">Modality</label>
                <select
                  value={newMediaType}
                  onChange={(e) => setNewMediaType(e.target.value as "text" | "image" | "video" | "audio")}
                  className="mt-1.5 w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3 py-2 text-xs text-white focus:border-[#D4AF37] focus:outline-hidden"
                >
                  <option value="text">AI Text</option>
                  <option value="image">AI Image</option>
                  <option value="video">AI Video</option>
                  <option value="audio">AI Audio</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#9FA6B2]">Summary / Forensics Log</label>
                <textarea
                  rows={3}
                  placeholder="Brief description of the evidence or rationale..."
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  className="mt-1.5 w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3 py-2 text-xs text-white focus:border-[#D4AF37] focus:outline-hidden"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="modalPrivate"
                  checked={newIsPrivate}
                  onChange={(e) => setNewIsPrivate(e.target.checked)}
                  className="rounded border-[#2B2F3D] bg-[#191C24] text-[#D4AF37] focus:ring-0"
                />
                <label htmlFor="modalPrivate" className="text-xs text-[#9FA6B2]">
                  Mark as confidential / private case
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#2B2F3D]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-[#2B2F3D] px-3.5 py-1.5 text-xs text-[#9FA6B2] hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-4 py-1.5 text-xs font-semibold text-black transition-opacity hover:opacity-95 disabled:opacity-50"
                >
                  {isSubmitting ? "Saving..." : "Commit Case"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
