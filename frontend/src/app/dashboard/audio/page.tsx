"use client";

import React from "react";
import Link from "next/link";
import { Ban, FileText, Image as ImageIcon } from "lucide-react";

export default function AudioDetectionPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D6B15E] font-bold">MOD-AUD-04</span>
            <span className="text-[#3A404D]">&bull;</span>
            <span className="text-xs text-[#A3A7B0]">Acoustic &amp; Synthetic Voice Forensics</span>
            <span className="text-[#3A404D]">&bull;</span>
            <span className="rounded-full bg-red-950/40 px-2 py-0.5 font-mono text-[10px] text-red-400 border border-red-500/30">
              CANCELLED
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#F5F5F2]">
            AI Audio &amp; Voice Clone Detection
          </h1>
          <p className="mt-1 text-xs text-[#A3A7B0]">
            CANCELLED — AI Audio Detection Engine is formally removed from the platform roadmap.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="self-start sm:self-auto rounded-lg border border-[#292D35] bg-[#12151B] px-3.5 py-1.5 text-xs text-[#A3A7B0] hover:border-[#D6B15E] hover:text-[#D6B15E] transition-colors"
        >
          &larr; Overview
        </Link>
      </div>

      <div className="rounded-2xl border border-red-500/30 bg-[#12151B] p-10 text-center space-y-4 shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400">
          <Ban className="h-7 w-7" />
        </div>
        <div>
          <h2 className="text-base font-bold text-[#F5F5F2] tracking-wide font-mono uppercase">
            Feature Formally Cancelled
          </h2>
          <p className="mt-2 text-xs text-[#A3A7B0] max-w-lg mx-auto leading-relaxed">
            In accordance with platform product governance, the Audio Detection Engine has been officially cancelled.
            No audio detection APIs, neural vocoder models, or database tables are active.
          </p>
        </div>

        <div className="pt-3 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/dashboard/text"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#292D35] bg-[#181C23] px-4 py-2 text-xs font-semibold text-[#F5F5F2] hover:border-[#D6B15E] transition-colors cursor-pointer"
          >
            <FileText className="h-3.5 w-3.5 text-[#D6B15E]" />
            <span>Launch Text Forensics</span>
          </Link>
          <Link
            href="/dashboard/image"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-4 py-2 text-xs font-bold text-[#090A0D] shadow-[0_0_12px_rgba(214,177,94,0.15)] hover:opacity-95 transition-opacity cursor-pointer"
          >
            <ImageIcon className="h-3.5 w-3.5" />
            <span>Launch Image Forensics</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
