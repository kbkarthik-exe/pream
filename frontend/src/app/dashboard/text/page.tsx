"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  cloudApi,
  CloudTextVerificationResponse,
  reportsApi,
  textApi,
  TextAnalysisResponse,
} from "@/lib/api";
import {
  FileText,
  Sparkles,
  UserCheck,
  Clipboard,
  RotateCcw,
  Download,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Activity,
  ShieldCheck,
  Clock,
  Layers,
  Cloud,
  ExternalLink,
} from "lucide-react";

const SAMPLE_AI_TEXT = `Artificial intelligence architectures represent a revolutionary milestone in computational linguistics. Natural language processing models demonstrate unprecedented capabilities in synthesizing coherent syntactic sequences across diverse discursive domains. By leveraging multi-head self-attention mechanisms and deep multilayer representations, these neural systems construct predictive probabilistic distributions over expansive lexical vocabularies. Furthermore, empirical investigations confirm that transformer architectures systematically minimize cross-entropy loss, ensuring contextual alignment and structural consistency throughout generated textual sequences. Consequently, automated content synthesis continues to reshape technological paradigms in digital communications.`;

const SAMPLE_HUMAN_TEXT = `I was wandering around downtown yesterday evening trying to find that old bookshop my professor told me about. Naturally, my phone died right when I turned the corner onto Elm Street. I ended up popping into a tiny coffee place instead, completely drenched from the sudden rainstorm, and struck up a random conversation with the barista about 90s indie bands. Honestly? Way better than finding the book. Sometimes getting completely lost turns into the best part of your week.`;

const SAMPLE_MIXED_TEXT = `I started researching deep learning architectures because my thesis advisor recommended looking into sequence models. The history of natural language processing underwent a profound paradigm shift following the publication of the transformer architecture. Multi-head self-attention mechanisms enable neural networks to construct contextualized token representations across arbitrary sequence positions without sequential recurrence. Honestly, trying to train those massive models on my university lab workstation was a total nightmare of out-of-memory errors and driver crashes. Ultimately, hybrid methodologies combining deterministic statistical telemetry with deep neural sequence models offer the optimal balance for synthetic media forensics.`;

