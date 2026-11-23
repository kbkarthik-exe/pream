"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  videoApi,
  reportsApi,
  type VideoAnalysisResponse,
  type VideoAnalysisHistoryItem,
} from "@/lib/api";
import {
  Film,
  UploadCloud,
  RotateCcw,
  Download,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Activity,
  Clock,
  Fingerprint,
  Cpu,
  Layers,
  ShieldCheck,
  Eye,
  Info,
} from "lucide-react";

const MAX_FILE_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const SUPPORTED_EXTS = [".mp4", ".mov", ".webm"];
const SUPPORTED_MIMES = ["video/mp4", "video/quicktime", "video/webm"];

export default function VideoDetectionPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [videoMeta, setVideoMeta] = useState<{ width: number; height: number; duration: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<string>("");
  const [saveToCases, setSaveToCases] = useState(false);
  const [queryHive, setQueryHive] = useState(false);
  const [result, setResult] = useState<VideoAnalysisResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [caseSaved, setCaseSaved] = useState(false);
  const [savedCaseId, setSavedCaseId] = useState<number | null>(null);
  const [history, setHistory] = useState<VideoAnalysisHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingHistoryId, setDownloadingHistoryId] = useState<number | null>(null);
  const [loadingHistoryDetailsId, setLoadingHistoryDetailsId] = useState<number | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoPreviewRef = useRef<HTMLVideoElement>(null);

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
    videoApi
      .getHistory()
      .then((records) => {
        if (!ignore) {
          setHistory(records);
          setHistoryError(null);
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : "Failed to load history.";
          setHistoryError(msg);
        }
      })
      .finally(() => {
        if (!ignore) {
          setLoadingHistory(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const records = await videoApi.getHistory();
      setHistory(records);
      setHistoryError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to refresh history.";
      setHistoryError(msg);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDownloadVideoPdf = async (analysisId?: number) => {
    const targetId = analysisId || result?.analysis_id;
    if (!targetId) return;

    if (analysisId) {
      setDownloadingHistoryId(analysisId);
    } else {
      setDownloadingPdf(true);
    }
    setErrorMsg(null);
    try {
      await videoApi.downloadPdf(targetId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to download forensic PDF report.";
      setErrorMsg(msg);
    } finally {
      if (analysisId) {
        setDownloadingHistoryId(null);
      } else {
        setDownloadingPdf(false);
      }
    }
  };

  const handleLoadAnalysisDetails = async (id: number) => {
    setLoadingHistoryDetailsId(id);
    setErrorMsg(null);
    try {
      const detailed = await videoApi.getAnalysis(id);
      setResult(detailed);
      setCaseSaved(Boolean(detailed.case_report_id));
      setSavedCaseId(detailed.case_report_id ?? null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to retrieve analysis record.";
      setErrorMsg(msg);
    } finally {
      setLoadingHistoryDetailsId(null);
    }
  };

  const validateAndProcessFile = (file: File) => {
    setErrorMsg(null);
    setResult(null);
    setCaseSaved(false);
    setSavedCaseId(null);

    // 1. File extension validation
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    const isMimeValid = SUPPORTED_MIMES.includes(file.type.toLowerCase());
    const isExtValid = SUPPORTED_EXTS.includes(ext);

    if (!isMimeValid && !isExtValid) {
      setErrorMsg(`Unsupported format (${file.type || ext}). AICF safely supports MP4 (.mp4), QuickTime (.mov), and WebM (.webm).`);
      return;
    }

    // 2. Empty file validation
    if (file.size === 0) {
      setErrorMsg("The selected video file is empty (0 bytes). Please upload a valid video stream.");
      return;
    }

    // 3. File size limit validation
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMsg(
        `Video file size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds maximum platform limit of ${MAX_FILE_SIZE_MB} MB.`
      );
      return;
    }

    setSelectedFile(file);

    // Create object URL for client preview & probe dimensions
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // Extract preliminary HTML5 video metadata
    const tempVideo = document.createElement("video");
    tempVideo.preload = "metadata";
    tempVideo.onloadedmetadata = () => {
      setVideoMeta({
        width: tempVideo.videoWidth,
        height: tempVideo.videoHeight,
        duration: tempVideo.duration,
      });
    };
    tempVideo.src = objectUrl;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const handleClear = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setVideoMeta(null);
    setResult(null);
    setErrorMsg(null);
    setCaseSaved(false);
    setSavedCaseId(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMsg("Please upload a video file to analyze.");
      return;
    }

    setIsAnalyzing(true);
    setErrorMsg(null);
    setResult(null);
    setCaseSaved(false);
    setSavedCaseId(null);

    try {
      setAnalysisStep("Uploading stream & extracting uniform temporal keyframes via OpenCV...");
      const analysisResult = await videoApi.analyze(selectedFile, saveToCases, queryHive);
      setResult(analysisResult);

      if (analysisResult.case_report_id) {
        setCaseSaved(true);
        setSavedCaseId(analysisResult.case_report_id);
      }

      await fetchHistory();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else if (err instanceof Error) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to execute video forensics. Please verify backend service availability.");
      }
    } finally {
      setIsAnalyzing(false);
      setAnalysisStep("");
    }
  };

  const handleManualSaveCase = async () => {
    if (!result || !selectedFile) return;
    setErrorMsg(null);
    try {
      const scorePct = `${(result.confidence_score * 100).toFixed(1)}%`;
      const summaryText =
        `Classification: ${result.classification} (Confidence: ${scorePct}). ` +
        `File: ${result.file_name} (${result.video_width}x${result.video_height}, ${result.duration_seconds.toFixed(1)}s, ${result.fps} fps). ` +
        `Sampled Frames: ${result.sampled_frame_count} | Mean AI: ${(result.ai_probability_mean * 100).toFixed(1)}%, ` +
        `Peak AI: ${(result.ai_probability_max * 100).toFixed(1)}% at t=${result.peak_frame_timestamp.toFixed(1)}s | ` +
        `Flicker Score: ${result.temporal_flicker_score.toFixed(4)}.`;

      const created = await reportsApi.create({
        title: `Video Forensic Audit: ${selectedFile.name}`,
        media_type: "video",
        summary: summaryText,
        is_private: true,
      });
      setCaseSaved(true);
      setSavedCaseId(created.id);
    } catch {
      setErrorMsg("Could not record video case report in database.");
    }
  };

  const getVerdictDetails = (classification: string) => {
    switch (classification) {
      case "Likely Manipulated":
      case "LIKELY_MANIPULATED":
      case "HIGHLY_LIKELY_AI":
        return {
          color: "text-amber-400",
          border: "border-amber-500/40",
          bg: "bg-amber-500/10",
          badge: "bg-amber-500/20 text-amber-300 border-amber-500/30",
          icon: AlertTriangle,
          label: "Likely Manipulated / Synthetic Deepfake",
        };
      case "SUSPECTED_AI":
        return {
          color: "text-amber-300",
          border: "border-amber-500/30",
          bg: "bg-amber-500/5",
          badge: "bg-amber-500/15 text-amber-200 border-amber-500/20",
          icon: AlertTriangle,
          label: "Suspected Synthetic / AI",
        };
      case "Likely Real":
      case "LIKELY_REAL":
      case "HIGHLY_LIKELY_AUTHENTIC":
        return {
          color: "text-emerald-400",
          border: "border-emerald-500/40",
          bg: "bg-emerald-500/10",
          badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
          icon: CheckCircle2,
          label: "Likely Real / Human Authentic",
        };
      case "LIKELY_AUTHENTIC":
        return {
          color: "text-emerald-300",
          border: "border-emerald-500/30",
          bg: "bg-emerald-500/5",
          badge: "bg-emerald-500/15 text-emerald-200 border-emerald-500/20",
          icon: CheckCircle2,
          label: "Likely Human Authentic",
        };
      case "Inconclusive":
      case "INCONCLUSIVE":
      default:
        return {
          color: "text-[#D6B15E]",
          border: "border-[#D6B15E]/40",
          bg: "bg-[#D6B15E]/10",
          badge: "bg-[#D6B15E]/20 text-[#F0D58A] border-[#D6B15E]/30",
          icon: HelpCircle,
          label: "Inconclusive / Mixed Signals",
        };
    }
  };

  const getFrameBadge = (frameClass: string) => {
    switch (frameClass) {
      case "HIGHLY_LIKELY_AI":
        return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "SUSPECTED_AI":
        return "bg-amber-500/10 text-amber-200 border-amber-500/20";
      case "HIGHLY_LIKELY_AUTHENTIC":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
      case "LIKELY_AUTHENTIC":
        return "bg-emerald-500/10 text-emerald-200 border-emerald-500/20";
      default:
        return "bg-[#181C23] text-[#A3A7B0] border-[#292D35]";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D6B15E] font-bold">MOD-VID-03</span>
            <span className="text-[#3A404D]">&bull;</span>
            <span className="text-xs text-[#A3A7B0]">Keyframe ViT Screening &amp; Temporal Flicker Forensics</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#F5F5F2]">
            AI Video Detection &amp; Temporal Forensics
          </h1>
          <p className="mt-1 text-xs text-[#A3A7B0]">
            Evaluate video streams for generative synthetic keyframes, temporal flicker discontinuities, and optical flow anomalies.
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
        {/* Upload & Form Column */}
        <div className="lg:col-span-6 space-y-4">
          <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#292D35] pb-3">
              <div className="flex items-center gap-2">
                <Film className="h-4 w-4 text-[#D6B15E]" />
                <span className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                  Video Stream Ingestion
                </span>
              </div>
              <span className="font-mono text-[10px] text-[#737984]">
                MP4, MOV, WebM &bull; Max 50 MB
              </span>
            </div>

            <form onSubmit={handleRunAnalysis} className="mt-4 space-y-4">
              {/* Drag and Drop Zone / Video Preview */}
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
                    accept="video/mp4,video/quicktime,video/webm"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[#292D35] bg-[#181C23] text-[#D6B15E]">
                    <UploadCloud className="h-7 w-7" />
                  </div>
                  <h3 className="mt-4 text-xs font-bold text-[#F5F5F2] uppercase tracking-wide">
                    Select or Drop Video File
                  </h3>
                  <p className="mt-1 text-[11px] text-[#A3A7B0]">
                    Stream ingest with OpenCV temporal frame extraction &amp; ViT screening
                  </p>
                  <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#292D35] bg-[#181C23] px-3 py-1 font-mono text-[10px] text-[#737984]">
                    <span>Magic Byte Validation</span>
                    <span>&bull;</span>
                    <span>Uniform 1.0s Sampling</span>
                    <span>&bull;</span>
                    <span>Temporal Differencing</span>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-[#292D35] bg-[#090A0D] p-4 space-y-4">
                  <div className="relative aspect-video max-h-72 w-full overflow-hidden rounded-xl bg-black flex items-center justify-center border border-[#292D35]">
                    <video
                      ref={videoPreviewRef}
                      src={previewUrl}
                      controls
                      playsInline
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>

                  {/* Metadata Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-[#A3A7B0] border-t border-[#292D35] pt-3">
                    <div className="flex items-center gap-2 truncate max-w-sm">
                      <span className="text-[#F5F5F2] font-semibold truncate">
                        {selectedFile?.name}
                      </span>
                      <span>&bull;</span>
                      <span>
                        {selectedFile ? (selectedFile.size / (1024 * 1024)).toFixed(2) : 0} MB
                      </span>
                      {videoMeta && (
                        <>
                          <span>&bull;</span>
                          <span>
                            {videoMeta.width}&times;{videoMeta.height} px
                          </span>
                          <span>&bull;</span>
                          <span>{videoMeta.duration.toFixed(1)}s</span>
                        </>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={handleClear}
                      className="flex items-center gap-1 text-[#737984] hover:text-red-400 transition-colors cursor-pointer shrink-0"
                      title="Clear selection"
                    >
                      <RotateCcw className="h-3 w-3" />
                      <span>Remove</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Advanced Options */}
              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3 space-y-2 text-xs">
                <label className="flex items-center gap-2 cursor-pointer text-[#A3A7B0] hover:text-[#F5F5F2] transition-colors">
                  <input
                    type="checkbox"
                    checked={saveToCases}
                    onChange={(e) => setSaveToCases(e.target.checked)}
                    className="rounded border-[#292D35] bg-[#090A0D] text-[#D6B15E] focus:ring-[#D6B15E]"
                  />
                  <span>Automatically log analysis into Case Reports</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-[#A3A7B0] hover:text-[#F5F5F2] transition-colors">
                  <input
                    type="checkbox"
                    checked={queryHive}
                    onChange={(e) => setQueryHive(e.target.checked)}
                    className="rounded border-[#292D35] bg-[#090A0D] text-[#D6B15E] focus:ring-[#D6B15E]"
                  />
                  <span>Enable optional Hive AI cloud adapter (requires server API key)</span>
                </label>
              </div>

              {/* Execution Controls */}
              <div className="flex items-center justify-between pt-2">
                <span className="text-[11px] text-[#737984] font-mono">
                  {selectedFile ? "Ready for frame extraction & analysis" : "No video payload loaded"}
                </span>

                <button
                  type="submit"
                  disabled={isAnalyzing || !selectedFile}
                  className="inline-flex items-center gap-2 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-5 py-2.5 font-mono text-xs font-bold text-[#090A0D] shadow-[0_0_15px_rgba(214,177,94,0.2)] transition-opacity hover:opacity-95 disabled:opacity-50 cursor-pointer"
                >
                  {isAnalyzing ? (
                    <>
                      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-black border-t-transparent" />
                      <span>Analyzing Video...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>Execute Video Forensics</span>
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* In-Flight Multi-Step Telemetry Ticker */}
            {isAnalyzing && (
              <div className="mt-4 rounded-xl border border-[#D6B15E]/30 bg-[#181C23] p-3 text-xs text-[#F0D58A] flex items-center gap-2.5 animate-pulse">
                <Activity className="h-4 w-4 animate-spin text-[#D6B15E] shrink-0" />
                <span className="font-mono text-[11px]">{analysisStep}</span>
              </div>
            )}

            {errorMsg && (
              <div className="mt-4 rounded-xl border border-red-500/30 bg-red-950/20 p-3 text-xs text-red-300 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>

          {/* Historical Video Analyses Drawer */}
          <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#292D35] pb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-[#D6B15E]" />
                <h3 className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                  Video Audit History
                </h3>
              </div>
              <span className="font-mono text-[10px] text-[#737984]">{history.length} records</span>
            </div>

            {loadingHistory ? (
              <div className="py-6 text-center text-xs text-[#737984] font-mono">Loading history...</div>
            ) : historyError ? (
              <div className="py-4 text-center text-xs text-red-400 font-mono">{historyError}</div>
            ) : history.length === 0 ? (
              <div className="py-6 text-center text-xs text-[#737984]">No previous video audits in session.</div>
            ) : (
              <div className="mt-3 space-y-2 max-h-72 overflow-y-auto pr-1">
                {history.map((item, vhIdx) => (
                  <div
                    key={`vidhist-${item.id ?? vhIdx}-${vhIdx}`}
                    className="flex items-center justify-between rounded-xl border border-[#292D35] bg-[#181C23] p-2.5 text-xs hover:border-[#3A404D] transition-colors"
                  >
                    <div
                      onClick={() => handleLoadAnalysisDetails(item.id)}
                      className="truncate max-w-[240px] cursor-pointer hover:opacity-80"
                      title="Click to view full forensic telemetry"
                    >
                      <div className="font-mono text-[11px] font-semibold text-[#F0D58A] truncate flex items-center gap-1.5">
                        <span>#{item.id}</span>
                        <span>&bull;</span>
                        <span className="truncate">{item.file_name}</span>
                      </div>
                      <div className="text-[10px] text-[#737984] truncate">
                        {item.classification} &bull; {(item.confidence_score * 100).toFixed(0)}% conf &bull; {item.duration_seconds.toFixed(1)}s
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => handleLoadAnalysisDetails(item.id)}
                        disabled={loadingHistoryDetailsId === item.id}
                        className="p-1.5 rounded-lg border border-[#292D35] bg-[#12151B] text-[#A3A7B0] hover:text-[#D6B15E] hover:border-[#D6B15E] disabled:opacity-50 transition-colors cursor-pointer"
                        title="Load forensic details"
                      >
                        {loadingHistoryDetailsId === item.id ? (
                          <span className="h-3 w-3 animate-spin rounded-full border-2 border-[#D6B15E] border-t-transparent block" />
                        ) : (
                          <Eye className="h-3.5 w-3.5" />
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDownloadVideoPdf(item.id)}
                        disabled={downloadingHistoryId === item.id}
                        className="p-1.5 rounded-lg border border-[#292D35] bg-[#12151B] text-[#D6B15E] hover:border-[#D6B15E] disabled:opacity-50 transition-colors cursor-pointer"
                        title="Download official PDF report"
                      >
                        {downloadingHistoryId === item.id ? (
                          <span className="h-3 w-3 animate-spin rounded-full border-2 border-[#D6B15E] border-t-transparent block" />
                        ) : (
                          <Download className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-6 space-y-4">
          {result ? (
            <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm space-y-5">
              {/* Verdict Banner */}
              {(() => {
                const verdict = getVerdictDetails(result.consensus_verdict || result.classification);
                const VerdictIcon = verdict.icon;
                return (
                  <div className={`rounded-xl border ${verdict.border} ${verdict.bg} p-4`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <VerdictIcon className={`h-6 w-6 ${verdict.color}`} />
                        <div>
                          <div className="font-mono text-[10px] tracking-widest text-[#A3A7B0] uppercase">
                            Video Forensic Verdict
                          </div>
                          <div className={`text-base font-bold ${verdict.color}`}>
                            {result.consensus_verdict || result.classification}
                          </div>
                          <div className="text-[11px] text-[#A3A7B0] font-mono">
                            {verdict.label}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-[10px] text-[#737984] uppercase">Consensus Confidence</div>
                        <div className="font-mono text-xl font-bold text-[#F5F5F2]">
                          {(result.confidence_score * 100).toFixed(1)}%
                        </div>
                        <div className="font-mono text-[10px] text-[#A3A7B0]">
                          Frame AI: {(result.ai_probability_mean * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Video Stream & Cryptographic Ledger */}
              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-[#D6B15E] uppercase tracking-wider">
                    <Fingerprint className="h-3.5 w-3.5" />
                    <span>Cryptographic SHA-256 Ledger</span>
                  </div>
                  <span className="font-mono text-[10px] text-[#737984]">
                    ID #{result.analysis_id}
                  </span>
                </div>
                <div className="font-mono text-[10px] text-[#A3A7B0] break-all bg-[#090A0D] p-2 rounded border border-[#292D35]">
                  {result.file_hash}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[10px]">
                  <div>
                    <span className="text-[#737984] block">DIMENSIONS</span>
                    <span className="text-[#F5F5F2] font-semibold">{result.video_width} &times; {result.video_height} px</span>
                  </div>
                  <div>
                    <span className="text-[#737984] block">DURATION</span>
                    <span className="text-[#F5F5F2] font-semibold">{result.duration_seconds.toFixed(1)}s ({result.fps} fps)</span>
                  </div>
                  <div>
                    <span className="text-[#737984] block">SAMPLED FRAMES</span>
                    <span className="text-[#F5F5F2] font-semibold">{result.sampled_frame_count} / {result.total_frames}</span>
                  </div>
                  <div>
                    <span className="text-[#737984] block">LATENCY</span>
                    <span className="text-[#F5F5F2] font-semibold">{result.processing_time_ms.toFixed(0)} ms</span>
                  </div>
                </div>
              </div>

              {/* Temporal & Peak Keyframe Metrics */}
              <div className="space-y-2.5">
                <div className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5" />
                  <span>Spatio-Temporal &amp; Keyframe Telemetry</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">PEAK AI KEYFRAME</span>
                    <span className="font-mono text-sm font-bold text-amber-400">
                      {(result.ai_probability_max * 100).toFixed(1)}%
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">
                      Observed at t = {result.peak_frame_timestamp.toFixed(1)}s
                    </span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">TEMPORAL FLICKER</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.temporal_flicker_score.toFixed(4)}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">
                      Inter-frame difference std dev
                    </span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">MEAN FRAME DELTA</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.temporal_telemetry?.mean_frame_difference !== undefined
                        ? result.temporal_telemetry.mean_frame_difference.toFixed(4)
                        : "—"}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">
                      Normalized pixel delta
                    </span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">FRAME CLASSIFIER</span>
                    <span className="font-mono text-xs font-bold text-[#D6B15E] truncate block">
                      Swin Transformer ViT
                    </span>
                    <span className="text-[10px] text-[#737984] block mt-0.5 truncate">
                      {result.frame_classifier_id}
                    </span>
                  </div>
                </div>
              </div>

              {/* Dedicated Facial Deepfake Forensics Panel */}
              <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-4 text-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-[#D6B15E] uppercase tracking-wider">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>Dedicated Facial Deepfake Detection</span>
                  </div>
                  <span
                    className={`rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-semibold ${
                      result.face_deepfake_status === "READY"
                        ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                        : result.face_deepfake_status === "NO_FACES_DETECTED"
                        ? "border-blue-500/40 bg-blue-500/10 text-blue-300"
                        : "border-amber-500/40 bg-amber-500/10 text-amber-300"
                    }`}
                  >
                    {result.face_deepfake_status === "READY"
                      ? "READY (MesoNet-4 Active)"
                      : result.face_deepfake_status === "NO_FACES_DETECTED"
                      ? "NO FACES DETECTED"
                      : "UNAVAILABLE (Weights Offline)"}
                  </span>
                </div>

                <p className="text-[11px] text-[#A3A7B0] leading-relaxed">
                  {result.facial_telemetry?.model_name || "MesoNet-4 Facial Forensics Head"} &bull; Evaluates 256x256 normalized face chips and 25% boundary seam gradient disparity for face-swap, blending, and reenactment artifacts.
                </p>

                {/* Facial Telemetry Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[10px]">
                  <div className="bg-[#090A0D] p-2 rounded border border-[#292D35]">
                    <span className="text-[#737984] block">FACES ANALYZED</span>
                    <span className="text-[#F5F5F2] font-semibold">
                      {result.facial_telemetry?.total_faces_analyzed ?? 0} ({result.facial_telemetry?.frames_with_faces ?? 0} frames)
                    </span>
                  </div>
                  <div className="bg-[#090A0D] p-2 rounded border border-[#292D35]">
                    <span className="text-[#737984] block">FACIAL MANIPULATION</span>
                    <span className="text-[#F5F5F2] font-semibold">
                      {result.facial_telemetry?.mean_facial_manipulation_score !== null && result.facial_telemetry?.mean_facial_manipulation_score !== undefined
                        ? `${(result.facial_telemetry.mean_facial_manipulation_score * 100).toFixed(1)}%`
                        : "Heuristic Seams"}
                    </span>
                  </div>
                  <div className="bg-[#090A0D] p-2 rounded border border-[#292D35]">
                    <span className="text-[#737984] block">SEAM DISPARITY (MAX)</span>
                    <span className="text-[#F5F5F2] font-semibold">
                      {result.facial_telemetry?.max_boundary_seam_delta !== undefined
                        ? result.facial_telemetry.max_boundary_seam_delta.toFixed(3)
                        : "0.000"}
                    </span>
                  </div>
                  <div className="bg-[#090A0D] p-2 rounded border border-[#292D35]">
                    <span className="text-[#737984] block">PEAK TIMESTAMP</span>
                    <span className="text-[#F5F5F2] font-semibold">
                      {result.facial_telemetry?.peak_manipulation_timestamp !== null && result.facial_telemetry?.peak_manipulation_timestamp !== undefined
                        ? `t=${result.facial_telemetry.peak_manipulation_timestamp.toFixed(1)}s`
                        : "—"}
                    </span>
                  </div>
                </div>

                {/* Suspicious Facial Temporal Segments */}
                {result.facial_telemetry?.suspicious_temporal_segments && result.facial_telemetry.suspicious_temporal_segments.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="font-mono text-[10px] text-amber-300 font-semibold block">
                      SUSPICIOUS FACIAL MANIPULATION SEGMENTS ({result.facial_telemetry.suspicious_temporal_segments.length})
                    </span>
                    <div className="space-y-1">
                      {result.facial_telemetry.suspicious_temporal_segments.map((seg, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between rounded bg-[#090A0D] px-2.5 py-1.5 border border-amber-500/20 text-[10px] font-mono text-amber-200"
                        >
                          <span>{seg.description}</span>
                          <span className="text-amber-400 font-bold">
                            {seg.peak_manipulation_score !== null && seg.peak_manipulation_score !== undefined
                              ? `${(seg.peak_manipulation_score * 100).toFixed(1)}%`
                              : `Seam: ${seg.peak_boundary_seam_delta.toFixed(3)}`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Sampled Keyframes Timeline Table */}
              {result.frame_scores && result.frame_scores.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                      <Film className="h-3.5 w-3.5" />
                      <span>Sampled Keyframes Timeline ({result.frame_scores.length})</span>
                    </div>
                    <span className="text-[10px] font-mono text-[#737984]">1.0s interval</span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-2 max-h-56 overflow-y-auto">
                    <table className="w-full text-left text-[11px] font-mono">
                      <thead>
                        <tr className="border-b border-[#292D35] text-[#737984] text-[10px]">
                          <th className="pb-1.5 pl-2">FRAME</th>
                          <th className="pb-1.5">TIMESTAMP</th>
                          <th className="pb-1.5">AI PROBABILITY</th>
                          <th className="pb-1.5 pr-2 text-right">CLASSIFICATION</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#292D35]/40">
                        {result.frame_scores.map((frame, fIdx) => (
                          <tr key={`frame-${frame.frame_index ?? fIdx}-${fIdx}`} className="hover:bg-[#12151B] transition-colors">
                            <td className="py-1.5 pl-2 text-[#F5F5F2] font-semibold">#{frame.frame_index}</td>
                            <td className="py-1.5 text-[#A3A7B0]">{frame.timestamp_seconds.toFixed(1)}s</td>
                            <td className="py-1.5">
                              <div className="flex items-center gap-2">
                                <span className={frame.ai_probability >= 0.7 ? "text-amber-400 font-bold" : "text-[#A3A7B0]"}>
                                  {(frame.ai_probability * 100).toFixed(1)}%
                                </span>
                                <div className="w-16 h-1.5 bg-[#090A0D] rounded-full overflow-hidden border border-[#292D35]">
                                  <div
                                    className={`h-full ${frame.ai_probability >= 0.7 ? "bg-amber-400" : frame.ai_probability <= 0.3 ? "bg-emerald-400" : "bg-[#D6B15E]"}`}
                                    style={{ width: `${Math.min(100, Math.max(0, frame.ai_probability * 100))}%` }}
                                  />
                                </div>
                              </div>
                            </td>
                            <td className="py-1.5 pr-2 text-right">
                              <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] border ${getFrameBadge(frame.classification)}`}>
                                {frame.classification}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

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
                          <span className="font-mono text-[10px] text-[#D6B15E] bg-[#090A0D] px-1.5 py-0.5 rounded border border-[#292D35] shrink-0">
                            {ev.metric}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Methodological Limitations */}
              {result.limitations && result.limitations.length > 0 && (
                <div className="rounded-xl border border-[#292D35] bg-[#181C23]/60 p-3.5 text-xs">
                  <span className="font-mono text-[10px] font-bold text-[#737984] uppercase block mb-1">
                    Methodological Limitations
                  </span>
                  <ul className="space-y-1 text-[11px] text-[#A3A7B0]">
                    {result.limitations.map((lim, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-[#D6B15E]">&bull;</span>
                        <span>{lim}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Mandatory Scientific Disclaimer */}
              <div className="border-t border-[#292D35] pt-3 text-[11px] text-[#737984] flex items-center gap-1.5">
                <Info className="h-3.5 w-3.5 shrink-0" />
                <span>All forensic classifications reflect probabilistic statistical patterns. They should be corroborated with additional provenance markers, custody logs, and multi-modal evidence.</span>
              </div>

              {/* Action Buttons: Save Case & Download PDF */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#292D35] pt-4">
                <button
                  type="button"
                  onClick={handleManualSaveCase}
                  disabled={caseSaved}
                  className="rounded-lg border border-[#292D35] bg-[#181C23] px-3.5 py-1.5 text-xs font-mono text-[#D6B15E] hover:border-[#D6B15E] disabled:opacity-50 transition-colors cursor-pointer"
                >
                  {caseSaved
                    ? savedCaseId
                      ? `✓ Case Logged (#${savedCaseId})`
                      : "✓ Case Saved to Reports"
                    : "+ Save Case to Reports"}
                </button>

                <button
                  type="button"
                  onClick={() => handleDownloadVideoPdf(result.analysis_id)}
                  disabled={downloadingPdf}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-3.5 py-1.5 font-mono text-xs font-bold text-[#090A0D] hover:opacity-95 disabled:opacity-50 transition-all cursor-pointer shadow-[0_0_12px_rgba(214,177,94,0.15)]"
                >
                  {downloadingPdf ? (
                    <>
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
                      <span>Generating PDF...</span>
                    </>
                  ) : (
                    <>
                      <Download className="h-3.5 w-3.5" />
                      <span>Download Case PDF</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-8 text-center shadow-sm space-y-3">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[#292D35] bg-[#181C23] text-[#737984]">
                <Film className="h-7 w-7" />
              </div>
              <h3 className="text-sm font-semibold text-[#F5F5F2]">Awaiting Video Payload</h3>
              <p className="text-xs text-[#737984] max-w-sm mx-auto leading-relaxed">
                Ingest an MP4, QuickTime MOV, or WebM video file to execute uniform temporal keyframe screening with Swin Vision Transformer and inter-frame flicker telemetry.
              </p>
              <div className="pt-2">
                <span className="inline-flex items-center gap-2 rounded-full border border-[#292D35] bg-[#181C23] px-3 py-1 font-mono text-[10px] text-[#D6B15E]">
                  <Activity className="h-3 w-3" />
                  <span>MOD-VID-03 Engine Operational</span>
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
