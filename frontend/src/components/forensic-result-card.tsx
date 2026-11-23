"use client";

import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Download,
  Info,
  Cpu,
  ShieldCheck,
} from "lucide-react";

export type ForensicClassification =
  | "LIKELY AI-GENERATED"
  | "LIKELY HUMAN"
  | "AI-ASSISTED"
  | "MANIPULATED"
  | "INCONCLUSIVE"
  | "HIGHLY_LIKELY_AI"
  | "SUSPECTED_AI"
  | "LIKELY_AUTHENTIC"
  | "HIGHLY_LIKELY_AUTHENTIC"
  | string;

export type ForensicStatus = "QUEUED" | "RUNNING" | "SUCCESS" | "FAILED" | "BLOCKED";

export interface ForensicEvidenceItem {
  signal: string;
  metric?: string;
  finding: string;
}

export interface ForensicResultProps {
  modality: "text" | "image" | "video" | "audio";
  modalityCode: string;
  status?: ForensicStatus;
  isEngineConfigured?: boolean;
  classification?: ForensicClassification | null;
  confidenceScore?: number | null; // ONLY displayed when calculated by a real implemented model
  evidence?: ForensicEvidenceItem[];
  limitations?: string[];
  pipelineNote?: string;
  onDownloadPdf?: () => void;
  isDownloadingPdf?: boolean;
}

