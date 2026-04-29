import type {
  ApiErrorPayload,
  EvaluationResponse,
  FineTuneRequest,
  FineTuneResponse,
  GenerateTemplateRequest,
  GenerateTemplateResponse,
  HealthResponse,
  PipelineRequest,
  PipelineResponse,
  TemplatesResponse,
  UploadResponse,
} from "../types/api";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

export class ApiClientError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...options.headers,
      },
    });
  } catch (error) {
    throw new ApiClientError(
      `Unable to reach the backend at ${API_BASE_URL}. Start it with: uvicorn backend.main:app --reload`,
    );
  }

  if (!response.ok) {
    throw new ApiClientError(await extractErrorMessage(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((item) => item.msg ?? JSON.stringify(item)).join("; ");
    }
    return payload.detail ?? `Request failed with HTTP ${response.status}`;
  } catch {
    return (await response.text()) || `Request failed with HTTP ${response.status}`;
  }
}

function cleanPayload<T extends Record<string, unknown>>(payload: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  ) as Partial<T>;
}

export const apiClient = {
  baseUrl: API_BASE_URL,

  health() {
    return request<HealthResponse>("/health");
  },

  uploadCsv(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return request<UploadResponse>("/api/upload", {
      method: "POST",
      body: formData,
    });
  },

  runPipeline(payload: PipelineRequest) {
    return request<PipelineResponse>("/api/run-pipeline", {
      method: "POST",
      body: JSON.stringify(cleanPayload(payload as unknown as Record<string, unknown>)),
    });
  },

  fineTune(payload: FineTuneRequest) {
    return request<FineTuneResponse>("/api/fine-tune", {
      method: "POST",
      body: JSON.stringify(cleanPayload(payload as unknown as Record<string, unknown>)),
    });
  },

  templates() {
    return request<TemplatesResponse>("/api/templates");
  },

  evaluation() {
    return request<EvaluationResponse>("/api/evaluation");
  },

  generateTemplate(payload: GenerateTemplateRequest) {
    return request<GenerateTemplateResponse>("/api/generate-template", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async downloadOutput(format: "csv" | "json" | "markdown") {
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}/api/outputs/${format}`);
    } catch {
      throw new ApiClientError(`Unable to download ${format}. Backend is not reachable.`);
    }

    if (!response.ok) {
      throw new ApiClientError(await extractErrorMessage(response), response.status);
    }

    return response.blob();
  },
};
