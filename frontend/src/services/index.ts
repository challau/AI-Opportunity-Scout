// All service implementations in one file for simplicity
import api from "@/lib/api";
import type {
  Event, EventListResponse, Notification, Resume,
  ResumeMatchResult, SearchResponse, TokenResponse,
  User, UserProfile, AdminStats, CrawlerLog,
} from "@/types";

// ─── Auth service ──────────────────────────────────────────────────────────────
export const authService = {
  register: async (d: { email: string; username: string; full_name: string; password: string }) =>
    (await api.post<TokenResponse>("/auth/register", d)).data,

  login: async (email: string, password: string) =>
    (await api.post<TokenResponse>("/auth/login", { email, password })).data,

  getMe: async (): Promise<User> => (await api.get("/auth/me")).data,

  getGoogleAuthUrl: () => `${process.env.NEXT_PUBLIC_API_URL}/api/auth/google`,
};

// ─── Events service ─────────────────────────────────────────────────────────────
export const eventsService = {
  listEvents: async (params?: object): Promise<EventListResponse> =>
    (await api.get("/events", { params })).data,

  getEvent: async (id: string): Promise<Event> => (await api.get(`/events/${id}`)).data,

  getTodayEvents: async (): Promise<Event[]> => (await api.get("/events/today")).data,

  getUpcomingDeadlines: async (days = 7): Promise<Event[]> =>
    (await api.get("/events/upcoming-deadlines", { params: { days } })).data,

  saveEvent: async (id: string): Promise<void> => { await api.post(`/events/${id}/save`); },

  unsaveEvent: async (id: string): Promise<void> => { await api.delete(`/events/${id}/save`); },

  getSavedEvents: async (page = 1): Promise<EventListResponse> =>
    (await api.get("/events/saved/me", { params: { page } })).data,
};

// ─── Users service ──────────────────────────────────────────────────────────────
export const usersService = {
  getProfile: async (): Promise<UserProfile> => (await api.get("/users/me/profile")).data,
  updateProfile: async (data: Partial<UserProfile>): Promise<UserProfile> =>
    (await api.patch("/users/me/profile", data)).data,
};

// ─── Search service ─────────────────────────────────────────────────────────────
export const searchService = {
  search: async (params: {
    query: string;
    search_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> => (await api.post("/search", params)).data,
};

// ─── Notifications service ─────────────────────────────────────────────────────
export const notificationsService = {
  getNotifications: async (params?: object): Promise<Notification[]> =>
    (await api.get("/notifications", { params })).data,

  getUnreadCount: async (): Promise<number> =>
    (await api.get("/notifications/unread-count")).data.count,

  markAsRead: async (id: string): Promise<void> => { await api.patch(`/notifications/${id}/read`); },

  markAllRead: async (): Promise<void> => { await api.patch("/notifications/read-all"); },
};

// ─── Resume service ─────────────────────────────────────────────────────────────
export const resumeService = {
  uploadResume: async (file: File): Promise<Resume> => {
    const fd = new FormData();
    fd.append("file", file);
    return (await api.post("/resume/upload", fd, { headers: { "Content-Type": "multipart/form-data" } })).data;
  },

  getMyResumes: async (): Promise<Resume[]> => (await api.get("/resume/my")).data,

  matchWithEvents: async (resumeId: string, topK = 10): Promise<ResumeMatchResult[]> =>
    (await api.post(`/resume/${resumeId}/match`, null, { params: { top_k: topK } })).data,
};

// ─── AI service ─────────────────────────────────────────────────────────────────
export const aiService = {
  chat: async (data: { message: string; conversation_history?: object[] }) =>
    (await api.post("/ai/chat", data)).data,

  getRecommendations: async (limit = 10): Promise<Event[]> =>
    (await api.get("/ai/recommendations", { params: { limit } })).data,

  triggerCrawl: async (platform = "all"): Promise<void> => {
    await api.post("/ai/trigger-crawl", null, { params: { platform } });
  },
};

// ─── Admin service ──────────────────────────────────────────────────────────────
export const adminService = {
  getStats: async (): Promise<AdminStats> => (await api.get("/admin/stats")).data,

  getCrawlerLogs: async (page = 1): Promise<CrawlerLog[]> =>
    (await api.get("/admin/crawler-logs", { params: { page } })).data,

  getEventsByPlatform: async (): Promise<Array<{ platform: string; count: number }>> =>
    (await api.get("/admin/analytics/events-by-platform")).data,

  getEventsByType: async (): Promise<Array<{ type: string; count: number }>> =>
    (await api.get("/admin/analytics/events-by-type")).data,

  listUsers: async (page = 1): Promise<User[]> =>
    (await api.get("/admin/users", { params: { page } })).data,
};

// Re-export token management
export { setTokens, clearTokens, getAccessToken } from "@/lib/api";
