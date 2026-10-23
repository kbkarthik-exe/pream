"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-[calc(100vh-140px)] flex-col items-center justify-center">
        <div className="relative flex h-16 w-16 items-center justify-center">
          <div className="absolute h-full w-full rounded-full border-2 border-[#D4AF37]/20 border-t-[#D4AF37] animate-spin" />
          <span className="font-mono text-xs font-bold text-[#D4AF37]">AICF</span>
        </div>
        <p className="mt-4 font-mono text-xs tracking-wider text-[#9FA6B2] uppercase">
          Verifying Forensic Session...
        </p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}
