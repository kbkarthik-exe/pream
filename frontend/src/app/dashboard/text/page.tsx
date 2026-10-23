"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  reportsApi,
  textApi,
  TextAnalysisResponse,
} from "@/lib/api";

const SAMPLE_AI_TEXT = `Artificial intelligence architectures represent a revolutionary milestone in computational linguistics. Natural language processing models demonstrate unprecedented capabilities in synthesizing coherent syntactic sequences across diverse discursive domains. By leveraging multi-head self-attention mechanisms and deep multilayer representations, these neural systems construct predictive probabilistic distributions over expansive lexical vocabularies. Furthermore, empirical investigations confirm that transformer architectures systematically minimize cross-entropy loss, ensuring contextual alignment and structural consistency throughout generated textual sequences. Consequently, automated content synthesis continues to reshape technological paradigms in digital communications.`;

const SAMPLE_HUMAN_TEXT = `I was wandering around downtown yesterday evening trying to find that old bookshop my professor told me about. Naturally, my phone died right when I turned the corner onto Elm Street. I ended up popping into a tiny coffee place instead, completely drenched from the sudden rainstorm, and struck up a random conversation with the barista about 90s indie bands. Honestly? Way better than finding the book. Sometimes getting completely lost turns into the best part of your week.`;

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

  const wordCount = textPayload.trim() ? textPayload.trim().split(/\s+/).length : 0;
  const charCount = textPayload.length;
  const maxChars = 15000;
  const minRecommendedWords = 50;

  // Fetch recent text analyses on mount
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
      // Ignored for unauthenticated or first-time views
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
      setErrorMsg("Clipboard access was blocked by your browser. Please paste directly using Ctrl+V.");
    }
  };

  const handleClear = () => {
    setTextPayload("");
    setResult(null);
    setErrorMsg(null);
    setCaseSaved(false);
  };

  const handleLoadSample = (sample: string) => {
    setTextPayload(sample);
    setErrorMsg(null);
    setResult(null);
    setCaseSaved(false);
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textPayload.trim()) {
      setErrorMsg("Please enter text payload to analyze.");
      return;
    }

    if (charCount > maxChars) {
      setErrorMsg(`Text payload exceeds maximum size of ${maxChars.toLocaleString()} characters.`);
      return;
    }

    setIsAnalyzing(true);
    setErrorMsg(null);
    setCaseSaved(false);

    // Multi-stage visual telemetry updates
    setAnalysisStep("Tokenizing sequence & computing n-gram distributions...");
    const stepTimer1 = setTimeout(() => {
      setAnalysisStep("Executing fine-tuned RoBERTa transformer inference...");
    }, 250);
    const stepTimer2 = setTimeout(() => {
      setAnalysisStep("Extracting sentence burstiness, lexical TTR & entropy...");
    }, 600);

    try {
      const resp = await textApi.analyze({
        text: textPayload,
        save_to_cases: saveToCases,
      });
      setResult(resp);
      if (resp.case_report_id) {
        setCaseSaved(true);
      }
      fetchHistory();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to execute text forensics analysis. Please verify your connection.");
      }
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setIsAnalyzing(false);
      setAnalysisStep("");
    }
  };

  const handleSaveToReports = async () => {
    if (!result) return;
    try {
      const scoreStr = result.confidence_score !== null ? `${(result.confidence_score * 100).toFixed(1)}%` : "N/A";
      await reportsApi.create({
        title: `Text Forensics: ${result.classification} (${result.word_count} words)`,
        media_type: "text",
        summary: `Analysis #${result.analysis_id} — Classification: ${result.classification} (${scoreStr}). Input Hash: ${result.input_hash.slice(0, 12)}... Sample: "${result.text_snippet}". Burstiness CV: ${result.burstiness_score.toFixed(2)}, TTR: ${result.type_token_ratio.toFixed(2)}.`,
        is_private: true,
      });
      setCaseSaved(true);
    } catch {
      setErrorMsg("Failed to save case to reports archive.");
    }
  };

  const getClassificationBadgeStyle = (classification: string) => {
    switch (classification) {
      case "LIKELY AI-GENERATED":
        return "border-red-500/50 bg-red-500/10 text-red-400";
      case "LIKELY HUMAN":
        return "border-emerald-500/50 bg-emerald-500/10 text-emerald-400";
      case "INCONCLUSIVE":
      default:
        return "border-amber-500/50 bg-amber-500/10 text-amber-300";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-semibold text-[#D4AF37]">MOD-TXT-01</span>
            <span className="text-[#6B7280]">&bull;</span>
            <span className="text-xs text-[#9FA6B2]">Natural Language Forensics</span>
            <span className="text-[#6B7280]">&bull;</span>
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-mono text-emerald-400">
              ENGINE ACTIVE
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            AI Text Forensics &amp; Synthetics Detection
          </h1>
          <p className="mt-1 text-xs text-[#9FA6B2]">
            Inspect prose against fine-tuned sequence classification transformers, sentence-cadence burstiness, and lexical entropy.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="self-start sm:self-auto rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3.5 py-1.5 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37]"
        >
          &larr; Back to Overview
        </Link>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Input Card */}
        <div className="flex flex-col rounded-xl border border-[#2B2F3D] bg-[#12141A]/95 p-6 shadow-xl backdrop-blur-md">
          {/* Card Header with counters */}
          <div className="flex flex-col gap-2 border-b border-[#2B2F3D] pb-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-white">Input Text Payload</h2>
              {wordCount >= minRecommendedWords ? (
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-400">
                  Reliable Volume
                </span>
              ) : wordCount >= 15 ? (
                <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] text-amber-300">
                  Short Sample ({minRecommendedWords}+ recommended)
                </span>
              ) : (
                <span className="rounded-full border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-400">
                  Min 15 words required
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 font-mono text-[11px] text-[#6B7280]">
              <span>
                Words: <strong className="text-[#F3E5AB]">{wordCount.toLocaleString()}</strong>
              </span>
              <span>
                Chars:{" "}
                <strong
                  className={charCount > maxChars ? "text-red-400" : "text-[#F3E5AB]"}
                >
                  {charCount.toLocaleString()}
                </strong>
                /{maxChars.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Quick Action Toolbar */}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handlePaste}
                className="inline-flex items-center gap-1.5 rounded-md border border-[#2B2F3D] bg-[#191C24] px-2.5 py-1 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37]"
              >
                <span>📋</span>
                <span>{pasteSuccess ? "Pasted!" : "Paste from Clipboard"}</span>
              </button>

              <button
                type="button"
                onClick={handleClear}
                disabled={!textPayload && !result && !errorMsg}
                className="rounded-md border border-[#2B2F3D] bg-[#191C24] px-2.5 py-1 text-xs text-[#9FA6B2] hover:border-red-500/50 hover:text-red-400 disabled:opacity-40"
              >
                Clear
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] text-[#6B7280]">Test Samples:</span>
              <button
                type="button"
                onClick={() => handleLoadSample(SAMPLE_AI_TEXT)}
                className="rounded border border-[#2B2F3D] bg-[#191C24] px-2 py-0.5 text-[11px] text-red-300 hover:border-red-500/50"
              >
                AI Sample
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample(SAMPLE_HUMAN_TEXT)}
                className="rounded border border-[#2B2F3D] bg-[#191C24] px-2 py-0.5 text-[11px] text-emerald-300 hover:border-emerald-500/50"
              >
                Human Sample
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {errorMsg && (
            <div className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
              <div className="flex items-center justify-between">
                <span>{errorMsg}</span>
                <button
                  type="button"
                  onClick={() => setErrorMsg(null)}
                  className="font-bold hover:text-white"
                >
                  &times;
                </button>
              </div>
            </div>
          )}

          {/* Textarea Form */}
          <form onSubmit={handleRunAnalysis} className="mt-3 flex flex-1 flex-col space-y-4">
            <div className="flex-1">
              <textarea
                rows={11}
                required
                value={textPayload}
                onChange={(e) => {
                  setTextPayload(e.target.value);
                  if (errorMsg) setErrorMsg(null);
                }}
                placeholder="Paste suspect article, academic abstract, email, essay, or generative content for forensic verification (minimum 15 words)..."
                className="block h-full min-h-[220px] w-full resize-y rounded-lg border border-[#2B2F3D] bg-[#191C24] p-3 text-xs leading-relaxed text-white placeholder-[#4B5563] focus:border-[#D4AF37] focus:outline-none focus:ring-1 focus:ring-[#D4AF37]/50"
              />
            </div>

            {/* Options & Submit */}
            <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:items-center sm:justify-between">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-[#9FA6B2]">
                <input
                  type="checkbox"
                  checked={saveToCases}
                  onChange={(e) => setSaveToCases(e.target.checked)}
                  className="h-3.5 w-3.5 rounded border-[#2B2F3D] bg-[#191C24] text-[#D4AF37] focus:ring-0 focus:ring-offset-0"
                />
                <span>Automatically archive case in platform reports</span>
              </label>

              <button
                type="submit"
                disabled={isAnalyzing || wordCount < 15 || charCount > maxChars}
                className="flex items-center justify-center gap-2 rounded-lg border border-[#D4AF37]/60 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-5 py-2.5 text-xs font-semibold text-black shadow-[0_0_15px_rgba(212,175,55,0.2)] transition-all hover:opacity-95 hover:shadow-[0_0_20px_rgba(212,175,55,0.35)] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (
                  <>
                    <svg className="h-4 w-4 animate-spin text-black" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Executing Pipeline...</span>
                  </>
                ) : (
                  <span>Execute Forensic Analysis</span>
                )}
              </button>
            </div>
          </form>

          {/* Progress / Step indicator during analysis */}
          {isAnalyzing && (
            <div className="mt-4 rounded-lg border border-[#D4AF37]/30 bg-[#191C24] p-3 text-xs text-[#D4AF37] flex items-center gap-2 animate-pulse">
              <span className="font-mono text-[10px] uppercase tracking-wider text-[#9FA6B2]">Pipeline:</span>
              <span>{analysisStep || "Processing..."}</span>
            </div>
          )}
        </div>

        {/* Results Column */}
        <div className="space-y-4">
          {!result ? (
            /* Standby Card */
            <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/95 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#D4AF37]/50 bg-[#191C24] font-mono text-xs font-bold text-[#D4AF37]">
                    TXT
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold tracking-wide text-white uppercase">
                      Text Forensics Telemetry
                    </h3>
                    <p className="text-[11px] text-[#9FA6B2]">roberta-base-openai-detector &bull; CPU Inference</p>
                  </div>
                </div>
                <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-0.5 font-mono text-[10px] text-blue-400">
                  STATUS: STANDBY
                </span>
              </div>

              <div className="mt-5 space-y-4">
                <div className="rounded-lg border border-[#2B2F3D] bg-[#191C24]/80 p-4">
                  <h4 className="text-xs font-semibold text-[#F3E5AB]">Forensic Engine Readiness</h4>
                  <p className="mt-1 text-xs leading-relaxed text-[#9FA6B2]">
                    The text analysis engine is loaded and ready. Paste a sample text on the left and click{" "}
                    <strong className="text-white">Execute Forensic Analysis</strong> to run the fine-tuned sequence classification transformer and extract empirical sentence burstiness metrics.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10]/60 p-3">
                    <span className="text-[10px] uppercase tracking-wider text-[#6B7280]">Primary Model</span>
                    <p className="mt-1 font-mono text-xs text-[#F3E5AB]">RoBERTa Classifier</p>
                    <p className="mt-0.5 text-[10px] text-[#9FA6B2]">OpenAI detector fine-tune</p>
                  </div>
                  <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10]/60 p-3">
                    <span className="text-[10px] uppercase tracking-wider text-[#6B7280]">Taxonomy Labels</span>
                    <p className="mt-1 font-mono text-xs text-white">3 Verified States</p>
                    <p className="mt-0.5 text-[10px] text-[#9FA6B2]">AI, Human, Inconclusive</p>
                  </div>
                </div>

                <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10]/60 p-3">
                  <span className="text-[10px] uppercase tracking-wider text-[#6B7280]">Epistemic Transparency</span>
                  <p className="mt-1 text-xs text-[#9FA6B2]">
                    Detector outputs are probabilistic estimations. The platform enforces strict uncertainty boundaries (0.30 to 0.70) and never fabricates certainty.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* Active Forensic Result Card */
            <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/95 p-6 shadow-2xl backdrop-blur-md">
              {/* Header */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#D4AF37]/50 bg-[#191C24] font-mono text-xs font-bold text-[#D4AF37]">
                    #{result.analysis_id}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold tracking-wide text-white uppercase">
                      Forensic Findings
                    </h3>
                    <p className="text-[11px] text-[#9FA6B2]">
                      {result.model_name} &bull; v{result.model_version} &bull; {result.processing_time_ms}ms
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full border px-3 py-1 font-mono text-xs font-bold ${getClassificationBadgeStyle(
                      result.classification
                    )}`}
                  >
                    {result.classification}
                  </span>
                </div>
              </div>

              {/* Confidence Level Gauge */}
              {result.confidence_score !== null && (
                <div className="mt-5 rounded-lg border border-[#2B2F3D] bg-[#191C24] p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs font-medium text-white">Empirical Confidence Level</span>
                      <p className="text-[10px] text-[#9FA6B2]">
                        Calculated from model softmax probability and calibrated thresholds
                      </p>
                    </div>
                    <span className="font-mono text-lg font-bold text-[#D4AF37]">
                      {(result.confidence_score * 100).toFixed(1)}%
                    </span>
                  </div>

                  {/* Gold Gauge Bar */}
                  <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-[#0B0C10]">
                    <div
                      className="h-full bg-gradient-to-r from-[#997A15] via-[#D4AF37] to-[#F3E5AB] transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(0, result.confidence_score * 100))}%` }}
                    />
                  </div>

                  {/* Comparative Probability Split */}
                  {result.ai_probability !== null && result.human_probability !== null && (
                    <div className="mt-3 grid grid-cols-2 gap-2 pt-2 border-t border-[#2B2F3D]/60 text-xs font-mono">
                      <div className="rounded bg-[#0B0C10]/60 p-2">
                        <span className="text-[10px] uppercase text-[#6B7280]">AI Probability</span>
                        <p className="text-sm font-bold text-red-400">
                          {(result.ai_probability * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="rounded bg-[#0B0C10]/60 p-2">
                        <span className="text-[10px] uppercase text-[#6B7280]">Human Probability</span>
                        <p className="text-sm font-bold text-emerald-400">
                          {(result.human_probability * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Evidentiary Signals Table */}
              {result.evidence && result.evidence.length > 0 && (
                <div className="mt-5">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-mono text-xs font-semibold text-[#D4AF37] uppercase">
                      Forensic Telemetry Evidence
                    </h4>
                    <span className="text-[10px] text-[#6B7280]">{result.evidence.length} Signals Evaluated</span>
                  </div>

                  <div className="divide-y divide-[#2B2F3D]/60 rounded-lg border border-[#2B2F3D] bg-[#0B0C10]/60">
                    {result.evidence.map((item, idx) => (
                      <div key={idx} className="p-3 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-white">{item.signal}</span>
                          {item.metric && (
                            <span className="font-mono text-[#F3E5AB] font-semibold">{item.metric}</span>
                          )}
                        </div>
                        <p className="mt-1 text-[11px] leading-relaxed text-[#9FA6B2]">{item.finding}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Case Archiving & Audit Hash */}
              <div className="mt-5 rounded-lg border border-[#2B2F3D] bg-[#191C24] p-3.5">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div className="font-mono text-[11px] text-[#6B7280] truncate max-w-xs">
                    <span>SHA-256: </span>
                    <span className="text-[#9FA6B2]">{result.input_hash}</span>
                  </div>

                  <button
                    type="button"
                    onClick={handleSaveToReports}
                    disabled={caseSaved}
                    className="self-start sm:self-auto rounded-lg border border-[#2B2F3D] bg-[#12141A] px-3 py-1.5 text-xs text-[#D4AF37] hover:border-[#D4AF37] disabled:opacity-50"
                  >
                    {caseSaved ? "✓ Archived in Cases" : "+ Save Case to Reports"}
                  </button>
                </div>
              </div>

              {/* Limitations & Caveats */}
              {result.limitations && result.limitations.length > 0 && (
                <div className="mt-5 rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-4">
                  <h4 className="text-xs font-semibold text-white">Scientific Limitations &amp; Disclaimers</h4>
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-[11px] text-[#9FA6B2] leading-relaxed">
                    {result.limitations.map((limit, idx) => (
                      <li key={idx}>{limit}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Investigation History Table */}
      <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/95 p-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-4">
          <div>
            <h3 className="text-base font-semibold text-white">Analyst Text Investigation Log</h3>
            <p className="text-xs text-[#9FA6B2]">
              User-scoped forensic history. Raw text is protected; only cryptographic hashes and snippets are retained.
            </p>
          </div>
          <button
            type="button"
            onClick={fetchHistory}
            disabled={loadingHistory}
            className="rounded-lg border border-[#2B2F3D] bg-[#191C24] px-3 py-1 text-xs text-[#9FA6B2] hover:border-[#D4AF37] hover:text-[#D4AF37]"
          >
            {loadingHistory ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {history.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#6B7280]">
            No previous text investigations recorded. Run an analysis above to build your audit case history.
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[#2B2F3D] font-mono text-[11px] uppercase tracking-wider text-[#6B7280]">
                <tr>
                  <th className="py-2.5 px-3">Case ID</th>
                  <th className="py-2.5 px-3">Snippet</th>
                  <th className="py-2.5 px-3">Words</th>
                  <th className="py-2.5 px-3">Classification</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2B2F3D]/50 text-[#9FA6B2]">
                {history.map((item) => (
                  <tr key={item.analysis_id || (item as unknown as { id: number }).id} className="hover:bg-[#191C24]/50">
                    <td className="py-3 px-3 font-mono text-[#F3E5AB]">
                      #{item.analysis_id || (item as unknown as { id: number }).id}
                    </td>
                    <td className="py-3 px-3 max-w-xs truncate text-white">
                      &ldquo;{item.text_snippet}&rdquo;
                    </td>
                    <td className="py-3 px-3 font-mono">{item.word_count}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-block rounded-full border px-2 py-0.5 font-mono text-[10px] font-bold ${getClassificationBadgeStyle(
                          item.classification
                        )}`}
                      >
                        {item.classification}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-[#D4AF37]">
                      {item.confidence_score !== null ? `${(item.confidence_score * 100).toFixed(1)}%` : "N/A"}
                    </td>
                    <td className="py-3 px-3 text-[11px] text-[#6B7280]">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
