/** API client — fetch wrapper with interceptors for all backend API modules. */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  params?: Record<string, string>;
  timeout?: number;
}

class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {}, params, timeout = 30000 } = options;

  // Build URL
  const url = new URL(`${BASE_URL}${endpoint}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.append(key, value);
    }
  }

  // Build fetch options
  const fetchOptions: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (body && method !== "GET") {
    fetchOptions.body = JSON.stringify(body);
  }

  // Timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  fetchOptions.signal = controller.signal;

  try {
    const response = await fetch(url.toString(), fetchOptions);
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => undefined);
      throw new ApiError(
        `API Error: ${response.status} ${response.statusText}`,
        response.status,
        errorData,
      );
    }

    return (await response.json()) as T;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("Request timeout", 408);
    }
    throw error;
  }
}

// -------- API Modules --------

export const conversationApi = {
  list: () => request("/conversations"),
  get: (id: string) => request(`/conversations/${id}`),
  create: (data: Record<string, unknown>) =>
    request("/conversations", { method: "POST", body: data }),
  update: (id: string, data: Record<string, unknown>) =>
    request(`/conversations/${id}`, { method: "PATCH", body: data }),
  delete: (id: string) => request(`/conversations/${id}`, { method: "DELETE" }),
  getMessages: (id: string, cursor?: string) => {
    const params = cursor ? { cursor } : undefined;
    return request(`/conversations/${id}/messages`, { params });
  },
  sendMessage: (id: string, content: string) =>
    request(`/conversations/${id}/messages`, { method: "POST", body: { content } }),
};

export const agentApi = {
  list: () => request("/agents"),
  get: (id: string) => request(`/agents/${id}`),
  create: (data: Record<string, unknown>) => request("/agents", { method: "POST", body: data }),
  update: (id: string, data: Record<string, unknown>) =>
    request(`/agents/${id}`, { method: "PATCH", body: data }),
  delete: (id: string) => request(`/agents/${id}`, { method: "DELETE" }),
  getVersions: (id: string) => request(`/agents/${id}/versions`),
  rollback: (id: string, version: number) =>
    request(`/agents/${id}/rollback`, { method: "POST", body: { version } }),
  getTemplates: () => request("/agents/templates"),
};

export const assetApi = {
  list: (params?: Record<string, string>) => request("/assets", { params }),
  get: (id: string) => request(`/assets/${id}`),
  upload: (formData: FormData) =>
    fetch(`${BASE_URL}/assets/upload`, { method: "POST", body: formData }),
  delete: (id: string) => request(`/assets/${id}`, { method: "DELETE" }),
  download: (id: string) => `${BASE_URL}/assets/${id}/download`,
};

export const monitorApi = {
  getHardware: () => request("/monitor/hardware"),
  getContainers: () => request("/monitor/containers"),
  getAgentActivities: () => request("/monitor/agents"),
  getHealth: () => request("/health"),
};

export const modelApi = {
  getModels: () => request("/models"),
  getProviders: () => request("/models/providers"),
  getStats: () => request("/models/stats"),
};

export { ApiError };
