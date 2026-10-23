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
  | "INCONCLUSIVE";

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
};

