"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { authApi, cloudApi, CloudProviderStatus } from "@/lib/api";
import {
  ShieldCheck,
  User,
  KeyRound,
  CheckCircle2,
  AlertTriangle,
  Cloud,
  Server,
  Lock,
  RefreshCw,
  ExternalLink,
  Trash2,
  Key,
  Info,
} from "lucide-react";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState<"profile" | "cloud">("profile");

  // Profile state
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Cloud Hub state
  const [providers, setProviders] = useState<CloudProviderStatus[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({});
  const [showKeyInputs, setShowKeyInputs] = useState<Record<string, boolean>>({});
  const [savingProvider, setSavingProvider] = useState<string | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [deletingProvider, setDeletingProvider] = useState<string | null>(null);
  const [cloudMessage, setCloudMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

  const fetchProviders = async () => {
    setLoadingProviders(true);
    try {
      const data = await cloudApi.getProviders();
      setProviders(data);
    } catch {
      // Ignore if unauthenticated or network drop
    } finally {
      setLoadingProviders(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    cloudApi
      .getProviders()
      .then((data) => {
        if (!ignore) {
          setProviders(data);
        }
      })
      .catch(() => {});

    return () => {
      ignore = true;
    };
  }, []);

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

  const handleSaveCredential = async (provider: string) => {
    const rawKey = keyInputs[provider]?.trim();
    if (!rawKey) {
      setCloudMessage({ type: "error", text: `Please enter a valid API key for ${provider}.` });
      return;
    }

    setSavingProvider(provider);
    setCloudMessage(null);
    try {
      const res = await cloudApi.saveCredential(provider, rawKey);
      setCloudMessage({ type: "success", text: res.message || "Credential saved and encrypted in vault." });
      setKeyInputs((prev) => ({ ...prev, [provider]: "" }));
      await fetchProviders();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to store credential.";
      setCloudMessage({ type: "error", text: msg });
    } finally {
      setSavingProvider(null);
    }
  };

  const handleDeleteCredential = async (provider: string) => {
    setDeletingProvider(provider);
    setCloudMessage(null);
    try {
      const res = await cloudApi.deleteCredential(provider);
      setCloudMessage({ type: "info", text: res.message || "Credential removed from vault." });
      await fetchProviders();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete credential.";
      setCloudMessage({ type: "error", text: msg });
    } finally {
      setDeletingProvider(null);
    }
  };

  const handleTestConnection = async (provider: string) => {
    setTestingProvider(provider);
    setCloudMessage(null);
    try {
      const customKey = keyInputs[provider]?.trim() || undefined;
      const res = await cloudApi.testConnection(provider, customKey);
      if (res.success) {
        setCloudMessage({ type: "success", text: `${provider.toUpperCase()}: ${res.message}` });
      } else {
        setCloudMessage({ type: "error", text: `${provider.toUpperCase()}: ${res.message}` });
      }
      await fetchProviders();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection test failed.";
      setCloudMessage({ type: "error", text: msg });
    } finally {
      setTestingProvider(null);
    }
  };

  const configuredCount = providers.filter((p) => p.is_configured).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D6B15E] font-bold">SYSTEM SECURITY</span>
            <span className="text-[#3A404D]">&bull;</span>
            <span className="text-xs text-[#A3A7B0]">Analyst Identity &amp; Cloud Ledger</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#F5F5F2]">
            Settings &amp; Providers
          </h1>
          <p className="mt-1 text-xs text-[#A3A7B0]">
            Manage your investigator profile, session security, and optional third-party cloud verification hubs.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="self-start sm:self-auto rounded-lg border border-[#292D35] bg-[#12151B] px-3.5 py-1.5 text-xs text-[#A3A7B0] hover:border-[#D6B15E] hover:text-[#D6B15E] transition-colors"
        >
          &larr; Overview
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-[#292D35] pb-2">
        <button
          type="button"
          onClick={() => setActiveTab("profile")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 font-mono text-xs font-bold transition-all cursor-pointer ${
            activeTab === "profile"
              ? "border border-[#D6B15E]/50 bg-[#181C23] text-[#F0D58A] shadow-[0_0_12px_rgba(214,177,94,0.1)]"
              : "border border-transparent text-[#737984] hover:text-[#A3A7B0] hover:bg-[#12151B]"
          }`}
        >
          <User className="h-3.5 w-3.5" />
          <span>Analyst Profile &amp; Credentials</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("cloud")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 font-mono text-xs font-bold transition-all cursor-pointer ${
            activeTab === "cloud"
              ? "border border-[#D6B15E]/50 bg-[#181C23] text-[#F0D58A] shadow-[0_0_12px_rgba(214,177,94,0.1)]"
              : "border border-transparent text-[#737984] hover:text-[#A3A7B0] hover:bg-[#12151B]"
          }`}
        >
          <Cloud className="h-3.5 w-3.5" />
          <span>Cloud Verification Hub</span>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-mono ${
              configuredCount > 0
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                : "bg-[#292D35] text-[#A3A7B0]"
            }`}
          >
            {configuredCount} / {providers.length || 3}
          </span>
        </button>
      </div>

      {/* TAB 1: ANALYST PROFILE */}
      {activeTab === "profile" && (
        <div className="space-y-6">
          {statusMessage && (
            <div
              className={`rounded-xl p-3.5 text-xs border flex items-center gap-2.5 ${
                statusMessage.type === "success"
                  ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-300"
                  : "border-rose-500/40 bg-rose-950/20 text-rose-300"
              }`}
            >
              {statusMessage.type === "success" ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
              )}
              <span>{statusMessage.text}</span>
            </div>
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Profile Card */}
            <div className="lg:col-span-4 rounded-2xl border border-[#292D35] bg-[#12151B] p-6 space-y-5 shadow-sm">
              <div className="flex items-center gap-3 border-b border-[#292D35] pb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[#D6B15E]/40 bg-[#181C23] font-mono text-lg font-bold text-[#D6B15E]">
                  {user?.username?.charAt(0).toUpperCase() || "A"}
                </div>
                <div className="truncate">
                  <div className="text-sm font-bold text-[#F5F5F2] truncate">{user?.full_name || user?.username}</div>
                  <div className="text-xs text-[#A3A7B0] font-mono">@{user?.username}</div>
                </div>
              </div>

              <div className="space-y-3.5 text-xs">
                <div>
                  <span className="text-[10px] text-[#737984] block font-mono uppercase">ANALYST ID</span>
                  <span className="font-mono text-[#F5F5F2] font-semibold">#{user?.id ?? "—"}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[#737984] block font-mono uppercase">EMAIL ADDRESS</span>
                  <span className="text-[#F5F5F2] font-mono">{user?.email || "—"}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[#737984] block font-mono uppercase">ACCOUNT STATUS</span>
                  <span className="inline-flex items-center gap-1.5 text-emerald-400 font-mono text-[11px] mt-0.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    ACTIVE INVESTIGATOR
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[#737984] block font-mono uppercase">AUTHENTICATION PROTOCOL</span>
                  <span className="font-mono text-[11px] text-[#F0D58A]">Argon2id + 256-bit SHA-256</span>
                </div>
              </div>
            </div>

            {/* Update Form */}
            <div className="lg:col-span-8 rounded-2xl border border-[#292D35] bg-[#12151B] p-6 shadow-sm">
              <div className="flex items-center gap-2 border-b border-[#292D35] pb-3">
                <User className="h-4 w-4 text-[#D6B15E]" />
                <h2 className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                  Analyst Identity Information
                </h2>
              </div>

              <form onSubmit={handleUpdateProfile} className="mt-5 space-y-4">
                <div>
                  <label className="block text-xs font-mono text-[#A3A7B0] uppercase">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Forensic Analyst Name"
                    className="mt-1.5 w-full rounded-xl border border-[#292D35] bg-[#090A0D] px-3.5 py-2 text-xs text-[#F5F5F2] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                  />
                </div>

                <div className="pt-3 border-t border-[#292D35]">
                  <div className="flex items-center gap-2">
                    <KeyRound className="h-3.5 w-3.5 text-[#D6B15E]" />
                    <h3 className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">Update Password (Optional)</h3>
                  </div>
                  <p className="text-[11px] text-[#737984] mt-0.5">
                    Leave current and new password blank if you do not wish to modify your credentials.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-mono text-[#A3A7B0] uppercase">Current Password</label>
                    <input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="mt-1.5 w-full rounded-xl border border-[#292D35] bg-[#090A0D] px-3.5 py-2 text-xs text-[#F5F5F2] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-[#A3A7B0] uppercase">New Password (min 10 chars)</label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="mt-1.5 w-full rounded-xl border border-[#292D35] bg-[#090A0D] px-3.5 py-2 text-xs text-[#F5F5F2] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-[#292D35] flex justify-end">
                  <button
                    type="submit"
                    disabled={isUpdating}
                    className="rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-5 py-2 font-mono text-xs font-bold text-[#090A0D] shadow-[0_0_12px_rgba(214,177,94,0.15)] hover:opacity-95 disabled:opacity-50 transition-opacity cursor-pointer"
                  >
                    {isUpdating ? "Saving Changes..." : "Save Profile Settings"}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Security Architecture Ledger */}
          <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-6 shadow-sm">
            <div className="flex items-center gap-2 border-b border-[#292D35] pb-3">
              <ShieldCheck className="h-4 w-4 text-[#D6B15E]" />
              <h2 className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                Security &amp; Forensic Integrity Standard
              </h2>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3 text-xs">
              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-4">
                <span className="font-mono text-[10px] text-[#D6B15E] font-bold">SEC-01 &bull; CRYPTOGRAPHY</span>
                <div className="mt-1 font-semibold text-[#F5F5F2]">Argon2id Hashing</div>
                <p className="mt-1 text-[11px] text-[#A3A7B0] leading-relaxed">
                  Password verification runs on memory-hard Argon2id configured with high time and memory costs to defeat GPU attacks.
                </p>
              </div>

              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-4">
                <span className="font-mono text-[10px] text-[#D6B15E] font-bold">SEC-02 &bull; SESSION VAULT</span>
                <div className="mt-1 font-semibold text-[#F5F5F2]">SHA-256 Vault</div>
                <p className="mt-1 text-[11px] text-[#A3A7B0] leading-relaxed">
                  256-bit entropy session tokens are never stored in raw form in the database; only cryptographic hashes are persisted.
                </p>
              </div>

              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-4">
                <span className="font-mono text-[10px] text-[#D6B15E] font-bold">SEC-03 &bull; RATE LIMITING</span>
                <div className="mt-1 font-semibold text-[#F5F5F2]">In-Memory Sliding Window</div>
                <p className="mt-1 text-[11px] text-[#A3A7B0] leading-relaxed">
                  Analyst login and registration endpoints are protected by dual IP and username sliding-window rate limiters.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CLOUD VERIFICATION HUB */}
      {activeTab === "cloud" && (
        <div className="space-y-6">
          {cloudMessage && (
            <div
              className={`rounded-xl p-3.5 text-xs border flex items-center gap-2.5 ${
                cloudMessage.type === "success"
                  ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-300"
                  : cloudMessage.type === "info"
                  ? "border-sky-500/40 bg-sky-950/20 text-sky-300"
                  : "border-rose-500/40 bg-rose-950/20 text-rose-300"
              }`}
            >
              {cloudMessage.type === "success" ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              ) : cloudMessage.type === "info" ? (
                <Info className="h-4 w-4 text-sky-400 shrink-0" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
              )}
              <span>{cloudMessage.text}</span>
            </div>
          )}

          {/* Privacy & Opt-In Governance Notice */}
          <div className="rounded-2xl border border-[#D6B15E]/30 bg-[#181C23] p-5">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-lg border border-[#D6B15E]/40 bg-[#090A0D] p-2 text-[#D6B15E]">
                <Lock className="h-4 w-4" />
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="font-mono font-bold uppercase tracking-wider text-[#F0D58A]">
                  Encrypted Third-Party Vault &amp; Air-Gapped Privacy Guarantee
                </div>
                <p className="text-[#A3A7B0] leading-relaxed">
                  AICF is fundamentally engineered as a <strong>local-first, privacy-preserving forensic platform</strong>. Local transformer models and signal heuristics operate 100% offline at zero cost. Cloud verification integrations are entirely optional and require <strong>explicit per-submission consent</strong>.
                </p>
                <div className="flex flex-wrap items-center gap-4 pt-1 font-mono text-[11px] text-[#737984]">
                  <span>&bull; PBKDF2-HMAC-SHA256 Encrypt-then-MAC</span>
                  <span>&bull; Zero Raw Key Client Leakage</span>
                  <span>&bull; Strict Per-Analyst Isolation</span>
                  <span>&bull; Audio Forensics Permanently Cancelled</span>
                </div>
              </div>
            </div>
          </div>

          {/* Provider Cards */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-[#A3A7B0]">
                Supported Cloud Detectors ({providers.length})
              </h2>
              <button
                type="button"
                onClick={fetchProviders}
                disabled={loadingProviders}
                className="flex items-center gap-1.5 rounded-lg border border-[#292D35] bg-[#12151B] px-3 py-1 font-mono text-[11px] text-[#A3A7B0] hover:text-[#D6B15E] hover:border-[#D6B15E] transition-colors cursor-pointer"
              >
                <RefreshCw className={`h-3 w-3 ${loadingProviders ? "animate-spin text-[#D6B15E]" : ""}`} />
                <span>Refresh Hub</span>
              </button>
            </div>

            <div className="grid grid-cols-1 gap-5">
              {providers.map((p) => {
                const isHive = p.provider === "hive";
                const isGptZero = p.provider === "gptzero";
                const isCopyleaks = p.provider === "copyleaks";
                const isSaving = savingProvider === p.provider;
                const isTesting = testingProvider === p.provider;
                const isDeleting = deletingProvider === p.provider;
                const showInput = showKeyInputs[p.provider] || !p.is_configured;

                return (
                  <div
                    key={p.provider}
                    className="rounded-2xl border border-[#292D35] bg-[#12151B] p-6 shadow-sm transition-all hover:border-[#3A404D]"
                  >
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-[#292D35] pb-4">
                      <div className="flex items-start gap-3">
                        <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-2.5 text-[#D6B15E]">
                          <Server className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2.5">
                            <h3 className="font-mono text-sm font-bold text-[#F5F5F2]">{p.name}</h3>
                            {/* Status Badge */}
                            {p.api_connection_status === "TEST_PASSED" ? (
                              <span className="rounded-md border border-emerald-500/40 bg-emerald-950/40 px-2 py-0.5 font-mono text-[10px] font-bold text-emerald-400">
                                READY / VERIFIED
                              </span>
                            ) : p.is_configured ? (
                              <span className="rounded-md border border-amber-500/40 bg-amber-950/40 px-2 py-0.5 font-mono text-[10px] font-bold text-amber-400">
                                CONFIGURED
                              </span>
                            ) : p.api_connection_status === "TEST_FAILED" ? (
                              <span className="rounded-md border border-rose-500/40 bg-rose-950/40 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-400">
                                CONNECTION ERROR
                              </span>
                            ) : (
                              <span className="rounded-md border border-[#292D35] bg-[#181C23] px-2 py-0.5 font-mono text-[10px] font-bold text-[#737984]">
                                CONFIGURATION REQUIRED
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-xs text-[#A3A7B0]">{p.description}</p>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 self-start">
                        {p.supported_types.map((t) => (
                          <span
                            key={t}
                            className="rounded-lg border border-[#292D35] bg-[#181C23] px-2 py-0.5 font-mono text-[10px] uppercase text-[#D6B15E]"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Metadata & Vault Status */}
                    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3 text-xs border-b border-[#292D35] pb-4">
                      <div>
                        <span className="block font-mono text-[10px] uppercase text-[#737984]">VAULT ENCRYPTED KEY</span>
                        <span className="font-mono text-[#F5F5F2] text-[11px]">
                          {p.masked_key || "None (Unconfigured)"}
                        </span>
                      </div>

                      <div>
                        <span className="block font-mono text-[10px] uppercase text-[#737984]">KEY ORIGIN</span>
                        <span className="font-mono text-[11px] capitalize text-[#A3A7B0]">
                          {p.source === "user" ? "Analyst Vault (Encrypted)" : p.source === "system" ? "System Environment" : "Not Provided"}
                        </span>
                      </div>

                      <div>
                        <span className="block font-mono text-[10px] uppercase text-[#737984]">LAST AUDIT STATUS</span>
                        <span
                          className={`font-mono text-[11px] truncate block ${
                            p.last_test_status === "SUCCESS"
                              ? "text-emerald-400"
                              : p.last_test_status === "ERROR"
                              ? "text-rose-400"
                              : "text-[#737984]"
                          }`}
                        >
                          {p.last_test_message || "Not tested yet"}
                        </span>
                      </div>
                    </div>

                    {/* Actions and Key Configuration */}
                    <div className="mt-4 flex flex-col gap-3">
                      {showInput && (
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                          <div className="relative flex-1">
                            <input
                              type="password"
                              value={keyInputs[p.provider] || ""}
                              onChange={(e) =>
                                setKeyInputs((prev) => ({ ...prev, [p.provider]: e.target.value }))
                              }
                              placeholder={
                                isHive
                                  ? "Paste Hive API Key (e.g. hiv_live_...)"
                                  : isGptZero
                                  ? "Paste GPTZero API Key"
                                  : isCopyleaks
                                  ? "Paste Copyleaks API Key / Bearer"
                                  : "Paste Provider API Key"
                              }
                              className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] px-3.5 py-2 font-mono text-xs text-[#F5F5F2] focus:border-[#D6B15E] focus:outline-hidden"
                            />
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleSaveCredential(p.provider)}
                              disabled={isSaving || !keyInputs[p.provider]?.trim()}
                              className="rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-3.5 py-2 font-mono text-xs font-bold text-[#090A0D] hover:opacity-95 disabled:opacity-40 transition-opacity cursor-pointer"
                            >
                              {isSaving ? "Encrypting..." : "Save Key"}
                            </button>

                            {p.is_configured && (
                              <button
                                type="button"
                                onClick={() =>
                                  setShowKeyInputs((prev) => ({ ...prev, [p.provider]: false }))
                                }
                                className="rounded-xl border border-[#292D35] bg-[#181C23] px-3 py-2 font-mono text-xs text-[#A3A7B0] hover:text-[#F5F5F2] transition-colors cursor-pointer"
                              >
                                Cancel
                              </button>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => handleTestConnection(p.provider)}
                            disabled={isTesting || (!p.is_configured && !keyInputs[p.provider]?.trim())}
                            className="flex items-center gap-1.5 rounded-xl border border-[#292D35] bg-[#181C23] px-3.5 py-1.5 font-mono text-xs font-semibold text-[#F5F5F2] hover:border-[#D6B15E] hover:text-[#D6B15E] disabled:opacity-40 transition-colors cursor-pointer"
                          >
                            <RefreshCw className={`h-3.5 w-3.5 ${isTesting ? "animate-spin text-[#D6B15E]" : ""}`} />
                            <span>{isTesting ? "Testing Ping..." : "Test Connection"}</span>
                          </button>

                          {p.is_configured && !showInput && (
                            <button
                              type="button"
                              onClick={() =>
                                setShowKeyInputs((prev) => ({ ...prev, [p.provider]: true }))
                              }
                              className="flex items-center gap-1.5 rounded-xl border border-[#292D35] bg-[#181C23] px-3 py-1.5 font-mono text-xs text-[#A3A7B0] hover:text-[#F5F5F2] transition-colors cursor-pointer"
                            >
                              <Key className="h-3.5 w-3.5 text-[#D6B15E]" />
                              <span>Update Key</span>
                            </button>
                          )}

                          {p.source === "user" && (
                            <button
                              type="button"
                              onClick={() => handleDeleteCredential(p.provider)}
                              disabled={isDeleting}
                              className="flex items-center gap-1.5 rounded-xl border border-rose-500/20 bg-rose-950/20 px-3 py-1.5 font-mono text-xs text-rose-400 hover:border-rose-500/40 hover:bg-rose-950/40 disabled:opacity-40 transition-colors cursor-pointer"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                              <span>{isDeleting ? "Deleting..." : "Remove Key"}</span>
                            </button>
                          )}
                        </div>

                        <a
                          href={p.doc_url}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="flex items-center gap-1 font-mono text-xs text-[#D6B15E] hover:underline"
                        >
                          <span>Official API Docs</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