export default function TextDetectionPage() {
  const [textPayload, setTextPayload] = useState("");
  const [saveToCases, setSaveToCases] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState("");
  const [result, setResult] = useState<TextAnalysisResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [pasteSuccess, setPasteSuccess] = useState(false);
  const [history, setHistory] = useState<TextAnalysisResponse[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [caseSaved, setCaseSaved] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingHistoryId, setDownloadingHistoryId] = useState<number | null>(null);

  // Optional Cloud Verification Hub state
  const [enableCloud, setEnableCloud] = useState(false);
  const [cloudConsent, setCloudConsent] = useState(false);
  const [cloudResult, setCloudResult] = useState<CloudTextVerificationResponse | null>(null);
  const [isVerifyingCloud, setIsVerifyingCloud] = useState(false);
  const [cloudError, setCloudError] = useState<string | null>(null);

  const wordCount = textPayload.trim() ? textPayload.trim().split(/\s+/).length : 0;
  const charCount = textPayload.length;
  const maxChars = 15000;
  const minRecommendedWords = 50;

  const handleDownloadTextPdf = async (analysisId?: number) => {
    const targetId = analysisId || result?.analysis_id;
    if (!targetId) return;

    if (analysisId) {
      setDownloadingHistoryId(analysisId);
    } else {
      setDownloadingPdf(true);
    }
    setErrorMsg(null);
    try {
      await textApi.downloadPdf(targetId);
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

  useEffect(() => {
    let ignore = false;
    textApi
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
      const records = await textApi.listAnalyses();
      setHistory(records);
    } catch {
      // Offline fallback
    } finally {
      setLoadingHistory(false);
    }
  };

  const handlePaste = async () => {
    try {
      const clipText = await navigator.clipboard.readText();
      if (clipText) {
        setTextPayload(clipText);
        setPasteSuccess(true);
        setErrorMsg(null);
        setTimeout(() => setPasteSuccess(false), 2000);
      }
    } catch {
      setErrorMsg("Clipboard access was blocked by your browser. Please paste directly with Ctrl+V.");
    }
  };

  const handleClear = () => {
    setTextPayload("");
    setResult(null);
    setErrorMsg(null);
    setCaseSaved(false);
    setCloudResult(null);
    setCloudError(null);
  };

  const handleLoadSample = (sample: string) => {
    setTextPayload(sample);
    setErrorMsg(null);
    setResult(null);
    setCaseSaved(false);
    setCloudResult(null);
    setCloudError(null);
  };

  const handleRunCloudVerification = async () => {
    if (!textPayload.trim()) {
      setCloudError("Please enter or paste text to verify.");
      return;
    }
    if (!cloudConsent) {
      setCloudError("Explicit analyst consent is required before transmitting payload to external APIs.");
      return;
    }

    setIsVerifyingCloud(true);
    setCloudError(null);
    try {
      const cRes = await cloudApi.verifyText(textPayload, true);
      setCloudResult(cRes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Cloud verification request failed.";
      setCloudError(msg);
    } finally {
      setIsVerifyingCloud(false);
    }
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textPayload.trim()) {
      setErrorMsg("Please enter or paste text to analyze.");
      return;
    }

    if (charCount > maxChars) {
      setErrorMsg(`Text exceeds maximum allowed length of ${maxChars.toLocaleString()} characters.`);
      return;
    }

    setIsAnalyzing(true);
    setErrorMsg(null);
    setResult(null);
    setCaseSaved(false);
    setCloudResult(null);
    setCloudError(null);

    try {
      setAnalysisStep("Tokenizing sequence & computing lexical distributions...");
      await new Promise((r) => setTimeout(r, 200));

      setAnalysisStep("Evaluating Shannon entropy, TTR, and burstiness...");
      await new Promise((r) => setTimeout(r, 200));

      setAnalysisStep("Executing RoBERTa neural classification head on CPU...");
      const analysisResult = await textApi.analyze({
        text: textPayload,
        save_to_cases: saveToCases,
      });

      setResult(analysisResult);
      await fetchHistory();

      if (saveToCases) {
        setCaseSaved(true);
      }

      // If user enabled optional cloud verification and gave consent
      if (enableCloud && cloudConsent) {
        try {
          setIsVerifyingCloud(true);
          const cRes = await cloudApi.verifyText(textPayload, true);
          setCloudResult(cRes);
        } catch (cErr: unknown) {
          const cMsg = cErr instanceof Error ? cErr.message : "Cloud verification failed.";
          setCloudError(cMsg);
        } finally {
          setIsVerifyingCloud(false);
        }
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to execute text forensics. Please verify backend connectivity.");
      }
    } finally {
      setIsAnalyzing(false);
      setAnalysisStep("");
    }
  };

  const handleManualSaveCase = async () => {
    if (!result) return;
    try {
      const aiPct = result.ai_probability !== null ? (result.ai_probability * 100).toFixed(1) : "N/A";
      await reportsApi.create({
        title: `Text Forensic Case #${result.analysis_id}: ${result.classification}`,
        media_type: "text",
        summary: `Analyzed ${result.word_count} words. Result: ${result.classification} (${aiPct}% AI confidence). Hash: ${result.input_hash}`,
        is_private: true,
      });
      setCaseSaved(true);
    } catch {
      setErrorMsg("Could not save case to repository.");
    }
  };

  const getVerdictDetails = (classification: string) => {
    switch (classification) {
      case "LIKELY AI-GENERATED":
        return {
          color: "text-amber-400",
          border: "border-amber-500/40",
          bg: "bg-amber-500/10",
          icon: AlertTriangle,
        };
      case "LIKELY HUMAN":
        return {
          color: "text-emerald-400",
          border: "border-emerald-500/40",
          bg: "bg-emerald-500/10",
          icon: CheckCircle2,
        };
      default:
        return {
          color: "text-[#D6B15E]",
          border: "border-[#D6B15E]/40",
          bg: "bg-[#D6B15E]/10",
          icon: HelpCircle,
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#D6B15E] font-bold">MOD-TXT-01</span>
            <span className="text-[#3A404D]">&bull;</span>
            <span className="text-xs text-[#A3A7B0]">Linguistic &amp; Transformer Forensics</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#F5F5F2]">
            AI Text Detection &amp; Synthetics Analysis
          </h1>
          <p className="mt-1 text-xs text-[#A3A7B0]">
            Analyze text sequences with genuine RoBERTa embeddings, lexical burstiness, Shannon entropy, and vocabulary variance.
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
        {/* Editor Form Column */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#292D35] pb-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-[#D6B15E]" />
                <span className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                  Input Text Payload
                </span>
              </div>

              {/* Sample loader chips */}
              <div className="flex items-center gap-1.5 text-xs">
                <button
                  type="button"
                  onClick={() => handleLoadSample(SAMPLE_AI_TEXT)}
                  className="inline-flex items-center gap-1 rounded-md border border-[#292D35] bg-[#181C23] px-2 py-1 text-[11px] text-[#A3A7B0] hover:border-[#D6B15E] hover:text-[#F0D58A] transition-colors cursor-pointer"
                >
                  <Sparkles className="h-3 w-3 text-[#D6B15E]" />
                  <span>AI Sample</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadSample(SAMPLE_HUMAN_TEXT)}
                  className="inline-flex items-center gap-1 rounded-md border border-[#292D35] bg-[#181C23] px-2 py-1 text-[11px] text-[#A3A7B0] hover:border-[#D6B15E] hover:text-[#F0D58A] transition-colors cursor-pointer"
                >
                  <UserCheck className="h-3 w-3 text-emerald-400" />
                  <span>Human Sample</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadSample(SAMPLE_MIXED_TEXT)}
                  className="inline-flex items-center gap-1 rounded-md border border-[#292D35] bg-[#181C23] px-2 py-1 text-[11px] text-[#A3A7B0] hover:border-[#D6B15E] hover:text-[#F0D58A] transition-colors cursor-pointer"
                >
                  <Sparkles className="h-3 w-3 text-cyan-400" />
                  <span>Mixed Sample</span>
                </button>
                <button
                  type="button"
                  onClick={handlePaste}
                  className="inline-flex items-center gap-1 rounded-md border border-[#292D35] bg-[#181C23] px-2 py-1 text-[11px] text-[#A3A7B0] hover:border-[#D6B15E] hover:text-[#F0D58A] transition-colors cursor-pointer"
                  title="Paste from clipboard"
                >
                  <Clipboard className="h-3 w-3" />
                  <span>{pasteSuccess ? "Pasted!" : "Paste"}</span>
                </button>
              </div>
            </div>

            <form onSubmit={handleRunAnalysis} className="mt-4 space-y-4">
              <div className="relative">
                <textarea
                  value={textPayload}
                  onChange={(e) => setTextPayload(e.target.value)}
                  placeholder="Paste or write document payload here to evaluate for synthetic language markers, vocabulary predictability, and transformer likelihood..."
                  rows={10}
                  className="w-full rounded-xl border border-[#292D35] bg-[#090A0D] p-4 text-xs font-mono text-[#F5F5F2] placeholder-[#737984] focus:border-[#D6B15E] focus:outline-hidden focus:ring-1 focus:ring-[#D6B15E]/50 leading-relaxed transition-colors"
                />
              </div>

              {/* Character and Word Telemetry */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] text-[#A3A7B0] font-mono border-t border-[#292D35] pt-3">
                <div className="flex items-center gap-3">
                  <span>
                    Words: <strong className={wordCount < minRecommendedWords ? "text-amber-400" : "text-[#F5F5F2]"}>{wordCount}</strong>
                    {wordCount < minRecommendedWords && wordCount > 0 && " (min 50 rec)"}
                  </span>
                  <span>&bull;</span>
                  <span>
                    Chars: <strong className={charCount > maxChars ? "text-red-400" : "text-[#F5F5F2]"}>{charCount.toLocaleString()}</strong> / {maxChars.toLocaleString()}
                  </span>
                </div>

                {textPayload && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="flex items-center gap-1 text-[#737984] hover:text-red-400 transition-colors cursor-pointer"
                  >
                    <RotateCcw className="h-3 w-3" />
                    <span>Clear</span>
                  </button>
                )}
              </div>

              {/* Execution Controls */}
              <div className="space-y-3 pt-2">
                <div className="flex flex-col gap-2.5">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-[#A3A7B0]">
                    <input
                      type="checkbox"
                      checked={saveToCases}
                      onChange={(e) => setSaveToCases(e.target.checked)}
                      className="rounded border-[#292D35] bg-[#181C23] text-[#D6B15E] focus:ring-[#D6B15E]"
                    />
                    <span>Automatically log to Case Reports</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer text-xs text-[#A3A7B0]">
                    <input
                      type="checkbox"
                      checked={enableCloud}
                      onChange={(e) => {
                        setEnableCloud(e.target.checked);
                        if (!e.target.checked) setCloudConsent(false);
                      }}
                      className="rounded border-[#292D35] bg-[#181C23] text-[#D6B15E] focus:ring-[#D6B15E]"
                    />
                    <span className="flex items-center gap-1.5">
                      <Cloud className="h-3 w-3 text-[#D6B15E]" />
                      <span>Enable Cloud Verification Hub (Hive / GPTZero / Copyleaks)</span>
                    </span>
                  </label>

                  {enableCloud && (
                    <div className="ml-5 rounded-xl border border-[#D6B15E]/30 bg-[#181C23] p-3 text-xs text-[#A3A7B0] space-y-1.5">
                      <label className="flex items-start gap-2 cursor-pointer text-[#F5F5F2]">
                        <input
                          type="checkbox"
                          checked={cloudConsent}
                          onChange={(e) => setCloudConsent(e.target.checked)}
                          className="mt-0.5 rounded border-[#292D35] bg-[#090A0D] text-[#D6B15E] focus:ring-[#D6B15E]"
                        />
                        <span className="text-[11px] leading-tight">
                          <strong>Explicit Consent:</strong> I authorize transmitting this document excerpt to external third-party cloud verification APIs.
                        </span>
                      </label>
                      <div className="text-[10px] text-[#737984]">
                        Local analysis remains primary. Credentials are authenticated and encrypted.
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={isAnalyzing || !textPayload.trim()}
                    className="inline-flex items-center gap-2 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-5 py-2.5 font-mono text-xs font-bold text-[#090A0D] shadow-[0_0_15px_rgba(214,177,94,0.2)] transition-opacity hover:opacity-95 disabled:opacity-50 cursor-pointer"
                  >
                    {isAnalyzing ? (
                      <>
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
                        <span>Executing Inference...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5" />
                        <span>Execute Forensics Analysis</span>
                      </>
                    )}
                  </button>
                </div>
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
        </div>

        {/* Results & History Column */}
        <div className="lg:col-span-5 space-y-4">
          {result ? (
            <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm space-y-5">
              {/* Verdict Banner */}
              {(() => {
                const verdict = getVerdictDetails(result.classification);
                const VerdictIcon = verdict.icon;
                const aiPct = result.ai_probability !== null ? (result.ai_probability * 100).toFixed(1) : "—";
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
                          {aiPct}%
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Non-English / Non-Latin Script Warning */}
              {result.language_warning && (
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-300 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
                  <div>
                    <span className="font-bold">Script / Language Notice:</span> {result.language_warning}
                  </div>
                </div>
              )}

              {/* Consensus Alignment & Uncertainty Drivers */}
              {result.ensemble?.disagreement_analysis && (
                <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3.5 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] font-bold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5" />
                      <span>Consensus Alignment &amp; Agreement</span>
                    </span>
                    {result.ensemble.evidence_strength && (
                      <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                        result.ensemble.evidence_strength === "STRONG"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : result.ensemble.evidence_strength === "MODERATE"
                          ? "bg-[#D6B15E]/10 text-[#F0D58A] border border-[#D6B15E]/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}>
                        Evidence: {result.ensemble.evidence_strength}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-[#A3A7B0] leading-relaxed">
                    {result.ensemble.disagreement_analysis}
                  </p>
                  {result.ensemble.reasons_for_uncertainty && result.ensemble.reasons_for_uncertainty.length > 0 && (
                    <div className="pt-2 border-t border-[#292D35] space-y-1">
                      <span className="font-mono text-[9px] text-[#737984] uppercase block font-semibold">
                        Forensic Uncertainty Drivers
                      </span>
                      <ul className="list-disc list-inside text-[10px] text-amber-300/80 space-y-0.5">
                        {result.ensemble.reasons_for_uncertainty.map((reason, idx) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Probability Meter */}
              {result.human_probability !== null && result.ai_probability !== null && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[11px] font-mono">
                    <span className="text-emerald-400">Human ({(result.human_probability * 100).toFixed(1)}%)</span>
                    <span className="text-amber-400">Synthetic AI ({(result.ai_probability * 100).toFixed(1)}%)</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-[#181C23] overflow-hidden flex border border-[#292D35]">
                    <div
                      style={{ width: `${result.human_probability * 100}%` }}
                      className="bg-emerald-500 transition-all duration-500"
                    />
                    <div
                      style={{ width: `${result.ai_probability * 100}%` }}
                      className="bg-amber-500 transition-all duration-500"
                    />
                  </div>
                </div>
              )}

              {/* Multi-Detector Model Availability & Consensus Hub */}
              {result.detector_scores && Object.keys(result.detector_scores).length > 0 && (
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5" />
                      <span>Multi-Detector Consensus Hub</span>
                    </div>
                    {result.ensemble?.active_detector_count !== undefined && (
                      <span className="font-mono text-[10px] text-[#A3A7B0]">
                        {result.ensemble.active_detector_count}/{result.ensemble.total_detector_count} Active
                      </span>
                    )}
                  </div>

                  <div className="space-y-2">
                    {Object.entries(result.detector_scores).map(([key, det]) => {
                      const isReady = det.status === "READY" || det.status === "SUCCESS";
                      const aiPct = det.ai_probability !== null && det.ai_probability !== undefined ? (det.ai_probability * 100).toFixed(1) : null;
                      return (
                        <div key={key} className="rounded-xl border border-[#292D35] bg-[#181C23] p-3 text-xs space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-[11px] font-bold text-[#F5F5F2] truncate max-w-[200px]">
                              {det.model_name}
                            </span>
                            <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                              isReady ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                              det.status === "RESOURCE_CONSTRAINED" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                              "bg-red-500/10 text-red-400 border border-red-500/20"
                            }`}>
                              {det.status}
                            </span>
                          </div>
                          {isReady && aiPct !== null ? (
                            <div className="space-y-1">
                              <div className="flex justify-between text-[10px] font-mono text-[#A3A7B0]">
                                <span>AI Confidence</span>
                                <span className="text-[#F0D58A] font-bold">{aiPct}%</span>
                              </div>
                              <div className="h-1.5 w-full rounded-full bg-[#12151B] overflow-hidden">
                                <div
                                  style={{ width: `${Math.min(100, Math.max(0, Number(aiPct)))}%` }}
                                  className="h-full bg-gradient-to-r from-[#D6B15E] to-amber-500 rounded-full"
                                />
                              </div>
                              {det.raw_output && (
                                <div className="flex items-center justify-between text-[9px] font-mono text-[#737984] pt-0.5">
                                  <span>Tokens: {String(det.raw_output.tokens_evaluated ?? "—")}</span>
                                  <span>Device: {String(det.raw_output.device ?? "cpu").toUpperCase()}</span>
                                </div>
                              )}
                            </div>
                          ) : (
                            <p className="text-[10px] text-[#737984] italic">
                              {det.status_detail || "Model weights unconfigured or resource-limited."}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {result.ensemble?.calibration_method && (
                    <div className="text-[10px] font-mono text-[#737984] pt-0.5">
                      Calibration: {result.ensemble.calibration_method}
                    </div>
                  )}
                </div>
              )}

              {/* Linguistic & Lexical Forensic Signals */}
              <div className="space-y-2.5">
                <div className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Lexical Evidentiary Signals</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">SHANNON ENTROPY</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.token_entropy !== undefined && result.token_entropy !== null ? result.token_entropy.toFixed(3) : "—"}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">Information density</span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">TYPE-TOKEN RATIO (TTR)</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.type_token_ratio !== undefined && result.type_token_ratio !== null ? result.type_token_ratio.toFixed(3) : "—"}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">Vocabulary diversity</span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">BURSTINESS SCORE</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.burstiness_score !== undefined && result.burstiness_score !== null ? result.burstiness_score.toFixed(3) : "—"}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">Sentence variance</span>
                  </div>

                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3">
                    <span className="font-mono text-[10px] text-[#737984] block">REPEATED N-GRAMS</span>
                    <span className="font-mono text-sm font-bold text-[#F5F5F2]">
                      {result.repeated_ngram_ratio !== undefined && result.repeated_ngram_ratio !== null ? (result.repeated_ngram_ratio * 100).toFixed(1) + "%" : "0%"}
                    </span>
                    <span className="text-[10px] text-[#A3A7B0] block mt-0.5">Syntactic repetition</span>
                  </div>
                </div>

                {/* Punctuation & Paragraph Dynamics */}
                {result.punctuation_metrics && (
                  <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-[#737984] uppercase font-bold">
                        Punctuation &amp; Syntactic Cadence
                      </span>
                      <span className="font-mono text-[10px] text-[#D6B15E]">
                        Density: {(result.punctuation_metrics.punctuation_density * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="grid grid-cols-4 gap-1.5 font-mono text-[10px] text-[#F5F5F2] pt-0.5">
                      <div className="bg-[#12151B] p-1.5 rounded border border-[#292D35] text-center">
                        <span className="text-[#737984] block text-[8px]">COMMAS</span>
                        {result.punctuation_metrics.comma_count}
                      </div>
                      <div className="bg-[#12151B] p-1.5 rounded border border-[#292D35] text-center">
                        <span className="text-[#737984] block text-[8px]">PERIODS</span>
                        {result.punctuation_metrics.period_count}
                      </div>
                      <div className="bg-[#12151B] p-1.5 rounded border border-[#292D35] text-center">
                        <span className="text-[#737984] block text-[8px]">SEMICOLONS</span>
                        {result.punctuation_metrics.semicolon_count}
                      </div>
                      <div className="bg-[#12151B] p-1.5 rounded border border-[#292D35] text-center">
                        <span className="text-[#737984] block text-[8px]">EXPRESSIVE (!/?)</span>
                        {result.punctuation_metrics.exclamation_count + result.punctuation_metrics.question_count}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Sentence-Level Cadence Inspector */}
              {result.sentence_analysis && result.sentence_analysis.length > 0 && (
                <div className="space-y-2 rounded-xl border border-[#292D35] bg-[#181C23] p-3.5 text-xs">
                  <div className="flex items-center justify-between border-b border-[#292D35] pb-2">
                    <span className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5" />
                      <span>Sentence-Level Cadence Telemetry</span>
                    </span>
                    <span className="font-mono text-[10px] text-[#737984]">
                      {result.sentence_analysis.length} sentences
                    </span>
                  </div>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1 pt-1">
                    {result.sentence_analysis.slice(0, 8).map((sent, sIdx) => (
                      <div
                        key={`sentence-${sent.sentence_idx ?? 0}-${sIdx}`}
                        className="rounded-lg border border-[#292D35] bg-[#12151B] p-2.5 space-y-1 text-xs"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-[10px] text-[#737984]">
                            #{sent.sentence_idx + 1} &bull; {sent.word_count} words
                          </span>
                          <div className="flex items-center gap-1.5">
                            {sent.has_transitional_opening && (
                              <span className="px-1.5 py-0.5 rounded text-[8px] font-mono font-bold uppercase bg-[#D6B15E]/10 text-[#F0D58A] border border-[#D6B15E]/20">
                                Transitional
                              </span>
                            )}
                            <span
                              className={`px-1.5 py-0.5 rounded text-[8px] font-mono font-bold uppercase ${
                                sent.relative_cadence === "MONOTONOUS"
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                  : sent.relative_cadence === "SHORT"
                                  ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                                  : sent.relative_cadence === "LONG"
                                  ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                                  : "bg-[#292D35] text-[#A3A7B0]"
                              }`}
                            >
                              {sent.relative_cadence}
                            </span>
                          </div>
                        </div>
                        <p className="text-[11px] text-[#F5F5F2] font-mono line-clamp-2">
                          &ldquo;{sent.text}&rdquo;
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Evidence Finding Item */}
              {result.evidence && result.evidence.length > 0 && (
                <div className="rounded-xl border border-[#292D35] bg-[#181C23] p-3.5 text-xs text-[#A3A7B0] leading-relaxed">
                  <span className="font-mono text-[10px] font-bold text-[#D6B15E] block uppercase mb-1">
                    Evidentiary Finding
                  </span>
                  {result.evidence.map((ev, i) => (
                    <div key={i} className="mb-1 text-[11px]">
                      <strong className="text-[#F5F5F2]">{ev.signal}:</strong> {ev.finding}
                    </div>
                  ))}
                </div>
              )}

              {/* Optional Cloud Verification Hub */}
              <div className="space-y-2.5 rounded-xl border border-[#292D35] bg-[#181C23] p-4 text-xs">
                <div className="flex items-center justify-between border-b border-[#292D35] pb-2.5">
                  <div className="font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider flex items-center gap-1.5">
                    <Cloud className="h-3.5 w-3.5" />
                    <span>Cloud Cross-Verification (Optional)</span>
                  </div>
                  <Link
                    href="/dashboard/settings"
                    className="font-mono text-[10px] text-[#A3A7B0] hover:text-[#D6B15E] flex items-center gap-1 transition-colors"
                  >
                    <span>Hub Settings</span>
                    <ExternalLink className="h-2.5 w-2.5" />
                  </Link>
                </div>

                {!cloudResult ? (
                  <div className="space-y-3 pt-1">
                    <p className="text-[11px] text-[#A3A7B0] leading-relaxed">
                      Optionally cross-examine this text against authorized cloud detectors (Hive AI, GPTZero, Copyleaks). Local ensemble results remain primary.
                    </p>

                    <label className="flex items-start gap-2 cursor-pointer text-[11px] text-[#F5F5F2] bg-[#12151B] p-2.5 rounded-lg border border-[#292D35]">
                      <input
                        type="checkbox"
                        checked={cloudConsent}
                        onChange={(e) => setCloudConsent(e.target.checked)}
                        className="mt-0.5 rounded border-[#292D35] bg-[#090A0D] text-[#D6B15E] focus:ring-[#D6B15E]"
                      />
                      <span className="leading-tight">
                        <strong>Analyst Consent:</strong> I authorize transmitting this document excerpt to external cloud verification APIs.
                      </span>
                    </label>

                    {cloudError && (
                      <div className="text-[11px] text-rose-400 flex items-center gap-1.5">
                        <AlertTriangle className="h-3 w-3 shrink-0" />
                        <span>{cloudError}</span>
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={handleRunCloudVerification}
                      disabled={isVerifyingCloud || !cloudConsent}
                      className="w-full rounded-lg border border-[#D6B15E]/40 bg-[#12151B] px-3 py-2 font-mono text-xs font-bold text-[#F0D58A] hover:border-[#D6B15E] hover:bg-[#181C23] disabled:opacity-40 transition-all cursor-pointer flex items-center justify-center gap-2"
                    >
                      {isVerifyingCloud ? (
                        <>
                          <span className="h-3 w-3 animate-spin rounded-full border-2 border-[#D6B15E] border-t-transparent" />
                          <span>Querying Cloud Hubs...</span>
                        </>
                      ) : (
                        <>
                          <Cloud className="h-3.5 w-3.5" />
                          <span>Run Cloud Verification</span>
                        </>
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2 pt-1">
                    {Object.entries(cloudResult.results).map(([providerName, r]) => {
                      const isSuccess = r.status === "SUCCESS";
                      const isConfigReq = r.status === "CONFIGURATION_REQUIRED";
                      const aiPct = r.ai_score !== null && r.ai_score !== undefined ? (r.ai_score * 100).toFixed(1) : null;
                      const humanPct = r.human_score !== null && r.human_score !== undefined ? (r.human_score * 100).toFixed(1) : null;

                      return (
                        <div
                          key={providerName}
                          className="rounded-lg border border-[#292D35] bg-[#12151B] p-2.5 text-xs space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-[11px] font-bold text-[#F5F5F2] uppercase">
                              {providerName}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                                isSuccess
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                  : isConfigReq
                                  ? "bg-[#292D35] text-[#A3A7B0]"
                                  : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              }`}
                            >
                              {r.status}
                            </span>
                          </div>

                          {isSuccess && aiPct !== null ? (
                            <div className="space-y-1">
                              <div className="flex justify-between text-[10px] font-mono text-[#A3A7B0]">
                                <span>AI: <strong className="text-amber-400">{aiPct}%</strong></span>
                                {humanPct && <span>Human: <strong className="text-emerald-400">{humanPct}%</strong></span>}
                              </div>
                              <div className="h-1.5 w-full rounded-full bg-[#090A0D] overflow-hidden">
                                <div
                                  style={{ width: `${Math.min(100, Math.max(0, Number(aiPct)))}%` }}
                                  className="h-full bg-gradient-to-r from-amber-500 to-[#D6B15E] rounded-full"
                                />
                              </div>
                            </div>
                          ) : (
                            <p className="text-[10px] text-[#737984]">
                              {r.error_message || (isConfigReq ? "API key not configured in Settings." : "Verification skipped or unavailable.")}
                            </p>
                          )}
                        </div>
                      );
                    })}

                    <div className="flex items-center justify-between pt-1">
                      <button
                        type="button"
                        onClick={() => setCloudResult(null)}
                        className="text-[10px] font-mono text-[#737984] hover:text-[#D6B15E] transition-colors cursor-pointer"
                      >
                        &larr; Query again / Clear
                      </button>
                      <span className="text-[9px] font-mono text-[#737984]">
                        Non-authoritative secondary check
                      </span>
                    </div>
                  </div>
                )}
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
                  onClick={() => handleDownloadTextPdf(result.analysis_id)}
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
                <FileText className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-sm font-semibold text-[#F5F5F2]">Awaiting Text Payload</h3>
              <p className="mt-1 text-xs text-[#737984] max-w-xs mx-auto">
                Paste your content or select a sample above and click &ldquo;Execute Forensics Analysis&rdquo; to begin.
              </p>
            </div>
          )}

          {/* Historical Text Analyses Drawer */}
          <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#292D35] pb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-[#D6B15E]" />
                <h3 className="text-xs font-bold text-[#F5F5F2] uppercase font-mono">
                  Text Analysis History
                </h3>
              </div>
              <span className="font-mono text-[10px] text-[#737984]">{history.length} records</span>
            </div>

            {loadingHistory ? (
              <div className="py-6 text-center text-xs text-[#737984] font-mono">Loading history...</div>
            ) : history.length === 0 ? (
              <div className="py-6 text-center text-xs text-[#737984]">No previous analyses in session.</div>
            ) : (
              <div className="mt-3 space-y-2 max-h-64 overflow-y-auto pr-1">
                {history.slice(0, 8).map((item, hIdx) => (
                  <div
                    key={`hist-${item.analysis_id ?? hIdx}-${hIdx}`}
                    className="flex items-center justify-between rounded-xl border border-[#292D35] bg-[#181C23] p-2.5 text-xs hover:border-[#3A404D] transition-colors"
                  >
                    <div className="truncate max-w-[180px]">
                      <div className="font-mono text-[11px] font-semibold text-[#F0D58A] truncate">
                        #{item.analysis_id} &bull; {item.classification}
                      </div>
                      <div className="text-[10px] text-[#737984] truncate">
                        {item.character_count} chars &bull; {item.ai_probability !== null ? (item.ai_probability * 100).toFixed(0) + "% AI" : "—"}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleDownloadTextPdf(item.analysis_id)}
                      disabled={downloadingHistoryId === item.analysis_id}
                      className="p-1.5 rounded-lg border border-[#292D35] bg-[#12151B] text-[#D6B15E] hover:border-[#D6B15E] disabled:opacity-50 transition-colors cursor-pointer"
                      title="Download PDF report"
                    >
                      {downloadingHistoryId === item.analysis_id ? (
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
