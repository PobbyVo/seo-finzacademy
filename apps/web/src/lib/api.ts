export type Topic = {
  topic_code: string;
  topic_name: string;
  pillar: string;
  topic_type: string;
  pillar_axis: string;
  main_topics: string[];
  source_ref: string;
};

export type ContentCode = {
  topic_code: string;
  content_code: string;
  content_topic: string;
  original_title: string;
  source_ref: string;
};

export type SourceKeyword = {
  topic_code: string;
  content_code: string;
  keyword: string;
  role: string;
  funnel: string;
  volume: number | null;
  kd: number | null;
  intent: string | null;
  serp: string | null;
  source_ref: string;
};

export type Project = {
  id: string;
  name: string;
  status: "DRAFT";
  mode: "DEMO";
  topic: Topic | null;
  content_codes: ContentCode[];
  source_keywords: SourceKeyword[];
  business_goal: null;
  target_audience: null;
  created_at: string;
  updated_at: string;
  snapshot_id: string;
  version: number;
};

export type Health = {
  status: "ok";
  mode: "DEMO";
  database: "ok";
  api_version: "v1";
};

type ErrorPayload = {
  error: {
    code: string;
    message_vi: string;
    fields: string[];
    next_action_vi: string;
    request_id: string;
  };
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly nextAction: string,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    throw new ApiError(
      "Không kết nối được API local.",
      "Kiểm tra FastAPI đang chạy rồi thử kết nối lại.",
    );
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ErrorPayload | null;
    throw new ApiError(
      payload?.error?.message_vi ?? "API local chưa thể xử lý yêu cầu.",
      payload?.error?.next_action_vi ?? "Kiểm tra FastAPI và thử kết nối lại.",
      payload?.error?.request_id,
    );
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/health"),
  projects: () => request<{ projects: Project[] }>("/projects"),
  project: (id: string) => request<Project>(`/projects/${encodeURIComponent(id)}`),
  topics: () => request<{ topics: Topic[] }>("/demo/topics"),
  createProject: (name: string) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify({ name }) }),
  loadDemo: (id: string, topicCode: string) =>
    request<Project>(`/projects/${encodeURIComponent(id)}/demo`, {
      method: "POST",
      body: JSON.stringify({ topic_code: topicCode }),
    }),
};
