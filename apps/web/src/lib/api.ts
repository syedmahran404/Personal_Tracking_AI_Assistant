/**
 * Type-safe API client.
 *
 * Centralizes auth header injection, JSON parsing, and 401-driven token
 * refresh. Used by every page; never call `fetch` directly.
 */
import { useAuthStore } from "@/stores/auth";
import type {
  AuthResponse,
  ChatSendResponse,
  ChatSessionDetail,
  ChatSessionPublic,
  DashboardSummary,
  DevicePublic,
  InsightPublic,
  LoginPayload,
  RangeKey,
  SignupPayload,
  TokenPair,
  User,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type FetchOptions = RequestInit & { auth?: boolean };

class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) {
    super(message);
  }
}

let refreshInFlight: Promise<TokenPair> | null = null;

async function refreshTokens(): Promise<TokenPair> {
  if (refreshInFlight) return refreshInFlight;
  const refresh_token = useAuthStore.getState().refreshToken;
  if (!refresh_token) throw new ApiError(401, "No refresh token");

  refreshInFlight = (async () => {
    const r = await fetch(`${API_URL}/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    });
    if (!r.ok) {
      useAuthStore.getState().clear();
      throw new ApiError(r.status, "Refresh failed");
    }
    const data = (await r.json()) as TokenPair;
    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
    return data;
  })().finally(() => {
    refreshInFlight = null;
  });

  return refreshInFlight;
}

async function request<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const { auth = true, ...init } = opts;
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }

  const doFetch = async (token?: string) => {
    if (auth && token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(`${API_URL}${path}`, { ...init, headers });
  };

  let token = auth ? useAuthStore.getState().accessToken ?? undefined : undefined;
  let res = await doFetch(token);

  if (auth && res.status === 401 && useAuthStore.getState().refreshToken) {
    try {
      const fresh = await refreshTokens();
      headers.delete("Authorization");
      token = fresh.access_token;
      res = await doFetch(token);
    } catch {
      // fall through to error
    }
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const body = text ? safeJson(text) : undefined;

  if (!res.ok) {
    const detail = (body as { detail?: string })?.detail ?? res.statusText;
    throw new ApiError(res.status, detail, body);
  }
  return body as T;
}

function safeJson(t: string) {
  try {
    return JSON.parse(t);
  } catch {
    return t;
  }
}

// ─── Public API ─────────────────────────────────────────────────────────
export const api = {
  // Auth
  signup: (payload: SignupPayload) =>
    request<AuthResponse>("/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: false,
    }),
  login: (payload: LoginPayload) =>
    request<AuthResponse>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
      auth: false,
    }),
  logout: () => request<void>("/v1/auth/logout", { method: "POST" }),

  // User
  me: () => request<User>("/v1/users/me"),
  updateMe: (data: Partial<Pick<User, "full_name" | "timezone" | "avatar_url">>) =>
    request<User>("/v1/users/me", { method: "PATCH", body: JSON.stringify(data) }),

  // Devices
  devices: () => request<DevicePublic[]>("/v1/devices"),

  // Analytics
  dashboard: (range: RangeKey = "7d") =>
    request<DashboardSummary>(`/v1/analytics/dashboard?range=${range}`),

  // Insights
  insights: () => request<InsightPublic[]>("/v1/insights"),
  generateWeekly: () =>
    request<InsightPublic>("/v1/insights/generate/weekly", { method: "POST" }),
  scanDistraction: () =>
    request<InsightPublic | null>("/v1/insights/scan/distraction", { method: "POST" }),

  // Chat
  chatSessions: () => request<ChatSessionPublic[]>("/v1/chat/sessions"),
  chatSession: (id: string) => request<ChatSessionDetail>(`/v1/chat/sessions/${id}`),
  sendChat: (body: { session_id?: string; message: string }) =>
    request<ChatSendResponse>("/v1/chat/send", { method: "POST", body: JSON.stringify(body) }),
  deleteChat: (id: string) =>
    request<void>(`/v1/chat/sessions/${id}`, { method: "DELETE" }),
};

export { ApiError };
