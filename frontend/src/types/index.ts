// Types for the entire application
export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  avatar_url?: string;
  is_active: boolean;
  is_admin: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface UserProfile {
  id: string;
  bio?: string;
  country?: string;
  college?: string;
  student_year?: number;
  interested_domains: string[];
  programming_languages: string[];
  preferred_platforms: string[];
  selected_sources: string[];
  email_notifications: boolean;
  telegram_notifications: boolean;
  notification_frequency: "instant" | "hourly" | "daily" | "weekly";
  telegram_chat_id?: string;
  last_notification_time?: string;
}

export interface Event {
  id: string;
  title: string;
  description?: string;
  short_summary?: string;
  platform: string;
  event_type: EventType;
  tags: string[];
  domains: string[];
  prize?: string;
  prize_amount?: number;
  location?: string;
  is_remote: boolean;
  is_free: boolean;
  eligibility?: string;
  organizer?: string;
  registration_deadline?: string;
  event_start_date?: string;
  event_end_date?: string;
  registration_url: string;
  image_url?: string;
  ai_score: number;
  participant_count: number;
  is_active: boolean;
  created_at: string;
  is_saved?: boolean;
}

export type EventType =
  | "hackathon"
  | "contest"
  | "internship"
  | "workshop"
  | "competition"
  | "quiz"
  | "open_source"
  | "hiring"
  | "conference";

export interface EventListResponse {
  items: Event[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Notification {
  id: string;
  title: string;
  body?: string;
  type: string;
  channel: string;
  is_read: boolean;
  event_id?: string;
  created_at: string;
}

export interface Resume {
  id: string;
  filename: string;
  file_size?: number;
  skills: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface ResumeMatchResult {
  event_id: string;
  event_title: string;
  match_percentage: number;
  matching_skills: string[];
  explanation: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  message: string;
  suggested_events: Event[];
  metadata: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  search_type: string;
  results: Event[];
  total: number;
  ai_explanation?: string;
}

export interface AdminStats {
  total_users: number;
  total_events: number;
  total_notifications: number;
  events_today: number;
  active_crawlers: number;
  last_crawl_at?: string;
}

export interface CrawlerLog {
  id: string;
  platform: string;
  status: "success" | "failed" | "partial" | "running";
  events_found: number;
  events_new: number;
  duration_seconds?: number;
  error_message?: string;
  started_at: string;
}

export type Platform =
  | "unstop" | "devfolio" | "hackerearth" | "hack2skill" | "devpost"
  | "kaggle" | "mlh" | "github" | "codeforces" | "codechef"
  | "atcoder" | "gsoc" | "gssoc" | "google" | "microsoft" | "ieee";

export interface SearchFilters {
  platform?: string[];
  event_type?: string[];
  is_remote?: boolean;
  is_free?: boolean;
  deadline_before?: string;
  deadline_after?: string;
}
