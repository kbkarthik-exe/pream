"use client";

import React from "react";

export type ForensicClassification =
  | "LIKELY AI-GENERATED"
  | "LIKELY HUMAN"
  | "AI-ASSISTED"
  | "MANIPULATED"
  | "INCONCLUSIVE";

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
}: ForensicResultProps) {
  // If engine is not configured yet, display strict unconfigured forensic banner
  if (!isEngineConfigured) {
    return (
      <div className="rounded-xl border border-[#D4AF37]/30 bg-[#12141A]/95 p-6 shadow-[0_0_25px_rgba(0,0,0,0.6)] backdrop-blur-md">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-4">
          <div className="flex items-center gap-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#D4AF37]/50 bg-[#191C24] font-mono text-xs font-bold text-[#D4AF37]">
              {modalityCode}
            </span>
            <div>
              <h3 className="text-sm font-semibold tracking-wide text-white uppercase">
                {modality} Forensics Result Specification
              </h3>
              <p className="text-[11px] text-[#9FA6B2]">
                Architectural Contract &bull; Decoupled Module
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-amber-300">
              STATUS: {status}
            </span>
          </div>
        </div>

        {/* Prominent Mandatory Engine Unconfigured Notice */}
        <div className="mt-5 rounded-lg border border-amber-500/30 bg-[#191C24]/90 p-4">
          <div className="flex items-start gap-3">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-xs font-bold text-amber-400">
              !
            </span>
            <div>
              <h4 className="text-xs font-bold tracking-wide text-[#F3E5AB] uppercase">
                Detection engine not configured yet.
              </h4>
              <p className="mt-1 text-xs leading-relaxed text-[#9FA6B2]">
                In compliance with AICF scientific integrity rules, simulated results and mock
                confidence scores are strictly forbidden. The modular AI architecture package for{" "}
                <span className="font-mono text-white">backend/app/ml/{modality}/</span> is
                scaffolded and awaits concrete inference weights and model pipelines in subsequent steps.
              </p>
            </div>
          </div>
        </div>

        {/* Planned Pipeline Telemetry Specification */}
        <div className="mt-5 space-y-3">
          <h4 className="font-mono text-xs font-semibold text-[#D4AF37] uppercase tracking-wider">
            Planned Telemetry &amp; Detection Pipeline
          </h4>
          <p className="text-xs leading-relaxed text-[#9FA6B2]">
            {pipelineNote ||
              `The ${modality} detection subsystem will extract forensic signals, calculate probabilistic score distributions, and generate auditable evidentiary reports.`}
          </p>

          <div className="grid grid-cols-1 gap-2 pt-2 sm:grid-cols-2">
            <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10]/60 p-3">
              <span className="text-[10px] uppercase tracking-wider text-[#6B7280]">
                Output Taxonomy
              </span>
              <p className="mt-1 font-mono text-xs text-[#F3E5AB]">
                5 Classes (LIKELY AI-GENERATED, LIKELY HUMAN, AI-ASSISTED, MANIPULATED, INCONCLUSIVE)
              </p>
            </div>
            <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10]/60 p-3">
              <span className="text-[10px] uppercase tracking-wider text-[#6B7280]">
                Forensic Principle
              </span>
              <p className="mt-1 text-xs text-[#9FA6B2]">
                Probabilistic uncertainty boundaries &bull; Zero false-certainty claims
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Active / Configured Engine Display (When real models are linked)
  const classificationStyles: Record<ForensicClassification, string> = {
    "LIKELY AI-GENERATED": "border-red-500/50 bg-red-500/10 text-red-400",
    "LIKELY HUMAN": "border-emerald-500/50 bg-emerald-500/10 text-emerald-400",
    "AI-ASSISTED": "border-amber-500/50 bg-amber-500/10 text-amber-300",
    "MANIPULATED": "border-purple-500/50 bg-purple-500/10 text-purple-400",
    "INCONCLUSIVE": "border-blue-500/50 bg-blue-500/10 text-blue-400",
  };

  return (
    <div className="rounded-xl border border-[#2B2F3D] bg-[#12141A]/95 p-6 shadow-xl backdrop-blur-md">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-[#2B2F3D] pb-4">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#D4AF37]/50 bg-[#191C24] font-mono text-xs font-bold text-[#D4AF37]">
            {modalityCode}
          </span>
          <div>
            <h3 className="text-sm font-semibold tracking-wide text-white uppercase">
              {modality} Forensic Findings
            </h3>
            <p className="text-[11px] text-[#9FA6B2]">Verified Model Telemetry</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-full border border-[#2B2F3D] bg-[#191C24] px-2.5 py-0.5 font-mono text-[10px] text-[#9FA6B2]">
            STATUS: {status}
          </span>
          {classification && (
            <span
              className={`rounded-full border px-3 py-0.5 font-mono text-xs font-bold ${
                classificationStyles[classification]
              }`}
            >
              {classification}
            </span>
          )}
        </div>
      </div>

      {/* Real Confidence Score (Only when calculated by a real model) */}
      {confidenceScore !== null && (
        <div className="mt-5 rounded-lg border border-[#2B2F3D] bg-[#191C24] p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#9FA6B2]">Empirical Confidence Level</span>
            <span className="font-mono text-base font-bold text-[#D4AF37]">
              {(confidenceScore * 100).toFixed(1)}%
            </span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[#0B0C10]">
            <div
              className="h-full bg-gradient-to-r from-[#997A15] to-[#D4AF37]"
              style={{ width: `${Math.min(100, Math.max(0, confidenceScore * 100))}%` }}
            />
          </div>
        </div>
      )}

      {/* Evidentiary Signals Table */}
      {evidence.length > 0 && (
        <div className="mt-5">
          <h4 className="font-mono text-xs font-semibold text-[#D4AF37] uppercase">
            Forensic Evidence
          </h4>
          <div className="mt-2 divide-y divide-[#2B2F3D]/60 rounded-lg border border-[#2B2F3D] bg-[#0B0C10]/60">
            {evidence.map((item, idx) => (
              <div key={idx} className="p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white">{item.signal}</span>
                  {item.metric && (
                    <span className="font-mono text-[#F3E5AB]">{item.metric}</span>
                  )}
                </div>
                <p className="mt-1 text-[11px] text-[#9FA6B2]">{item.finding}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scientific Limitations */}
      {limitations.length > 0 && (
        <div className="mt-5 rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-4">
          <h4 className="text-xs font-semibold text-white">Scientific Limitations &amp; Caveats</h4>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-[11px] text-[#9FA6B2]">
            {limitations.map((limit, idx) => (
              <li key={idx}>{limit}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