export function ForensicResultCard({
  modality,
  modalityCode,
  status = "BLOCKED",
  isEngineConfigured = false,
  classification = null,
  confidenceScore = null,
  evidence = [],
  limitations = [],
  pipelineNote,
  onDownloadPdf,
  isDownloadingPdf = false,
}: ForensicResultProps) {
  // If engine is not configured yet, display strict unconfigured forensic banner
  if (!isEngineConfigured) {
    return (
      <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-4">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-[#D6B15E]/40 bg-[#181C23] font-mono text-xs font-bold text-[#D6B15E]">
              {modalityCode}
            </span>
            <div>
              <h3 className="text-sm font-semibold tracking-wide text-[#F5F5F2] uppercase">
                {modality} Forensics Engine Architecture
              </h3>
              <p className="text-[11px] text-[#A3A7B0]">
                Modular Interface &bull; Engine Status Disclosure
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 font-mono text-[10px] font-bold text-amber-300">
              STATUS: {status}
            </span>
          </div>
        </div>

        {/* Prominent Mandatory Engine Unconfigured Notice */}
        <div className="mt-5 rounded-xl border border-amber-500/30 bg-[#181C23] p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold tracking-wide text-[#F0D58A] uppercase">
                Detection engine not configured yet
              </h4>
              <p className="mt-1 text-xs leading-relaxed text-[#A3A7B0]">
                In compliance with AICF scientific integrity rules, simulated results and mock
                confidence scores are strictly forbidden. The modular AI architecture package for{" "}
                <span className="font-mono text-[#F5F5F2]">backend/app/ml/{modality}/</span> is
                scaffolded and awaits concrete inference weights and model pipelines.
              </p>
            </div>
          </div>
        </div>

        {/* Planned Pipeline Telemetry Specification */}
        <div className="mt-5 space-y-3">
          <div className="flex items-center gap-2 font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider">
            <Cpu className="h-3.5 w-3.5" />
            <span>Planned Telemetry &amp; Detection Pipeline</span>
          </div>
          <p className="text-xs leading-relaxed text-[#A3A7B0]">
            {pipelineNote ||
              `The ${modality} detection subsystem will extract forensic signals, calculate probabilistic score distributions, and generate auditable evidentiary reports.`}
          </p>
        </div>

        {/* Disclaimers & Ethics */}
        <div className="mt-6 border-t border-[#292D35] pt-4">
          <div className="flex items-center gap-1.5 text-[11px] text-[#737984]">
            <Info className="h-3.5 w-3.5 shrink-0" />
            <span>Forensic AI classifications are probabilistic assessments, never definitive proof of origin.</span>
          </div>
        </div>
      </div>
    );
  }

  // Configured Engine Forensic Result
  const getVerdictStyle = (verdict: ForensicClassification | null) => {
    switch (verdict) {
      case "LIKELY AI-GENERATED":
      case "HIGHLY_LIKELY_AI":
      case "SUSPECTED_AI":
        return {
          border: "border-amber-500/40",
          bg: "bg-amber-500/10",
          text: "text-amber-400",
          icon: AlertTriangle,
          label: verdict === "HIGHLY_LIKELY_AI" ? "Highly Likely Synthetic / AI-Generated" : "Likely Synthetic / AI-Generated",
        };
      case "LIKELY HUMAN":
      case "LIKELY_AUTHENTIC":
      case "HIGHLY_LIKELY_AUTHENTIC":
        return {
          border: "border-emerald-500/40",
          bg: "bg-emerald-500/10",
          text: "text-emerald-400",
          icon: CheckCircle2,
          label: verdict === "HIGHLY_LIKELY_AUTHENTIC" ? "Highly Likely Human Authentic" : "Likely Human Authentic",
        };
      case "INCONCLUSIVE":
      default:
        return {
          border: "border-[#D6B15E]/40",
          bg: "bg-[#D6B15E]/10",
          text: "text-[#D6B15E]",
          icon: HelpCircle,
          label: "Inconclusive / Mixed Signals",
        };
    }
  };

  const style = getVerdictStyle(classification);
  const VerdictIcon = style.icon;

  return (
    <div className="rounded-2xl border border-[#292D35] bg-[#12151B] p-6 shadow-xl backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-4">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-[#D6B15E]/40 bg-[#181C23] font-mono text-xs font-bold text-[#D6B15E]">
            {modalityCode}
          </span>
          <div>
            <h3 className="text-sm font-semibold tracking-wide text-[#F5F5F2] uppercase">
              {modality} Forensic Verdict
            </h3>
            <p className="text-[11px] text-[#A3A7B0]">
              Empirical Inference Result &bull; Calibrated Boundaries
            </p>
          </div>
        </div>

        {onDownloadPdf && (
          <button
            type="button"
            onClick={onDownloadPdf}
            disabled={isDownloadingPdf}
            className="inline-flex items-center gap-2 rounded-lg border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-3.5 py-1.5 font-mono text-xs font-bold text-[#090A0D] hover:opacity-95 disabled:opacity-50 transition-all cursor-pointer shadow-[0_0_12px_rgba(214,177,94,0.15)]"
          >
            {isDownloadingPdf ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
                <span>Generating PDF...</span>
              </>
            ) : (
              <>
                <Download className="h-3.5 w-3.5" />
                <span>Download Report PDF</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Main Classification Banner */}
      <div className={`mt-5 rounded-xl border ${style.border} ${style.bg} p-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <VerdictIcon className={`h-6 w-6 ${style.text}`} />
            <div>
              <div className="font-mono text-[10px] tracking-widest uppercase text-[#A3A7B0]">
                Forensic Classification
              </div>
              <div className={`text-base font-bold ${style.text}`}>
                {classification || "ANALYSIS COMPLETED"}
              </div>
            </div>
          </div>

          {confidenceScore !== null && confidenceScore !== undefined && (
            <div className="text-right">
              <div className="font-mono text-[10px] text-[#737984] uppercase">AI Confidence</div>
              <div className="font-mono text-lg font-bold text-[#F5F5F2]">
                {(confidenceScore * 100).toFixed(1)}%
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Evidentiary Signals Breakdown */}
      {evidence.length > 0 && (
        <div className="mt-5 space-y-3">
          <div className="flex items-center gap-2 font-mono text-xs font-semibold text-[#D6B15E] uppercase tracking-wider">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Evidentiary Signals &amp; Forensic Features</span>
          </div>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {evidence.map((item, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-[#292D35] bg-[#181C23] p-3 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] font-semibold text-[#F0D58A]">
                    {item.signal}
                  </span>
                  {item.metric && (
                    <span className="font-mono text-[10px] text-[#A3A7B0] bg-[#090A0D] px-2 py-0.5 rounded border border-[#292D35]">
                      {item.metric}
                    </span>
                  )}
                </div>
                <p className="mt-1.5 text-[11px] text-[#A3A7B0] leading-relaxed">
                  {item.finding}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Limitations Block */}
      {limitations.length > 0 && (
        <div className="mt-5 rounded-xl border border-[#292D35] bg-[#181C23]/60 p-3.5 text-xs">
          <span className="font-mono text-[10px] font-bold text-[#737984] uppercase block mb-1">
            Methodological Limitations
          </span>
          <ul className="space-y-1 text-[11px] text-[#A3A7B0]">
            {limitations.map((lim, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-[#D6B15E]">&bull;</span>
                <span>{lim}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Mandatory Scientific Disclaimer */}
      <div className="mt-5 border-t border-[#292D35] pt-3 text-[11px] text-[#737984]">
        All forensic classifications reflect probabilistic statistical patterns. They should be corroborated with additional provenance markers, custody logs, and multi-modal evidence.
      </div>
    </div>
  );
}
