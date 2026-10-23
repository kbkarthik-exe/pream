"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const { user, register, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  // Real-time password criteria
  const hasMinLength = password.length >= 8;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasSpecialOrDigit = /[0-9!@#$%^&*(),.?":{}|<>]/.test(password);
  const passwordsMatch = password.length > 0 && password === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validations
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please provide a valid institutional or personal email address.");
      return;
    }

    if (!/^[a-zA-Z0-9_]{3,30}$/.test(username)) {
      setError("Username must be 3-30 characters and only contain letters, numbers, or underscores.");
      return;
    }

    if (!hasMinLength || !hasUpperCase || !hasLowerCase || !hasSpecialOrDigit) {
      setError("Password does not meet the forensic security complexity criteria.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please re-enter.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        email,
        username,
        password,
        full_name: fullName.trim() || undefined,
      });
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to the authentication server. Please try again.");
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
              Analyst Registration
            </h1>
            <p className="mt-1.5 text-xs text-[#9FA6B2]">
              Provision a verified analyst identity with cryptographic session credentials
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              role="alert"
              className="mt-6 rounded-lg border border-red-500/40 bg-red-500/10 p-3.5 text-xs text-red-300"
            >
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-red-400">ERROR:</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Registration Form */}
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="email"
                className="block font-mono text-xs font-medium text-[#F3E5AB]"
              >
                Analyst Email
              </label>
              <div className="mt-1.5">
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@forensics.aicf.internal"
                  className="block w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2.5 text-sm text-[#F8F9FA] placeholder-[#4B5563] shadow-inner focus:border-[#D4AF37] focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="username"
                className="block font-mono text-xs font-medium text-[#F3E5AB]"
              >
                Analyst Callsign (Username)
              </label>
              <div className="mt-1.5">
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="analyst_callsign"
                  className="block w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2.5 text-sm text-[#F8F9FA] placeholder-[#4B5563] shadow-inner focus:border-[#D4AF37] focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="fullName"
                className="block font-mono text-xs font-medium text-[#9FA6B2]"
              >
                Full Name <span className="text-[10px] text-[#6B7280]">(Optional)</span>
              </label>
              <div className="mt-1.5">
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Dr. Jordan Mercer"
                  className="block w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2.5 text-sm text-[#F8F9FA] placeholder-[#4B5563] shadow-inner focus:border-[#D4AF37] focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block font-mono text-xs font-medium text-[#F3E5AB]"
              >
                Master Password (Argon2id Protected)
              </label>
              <div className="mt-1.5">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••••••"
                  className="block w-full rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3.5 py-2.5 text-sm text-[#F8F9FA] placeholder-[#4B5563] shadow-inner focus:border-[#D4AF37] focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                />
              </div>

              {/* Password complexity checklist */}
              <div className="mt-2.5 grid grid-cols-2 gap-1.5 text-[11px]">
                <div className={`flex items-center gap-1.5 ${hasMinLength ? "text-emerald-400" : "text-[#6B7280]"}`}>
                  <span>{hasMinLength ? "✓" : "○"}</span> 8+ Characters
                </div>
                <div className={`flex items-center gap-1.5 ${hasUpperCase ? "text-emerald-400" : "text-[#6B7280]"}`}>
                  <span>{hasUpperCase ? "✓" : "○"}</span> Uppercase (A-Z)
                </div>
                <div className={`flex items-center gap-1.5 ${hasLowerCase ? "text-emerald-400" : "text-[#6B7280]"}`}>
                  <span>{hasLowerCase ? "✓" : "○"}</span> Lowercase (a-z)
                </div>
                <div className={`flex items-center gap-1.5 ${hasSpecialOrDigit ? "text-emerald-400" : "text-[#6B7280]"}`}>
                  <span>{hasSpecialOrDigit ? "✓" : "○"}</span> Number/Symbol
                </div>
              </div>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block font-mono text-xs font-medium text-[#F3E5AB]"
              >
                Confirm Password
              </label>
              <div className="mt-1.5">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••••••"
                  className={`block w-full rounded-lg border bg-[#191C24] px-3.5 py-2.5 text-sm text-[#F8F9FA] placeholder-[#4B5563] shadow-inner focus:outline-none ${
                    confirmPassword && !passwordsMatch
                      ? "border-red-500 focus:border-red-500"
                      : "border-[#2B2F3D] focus:border-[#D4AF37]"
                  }`}
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-4 py-2.5 text-center text-sm font-semibold text-black shadow-[0_0_15px_rgba(212,175,55,0.2)] transition-all hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSubmitting ? "Provisioning Identity..." : "Complete Registration"}
              </button>
            </div>
          </form>

          {/* Footer Link */}
          <div className="mt-6 border-t border-[#2B2F3D]/80 pt-4 text-center">
            <p className="text-xs text-[#9FA6B2]">
              Already hold an analyst identity?{" "}
              <Link
                href="/login"
                className="font-medium text-[#D4AF37] underline underline-offset-4 hover:text-[#F3E5AB]"
              >
                Sign in to Console
              </Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
