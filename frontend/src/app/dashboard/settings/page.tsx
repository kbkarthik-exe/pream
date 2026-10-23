"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { authApi } from "@/lib/api";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    setStatusMessage(null);

    try {
      await authApi.updateProfile({
        full_name: fullName.trim() || undefined,
        current_password: currentPassword || undefined,
        new_password: newPassword || undefined,
      });

      await refreshUser();
      setStatusMessage({ type: "success", text: "Analyst profile and credentials updated successfully." });
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update profile settings.";
      setStatusMessage({ type: "error", text: msg });
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D4AF37]">SYSTEM CONFIGURATION</span>
            <span className="text-[#6B7280]">&bull;</span>
            <span className="text-xs text-[#9FA6B2]">Analyst Identity &amp; Platform Security</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            Settings &amp; Account Profile
          </h1>
          <p className="mt-1 text-xs text-[#9FA6B2]">
            Manage your forensic analyst credentials, examine cryptographic session security, and update investigator details.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="self-start sm:self-auto rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3.5 py-1.5 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37]"
        >
          &larr; Back to Overview
        </Link>
      </div>

      {statusMessage && (
        <div
          className={`rounded-lg p-3.5 text-xs border ${
            statusMessage.type === "success"
              ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-300"
              : "border-rose-500/40 bg-rose-950/20 text-rose-300"
          }`}
        >
          {statusMessage.text}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Profile Card */}
        <div className="lg:col-span-1 rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-6 space-y-5">
          <div className="flex items-center gap-3 border-b border-[#2B2F3D] pb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full border border-[#D4AF37]/50 bg-[#191C24] font-mono text-lg font-bold text-[#D4AF37]">
              {user?.username?.charAt(0).toUpperCase() || "A"}
            </div>
            <div>
              <div className="text-sm font-semibold text-white">{user?.full_name || user?.username}</div>
              <div className="text-xs text-[#9FA6B2]">@{user?.username}</div>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[11px] text-[#6B7280] block font-mono">ANALYST ID</span>
              <span className="font-mono text-white">#{user?.id ?? "—"}</span>
            </div>
            <div>
              <span className="text-[11px] text-[#6B7280] block font-mono">EMAIL ADDRESS</span>
              <span className="text-white">{user?.email || "—"}</span>
            </div>
            <div>
              <span className="text-[11px] text-[#6B7280] block font-mono">ACCOUNT STATUS</span>
              <span className="inline-flex items-center gap-1.5 text-emerald-400 font-mono text-[11px]">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                ACTIVE INVESTIGATOR
              </span>
            </div>
            <div>
              <span className="text-[11px] text-[#6B7280] block font-mono">AUTHENTICATION METHOD</span>
              <span className="font-mono text-[11px] text-[#D4AF37]">Argon2id + SHA-256 Cookie</span>
            </div>
          </div>
        </div>

        {/* Update Form */}
        <div className="lg:col-span-2 rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-6">
          <h2 className="text-sm font-bold text-white border-b border-[#2B2F3D] pb-3">
            Analyst Identity Information
          </h2>

          <form onSubmit={handleUpdateProfile} className="mt-5 space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#9FA6B2]">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Forensic Analyst Name"
                className="mt-1.5 w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2 text-xs text-white focus:border-[#D4AF37] focus:outline-hidden"
              />
            </div>

            <div className="pt-2 border-t border-[#2B2F3D]">
              <h3 className="text-xs font-semibold text-white">Update Password (Optional)</h3>
              <p className="text-[11px] text-[#6B7280] mt-0.5">
                Leave blank if you do not want to modify your credentials.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-[#9FA6B2]">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="mt-1.5 w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2 text-xs text-white focus:border-[#D4AF37] focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#9FA6B2]">New Password (min 10 chars)</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="mt-1.5 w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2 text-xs text-white focus:border-[#D4AF37] focus:outline-hidden"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-[#2B2F3D] flex justify-end">
              <button
                type="submit"
                disabled={isUpdating}
                className="rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-5 py-2 text-xs font-semibold text-black transition-opacity hover:opacity-95 disabled:opacity-50"
              >
                {isUpdating ? "Saving Changes..." : "Save Profile Settings"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Security Architecture Ledger */}
      <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-6">
        <h2 className="text-sm font-bold text-white border-b border-[#2B2F3D] pb-3">
          Security &amp; Forensic Integrity Standard
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3 text-xs">
          <div className="rounded-lg border border-[#2B2F3D] bg-[#191C24]/60 p-4">
            <span className="font-mono text-[10px] text-[#D4AF37]">SEC-01</span>
            <div className="mt-1 font-semibold text-white">Argon2id Hashing</div>
            <p className="mt-1 text-[11px] text-[#9FA6B2]">
              Password verification runs on memory-hard Argon2id configured to defeat ASIC/GPU attacks.
            </p>
          </div>

          <div className="rounded-lg border border-[#2B2F3D] bg-[#191C24]/60 p-4">
            <span className="font-mono text-[10px] text-[#D4AF37]">SEC-02</span>
            <div className="mt-1 font-semibold text-white">SHA-256 Session Vault</div>
            <p className="mt-1 text-[11px] text-[#9FA6B2]">
              Session tokens are never stored in raw form in the database; only cryptographic hashes are stored.
            </p>
          </div>

          <div className="rounded-lg border border-[#2B2F3D] bg-[#191C24]/60 p-4">
            <span className="font-mono text-[10px] text-[#D4AF37]">SEC-03</span>
            <div className="mt-1 font-semibold text-white">In-Memory Token Bucket</div>
            <p className="mt-1 text-[11px] text-[#9FA6B2]">
              Registration and login endpoints are shielded by dual IP and username rate limiters.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
