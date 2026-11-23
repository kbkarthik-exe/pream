"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  ShieldCheck,
  UserPlus,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

export default function RegisterPage() {
  const { user, register, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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
      setError("Callsign must be 3-30 characters and only contain letters, numbers, or underscores.");
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
        <div className="rounded-3xl border border-[#292D35] bg-[#12151B] p-8 shadow-[0_0_50px_rgba(0,0,0,0.85)] backdrop-blur-md">
          {/* Header */}
          <div className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[#D6B15E]/40 bg-[#181C23] shadow-[0_0_20px_rgba(214,177,94,0.15)]">
              <ShieldCheck className="h-7 w-7 text-[#D6B15E]" />
            </div>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-[#F5F5F2]">
              Analyst Registration
            </h1>
            <p className="mt-1.5 text-xs text-[#A3A7B0]">
              Provision an authenticated investigator account with cryptographic session tokens
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              role="alert"
              className="mt-6 rounded-xl border border-red-500/40 bg-red-500/10 p-3.5 text-xs text-red-300 flex items-center gap-2"
            >
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
              <div>
                <span className="font-mono font-bold text-red-400 mr-1">REGISTRATION FAILED:</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="email"
                className="block font-mono text-xs font-medium text-[#A3A7B0] uppercase"
              >
                Institutional Email *
              </label>
              <div className="relative mt-1.5">
                <Mail className="absolute left-3.5 top-2.5 h-4 w-4 text-[#737984]" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@agency.gov or user@domain.com"
                  className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] pl-10 pr-4 py-2.5 text-xs text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="username"
                className="block font-mono text-xs font-medium text-[#A3A7B0] uppercase"
              >
                Analyst Callsign / Username *
              </label>
              <div className="relative mt-1.5">
                <User className="absolute left-3.5 top-2.5 h-4 w-4 text-[#737984]" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. investigator_jensen"
                  className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] pl-10 pr-4 py-2.5 text-xs text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="fullName"
                className="block font-mono text-xs font-medium text-[#A3A7B0] uppercase"
              >
                Full Name (Optional)
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Agent Adam Jensen"
                className="mt-1.5 w-full rounded-xl border border-[#292D35] bg-[#090A0D] px-3.5 py-2.5 text-xs text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden font-mono"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block font-mono text-xs font-medium text-[#A3A7B0] uppercase"
              >
                Secure Password *
              </label>
              <div className="relative mt-1.5">
                <Lock className="absolute left-3.5 top-2.5 h-4 w-4 text-[#737984]" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] pl-10 pr-10 py-2.5 text-xs text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-2.5 text-[#737984] hover:text-[#F5F5F2] transition-colors cursor-pointer"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Live Password Criteria Meter */}
            {password.length > 0 && (
              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3 text-[11px] font-mono space-y-1.5">
                <div className="text-[#A3A7B0] font-bold text-[10px] uppercase">Forensic Complexity Criteria:</div>
                <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                  <span className={hasMinLength ? "text-emerald-400 flex items-center gap-1" : "text-[#737984] flex items-center gap-1"}>
                    {hasMinLength ? "✓" : "○"} 8+ Characters
                  </span>
                  <span className={hasUpperCase ? "text-emerald-400 flex items-center gap-1" : "text-[#737984] flex items-center gap-1"}>
                    {hasUpperCase ? "✓" : "○"} Uppercase (A-Z)
                  </span>
                  <span className={hasLowerCase ? "text-emerald-400 flex items-center gap-1" : "text-[#737984] flex items-center gap-1"}>
                    {hasLowerCase ? "✓" : "○"} Lowercase (a-z)
                  </span>
                  <span className={hasSpecialOrDigit ? "text-emerald-400 flex items-center gap-1" : "text-[#737984] flex items-center gap-1"}>
                    {hasSpecialOrDigit ? "✓" : "○"} Number / Symbol
                  </span>
                </div>
              </div>
            )}

            <div>
              <label
                htmlFor="confirmPassword"
                className="block font-mono text-xs font-medium text-[#A3A7B0] uppercase"
              >
                Confirm Password *
              </label>
              <div className="relative mt-1.5">
                <Lock className="absolute left-3.5 top-2.5 h-4 w-4 text-[#737984]" />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] pl-10 pr-10 py-2.5 text-xs text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3.5 top-2.5 text-[#737984] hover:text-[#F5F5F2] transition-colors cursor-pointer"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {confirmPassword.length > 0 && !passwordsMatch && (
                <p className="mt-1 text-[10px] text-red-400 font-mono">Passwords do not match.</p>
              )}
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] py-2.5 font-mono text-xs font-bold text-[#090A0D] shadow-[0_0_15px_rgba(214,177,94,0.2)] hover:opacity-95 disabled:opacity-50 transition-all cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
                    <span>Provisioning Identity...</span>
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    <span>Create Forensic Credentials</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Footer Navigation */}
          <div className="mt-6 border-t border-[#292D35] pt-4 text-center text-xs text-[#A3A7B0]">
            Already have an active analyst account?{" "}
            <Link
              href="/login"
              className="font-medium text-[#D6B15E] hover:text-[#F0D58A] transition-colors inline-flex items-center gap-1"
            >
              <span>Sign in to console</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
