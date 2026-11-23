"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  ShieldCheck,
  LogIn,
  Eye,
  EyeOff,
  AlertTriangle,
  ArrowRight,
  Lock,
  User,
} from "lucide-react";

export default function LoginPage() {
  const { user, login, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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
        <div className="rounded-3xl border border-[#292D35] bg-[#12151B] p-8 shadow-[0_0_50px_rgba(0,0,0,0.85)] backdrop-blur-md">
          {/* Header */}
          <div className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[#D6B15E]/40 bg-[#181C23] shadow-[0_0_20px_rgba(214,177,94,0.15)]">
              <ShieldCheck className="h-7 w-7 text-[#D6B15E]" />
            </div>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-[#F5F5F2]">
              Analyst Portal Access
            </h1>
            <p className="mt-1.5 text-xs text-[#A3A7B0]">
              Enter your institutional credentials to establish an authenticated session
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
                <span className="font-mono font-bold text-red-400 mr-1">AUTH FAILED:</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="identifier"
                className="block font-mono text-xs font-medium text-[#A3A7B0] uppercase"
              >
                Analyst ID / Email / Callsign
              </label>
              <div className="relative mt-1.5">
                <User className="absolute left-3.5 top-2.5 h-4 w-4 text-[#737984]" />
                <input
                  id="identifier"
                  name="identifier"
                  type="text"
                  autoComplete="username"
                  required
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="analyst@aicf.org or username"
                  className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] pl-10 pr-4 py-2.5 text-xs text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden font-mono"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block font-mono text-xs font-medium text-[#A3A7B0] uppercase"
              >
                Password
              </label>
              <div className="relative mt-1.5">
                <Lock className="absolute left-3.5 top-2.5 h-4 w-4 text-[#737984]" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
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

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] py-2.5 font-mono text-xs font-bold text-[#090A0D] shadow-[0_0_15px_rgba(214,177,94,0.2)] hover:opacity-95 disabled:opacity-50 transition-all cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
                    <span>Verifying Credentials...</span>
                  </>
                ) : (
                  <>
                    <LogIn className="h-4 w-4" />
                    <span>Authenticate &amp; Launch Console</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Footer Navigation */}
          <div className="mt-6 border-t border-[#292D35] pt-4 text-center text-xs text-[#A3A7B0]">
            Need new credentials?{" "}
            <Link
              href="/register"
              className="font-medium text-[#D6B15E] hover:text-[#F0D58A] transition-colors inline-flex items-center gap-1"
            >
              <span>Register new account</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
