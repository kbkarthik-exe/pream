export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  identifier: string;
  password: string;
}

export interface ProfileUpdatePayload {
  full_name?: string;
  current_password?: string;
  new_password?: string;
}

export interface ForensicReport {
  id: number;
  user_id: number;
  title: string;
  media_type: "text" | "image" | "video" | "audio" | string;
  summary: string;
  is_private: boolean;
  created_at: string;
}

export interface ReportCreatePayload {
  title: string;
  media_type: "text" | "image" | "video" | "audio";
  summary: string;
  is_private?: boolean;
}

export interface DashboardStats {
  total_reports: number;
  text_reports: number;
  image_reports: number;
  video_reports: number;
  audio_reports: number;
  active_sessions: number;
}

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMessage = `Request failed with status ${res.status}`;
    let details: unknown = null;
    try {
      const data = await res.json();
      details = data;
      if (typeof data.detail === "string") {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMessage = data.detail
          .map((err: { msg?: string }) => err.msg || "Validation error")
          .join("; ");
      }
    } catch {
      // Non-JSON response error
    }
    throw new ApiError(errorMessage, res.status, details);
  }
  return res.json();
}

async function downloadBlob(url: string, defaultFilename: string): Promise<void> {
  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) {
    let errorMessage = `Failed to download PDF report (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") {
        errorMessage = data.detail;
      }
    } catch {
      // Non-JSON response
    }
    throw new ApiError(errorMessage, res.status);
  }

  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition");
  let filename = defaultFilename;
  if (disposition && disposition.includes("filename=")) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1].trim();
    }
  }

  const blobUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(blobUrl);
}


export const authApi = {
  async register(payload: RegisterPayload): Promise<User> {
    const res = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    });
    return handleResponse<User>(res);
  },

  async login(payload: LoginPayload): Promise<User> {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    });
    return handleResponse<User>(res);
  },

  async logout(): Promise<{ message: string }> {
    const res = await fetch("/api/v1/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    return handleResponse<{ message: string }>(res);
  },

  async getMe(): Promise<User> {
    const res = await fetch("/api/v1/auth/me", {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<User>(res);
  },

  async getStatus(): Promise<{ authenticated: boolean; user: User | null }> {
    try {
      const res = await fetch("/api/v1/auth/status", {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) return { authenticated: false, user: null };
      return res.json();
    } catch {
      return { authenticated: false, user: null };
    }
  },

  async updateProfile(payload: ProfileUpdatePayload): Promise<User> {
    const res = await fetch("/api/v1/auth/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    });
    return handleResponse<User>(res);
  },
};

export const reportsApi = {
  async list(mediaType?: string): Promise<ForensicReport[]> {
    const url = mediaType ? `/api/v1/reports?media_type=${encodeURIComponent(mediaType)}` : "/api/v1/reports";
    const res = await fetch(url, {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<ForensicReport[]>(res);
  },

  async create(payload: ReportCreatePayload): Promise<ForensicReport> {
    const res = await fetch("/api/v1/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    });
    return handleResponse<ForensicReport>(res);
  },

  async get(id: number): Promise<ForensicReport> {
    const res = await fetch(`/api/v1/reports/${id}`, {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<ForensicReport>(res);
  },

  async downloadPdf(id: number): Promise<void> {
    return downloadBlob(`/api/v1/reports/${id}/pdf`, `AICF-Case-Report-${id}.pdf`);
  },
};

export const dashboardApi = {
  async getStats(): Promise<DashboardStats> {
    const res = await fetch("/api/v1/dashboard/stats", {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<DashboardStats>(res);
  },
};

export interface EvidenceItem {
  signal: string;
  metric?: string;
  finding: string;
}

export type TextClassification =
  | "LIKELY AI-GENERATED"
  | "LIKELY HUMAN"
  | "INCONCLUSIVE";

export interface TextAnalysisRequest {
  text: string;
  save_to_cases?: boolean;
}

export interface SentenceAnalysisItem {
  sentence_idx: number;
  text: string;
  word_count: number;
  char_count: number;
  relative_cadence: string;
  punct_count: number;
  has_transitional_opening: boolean;
}

export interface ParagraphAnalysisItem {
  paragraph_idx: number;
  text_snippet: string;
  word_count: number;
  sentence_count: number;
  avg_sentence_len: number;
  type_token_ratio: number;
}

export interface PunctuationMetrics {
  comma_count: number;
  period_count: number;
  semicolon_count: number;
  colon_count: number;
  exclamation_count: number;
  question_count: number;
  hyphen_count: number;
  total_punctuation_count: number;
  punctuation_density: number;
}

export interface DetectorScore {
  model_name: string;
  model_version: string;
  status: string;
  status_detail?: string | null;
  ai_probability: number | null;
  human_probability: number | null;
  confidence_score: number | null;
  latency_ms: number;
  raw_output?: Record<string, unknown> | null;
}

export interface EnsembleBreakdown {
  ensemble_method: string;
  calibration_method: string;
  detectors: Record<string, DetectorScore>;
  active_detector_count: number;
  total_detector_count: number;
  agreement_score?: number | null;
  uncertainty_margin?: number | null;
  disagreement_analysis?: string | null;
  evidence_strength?: string | null;
  reasons_for_uncertainty?: string[];
}

export interface TextAnalysisResponse {
  analysis_id: number;
  user_id: number;
  input_hash: string;
  text_snippet: string;
  word_count: number;
  character_count: number;
  model_name: string;
  model_version: string;
  status: string;
  classification: TextClassification;
  confidence_score: number | null;
  ai_probability: number | null;
  human_probability: number | null;
  perplexity_score: number;
  burstiness_score: number;
  token_entropy: number;
  type_token_ratio: number;
  repeated_ngram_ratio: number;
  detector_scores?: Record<string, DetectorScore>;
  ensemble?: EnsembleBreakdown | null;
  sentence_analysis?: SentenceAnalysisItem[];
  paragraph_analysis?: ParagraphAnalysisItem[];
  punctuation_metrics?: PunctuationMetrics | null;
  sentence_length_distribution?: Record<string, number>;
  syntactic_repetition?: Record<string, unknown>;
  language_warning?: string | null;
  evidence: EvidenceItem[];
  limitations: string[];
  processing_time_ms: number;
  created_at: string;
  case_report_id?: number | null;
}

export const textApi = {
  async analyze(payload: TextAnalysisRequest): Promise<TextAnalysisResponse> {
    const res = await fetch("/api/v1/text/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    });
    return handleResponse<TextAnalysisResponse>(res);
  },

  async listAnalyses(): Promise<TextAnalysisResponse[]> {
    const res = await fetch("/api/v1/text/analyses", {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<TextAnalysisResponse[]>(res);
  },

  async getAnalysis(id: number): Promise<TextAnalysisResponse> {
    const res = await fetch(`/api/v1/text/analyses/${id}`, {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<TextAnalysisResponse>(res);
  },

  async downloadPdf(id: number): Promise<void> {
    return downloadBlob(`/api/v1/text/analyses/${id}/pdf`, `AICF-Text-Report-${id}.pdf`);
  },
};

export interface ImageEvidenceItem {
  signal: string;
  metric?: string;
  finding: string;
}

export interface ProvenanceInfo {
  has_exif: boolean;
  exif_summary: {
    camera_make?: string | null;
    camera_model?: string | null;
    lens_model?: string | null;
    software?: string | null;
    create_date?: string | null;
  };
  has_ai_metadata: boolean;
  ai_prompt_snippet?: string | null;
  has_c2pa: boolean;
  c2pa_finding: string;
  provenance_summary: string;
}

export type ImageClassification =
  | "LIKELY AI-GENERATED"
  | "LIKELY HUMAN"
  | "INCONCLUSIVE"
  | "Likely AI-generated"
  | "Likely Real"
  | "Inconclusive"
  | string;

export interface ImageDetectorScore {
  detector_id: string;
  model_name: string;
  status: string;
  raw_probability: number | null;
  calibrated_score: number | null;
  latency_ms: number;
  evidence: string[];
}

export interface ImageHeatmapData {
  method: string;
  ela_mean_error: number;
  ela_max_error: number;
  ela_discontinuity_score: number;
  heatmap_data_url: string | null;
  noise_residual_data_url: string | null;
  explanation: string;
}

export interface ImageEnsembleBreakdown {
  consensus_score: number;
  confidence: number;
  classification: string;
  temperature_applied: number;
  covariance_penalty: number;
  spectral_prior_weight: number;
  active_detectors_count: number;
  notes: string[];
}

export interface ImageAnalysisResponse {
  analysis_id: number;
  user_id: number;
  file_hash: string;
  file_name: string;
  file_size_bytes: number;
  image_width: number;
  image_height: number;
  image_format: string;
  model_name: string;
  model_version: string;
  status: string;
  classification: ImageClassification;
  confidence_score: number | null;
  ai_probability: number | null;
  human_probability: number | null;
  raw_score?: number | null;
  fft_high_freq_ratio: number;
  spectral_anisotropy: number;
  noise_variance: number;
  has_ai_metadata: boolean;
  has_c2pa: boolean;
  provenance?: ProvenanceInfo | null;
  evidence: ImageEvidenceItem[];
  limitations: string[];
  detector_scores?: ImageDetectorScore[];
  ensemble?: ImageEnsembleBreakdown | null;
  heatmap?: ImageHeatmapData | null;
  processing_time_ms: number;
  created_at: string;
  case_report_id?: number | null;
}

export interface ImageAnalysisHistoryItem {
  id: number;
  file_hash: string;
  file_name: string;
  file_size_bytes: number;
  image_width: number;
  image_height: number;
  image_format: string;
  model_name: string;
  model_version: string;
  classification: ImageClassification;
  confidence_score: number | null;
  status: string;
  processing_time_ms: number;
  created_at: string;
}

export const imageApi = {
  async analyze(file: File, saveToCases: boolean = false): Promise<ImageAnalysisResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("save_to_cases", String(saveToCases));

    const res = await fetch("/api/v1/image/analyze", {
      method: "POST",
      body: formData,
      credentials: "include",
    });
    return handleResponse<ImageAnalysisResponse>(res);
  },

  async listAnalyses(): Promise<ImageAnalysisHistoryItem[]> {
    const res = await fetch("/api/v1/image/history", {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<ImageAnalysisHistoryItem[]>(res);
  },

  async getAnalysis(id: number): Promise<ImageAnalysisResponse> {
    const res = await fetch(`/api/v1/image/${id}`, {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<ImageAnalysisResponse>(res);
  },

  async downloadPdf(id: number): Promise<void> {
    return downloadBlob(`/api/v1/image/${id}/pdf`, `AICF-Image-Report-${id}.pdf`);
  },
};

export interface FrameScoreItem {
  frame_index: number;
  timestamp_seconds: number;
  ai_probability: number;
  human_probability: number;
  classification: string;
}

export interface TemporalTelemetryInfo {
  mean_frame_difference: number;
  temporal_flicker_score: number;
  suspicious_transition_timestamps: number[];
  is_heuristic: boolean;
  heuristic_notes: string;
}

export interface HiveAnalysisInfo {
  is_configured: boolean;
  status: string;
  provider_name: string;
  model_version?: string | null;
  ai_generated_score?: number | null;
  deepfake_score?: number | null;
  classes_detected?: Array<Record<string, unknown>> | null;
  raw_response_summary?: string | null;
  error_message?: string | null;
}

export interface VideoEvidenceItem {
  signal: string;
  metric?: string | null;
  finding: string;
}

export type VideoClassification =
  | "HIGHLY_LIKELY_AI"
  | "SUSPECTED_AI"
  | "INCONCLUSIVE"
  | "LIKELY_AUTHENTIC"
  | "HIGHLY_LIKELY_AUTHENTIC"
  | string;

export interface FacialFrameRecordItem {
  frame_index: number;
  timestamp_seconds: number;
  face_count: number;
  face_detected: boolean;
  primary_bbox?: number[] | null;
  face_manipulation_score?: number | null;
  boundary_seam_delta?: number | null;
  is_low_res: boolean;
  verdict: string;
}

export interface SuspiciousSegmentItem {
  start_timestamp_seconds: number;
  end_timestamp_seconds: number;
  frame_count: number;
  peak_manipulation_score?: number | null;
  peak_boundary_seam_delta: number;
  description: string;
}

export interface FacialDeepfakeTelemetryInfo {
  model_name: string;
  model_version: string;
  model_license: string;
  availability: string;
  total_faces_analyzed: number;
  frames_with_faces: number;
  total_frames_sampled: number;
  mean_facial_manipulation_score?: number | null;
  max_facial_manipulation_score?: number | null;
  mean_boundary_seam_delta: number;
  max_boundary_seam_delta: number;
  peak_manipulation_timestamp?: number | null;
  low_resolution_frames_count: number;
  timeline: FacialFrameRecordItem[];
  suspicious_temporal_segments: SuspiciousSegmentItem[];
  error_message?: string | null;
}

export interface VideoConsensusBreakdownInfo {
  verdict: string;
  confidence_score: number;
  composite_manipulation_score: number;
  frame_screening_score: number;
  frame_classifier_status: string;
  facial_deepfake_score?: number | null;
  facial_detector_status: string;
  boundary_seam_delta: number;
  temporal_flicker_score: number;
}

export interface VideoAnalysisResponse {
  analysis_id: number;
  user_id: number;
  file_hash: string;
  file_name: string;
  file_size_bytes: number;
  duration_seconds: number;
  video_width: number;
  video_height: number;
  fps: number;
  total_frames: number;
  sampled_frame_count: number;
  model_name: string;
  model_version: string;
  frame_classifier_id: string;
  status: string;
  classification: VideoClassification;
  consensus_verdict?: string | null;
  confidence_score: number;
  ai_probability_mean: number;
  ai_probability_max: number;
  peak_frame_timestamp: number;
  temporal_flicker_score: number;
  face_deepfake_status: string;
  frame_scores: FrameScoreItem[];
  temporal_telemetry?: TemporalTelemetryInfo | null;
  facial_telemetry?: FacialDeepfakeTelemetryInfo | null;
  consensus?: VideoConsensusBreakdownInfo | null;
  hive_result?: HiveAnalysisInfo | null;
  evidence: VideoEvidenceItem[];
  limitations: string[];
  processing_time_ms: number;
  created_at: string;
  case_report_id?: number | null;
}

export interface VideoAnalysisHistoryItem {
  id: number;
  file_hash: string;
  file_name: string;
  file_size_bytes: number;
  duration_seconds: number;
  video_width: number;
  video_height: number;
  fps: number;
  total_frames: number;
  sampled_frame_count: number;
  model_name: string;
  model_version: string;
  classification: VideoClassification;
  consensus_verdict?: string | null;
  face_deepfake_status?: string | null;
  confidence_score: number;
  ai_probability_mean: number;
  ai_probability_max: number;
  peak_frame_timestamp: number;
  temporal_flicker_score: number;
  status: string;
  processing_time_ms: number;
  created_at: string;
}

export const videoApi = {
  async analyze(
    file: File,
    saveToCases: boolean = false,
    queryHive: boolean = false
  ): Promise<VideoAnalysisResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("save_to_cases", String(saveToCases));
    formData.append("query_hive", String(queryHive));

    const res = await fetch("/api/v1/video/analyze", {
      method: "POST",
      body: formData,
      credentials: "include",
    });
    return handleResponse<VideoAnalysisResponse>(res);
  },

  async getHistory(): Promise<VideoAnalysisHistoryItem[]> {
    const res = await fetch("/api/v1/video/history", {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<VideoAnalysisHistoryItem[]>(res);
  },

  async getAnalysis(id: number): Promise<VideoAnalysisResponse> {
    const res = await fetch(`/api/v1/video/analyses/${id}`, {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<VideoAnalysisResponse>(res);
  },

  async downloadPdf(id: number): Promise<void> {
    return downloadBlob(`/api/v1/video/analyses/${id}/pdf`, `AICF-Video-Report-${id}.pdf`);
  },
};

export type EvaluationStatus =
  | "EVALUATED"
  | "EVALUATION REQUIRED"
  | "MODEL UNAVAILABLE"
  | "INSUFFICIENT DATA"
  | "EVALUATION FAILED"
  | "CANCELLED";

export interface PerformanceMetrics {
  accuracy: number | null;
  accuracy_ci_95?: [number, number];
  precision: number | null;
  precision_ci_95?: [number, number];
  recall: number | null;
  recall_ci_95?: [number, number];
  f1_score: number | null;
  false_positive_rate: number | null;
  false_negative_rate: number | null;
  brier_score: number | null;
  expected_calibration_error: number | null;
}

export interface ConfusionMatrix {
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  matrix_2x2: number[][];
  labels: {
    rows: string[];
    columns: string[];
  };
}

export interface ModelSpecifications {
  model_name: string;
  version: string;
  architecture: string;
  source: string;
  license: string;
  intended_task: string;
  device?: string;
  limitations: string[];
}

export interface DatasetMetadata {
  dataset_name: string;
  license: string;
  permitted_use?: string;
  sample_count: number;
  class_definitions?: Record<string, string>;
  class_balance?: string;
  preprocessing?: string;
  known_limitations: string[];
}

export interface ModalityEvaluation {
  modality: "text" | "image" | "video" | "audio";
  evaluation_timestamp: string;
  elapsed_seconds?: number;
  model_specifications: ModelSpecifications;
  dataset_metadata: DatasetMetadata;
  evaluation_results: {
    status: EvaluationStatus;
    total_samples?: number;
    evaluated_samples?: number;
    inconclusive_samples?: number;
    error_samples?: number;
    class_counts?: {
      ground_truth_synthetic: number;
      ground_truth_authentic: number;
      predicted_synthetic: number;
      predicted_authentic: number;
    };
    confusion_matrix?: ConfusionMatrix;
    metrics?: PerformanceMetrics;
    message?: string;
  };
  sample_records?: Array<{
    sample_id: string;
    ground_truth: number;
    predicted_label?: number;
    classification?: string;
    ai_probability?: number;
    domain?: string;
    source?: string;
    file_path?: string;
    error?: string;
  }>;
}

export interface EvaluationSummary {
  timestamp: string;
  text: ModalityEvaluation;
  image: ModalityEvaluation;
  video: ModalityEvaluation;
  audio: ModalityEvaluation;
}

export const evaluationApi = {
  async getSummary(): Promise<EvaluationSummary> {
    const res = await fetch("/api/v1/evaluation/summary", {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<EvaluationSummary>(res);
  },

  async run(modality: "all" | "text" | "image" = "all"): Promise<unknown> {
    const res = await fetch(`/api/v1/evaluation/run?modality=${encodeURIComponent(modality)}`, {
      method: "POST",
      credentials: "include",
    });
    return handleResponse<unknown>(res);
  },

  async getModality(
    modality: "text" | "image" | "video" | "audio"
  ): Promise<ModalityEvaluation> {
    const res = await fetch(`/api/v1/evaluation/${encodeURIComponent(modality)}`, {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<ModalityEvaluation>(res);
  },
};

export interface CloudProviderStatus {
  provider: string;
  name: string;
  description: string;
  supported_types: string[];
  is_configured: boolean;
  source: string;
  masked_key: string | null;
  api_connection_status: string;
  last_tested_at: string | null;
  last_test_status: string | null;
  last_test_message: string | null;
  doc_url: string;
}

export interface CloudOperationResponse {
  success: boolean;
  message: string;
  provider?: string | null;
}

export interface CloudProviderResultItem {
  is_configured: boolean;
  status: string;
  ai_score: number | null;
  human_score: number | null;
  error_message?: string | null;
}

export interface CloudTextVerificationResponse {
  consent_granted: boolean;
  results: Record<string, CloudProviderResultItem>;
  error?: string | null;
}

export const cloudApi = {
  async getProviders(): Promise<CloudProviderStatus[]> {
    const res = await fetch("/api/v1/cloud/providers", {
      method: "GET",
      credentials: "include",
    });
    return handleResponse<CloudProviderStatus[]>(res);
  },

  async saveCredential(provider: string, apiKey: string): Promise<CloudOperationResponse> {
    const res = await fetch("/api/v1/cloud/credentials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ provider, api_key: apiKey }),
    });
    return handleResponse<CloudOperationResponse>(res);
  },

  async deleteCredential(provider: string): Promise<CloudOperationResponse> {
    const res = await fetch(`/api/v1/cloud/credentials/${encodeURIComponent(provider)}`, {
      method: "DELETE",
      credentials: "include",
    });
    return handleResponse<CloudOperationResponse>(res);
  },

  async testConnection(provider: string, apiKey?: string): Promise<CloudOperationResponse> {
    const res = await fetch("/api/v1/cloud/test-connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ provider, api_key: apiKey }),
    });
    return handleResponse<CloudOperationResponse>(res);
  },

  async verifyText(text: string, userConsent: boolean, providers?: string[]): Promise<CloudTextVerificationResponse> {
    const res = await fetch("/api/v1/cloud/verify-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        text,
        user_consent: userConsent,
        providers,
      }),
    });
    return handleResponse<CloudTextVerificationResponse>(res);
  },
};


