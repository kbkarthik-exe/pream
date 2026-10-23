"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ForensicResultCard } from "@/components/forensic-result-card";
import { reportsApi } from "@/lib/api";

export default function ImageDetectionPage() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [logSuccess, setLogSuccess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFileName(e.target.files[0].name);
      setShowResult(false);
      setLogSuccess(false);
    }
  };

  const handleRunAnalysis = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileName) return;

    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
      setShowResult(true);
    }, 400);
  };

  const handleSaveInvestigation = async () => {
    if (!fileName) return;
    try {
      await reportsApi.create({
        title: `Image Forensics: ${fileName}`,
        media_type: "image",
        summary: `Inspected image file ${fileName} for diffusion noise and frequency artifacts.`,
        is_private: true,
      });
      setLogSuccess(true);
    } catch {
      // Handled
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D4AF37]">MOD-IMG-02</span>
            <span className="text-[#6B7280]">&bull;</span>
            <span className="text-xs text-[#9FA6B2]">Computer Vision Forensics</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            AI Image Detection &amp; Pixel Forensics
          </h1>
          <p className="mt-1 text-xs text-[#9FA6B2]">
            Inspect images for latent diffusion noise residuals, Discrete Cosine Transform (DCT) frequency grid spikes, and EXIF telemetry tampering.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="self-start sm:self-auto rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3.5 py-1.5 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37]"
        >
          &larr; Back to Overview
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-6">
          <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-3">
            <h2 className="text-sm font-semibold text-white">Image Upload &amp; Ingestion</h2>
            <span className="font-mono text-[11px] text-[#6B7280]">PNG, JPG, WEBP</span>
          </div>

          <form onSubmit={handleRunAnalysis} className="mt-4 space-y-4">
            <div className="rounded-lg border-2 border-dashed border-[#2B2F3D] bg-[#191C24]/60 p-8 text-center hover:border-[#D4AF37]/50 transition-colors">
              <input
                id="imageUpload"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="imageUpload" className="cursor-pointer">
                <span className="font-mono text-2xl text-[#D4AF37]">◩</span>
                <p className="mt-2 text-xs font-semibold text-white">
                  {fileName ? `Selected: ${fileName}` : "Click to select or drop image"}
                </p>
                <p className="mt-1 text-[11px] text-[#6B7280]">
                  Supports standard forensic resolution up to 4K
                </p>
              </label>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-[#6B7280]">
                {fileName ? "Ready to submit to pipeline" : "No file selected"}
              </span>
              <button
                type="submit"
                disabled={isAnalyzing || !fileName}
                className="rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-5 py-2 text-xs font-semibold text-black transition-opacity hover:opacity-95 disabled:opacity-50"
              >
                {isAnalyzing ? "Processing Frames..." : "Scan Image Authenticity"}
              </button>
            </div>
          </form>

          {showResult && (
            <div className="mt-4 border-t border-[#2B2F3D] pt-4 flex items-center justify-between">
              <span className="text-xs text-[#9FA6B2]">Audit Case Logger:</span>
              <button
                type="button"
                onClick={handleSaveInvestigation}
                disabled={logSuccess}
                className="rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3 py-1.5 text-xs text-[#D4AF37] hover:border-[#D4AF37]"
              >
                {logSuccess ? "✓ Logged in PostgreSQL" : "+ Save Case to Reports"}
              </button>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <ForensicResultCard
            modality="image"
            modalityCode="MOD-IMG-02"
            status={showResult ? "BLOCKED" : "QUEUED"}
            isEngineConfigured={false}
            pipelineNote="The Image Forensics pipeline utilizes Spatial Rich Models (SRM), 2D Fourier frequency domain analysis, and diffusion latent residual extraction. Modular package is situated in backend/app/ml/image/."
          />
        </div>
      </div>
    </div>
  );
}
