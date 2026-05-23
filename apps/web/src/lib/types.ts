// Mirrors backend Pydantic schemas. Keep in sync.
export type RangeKey = "today" | "7d" | "30d" | "90d";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  timezone: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse extends TokenPair {
  user: User;
}

export interface SignupPayload {
  email: string;
  password: string;
  full_name?: string;
  timezone?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface DevicePublic {
  id: string;
  name: string;
  platform: string;
  hostname: string | null;
  agent_version: string | null;
  last_seen_at: string | null;
  created_at: string;
}

export interface ProductivityScore {
  score: number;
  focus_score: number;
  productive_seconds: number;
  distracting_seconds: number;
  neutral_seconds: number;
  total_tracked_seconds: number;
}

export interface AppShare {
  app_name: string;
  duration_seconds: number;
  share: number;
  category: "productive" | "neutral" | "distracting" | "unknown";
}

export interface HourBucket {
  hour: number;
  productive_seconds: number;
  distracting_seconds: number;
}

export interface DayBucket {
  day: string;
  productive_seconds: number;
  distracting_seconds: number;
  coding_seconds: number;
  score: number;
}

export interface CodingSummary {
  total_seconds: number;
  active_seconds: number;
  sessions: number;
  languages: { language: string; seconds: number }[];
  projects: { project: string; seconds: number }[];
}

export interface StreakInfo {
  current_streak_days: number;
  longest_streak_days: number;
  today_productive_seconds: number;
}

export interface DashboardSummary {
  productivity: ProductivityScore;
  coding: CodingSummary;
  top_apps: AppShare[];
  by_hour: HourBucket[];
  by_day: DayBucket[];
  streak: StreakInfo;
  period: { start: string; end: string };
}

export type InsightKind =
  | "daily_summary"
  | "weekly_summary"
  | "distraction_alert"
  | "burnout_warning"
  | "focus_tip"
  | "streak"
  | "recommendation";

export interface InsightPublic {
  id: string;
  kind: InsightKind;
  title: string;
  body: string;
  severity: string;
  score: number | null;
  metrics: Record<string, unknown> | null;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
}

export type ChatRole = "user" | "assistant" | "system" | "tool";

export interface ChatMessagePublic {
  id: string;
  role: ChatRole;
  content: string;
  created_at: string;
}

export interface ChatSessionPublic {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSessionPublic {
  messages: ChatMessagePublic[];
}

export interface ChatSendResponse {
  session: ChatSessionPublic;
  message: ChatMessagePublic;
}
