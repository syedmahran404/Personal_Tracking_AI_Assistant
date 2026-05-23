/**
 * Thin API client for the agent.
 *
 * Talks to the same backend the web app uses. On 401 we attempt one
 * refresh and replay the request; failure means the user must re-auth.
 */
import axios, { AxiosError, AxiosInstance } from "axios";
import { config } from "./config";
import { logger } from "./logger";

interface AppUsageEventPayload {
  app_name: string;
  window_title: string | null;
  bundle_id: string | null;
  started_at: string;
  ended_at: string;
  is_idle: boolean;
}

interface DeviceRegisterResponse {
  id: string;
  name: string;
  platform: string;
}

class AgentApi {
  private http: AxiosInstance;
  private refreshing: Promise<boolean> | null = null;

  constructor() {
    this.http = axios.create({
      baseURL: config.get("apiUrl"),
      timeout: 15_000,
    });

    this.http.interceptors.request.use((req) => {
      const token = config.get("accessToken");
      if (token) {
        req.headers.Authorization = `Bearer ${token}`;
      }
      return req;
    });
  }

  private async refresh(): Promise<boolean> {
    if (this.refreshing) return this.refreshing;
    const refresh_token = config.get("refreshToken");
    if (!refresh_token) return false;

    this.refreshing = (async () => {
      try {
        const r = await axios.post(
          `${config.get("apiUrl")}/v1/auth/refresh`,
          { refresh_token },
        );
        config.set("accessToken", r.data.access_token);
        config.set("refreshToken", r.data.refresh_token);
        return true;
      } catch (err) {
        logger.warn("api.refresh.failed", err);
        return false;
      } finally {
        this.refreshing = null;
      }
    })();
    return this.refreshing;
  }

  private async retryOn401<T>(fn: () => Promise<T>): Promise<T> {
    try {
      return await fn();
    } catch (err) {
      const e = err as AxiosError;
      if (e.response?.status === 401 && (await this.refresh())) {
        return fn();
      }
      throw err;
    }
  }

  async login(email: string, password: string): Promise<{ user: { id: string; email: string } }> {
    const r = await axios.post(`${config.get("apiUrl")}/v1/auth/login`, { email, password });
    config.set("accessToken", r.data.access_token);
    config.set("refreshToken", r.data.refresh_token);
    return { user: r.data.user };
  }

  async registerDevice(payload: {
    name: string;
    platform: string;
    hostname?: string;
    agent_version?: string;
  }): Promise<DeviceRegisterResponse> {
    return this.retryOn401(async () => {
      const r = await this.http.post<DeviceRegisterResponse>("/v1/devices", payload);
      return r.data;
    });
  }

  async ingestEvents(events: AppUsageEventPayload[], deviceId: string | null): Promise<{ accepted: number }> {
    return this.retryOn401(async () => {
      const r = await this.http.post("/v1/tracking/events", {
        device_id: deviceId,
        events,
      });
      return r.data;
    });
  }
}

export const api = new AgentApi();
