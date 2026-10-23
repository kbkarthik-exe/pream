"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { user, login, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!identifier.trim()) {
      setError("Please enter your analyst callsign or email address.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login({
        identifier: identifier.trim(),
        password,
      });
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Authentication server unavailable. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-[calc(100vh-140px)] items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-[#2B2F3D] bg-[#12141A]/95 p-8 shadow-[0_0_40px_rgba(0,0,0,0.85)] backdrop-blur-md">
          {/* Header */}
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-[#D4AF37]/50 bg-[#191C24] shadow-[0_0_15px_rgba(212,175,55,0.2)]">
              <span className="font-mono text-xl font-bold text-[#D4AF37]">Ψ</span>
            </div>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-white">
              Forensic Console Access
            </h1>
            <p className="mt-1.5 text-xs text-[#9FA6B2]">
              Authenticate with your institutional credentials to establish a secure session
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              role="alert"
              className="mt-6 rounded-lg border border-red-500/40 bg-red-500/10 p-3.5 text-xs text-red-300"
            >
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-red-400">AUTH REJECTED:</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="identifier"
                className="block font-mono text-xs font-medium text-[#F3E5AB]"
              >
                Analyst ID / Email / Username
              </label>
              <div className="mt-1.5">
                <input
                  id="identifier"
                  name="identifier"
                  type="text"
                  required
                  autoComplete="username"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="analyst_callsign or name@aicf.internal"
                  className="block w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2.5 text-sm text-[#F8F9FA] placeholder-[#4B5563] shadow-inner focus:border-[#D4AF37] focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block font-mono text-xs font-medium text-[#F3E5AB]"
                >
                  Cryptographic Token / Password
                </label>
                <span className="text-[10px] text-[#9FA6B2]">
                  Argon2id Verified
                </span>
              </div>
              <div className="mt-1.5">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••••••"
                  className="block w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2.5 text-sm text-[#F8F9FA] placeholder-[#4B5563] shadow-inner focus:border-[#D4AF37] focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-4 py-2.5 text-center text-sm font-semibold text-black shadow-[0_0_15px_rgba(212,175,55,0.2)] transition-all hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSubmitting ? "Establishing Session..." : "Authorize Session"}
              </button>
            </div>
          </form>

          {/* Footer Link */}
          <div className="mt-6 border-t border-[#2B2F3D]/80 pt-4 text-center">
            <p className="text-xs text-[#9FA6B2]">
              Need analyst credentials?{" "}
              <Link
                href="/register"
                className="font-medium text-[#D4AF37] underline underline-offset-4 hover:text-[#F3E5AB]"
              >
                Register an Account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
