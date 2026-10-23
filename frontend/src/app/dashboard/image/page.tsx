"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  imageApi,
  ImageAnalysisHistoryItem,
  ImageAnalysisResponse,
  reportsApi,
} from "@/lib/api";

const MAX_FILE_SIZE_MB = 15;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const SUPPORTED_EXTS = ["image/jpeg", "image/png", "image/webp"];

export default function ImageDetectionPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [imageDims, setImageDims] = useState<{ width: number; height: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<string>("");
  const [saveToCases, setSaveToCases] = useState(false);
  const [result, setResult] = useState<ImageAnalysisResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [caseSaved, setCaseSaved] = useState(false);
  const [history, setHistory] = useState<ImageAnalysisHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Revoke object URL on unmount or file change to prevent memory leaks
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // Load history on mount
  useEffect(() => {
    let ignore = false;
    imageApi
      .listAnalyses()
      .then((records) => {
        if (!ignore) {
          setHistory(records);
        }
      })
      .catch(() => {});

    return () => {
      ignore = true;
    };
  }, []);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const records = await imageApi.listAnalyses();
      setHistory(records);
    } catch {
      // Ignored for unauthenticated or first-time views
    } finally {
      setLoadingHistory(false);
    }
  };

  const processFile = (file: File) => {
    setErrorMsg(null);
    setResult(null);
    setCaseSaved(false);

    // Validate mime type
    if (!SUPPORTED_EXTS.includes(file.type.toLowerCase()) && !file.name.match(/\.(jpe?g|png|webp)$/i)) {
      setErrorMsg("Unsupported file format. AICF safely supports only JPEG, PNG, and WebP images.");
      return;
    }

    // Validate size limit
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMsg(
        `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds platform limit of ${MAX_FILE_SIZE_MB} MB.`
      );
      return;
    }

    if (file.size === 0) {
      setErrorMsg("The selected file is empty (0 bytes).");
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    const objUrl = URL.createObjectURL(file);
    setSelectedFile(file);
    setPreviewUrl(objUrl);

    // Extract image dimensions client-side for immediate analyst telemetry
    const img = new Image();
    img.onload = () => {
      setImageDims({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = () => {
      setImageDims(null);
    };
    img.src = objUrl;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleClear = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setImageDims(null);
    setResult(null);
    setErrorMsg(null);
    setCaseSaved(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMsg("Please select or drop an image file to analyze.");
      return;
    }

    setIsAnalyzing(true);
    setErrorMsg(null);
    setCaseSaved(false);

    // Progressive visual telemetry steps
    setAnalysisStep("Decoding raster buffer & computing SHA-256 hash...");
    const timer1 = setTimeout(() => {
      setAnalysisStep("Executing Swin Vision Transformer deep feature inference...");
    }, 350);
    const timer2 = setTimeout(() => {
      setAnalysisStep("Computing 2D Fast Fourier Transform (FFT) frequency spectrum...");
    }, 850);
    const timer3 = setTimeout(() => {
      setAnalysisStep("Inspecting EXIF metadata & C2PA Content Credentials...");
    }, 1350);

    try {
      const resp = await imageApi.analyze(selectedFile, saveToCases);
      setResult(resp);
      if (resp.case_report_id) {
        setCaseSaved(true);
      }
      fetchHistory();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to execute image forensics analysis. Please verify backend connection.");
      }
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setIsAnalyzing(false);
      setAnalysisStep("");
    }
  };

  const handleSaveToReports = async () => {
    if (!result) return;
    try {
      const scoreStr =
        result.confidence_score !== null
          ? `${(result.confidence_score * 100).toFixed(1)}%`
          : "N/A";
      await reportsApi.create({
        title: `Image Forensics: ${result.file_name}`,
        media_type: "image",
        summary: `Analysis #${result.analysis_id} — Classification: ${result.classification} (${scoreStr}). File: ${result.file_name} (${result.image_width}x${result.image_height}, ${result.image_format}). SHA-256: ${result.file_hash.slice(0, 12)}... FFT Anisotropy: ${result.spectral_anisotropy.toFixed(2)}, Noise Var: ${result.noise_variance.toFixed(1)}.`,
        is_private: true,
      });
      setCaseSaved(true);
    } catch {
      setErrorMsg("Failed to save report to case archive.");
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D4AF37]">MOD-IMG-02</span>
            <span className="text-[#6B7280]">&bull;</span>
            <span className="text-xs text-[#9FA6B2]">Computer Vision Forensics</span>
            <span className="text-[#6B7280]">&bull;</span>
            <span className="rounded bg-[#1B221B] px-1.5 py-0.5 font-mono text-[10px] text-[#4ADE80] border border-[#2E4A2E]">
              SWIN-TRANSFORMER LIVE
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            AI Image Detection &amp; Pixel Forensics
          </h1>
          <p className="mt-1 text-xs text-[#9FA6B2]">
            Inspect imagery for synthetic diffusion artifacts, 2D Fourier frequency domain grid spikes,
            Laplacian noise anomalies, and C2PA Content Credentials.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowHistoryDrawer(!showHistoryDrawer)}
            className="rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3.5 py-1.5 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37] transition-colors"
          >
            {showHistoryDrawer ? "Hide History" : `Past Scans (${history.length})`}
          </button>
          <Link
            href="/dashboard"
            className="rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3.5 py-1.5 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37] transition-colors"
          >
            &larr; Overview
          </Link>
        </div>
      </div>

      {/* History Drawer */}
      {showHistoryDrawer && (
        <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A] p-4">
          <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-white">Analyst Image Scan History</span>
              <span className="font-mono text-[11px] text-[#9FA6B2]">({history.length} records)</span>
            </div>
            <Link
              href="/dashboard/reports?media_type=image"
              className="text-xs text-[#D4AF37] hover:underline"
            >
              View in Forensic Reports Archive &rarr;
            </Link>
          </div>

          {loadingHistory ? (
            <p className="py-4 text-center text-xs text-[#9FA6B2]">Loading investigation records...</p>
          ) : history.length === 0 ? (
            <p className="py-4 text-center text-xs text-[#6B7280]">
              No previous image analyses found for your analyst account.
            </p>
          ) : (
            <div className="mt-3 max-h-60 overflow-y-auto divide-y divide-[#2B2F3D]/50 text-xs">
              {history.map((item) => (
                <div key={item.id} className="py-2.5 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-medium text-white truncate">{item.file_name}</p>
                    <p className="font-mono text-[10px] text-[#6B7280]">
                      {item.image_width}x{item.image_height} {item.image_format} &bull;{" "}
                      {formatFileSize(item.file_size_bytes)} &bull; SHA-256: {item.file_hash.slice(0, 10)}...
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span
                      className={`font-mono text-[11px] px-2 py-0.5 rounded font-semibold ${
                        item.classification === "LIKELY AI-GENERATED"
                          ? "bg-[#331111] text-[#F87171] border border-[#552222]"
                          : item.classification === "LIKELY HUMAN"
                          ? "bg-[#11291A] text-[#4ADE80] border border-[#1C4D2E]"
                          : "bg-[#2A2311] text-[#FBBF24] border border-[#4E3F18]"
                      }`}
                    >
                      {item.classification}
                    </span>
                    <span className="font-mono text-[11px] text-[#9FA6B2]">
                      {item.confidence_score !== null ? `${(item.confidence_score * 100).toFixed(0)}%` : "N/A"}
                    </span>
                    <span className="font-mono text-[10px] text-[#6B7280]">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Column: Upload, Drop Zone, Preview & Controls */}
        <div className="space-y-4">
          <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-6">
            <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-3">
              <h2 className="text-sm font-semibold text-white">Image Ingestion &amp; Raster Decoding</h2>
              <span className="font-mono text-[11px] text-[#D4AF37]">JPEG &bull; PNG &bull; WEBP</span>
            </div>

            <form onSubmit={handleRunAnalysis} className="mt-4 space-y-4">
              {/* Drag & Drop Container */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`relative rounded-xl border-2 border-dashed p-6 text-center transition-all ${
                  isDragging
                    ? "border-[#D4AF37] bg-[#D4AF37]/5"
                    : selectedFile
                    ? "border-[#D4AF37]/40 bg-[#161922]"
                    : "border-[#2B2F3D] bg-[#191C24]/60 hover:border-[#D4AF37]/40"
                }`}
              >
                <input
                  ref={fileInputRef}
                  id="imageUpload"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleFileChange}
                  className="hidden"
                />

                {!selectedFile ? (
                  <label htmlFor="imageUpload" className="cursor-pointer block py-6">
                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#12141A] border border-[#2B2F3D] text-[#D4AF37]">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                    <p className="mt-3 text-xs font-semibold text-white">
                      Drag &amp; drop forensic image, or <span className="text-[#D4AF37] underline">browse files</span>
                    </p>
                    <p className="mt-1 font-mono text-[11px] text-[#6B7280]">
                      Max file size: {MAX_FILE_SIZE_MB} MB &bull; Max resolution: 16 MP (4096px)
                    </p>
                  </label>
                ) : (
                  <div className="space-y-4">
                    {/* Image Preview Container */}
                    <div className="relative mx-auto max-h-72 overflow-hidden rounded-lg border border-[#2B2F3D] bg-black/40 flex items-center justify-center">
                      {previewUrl && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={previewUrl}
                          alt="Forensic candidate preview"
                          className="max-h-64 max-w-full object-contain"
                        />
                      )}
                    </div>

                    {/* Image Metadata Bar */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-left rounded-lg border border-[#2B2F3D] bg-[#12141A] p-2.5 font-mono text-[11px]">
                      <div>
                        <span className="text-[#6B7280] block text-[10px]">FILE NAME</span>
                        <span className="text-white truncate block" title={selectedFile.name}>
                          {selectedFile.name}
                        </span>
                      </div>
                      <div>
                        <span className="text-[#6B7280] block text-[10px]">PAYLOAD SIZE</span>
                        <span className="text-[#D4AF37]">{formatFileSize(selectedFile.size)}</span>
                      </div>
                      <div className="col-span-2 sm:col-span-1">
                        <span className="text-[#6B7280] block text-[10px]">DIMENSIONS</span>
                        <span className="text-white">
                          {imageDims ? `${imageDims.width} × ${imageDims.height} px` : "Detecting..."}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-center gap-3">
                      <label
                        htmlFor="imageUpload"
                        className="cursor-pointer rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3 py-1.5 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37]"
                      >
                        Change Image
                      </label>
                      <button
                        type="button"
                        onClick={handleClear}
                        className="rounded-lg border border-[#4A2020] bg-[#2A1212] px-3 py-1.5 text-xs text-[#F87171] hover:bg-[#3A1818]"
                      >
                        Remove Image
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Controls & Submit */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={saveToCases}
                    onChange={(e) => setSaveToCases(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-[#2B2F3D] bg-[#191C24] text-[#D4AF37] focus:ring-0"
                  />
                  <span className="text-xs text-[#9FA6B2]">
                    Automatically persist to Forensic Cases Archive
                  </span>
                </label>

                <div className="flex items-center gap-2">
                  <button
                    type="submit"
                    disabled={isAnalyzing || !selectedFile}
                    className="w-full sm:w-auto rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] via-[#E5C158] to-[#F3E5AB] px-5 py-2 text-xs font-semibold text-black transition-opacity hover:opacity-95 disabled:opacity-40"
                  >
                    {isAnalyzing ? "Executing Forensics..." : "Scan Image Authenticity"}
                  </button>
                </div>
              </div>
            </form>

            {/* In-Flight Multi-Stage Telemetry */}
            {isAnalyzing && (
              <div className="mt-4 rounded-lg border border-[#D4AF37]/30 bg-[#161922] p-4 text-xs">
                <div className="flex items-center gap-3">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#D4AF37] border-t-transparent" />
                  <span className="font-mono text-[#D4AF37] font-medium">{analysisStep}</span>
                </div>
                <div className="mt-3 h-1 w-full overflow-hidden rounded bg-[#2B2F3D]">
                  <div className="h-full bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] animate-pulse w-3/4" />
                </div>
              </div>
            )}

            {/* Error Banner */}
            {errorMsg && (
              <div className="mt-4 rounded-lg border border-[#552222] bg-[#2A1111] p-3 text-xs text-[#F87171] flex items-start justify-between">
                <div>
                  <span className="font-semibold block">Forensic Processing Error</span>
                  <p className="mt-0.5">{errorMsg}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setErrorMsg(null)}
                  className="text-[#F87171] hover:text-white ml-2"
                >
                  &times;
                </button>
              </div>
            )}
          </div>

          {/* Quick Technical Specs Card */}
          <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/60 p-4 font-mono text-[11px] text-[#9FA6B2] space-y-1.5">
            <div className="text-xs font-semibold text-white mb-2 font-sans flex items-center justify-between">
              <span>Verification Pipeline Telemetry</span>
              <span className="text-[#D4AF37] text-[10px]">v1.0.0</span>
            </div>
            <p>&bull; Model: Swin-Transformer (AutoModelForImageClassification)</p>
            <p>&bull; Weights: umm-maybe/AI-image-detector (CC-BY-4.0)</p>
            <p>&bull; Spectral Analysis: 2D FFT Radial Octant Power &amp; Anisotropy</p>
            <p>&bull; Noise Telemetry: Discrete 2D Laplacian Residual Variance</p>
            <p>&bull; Provenance: EXIF, PNG chunks, and C2PA Content Credentials</p>
          </div>
        </div>

        {/* Right Column: Forensic Analysis Result */}
        <div className="space-y-4">
          {!result ? (
            <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/90 p-8 text-center space-y-4">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#191C24] border border-[#2B2F3D] text-[#6B7280]">
                <span className="font-mono text-xl">◩</span>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Awaiting Candidate Image</h3>
                <p className="mt-1 text-xs text-[#6B7280] max-w-sm mx-auto">
                  Select or drag an image into the ingestion panel to execute vision transformer classification,
                  2D Fourier spectral breakdown, and container provenance verification.
                </p>
              </div>
              <div className="inline-flex items-center gap-2 rounded bg-[#191C24] px-3 py-1 font-mono text-[11px] text-[#9FA6B2] border border-[#2B2F3D]">
                <span>Status:</span>
                <span className="text-[#D4AF37]">STANDBY</span>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A] p-6 space-y-5">
              {/* Result Header & Classification */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-4">
                <div>
                  <span className="font-mono text-[10px] text-[#9FA6B2]">
                    CASE #{result.analysis_id} &bull; SHA-256: {result.file_hash.slice(0, 10)}...
                  </span>
                  <div className="mt-1 flex items-center gap-2">
                    <span
                      className={`inline-block px-3 py-1 rounded text-xs font-bold font-mono tracking-wide ${
                        result.classification === "LIKELY AI-GENERATED"
                          ? "bg-[#3D1414] text-[#F87171] border border-[#7A2828]"
                          : result.classification === "LIKELY HUMAN"
                          ? "bg-[#112F1C] text-[#4ADE80] border border-[#1E5C34]"
                          : "bg-[#332A14] text-[#FBBF24] border border-[#6B5521]"
                      }`}
                    >
                      {result.classification}
                    </span>
                    <span className="text-xs text-[#9FA6B2] font-mono">
                      {result.confidence_score !== null
                        ? `Confidence: ${(result.confidence_score * 100).toFixed(1)}%`
                        : "Blocked"}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleSaveToReports}
                    disabled={caseSaved}
                    className="rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3 py-1.5 text-xs text-[#D4AF37] hover:border-[#D4AF37] transition-colors disabled:opacity-60"
                  >
                    {caseSaved ? "✓ Case Logged" : "+ Save to Cases"}
                  </button>
                </div>
              </div>

              {/* Confidence Distribution Bars */}
              {result.ai_probability !== null && result.human_probability !== null && (
                <div className="rounded-lg border border-[#2B2F3D] bg-[#161922] p-4 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">Probabilistic Class Distribution</span>
                    <span className="font-mono text-[10px] text-[#9FA6B2]">Thresholds: 70% AI / 30% Human</span>
                  </div>

                  {/* Synthetic Probability */}
                  <div>
                    <div className="flex justify-between font-mono text-[11px] text-[#9FA6B2] mb-1">
                      <span>Synthetic / AI Probability</span>
                      <span className="text-[#F87171] font-semibold">
                        {(result.ai_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 w-full rounded bg-[#2B2F3D] overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[#D4AF37] to-[#F87171]"
                        style={{ width: `${Math.min(100, Math.max(0, result.ai_probability * 100))}%` }}
                      />
                    </div>
                  </div>

                  {/* Authentic Photography Probability */}
                  <div>
                    <div className="flex justify-between font-mono text-[11px] text-[#9FA6B2] mb-1">
                      <span>Authentic Photography Probability</span>
                      <span className="text-[#4ADE80] font-semibold">
                        {(result.human_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 w-full rounded bg-[#2B2F3D] overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[#D4AF37] to-[#4ADE80]"
                        style={{ width: `${Math.min(100, Math.max(0, result.human_probability * 100))}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Forensic Evidence Signals */}
              <div>
                <h4 className="text-xs font-semibold text-white mb-2">Computed Forensic Evidence Signals</h4>
                <div className="space-y-2">
                  {result.evidence.map((item, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-[#2B2F3D] bg-[#161922] p-3 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white">{item.signal}</span>
                        {item.metric && (
                          <span className="font-mono text-[10px] text-[#D4AF37] bg-[#12141A] px-2 py-0.5 rounded border border-[#2B2F3D]">
                            {item.metric}
                          </span>
                        )}
                      </div>
                      <p className="text-[#9FA6B2] text-[11px] leading-relaxed">{item.finding}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Provenance & Metadata Container Box */}
              {result.provenance && (
                <div className="rounded-lg border border-[#2B2F3D] bg-[#161922] p-3.5 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">Container Metadata &amp; Provenance</span>
                    <span
                      className={`font-mono text-[10px] px-2 py-0.5 rounded ${
                        result.has_ai_metadata
                          ? "bg-[#3D1414] text-[#F87171] border border-[#7A2828]"
                          : result.has_c2pa
                          ? "bg-[#112F1C] text-[#4ADE80] border border-[#1E5C34]"
                          : "bg-[#12141A] text-[#9FA6B2] border border-[#2B2F3D]"
                      }`}
                    >
                      {result.has_ai_metadata
                        ? "AI PROMPT FOUND"
                        : result.has_c2pa
                        ? "C2PA SIGNED"
                        : "UNMARKED CONTAINER"}
                    </span>
                  </div>

                  <p className="text-[11px] text-[#9FA6B2]">{result.provenance.provenance_summary}</p>

                  {result.provenance.exif_summary?.camera_make && (
                    <div className="font-mono text-[10px] text-[#6B7280]">
                      Camera Hardware: {result.provenance.exif_summary.camera_make}{" "}
                      {result.provenance.exif_summary.camera_model}
                    </div>
                  )}

                  {result.provenance.ai_prompt_snippet && (
                    <div className="rounded bg-[#12141A] p-2 font-mono text-[10px] text-[#FBBF24] border border-[#2B2F3D] break-words">
                      <span className="text-[#6B7280] block text-[9px]">EXTRACTED GENERATIVE PROMPT:</span>
                      &quot;{result.provenance.ai_prompt_snippet}&quot;
                    </div>
                  )}
                </div>
              )}

              {/* File Specs & Cryptography */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[10px] rounded-lg border border-[#2B2F3D] bg-[#12141A] p-3">
                <div>
                  <span className="text-[#6B7280] block">RESOLUTION</span>
                  <span className="text-white">
                    {result.image_width} × {result.image_height}
                  </span>
                </div>
                <div>
                  <span className="text-[#6B7280] block">FORMAT</span>
                  <span className="text-[#D4AF37]">{result.image_format}</span>
                </div>
                <div>
                  <span className="text-[#6B7280] block">INFERENCE TIME</span>
                  <span className="text-white">{result.processing_time_ms} ms</span>
                </div>
                <div>
                  <span className="text-[#6B7280] block">SHA-256 HASH</span>
                  <span className="text-[#9FA6B2] truncate block" title={result.file_hash}>
                    {result.file_hash.slice(0, 10)}...
                  </span>
                </div>
              </div>

              {/* Methodological Boundaries & Scientific Disclaimers */}
              <div className="rounded-lg border border-[#2B2F3D]/60 bg-[#0F1117] p-3 text-[11px] text-[#6B7280] space-y-1">
                <span className="text-xs font-semibold text-[#9FA6B2] block">
                  Methodological Epistemic Boundaries
                </span>
                <ul className="list-disc pl-4 space-y-1">
                  {result.limitations.map((lim, idx) => (
                    <li key={idx}>{lim}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
