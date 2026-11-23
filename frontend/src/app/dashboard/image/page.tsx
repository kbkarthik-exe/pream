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
import {
  Image as ImageIcon,
  UploadCloud,
  RotateCcw,
  Download,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Activity,
  Clock,
  Fingerprint,
  Cpu,
  Layers,
  Sparkles,
  Flame,
  ShieldCheck,
} from "lucide-react";

const MAX_FILE_SIZE_MB = 15;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const SUPPORTED_EXTS = ["image/jpeg", "image/png", "image/webp"];

type HeatmapViewMode = "original" | "ela" | "noise";

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
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingHistoryId, setDownloadingHistoryId] = useState<number | null>(null);
  const [heatmapView, setHeatmapView] = useState<HeatmapViewMode>("original");

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Revoke object URL on unmount or file change
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
      // Fallback
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDownloadImagePdf = async (analysisId?: number) => {
    const targetId = analysisId || result?.analysis_id;
    if (!targetId) return;

    if (analysisId) {
      setDownloadingHistoryId(analysisId);
    } else {
      setDownloadingPdf(true);
    }
    setErrorMsg(null);
    try {
      await imageApi.downloadPdf(targetId);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(`Failed to download report: ${err.message}`);
      } else {
        setErrorMsg("Failed to download PDF report from backend.");
      }
    } finally {
      if (analysisId) {
        setDownloadingHistoryId(null);
      } else {
        setDownloadingPdf(false);
      }
    }
  };

  const validateAndStageFile = (file: File) => {
    setErrorMsg(null);
    setResult(null);
    setCaseSaved(false);
    setHeatmapView("original");

    if (!SUPPORTED_EXTS.includes(file.type.toLowerCase())) {
      const ext = file.name.split(".").pop()?.toUpperCase() || "UNKNOWN";
      setErrorMsg(`Format '${ext}' is unsupported. Only JPEG, PNG, and WebP are supported.`);
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
      setErrorMsg(`File size (${sizeMb} MB) exceeds maximum limit of ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    if (file.size === 0) {
      setErrorMsg("File is empty (0 bytes). Please upload a valid image file.");
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    const objectUrl = URL.createObjectURL(file);
    setSelectedFile(file);
    setPreviewUrl(objectUrl);

    // Read natural dimensions
    const img = new window.Image();
    img.onload = () => {
      setImageDims({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.src = objectUrl;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndStageFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndStageFile(e.dataTransfer.files[0]);
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
    setHeatmapView("original");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMsg(null);
    setCaseSaved(false);
    setAnalysisStep("Initializing Swin Vision Transformer & ViT Ensemble...");

    const stepTimer1 = setTimeout(() => {
      setAnalysisStep("Computing 2D Fast Fourier Transform (FFT) & Anisotropy...");
    }, 450);

    const stepTimer2 = setTimeout(() => {
      setAnalysisStep("Generating Error Level Analysis (ELA) & Compression Heatmaps...");
    }, 900);

    try {
      const data = await imageApi.analyze(selectedFile, saveToCases);
      setResult(data);
      if (saveToCases) {
        setCaseSaved(true);
      }
      fetchHistory();
    } catch (err: unknown) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to execute image forensics. Please verify backend connectivity.");
      }
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setIsAnalyzing(false);
      setAnalysisStep("");
    }
  };

  const handleManualSaveCase = async () => {
    if (!result || !selectedFile) return;
    try {
      const aiPct = result.ai_probability !== null ? (result.ai_probability * 100).toFixed(1) + "%" : "N/A";
      const provSummary = result.provenance?.provenance_summary || "Automated image forensics executed.";
      await reportsApi.create({
        title: `Image Forensic Audit: ${selectedFile.name}`,
        media_type: "image",
        summary: `Result: ${result.classification} (${aiPct} AI confidence). SHA-256: ${result.file_hash}. ${provSummary}`,
        is_private: true,
      });
      setCaseSaved(true);
    } catch {
      setErrorMsg("Could not save case to repository.");
    }
  };

  const getVerdictDetails = (classification: string) => {
    const upper = classification.toUpperCase();
    if (upper.includes("AI-GENERATED") || upper.includes("FAKE")) {
      return {
        color: "text-amber-400",
        border: "border-amber-500/40",
        bg: "bg-amber-500/10",
        icon: AlertTriangle,
      };
    }
    if (upper.includes("HUMAN") || upper.includes("REAL")) {
      return {
        color: "text-emerald-400",
        border: "border-emerald-500/40",
        bg: "bg-emerald-500/10",
        icon: CheckCircle2,
      };
    }
    return {
      color: "text-[#D6B15E]",
      border: "border-[#D6B15E]/40",
      bg: "bg-[#D6B15E]/10",
      icon: HelpCircle,
    };
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "READY":
        return <span className="rounded bg-emerald-950/40 border border-emerald-500/40 px-1.5 py-0.5 font-mono text-[9px] text-emerald-300 font-bold">READY</span>;
      case "RESOURCE_CONSTRAINED":
        return <span className="rounded bg-amber-950/40 border border-amber-500/40 px-1.5 py-0.5 font-mono text-[9px] text-amber-300 font-bold">RESOURCE CONSTRAINED</span>;
      case "UNAVAILABLE":
        return <span className="rounded bg-neutral-900 border border-neutral-700 px-1.5 py-0.5 font-mono text-[9px] text-neutral-400 font-bold">UNAVAILABLE</span>;
      case "CONFIGURATION_REQUIRED":
        return <span className="rounded bg-blue-950/40 border border-blue-500/40 px-1.5 py-0.5 font-mono text-[9px] text-blue-300 font-bold">OPTIONAL CLOUD</span>;
      default:
        return <span className="rounded bg-red-950/40 border border-red-500/40 px-1.5 py-0.5 font-mono text-[9px] text-red-300 font-bold">{status}</span>;
    }
  };

  // Determine current image display source based on selected heatmap tab
  const getActiveDisplayImage = () => {
    if (heatmapView === "ela" && result?.heatmap?.heatmap_data_url) {
      return result.heatmap.heatmap_data_url;
    }
    if (heatmapView === "noise" && result?.heatmap?.noise_residual_data_url) {
      return result.heatmap.noise_residual_data_url;
    }
    return previewUrl;
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D6B15E] font-bold">MOD-IMG-02</span>
            <span className="text-[#3A404D]">&bull;</span>
            <span className="text-xs text-[#A3A7B0]">Multi-Model Vision &amp; Compression Forensics</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#F5F5F2]">
            AI Image Detection &amp; Generative Forensics
          </h1>
          <p className="mt-1 text-xs text-[#A3A7B0]">
            Evaluate digital imagery for synthetic markers using Swin ViT, ViT-Base global attention, 2D Fourier (FFT) octant anisotropy, and Error Level Analysis (ELA) heatmaps.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="self-start sm:self-auto rounded-lg border border-[#292D35] bg-[#12151B] px-3.5 py-1.5 text-xs text-[#A3A7B0] hover:border-[#D6B15E] hover:text-[#D6B15E] transition-colors"
        >
          &larr; Overview
        </Link>
      </div>

      {/* Main Analysis Workspace */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Upload & Viewer Column */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#292D35] pb-3">
              <div className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4 text-[#D6B15E]" />
                <span className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                  Image Payload &amp; Forensic Heatmap Viewer
                </span>
              </div>
              <span className="font-mono text-[10px] text-[#737984]">
                JPEG, PNG, WebP &bull; Max 15 MB
              </span>
            </div>

            <form onSubmit={handleRunAnalysis} className="mt-4 space-y-4">
              {/* Drag and Drop Zone / Image & Heatmap Preview */}
              {!previewUrl ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`rounded-2xl border-2 border-dashed p-10 text-center transition-all cursor-pointer ${
                    isDragging
                      ? "border-[#D6B15E] bg-[#181C23] shadow-[0_0_20px_rgba(214,177,94,0.15)]"
                      : "border-[#292D35] bg-[#090A0D] hover:border-[#D6B15E]/50 hover:bg-[#12151B]"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[#292D35] bg-[#181C23] text-[#D6B15E]">
                    <UploadCloud className="h-7 w-7" />
                  </div>
                  <h3 className="mt-4 text-xs font-bold text-[#F5F5F2] uppercase tracking-wide">
                    Drag &amp; Drop Image Payload
                  </h3>
                  <p className="mt-1 text-[11px] text-[#A3A7B0]">
                    Or click to browse your workstation filesystem
                  </p>
                  <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#292D35] bg-[#181C23] px-3 py-1 font-mono text-[10px] text-[#737984]">
                    <span>Magic Byte Validation</span>
                    <span>&bull;</span>
                    <span>In-Memory Pillow Decoding</span>
                    <span>&bull;</span>
                    <span>Error Level Analysis</span>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-[#292D35] bg-[#090A0D] p-4 space-y-4">
                  {/* Heatmap Layer View Tabs */}
                  {result?.heatmap && (
                    <div className="flex items-center justify-between border-b border-[#292D35] pb-2.5">
                      <div className="flex items-center gap-1.5 font-mono text-xs">
                        <button
                          type="button"
                          onClick={() => setHeatmapView("original")}
                          className={`px-3 py-1 rounded-lg transition-colors cursor-pointer text-[11px] font-bold ${
                            heatmapView === "original"
                              ? "bg-[#D6B15E] text-[#090A0D]"
                              : "bg-[#181C23] text-[#A3A7B0] hover:text-[#F5F5F2] border border-[#292D35]"
                          }`}
                        >
                          Original Image
                        </button>
                        <button
                          type="button"
                          onClick={() => setHeatmapView("ela")}
                          className={`flex items-center gap-1 px-3 py-1 rounded-lg transition-colors cursor-pointer text-[11px] font-bold ${
                            heatmapView === "ela"
                              ? "bg-[#D6B15E] text-[#090A0D]"
                              : "bg-[#181C23] text-[#A3A7B0] hover:text-[#F5F5F2] border border-[#292D35]"
                          }`}
                        >
                          <Flame className="h-3 w-3" />
                          <span>ELA Heatmap (Q=95)</span>
                        </button>
                        {result.heatmap.noise_residual_data_url && (
                          <button
                            type="button"
                            onClick={() => setHeatmapView("noise")}
                            className={`px-3 py-1 rounded-lg transition-colors cursor-pointer text-[11px] font-bold ${
                              heatmapView === "noise"
                                ? "bg-[#D6B15E] text-[#090A0D]"
                                : "bg-[#181C23] text-[#A3A7B0] hover:text-[#F5F5F2] border border-[#292D35]"
                            }`}
                          >
                            Noise Residual Map
                          </button>
                        )}
                      </div>

                      <span className="font-mono text-[10px] text-[#737984]">
                        Layer: {heatmapView.toUpperCase()}
                      </span>
                    </div>
                  )}

                  {/* Image Display Surface */}
                  <div className="relative aspect-video max-h-80 w-full overflow-hidden rounded-xl bg-black flex items-center justify-center border border-[#292D35]">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={getActiveDisplayImage() || previewUrl}
                      alt="Active forensic display"
                      className="max-h-full max-w-full object-contain"
                    />

                    {/* Overlay Tag */}
                    <div className="absolute top-2 left-2 rounded bg-black/70 backdrop-blur-sm border border-[#292D35] px-2 py-0.5 font-mono text-[10px] text-[#D6B15E]">
                      {heatmapView === "original"
                        ? "RAW CAPTURE"
                        : heatmapView === "ela"
                        ? "ELA COMPRESSION RESIDUALS"
                        : "SPATIAL NOISE VARIANCE"}
                    </div>
                  </div>

                  {/* Colormap Legend for Heatmaps */}
                  {heatmapView !== "original" && (
                    <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3 text-xs space-y-2">
                      <div className="flex items-center justify-between text-[10px] font-mono text-[#A3A7B0]">
                        <span>Thermal Heatmap Scale:</span>
                        <span>Blue (Authentic Baseline) &rarr; Cyan &rarr; Green &rarr; Yellow &rarr; Red (High Anomaly)</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-gradient-to-r from-blue-700 via-cyan-400 via-green-400 via-yellow-400 to-red-600 border border-[#292D35]" />
                      <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-[10px] text-[#737984]">
                        <div>
                          <span className="block text-[#A3A7B0]">MEAN ERROR</span>
                          <span className="text-[#F5F5F2] font-bold">{result?.heatmap?.ela_mean_error.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="block text-[#A3A7B0]">MAX ERROR SPIKE</span>
                          <span className="text-[#F5F5F2] font-bold">{result?.heatmap?.ela_max_error.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="block text-[#A3A7B0]">DISCONTINUITY SD</span>
                          <span className="text-[#D6B15E] font-bold">{result?.heatmap?.ela_discontinuity_score.toFixed(2)} SD</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Metadata Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-[#A3A7B0] border-t border-[#292D35] pt-3">
                    <div className="flex items-center gap-3">
                      <span className="text-[#F5F5F2] font-semibold truncate max-w-xs">
                        {selectedFile?.name}
                      </span>
                      <span>&bull;</span>
                      <span>
                        {selectedFile ? (selectedFile.size / (1024 * 1024)).toFixed(2) : 0} MB
                      </span>
                      {imageDims && (
                        <>
                          <span>&bull;</span>
                          <span>
                            {imageDims.width} &times; {imageDims.height} px
                          </span>
                        </>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={handleClear}
                      className="flex items-center gap-1 text-[#737984] hover:text-red-400 transition-colors cursor-pointer"
                    >
                      <RotateCcw className="h-3 w-3" />
                      <span>Remove</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Execution Controls */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-[#A3A7B0]">
                  <input
                    type="checkbox"
                    checked={saveToCases}
                    onChange={(e) => setSaveToCases(e.target.checked)}
                    className="rounded border-[#292D35] bg-[#181C23] text-[#D6B15E] focus:ring-[#D6B15E]"
                  />
                  <span>Automatically log to Case Reports</span>
                </label>

                <button
                  type="submit"
                  disabled={isAnalyzing || !selectedFile}
                  className="inline-flex items-center gap-2 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-5 py-2.5 font-mono text-xs font-bold text-[#090A0D] shadow-[0_0_15px_rgba(214,177,94,0.2)] transition-opacity hover:opacity-95 disabled:opacity-50 cursor-pointer"
                >
                  {isAnalyzing ? (
                    <>
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
                      <span>Executing Multi-Model Audit...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>Execute Forensic Image Audit</span>
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* In-Flight Multi-Step Telemetry Ticker */}
            {isAnalyzing && (
              <div className="mt-4 rounded-xl border border-[#D6B15E]/30 bg-[#181C23] p-3 text-xs text-[#F0D58A] flex items-center gap-2.5 animate-pulse">
                <Activity className="h-4 w-4 animate-spin text-[#D6B15E]" />
                <span className="font-mono text-[11px]">{analysisStep}</span>
              </div>
            )}

            {errorMsg && (
              <div className="mt-4 rounded-xl border border-red-500/30 bg-red-950/20 p-3 text-xs text-red-300 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>

          {/* Multi-Detector Vision Consensus Hub */}
          {result?.detector_scores && result.detector_scores.length > 0 && (
            <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-[#292D35] pb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-[#D6B15E]" />
                  <h3 className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                    Multi-Detector Vision Consensus Hub
                  </h3>
                </div>
                {result.ensemble && (
                  <span className="font-mono text-[10px] text-[#D6B15E]">
                    {result.ensemble.active_detectors_count} Active Models &bull; T={result.ensemble.temperature_applied} &bull; &rho;={result.ensemble.covariance_penalty}
                  </span>
                )}
              </div>

              {/* Individual Model Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.detector_scores.map((detector, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-[#292D35] bg-[#181C23] p-3.5 space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-mono text-[11px] font-bold text-[#F5F5F2]">
                          {detector.model_name}
                        </div>
                        <div className="font-mono text-[9px] text-[#737984]">
                          {detector.detector_id}
                        </div>
                      </div>
                      {getStatusBadge(detector.status)}
                    </div>

                    {/* Progress Bar & Scores */}
                    {detector.calibrated_score !== null && detector.calibrated_score !== undefined ? (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between font-mono text-[10px]">
                          <span className="text-[#A3A7B0]">Calibrated AI Prob:</span>
                          <span className="font-bold text-[#D6B15E]">
                            {(detector.calibrated_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-[#090A0D] overflow-hidden border border-[#292D35]">
                          <div
                            className="h-full bg-gradient-to-r from-emerald-500 via-[#D6B15E] to-amber-500"
                            style={{ width: `${Math.min(100, Math.max(0, detector.calibrated_score * 100))}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="font-mono text-[10px] text-[#737984] italic">
                        Model offline or optional credentials not supplied.
                      </div>
                    )}

                    {/* Evidence Snippet */}
                    {detector.evidence && detector.evidence.length > 0 && (
                      <div className="text-[10px] text-[#A3A7B0] line-clamp-2 border-t border-[#292D35] pt-1.5">
                        {detector.evidence[0]}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Ensemble Consensus Telemetry */}
              {result.ensemble && (
                <div className="rounded-xl border border-[#D6B15E]/30 bg-[#090A0D] p-3.5 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-mono text-[10px] text-[#D6B15E] font-bold uppercase">
                    <span>Ensemble Consensus Telemetry</span>
                    <span>Consensus: {(result.ensemble.consensus_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="space-y-1">
                    {result.ensemble.notes.map((note, nIdx) => (
                      <div key={nIdx} className="text-[10px] text-[#A3A7B0] flex items-start gap-1.5">
                        <span className="text-[#D6B15E]">&bull;</span>
                        <span>{note}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Results & History Column */}
        <div className="lg:col-span-5 space-y-4">
          {result ? (
            <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm space-y-5">
              {/* Verdict Banner */}
              {(() => {
                const verdict = getVerdictDetails(result.classification);
                const VerdictIcon = verdict.icon;
                return (
                  <div className={`rounded-xl border ${verdict.border} ${verdict.bg} p-4`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <VerdictIcon className={`h-6 w-6 ${verdict.color}`} />
                        <div>
                          <div className="font-mono text-[10px] tracking-widest text-[#A3A7B0] uppercase">
                            Verdict Classification
                          </div>
                          <div className={`text-base font-bold ${verdict.color}`}>
                            {result.classification}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-[10px] text-[#737984] uppercase">AI Confidence</div>
                        <div className="font-mono text-lg font-bold text-[#F5F5F2]">
                          {result.ai_probability !== null ? (result.ai_probability * 100).toFixed(1) + "%" : "—"}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Provenance & Cryptographic Ledger */}
              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3.5 space-y-2 text-xs">
                <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-[#D6B15E] uppercase tracking-wider">
                  <Fingerprint className="h-3.5 w-3.5" />
                  <span>Provenance &amp; Cryptographic SHA-256</span>
                </div>
                <div className="font-mono text-[10px] text-[#A3A7B0] break-all bg-[#090A0D] p-2 rounded border border-[#292D35]">
                  {result.file_hash}
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[10px]">
                  <div>
                    <span className="text-[#737984] block">CAMERA / SOFTWARE</span>
                    <span className="text-[#F5F5F2] truncate block">
                      {result.provenance?.exif_summary?.camera_model || result.provenance?.exif_summary?.software || "None (Stripped)"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#737984] block">C2PA CREDENTIALS</span>
                    <span className={result.has_c2pa ? "text-emerald-400 font-bold" : "text-[#737984]"}>
                      {result.has_c2pa ? "Verified Signature" : "Not Present"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Spatial & Frequency Forensic Indicators */}
              <div className="space-y-2.5">
                <div className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5" />
                  <span>Spatial &amp; Frequency Metrics</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">2D FFT ANISOTROPY</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.spectral_anisotropy.toFixed(3)}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">Octant symmetry variance</span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">SPECTRAL HIGH-FREQ</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {(result.fft_high_freq_ratio * 100).toFixed(1)}%
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">Nyquist energy ratio</span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">LAPLACIAN VARIANCE</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.noise_variance.toFixed(1)}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">High-pass noise residual</span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">ELA DISCONTINUITY</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.heatmap?.ela_discontinuity_score !== undefined ? `${result.heatmap.ela_discontinuity_score.toFixed(2)} SD` : "—"}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">Compression error SD</span>
                  </div>
                </div>
              </div>

              {/* Forensic Evidence Signals */}
              {result.evidence && result.evidence.length > 0 && (
                <div className="space-y-1.5">
                  <div className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5" />
                    <span>Forensic Evidence Signals</span>
                  </div>
                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3 space-y-2">
                    {result.evidence.map((ev, idx) => (
                      <div key={idx} className="flex items-start justify-between gap-2 text-xs border-b border-[#292D35]/50 pb-1.5 last:border-0 last:pb-0">
                        <div>
                          <span className="font-mono font-semibold text-[#F5F5F2]">{ev.signal}: </span>
                          <span className="text-[#A3A7B0]">{ev.finding}</span>
                        </div>
                        {ev.metric && (
                          <span className="font-mono text-[10px] text-[#D6B15E] bg-[#090A0D] px-1.5 py-0.5 rounded shrink-0">
                            {ev.metric}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Forensic Summary */}
              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3.5 text-xs text-[#A3A7B0] leading-relaxed">
                <span className="font-mono text-[10px] font-bold text-[#D6B15E] block uppercase mb-1">
                  Forensic Summary
                </span>
                {result.provenance?.provenance_summary || "Image analysis executed across Swin ViT, ViT-Base, FFT spectral, and ELA metrics."}
              </div>

              {/* Action Buttons: Save Case & Download PDF */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#292D35] pt-4">
                <button
                  type="button"
                  onClick={handleManualSaveCase}
                  disabled={caseSaved}
                  className="rounded-lg border border-[#292D35] bg-[#181C23] px-3 py-1.5 text-xs font-mono text-[#D6B15E] hover:border-[#D6B15E] disabled:opacity-50 transition-colors cursor-pointer"
                >
                  {caseSaved ? "✓ Case Saved to Reports" : "+ Save to Case Ledger"}
                </button>

                <button
                  type="button"
                  onClick={() => handleDownloadImagePdf(result.analysis_id)}
                  disabled={downloadingPdf}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-3.5 py-1.5 font-mono text-xs font-bold text-[#090A0D] hover:opacity-95 disabled:opacity-50 transition-all cursor-pointer shadow-[0_0_12px_rgba(214,177,94,0.15)]"
                >
                  {downloadingPdf ? (
                    <>
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <Download className="h-3.5 w-3.5" />
                      <span>Download PDF</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-8 text-center shadow-sm">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-[#292D35] bg-[#181C23] text-[#737984]">
                <ImageIcon className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-sm font-semibold text-[#F5F5F2]">Awaiting Image Payload</h3>
              <p className="mt-1 text-xs text-[#737984] max-w-xs mx-auto">
                Drop or select a JPEG, PNG, or WebP file to extract Multi-Model Vision Transformer activations, 2D FFT spectral metrics, and ELA heatmaps.
              </p>
            </div>
          )}

          {/* Historical Image Analyses Drawer */}
          <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#292D35] pb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-[#D6B15E]" />
                <h3 className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                  Image Analysis History
                </h3>
              </div>
              <span className="font-mono text-[10px] text-[#737984]">{history.length} records</span>
            </div>

            {loadingHistory ? (
              <div className="py-6 text-center text-xs text-[#737984] font-mono">Loading history...</div>
            ) : history.length === 0 ? (
              <div className="py-6 text-center text-xs text-[#737984]">No previous image audits in session.</div>
            ) : (
              <div className="mt-3 space-y-2 max-h-64 overflow-y-auto pr-1">
                {history.slice(0, 8).map((item, ihIdx) => (
                  <div
                    key={`imghist-${item.id ?? ihIdx}-${ihIdx}`}
                    className="flex items-center justify-between rounded-xl border border-[#292D35] bg-[#181C23] p-2.5 text-xs hover:border-[#3A404D] transition-colors"
                  >
                    <div className="truncate max-w-[180px]">
                      <div className="font-mono text-[11px] font-semibold text-[#F0D58A] truncate">
                        #{item.id} &bull; {item.classification}
                      </div>
                      <div className="text-[10px] text-[#737984] truncate">
                        {item.image_width} &times; {item.image_height} px &bull; {item.confidence_score !== null ? (item.confidence_score * 100).toFixed(0) + "% conf" : "—"}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleDownloadImagePdf(item.id)}
                      disabled={downloadingHistoryId === item.id}
                      className="p-1.5 rounded-lg border border-[#292D35] bg-[#12151B] text-[#D6B15E] hover:border-[#D6B15E] disabled:opacity-50 transition-colors cursor-pointer"
                      title="Download PDF report"
                    >
                      {downloadingHistoryId === item.id ? (
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-[#D6B15E] border-t-transparent block" />
                      ) : (
                        <Download className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
