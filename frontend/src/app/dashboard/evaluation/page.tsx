"use client";

import React, { useEffect, useState } from "react";
import {
  evaluationApi,
  EvaluationStatus,
  EvaluationSummary,
  ModalityEvaluation,
} from "@/lib/api";
import {
  FileText,
  Image as ImageIcon,
  Film,
  Volume2,
  RotateCcw,
  Clock,
} from "lucide-react";

type TabFilter = "all" | "text" | "image" | "video" | "audio";

export default function ModelEvaluationPage() {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runningModality, setRunningModality] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabFilter>("all");
  const [expandedSamples, setExpandedSamples] = useState<Record<string, boolean>>({});

  const fetchBenchmarks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await evaluationApi.getSummary();
      setSummary(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load model evaluation benchmarks.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const data = await evaluationApi.getSummary();
        if (!ignore) {
          setSummary(data);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load model evaluation benchmarks.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, []);

  const handleRunEvaluation = async (modality: "all" | "text" | "image" = "all") => {
    try {
      setRunning(true);
      setRunningModality(modality);
      setError(null);
      await evaluationApi.run(modality);
      await fetchBenchmarks();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : `Failed to execute evaluation for ${modality}.`);
    } finally {
      setRunning(false);
      setRunningModality(null);
    }
  };

  const toggleSampleDrawer = (modalityKey: string) => {
    setExpandedSamples((prev) => ({
      ...prev,
      [modalityKey]: !prev[modalityKey],
    }));
  };

  const renderStatusBadge = (status: EvaluationStatus) => {
    switch (status) {
      case "EVALUATED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-950/40 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            EVALUATED
          </span>
        );
      case "MODEL UNAVAILABLE":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-950/40 px-2.5 py-0.5 text-xs font-semibold text-amber-400">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            MODEL UNAVAILABLE
          </span>
        );
      case "EVALUATION REQUIRED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-yellow-500/40 bg-yellow-950/40 px-2.5 py-0.5 text-xs font-semibold text-yellow-300">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-400" />
            EVALUATION REQUIRED
          </span>
        );
      case "INSUFFICIENT DATA":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-600/40 bg-zinc-800/40 px-2.5 py-0.5 text-xs font-semibold text-zinc-300">
            INSUFFICIENT DATA
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/40 bg-purple-950/40 px-2.5 py-0.5 text-xs font-semibold text-purple-300">
            CANCELLED
          </span>
        );
      case "EVALUATION FAILED":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-500/40 bg-rose-950/40 px-2.5 py-0.5 text-xs font-semibold text-rose-400">
            EVALUATION FAILED
          </span>
        );
    }
  };

  const renderModalityCard = (mod: ModalityEvaluation) => {
    const isEvaluated = mod.evaluation_results?.status === "EVALUATED";
    const cm = mod.evaluation_results?.confusion_matrix;
    const metrics = mod.evaluation_results?.metrics;
    const counts = mod.evaluation_results?.class_counts;
    const isExpanded = !!expandedSamples[mod.modality];

    return (
      <div
        key={mod.modality}
        className="rounded-xl border border-[#2B2F3D] bg-[#12141A] p-6 shadow-xl transition-all duration-200"
      >
        {/* Card Header */}
        <div className="flex flex-col gap-4 border-b border-[#2B2F3D] pb-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D6B15E]/40 bg-[#181C23] text-[#D6B15E]">
              {mod.modality === "text" && <FileText className="h-5 w-5" />}
              {mod.modality === "image" && <ImageIcon className="h-5 w-5" />}
              {mod.modality === "video" && <Film className="h-5 w-5" />}
              {mod.modality === "audio" && <Volume2 className="h-5 w-5" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-mono text-base font-bold tracking-wide text-white uppercase">
                  {mod.modality} Forensics Engine
                </h3>
                {renderStatusBadge(mod.evaluation_results?.status || "EVALUATION REQUIRED")}
              </div>
              <p className="text-xs text-[#9FA6B2] mt-0.5">
                Model: <span className="font-mono text-[#F0D58A]">{mod.model_specifications.model_name}</span>{" "}
                (v{mod.model_specifications.version}) • {mod.model_specifications.architecture}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {mod.elapsed_seconds !== undefined && (
              <span className="font-mono text-xs text-[#A3A7B0] bg-[#181C23] px-2.5 py-1 rounded-lg border border-[#292D35] flex items-center gap-1.5">
                <Clock className="h-3 w-3 text-[#D6B15E]" />
                <span>{mod.elapsed_seconds}s</span>
              </span>
            )}
            {(mod.modality === "text" || mod.modality === "image") && (
              <button
                type="button"
                onClick={() => handleRunEvaluation(mod.modality as "text" | "image")}
                disabled={running}
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#D6B15E]/50 bg-[#D6B15E]/10 px-3 py-1.5 font-mono text-xs font-semibold text-[#D6B15E] hover:bg-[#D6B15E]/20 disabled:opacity-50 transition-all cursor-pointer"
              >
                {running && runningModality === mod.modality ? (
                  <>
                    <RotateCcw className="h-3 w-3 animate-spin text-[#D6B15E]" />
                    <span>Evaluating...</span>
                  </>
                ) : (
                  <>
                    <RotateCcw className="h-3 w-3 text-[#D6B15E]" />
                    <span>Re-evaluate</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Unconfigured / Cancelled Engine States */}
        {!isEvaluated && (
          <div className="mt-5 rounded-lg border border-zinc-800 bg-[#0B0C10] p-5">
            <div className="flex items-start gap-3">
              <span className="text-xl">
                {mod.modality === "audio" ? "🚫" : "⏳"}
              </span>
              <div>
                <h4 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                  {mod.modality === "audio" ? "Engine Formally Cancelled" : "Evaluation Prerequisites Not Met"}
                </h4>
                <p className="mt-1 text-xs text-[#9FA6B2]">
                  {mod.evaluation_results?.message ||
                    "Model weights or evaluation datasets are not currently configured for this detection engine."}
                </p>
                {mod.modality === "video" && (
                  <div className="mt-3 text-xs text-[#6B7280]">
                    Required for Video Evaluation: Local face crop pipeline, 3D ConvNet/Transformer weights,
                    and labeled synthetic manipulation dataset (e.g. FaceForensics++).
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Evaluated Engine Content */}
        {isEvaluated && (
          <div className="mt-6 space-y-6">
            {/* Key Statistical Metrics Grid */}
            <div>
              <h4 className="font-mono text-xs font-semibold text-[#D4AF37] tracking-wider uppercase mb-3">
                Classification Performance Metrics (95% Wilson CI)
              </h4>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-3 text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#9FA6B2]">
                    Accuracy
                  </span>
                  <div className="mt-1 font-mono text-lg font-bold text-white">
                    {metrics?.accuracy !== null ? `${(metrics!.accuracy * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  {metrics?.accuracy_ci_95 && (
                    <span className="text-[10px] font-mono text-[#6B7280]">
                      CI: [{(metrics.accuracy_ci_95[0] * 100).toFixed(1)}%, {(metrics.accuracy_ci_95[1] * 100).toFixed(1)}%]
                    </span>
                  )}
                </div>

                <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-3 text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#9FA6B2]">
                    Precision
                  </span>
                  <div className="mt-1 font-mono text-lg font-bold text-emerald-400">
                    {metrics?.precision !== null ? `${(metrics!.precision * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  {metrics?.precision_ci_95 && (
                    <span className="text-[10px] font-mono text-[#6B7280]">
                      CI: [{(metrics.precision_ci_95[0] * 100).toFixed(1)}%, {(metrics.precision_ci_95[1] * 100).toFixed(1)}%]
                    </span>
                  )}
                </div>

                <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-3 text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#9FA6B2]">
                    Recall (TPR)
                  </span>
                  <div className="mt-1 font-mono text-lg font-bold text-blue-400">
                    {metrics?.recall !== null ? `${(metrics!.recall * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  {metrics?.recall_ci_95 && (
                    <span className="text-[10px] font-mono text-[#6B7280]">
                      CI: [{(metrics.recall_ci_95[0] * 100).toFixed(1)}%, {(metrics.recall_ci_95[1] * 100).toFixed(1)}%]
                    </span>
                  )}
                </div>

                <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-3 text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#9FA6B2]">
                    F1-Score
                  </span>
                  <div className="mt-1 font-mono text-lg font-bold text-purple-400">
                    {metrics?.f1_score !== null ? metrics!.f1_score.toFixed(3) : "N/A"}
                  </div>
                  <span className="text-[10px] font-mono text-[#6B7280]">Harmonic Mean</span>
                </div>

                <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-3 text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#9FA6B2]">
                    FPR (Type I)
                  </span>
                  <div className="mt-1 font-mono text-lg font-bold text-rose-400">
                    {metrics?.false_positive_rate !== null ? `${(metrics!.false_positive_rate * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  <span className="text-[10px] font-mono text-[#6B7280]">False Alarm</span>
                </div>

                <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-3 text-center">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#9FA6B2]">
                    FNR (Type II)
                  </span>
                  <div className="mt-1 font-mono text-lg font-bold text-amber-400">
                    {metrics?.false_negative_rate !== null ? `${(metrics!.false_negative_rate * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  <span className="text-[10px] font-mono text-[#6B7280]">Miss Rate</span>
                </div>
              </div>
            </div>

            {/* Confusion Matrix & Calibration Split */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* 2x2 Confusion Matrix */}
              <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-4">
                <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-2 mb-3">
                  <h4 className="font-mono text-xs font-semibold text-[#D4AF37] uppercase tracking-wider">
                    Binary Confusion Matrix (2x2)
                  </h4>
                  <span className="text-[10px] font-mono text-[#9FA6B2]">
                    N = {mod.evaluation_results?.evaluated_samples || 0} evaluated
                  </span>
                </div>

                {cm ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-center border-collapse">
                      <thead>
                        <tr>
                          <th className="p-2 text-[10px] font-mono text-[#6B7280] text-left">Actual \ Pred</th>
                          <th className="p-2 text-[10px] font-mono text-emerald-400 uppercase">
                            Pred Authentic (0)
                          </th>
                          <th className="p-2 text-[10px] font-mono text-rose-400 uppercase">
                            Pred Synthetic (1)
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#2B2F3D] text-xs font-mono">
                        <tr>
                          <td className="p-2 text-left font-medium text-emerald-400 text-[11px]">
                            Actual Authentic (0)
                          </td>
                          <td className="p-3 bg-emerald-950/20 font-bold text-emerald-300">
                            TN: {cm.true_negatives}
                            <span className="block text-[9px] text-[#9FA6B2] font-normal">True Negative</span>
                          </td>
                          <td className="p-3 bg-rose-950/20 font-bold text-rose-300">
                            FP: {cm.false_positives}
                            <span className="block text-[9px] text-rose-400/80 font-normal">Type I Error</span>
                          </td>
                        </tr>
                        <tr>
                          <td className="p-2 text-left font-medium text-rose-400 text-[11px]">
                            Actual Synthetic (1)
                          </td>
                          <td className="p-3 bg-amber-950/20 font-bold text-amber-300">
                            FN: {cm.false_negatives}
                            <span className="block text-[9px] text-amber-400/80 font-normal">Type II Error</span>
                          </td>
                          <td className="p-3 bg-emerald-950/20 font-bold text-emerald-300">
                            TP: {cm.true_positives}
                            <span className="block text-[9px] text-[#9FA6B2] font-normal">True Positive</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-[#6B7280]">Confusion matrix unavailable.</p>
                )}

                <div className="mt-3 flex justify-between text-[11px] font-mono text-[#9FA6B2] border-t border-[#2B2F3D] pt-2">
                  <span>Ground Truth Synthetic: {counts?.ground_truth_synthetic ?? 0}</span>
                  <span>Ground Truth Authentic: {counts?.ground_truth_authentic ?? 0}</span>
                </div>
              </div>

              {/* Calibration & Sample Accounting */}
              <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-2 mb-3">
                    <h4 className="font-mono text-xs font-semibold text-[#D4AF37] uppercase tracking-wider">
                      Probabilistic Calibration & Audit
                    </h4>
                    <span className="text-[10px] font-mono text-[#9FA6B2]">Statistical Validation</span>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[#9FA6B2]">Brier Score (Mean Squared Probability Error):</span>
                      <span className="font-mono font-bold text-white">
                        {metrics?.brier_score !== null && metrics?.brier_score !== undefined
                          ? metrics.brier_score.toFixed(4)
                          : "N/A"}
                      </span>
                    </div>

                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[#9FA6B2]">Expected Calibration Error (ECE):</span>
                      <span className="font-mono font-bold text-white">
                        {metrics?.expected_calibration_error !== null && metrics?.expected_calibration_error !== undefined
                          ? metrics.expected_calibration_error.toFixed(4)
                          : "N/A"}
                      </span>
                    </div>

                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[#9FA6B2]">Inconclusive Predictions (Gated):</span>
                      <span className="font-mono font-bold text-yellow-400">
                        {mod.evaluation_results?.inconclusive_samples ?? 0}
                      </span>
                    </div>

                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[#9FA6B2]">Inference Errors / Failed Samples:</span>
                      <span className="font-mono font-bold text-rose-400">
                        {mod.evaluation_results?.error_samples ?? 0}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 border-t border-[#2B2F3D] pt-3">
                  <p className="text-[11px] text-[#6B7280] italic">
                    Note: Brier scores closer to 0.0 indicate high probabilistic reliability. Models subject to severe
                    distribution shift exhibit higher ECE, confirming that raw probability outputs require threshold
                    gating rather than blind acceptance.
                  </p>
                </div>
              </div>
            </div>

            {/* Model & Dataset Metadata Specs */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Model Specifications */}
              <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-4 text-xs">
                <h4 className="font-mono text-xs font-semibold text-[#D4AF37] uppercase tracking-wider border-b border-[#2B2F3D] pb-2 mb-3">
                  Configured Model Profile
                </h4>
                <dl className="space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">Model Identifier:</dt>
                    <dd className="text-white">{mod.model_specifications.model_name}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">Version:</dt>
                    <dd className="text-white">{mod.model_specifications.version}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">HuggingFace Source:</dt>
                    <dd className="text-blue-400 truncate max-w-[200px]">
                      {mod.model_specifications.source}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">License:</dt>
                    <dd className="text-white">{mod.model_specifications.license}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">Execution Device:</dt>
                    <dd className="text-[#D4AF37]">{mod.model_specifications.device || "cpu"}</dd>
                  </div>
                  <div className="pt-2">
                    <dt className="text-[#9FA6B2] mb-1">Intended Task:</dt>
                    <dd className="text-[#F8F9FA] font-sans text-xs">
                      {mod.model_specifications.intended_task}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Dataset Metadata */}
              <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-4 text-xs">
                <h4 className="font-mono text-xs font-semibold text-[#D4AF37] uppercase tracking-wider border-b border-[#2B2F3D] pb-2 mb-3">
                  Benchmark Dataset Provenance
                </h4>
                <dl className="space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">Dataset Name:</dt>
                    <dd className="text-white">{mod.dataset_metadata.dataset_name}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">License:</dt>
                    <dd className="text-white">{mod.dataset_metadata.license}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">Sample Count:</dt>
                    <dd className="text-white">{mod.dataset_metadata.sample_count}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[#9FA6B2]">Class Balance:</dt>
                    <dd className="text-emerald-400">{mod.dataset_metadata.class_balance || "Balanced"}</dd>
                  </div>
                  <div className="pt-2">
                    <dt className="text-[#9FA6B2] mb-1">Preprocessing Protocol:</dt>
                    <dd className="text-[#F8F9FA] font-sans text-xs">
                      {mod.dataset_metadata.preprocessing}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Scientific Limitations & Epistemic Boundaries */}
            <div className="rounded-lg border border-amber-500/20 bg-amber-950/10 p-4">
              <h4 className="font-mono text-xs font-semibold text-amber-300 uppercase tracking-wider mb-2 flex items-center gap-2">
                <span>⚠️</span> Documented Scientific Limitations & Domain Boundaries
              </h4>
              <ul className="list-disc list-inside space-y-1 text-xs text-[#9FA6B2]">
                {mod.model_specifications.limitations.map((lim, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {lim}
                  </li>
                ))}
                {mod.dataset_metadata.known_limitations.map((lim, idx) => (
                  <li key={`ds-${idx}`} className="leading-relaxed text-[#6B7280]">
                    [Dataset Constraint] {lim}
                  </li>
                ))}
              </ul>
            </div>

            {/* Individual Sample Audit Drawer */}
            {mod.sample_records && mod.sample_records.length > 0 && (
              <div className="rounded-lg border border-[#2B2F3D] bg-[#0B0C10] p-4">
                <button
                  type="button"
                  onClick={() => toggleSampleDrawer(mod.modality)}
                  className="flex w-full items-center justify-between font-mono text-xs font-semibold text-[#D4AF37] uppercase tracking-wider hover:text-[#F3E5AB] transition-colors"
                >
                  <span>
                    Per-Sample Forensic Prediction Audit Trail ({mod.sample_records.length} items)
                  </span>
                  <span>{isExpanded ? "▲ Collapse" : "▼ Expand Records"}</span>
                </button>

                {isExpanded && (
                  <div className="mt-4 max-h-96 overflow-y-auto overflow-x-auto">
                    <table className="w-full text-left font-mono text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-[#2B2F3D] text-[10px] text-[#6B7280]">
                          <th className="p-2">Sample ID</th>
                          <th className="p-2">Ground Truth</th>
                          <th className="p-2">Prediction</th>
                          <th className="p-2">Classification</th>
                          <th className="p-2 text-right">AI Prob</th>
                          <th className="p-2">Domain / Source</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#2B2F3D]/50 text-[11px]">
                        {mod.sample_records.map((rec) => {
                          const isMatch = rec.ground_truth === rec.predicted_label;
                          return (
                            <tr
                              key={rec.sample_id}
                              className={`hover:bg-[#191C24]/50 ${
                                rec.error
                                  ? "bg-rose-950/20"
                                  : isMatch
                                  ? "bg-transparent"
                                  : "bg-amber-950/10"
                              }`}
                            >
                              <td className="p-2 text-white">{rec.sample_id}</td>
                              <td className="p-2">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] ${
                                    rec.ground_truth === 1
                                      ? "bg-purple-950/50 text-purple-300 border border-purple-500/30"
                                      : "bg-emerald-950/50 text-emerald-300 border border-emerald-500/30"
                                  }`}
                                >
                                  {rec.ground_truth === 1 ? "Synthetic (1)" : "Authentic (0)"}
                                </span>
                              </td>
                              <td className="p-2">
                                {rec.predicted_label === 1 && (
                                  <span className="text-purple-400">Synthetic</span>
                                )}
                                {rec.predicted_label === 0 && (
                                  <span className="text-emerald-400">Authentic</span>
                                )}
                                {rec.predicted_label === -1 && (
                                  <span className="text-yellow-400">Inconclusive</span>
                                )}
                                {rec.error && <span className="text-rose-400">Error</span>}
                              </td>
                              <td className="p-2 text-[#9FA6B2]">
                                {rec.classification || rec.error || "N/A"}
                              </td>
                              <td className="p-2 text-right font-bold text-white">
                                {rec.ai_probability !== undefined
                                  ? `${(rec.ai_probability * 100).toFixed(1)}%`
                                  : "—"}
                              </td>
                              <td className="p-2 text-[#6B7280] truncate max-w-[220px]">
                                {rec.domain || rec.source || rec.file_path || "—"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const filteredModalities = () => {
    if (!summary) return [];
    if (activeTab === "text") return [summary.text];
    if (activeTab === "image") return [summary.image];
    if (activeTab === "video") return [summary.video];
    if (activeTab === "audio") return [summary.audio];
    return [summary.text, summary.image, summary.video, summary.audio];
  };

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 max-w-7xl mx-auto">
      {/* Top Page Header */}
      <div className="flex flex-col gap-4 border-b border-[#2B2F3D] pb-6 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#D4AF37] uppercase tracking-widest">
              AICF Authenticity Benchmarking
            </span>
            <span className="rounded bg-[#191C24] px-2 py-0.5 font-mono text-[10px] text-[#9FA6B2] border border-[#2B2F3D]">
              Step 09
            </span>
          </div>
          <h1 className="mt-1 font-mono text-2xl font-bold tracking-tight text-white md:text-3xl">
            Model Evaluation & Benchmarking
          </h1>
          <p className="mt-1 max-w-3xl text-xs text-[#9FA6B2] leading-relaxed">
            Empirical, verifiable accuracy measurements calculated on real configured inference models
            and open datasets. Transparently accounts for error distributions, confusion matrices, and
            domain boundaries with zero placeholder figures.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => handleRunEvaluation("all")}
            disabled={running || loading}
            className="inline-flex items-center gap-2 rounded-lg border border-[#D4AF37] bg-[#D4AF37] px-4 py-2 font-mono text-xs font-bold text-[#0B0C10] shadow-[0_0_15px_rgba(212,175,55,0.3)] hover:bg-[#F3E5AB] disabled:opacity-50 transition-all"
          >
            {running && runningModality === "all" ? (
              <>
                <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Benchmarking Engines...
              </>
            ) : (
              <>⚡ Re-Run All Benchmarks</>
            )}
          </button>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/20 p-4 text-xs text-rose-300">
          <span className="font-bold">Evaluation Notice:</span> {error}
        </div>
      )}

      {/* Modality Filter Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-[#2B2F3D] pb-4">
        {[
          { id: "all", label: "All Forensics Engines" },
          { id: "text", label: "AI Text (RoBERTa)" },
          { id: "image", label: "AI Image (Swin ViT)" },
          { id: "video", label: "AI Video (Unconfigured)" },
          { id: "audio", label: "AI Audio (Cancelled)" },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id as TabFilter)}
            className={`rounded-lg px-4 py-2 font-mono text-xs font-medium transition-all ${
              activeTab === tab.id
                ? "border border-[#D4AF37] bg-[#D4AF37]/15 text-[#D4AF37] shadow-[0_0_10px_rgba(212,175,55,0.15)]"
                : "border border-[#2B2F3D] bg-[#12141A] text-[#9FA6B2] hover:bg-[#191C24] hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="flex h-64 items-center justify-center rounded-xl border border-[#2B2F3D] bg-[#12141A]">
          <div className="flex flex-col items-center gap-3">
            <svg className="h-6 w-6 animate-spin text-[#D4AF37]" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <span className="font-mono text-xs text-[#9FA6B2]">
              Loading verified forensic benchmarks...
            </span>
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          {filteredModalities().map((mod) => renderModalityCard(mod))}
        </div>
      )}
    </div>
  );
}
