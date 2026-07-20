// API service layer — centralizes all HTTP calls to FastAPI backend
import axios, { AxiosInstance, AxiosError } from "axios";
import { TokenResponse } from "@/types";

// Same-origin by default: API calls go to this domain and Next.js rewrites
// proxy them to the backend. Set NEXT_PUBLIC_API_URL only for local dev.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// ─── Token management ─────────────────────────────────────────────────────────
const getAccessToken = () =>
  typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
const getRefreshToken = () =>
  typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
const setTokens = (tokens: TokenResponse) => {
  localStorage.setItem("access_token", tokens.access_token);
  localStorage.setItem("refresh_token", tokens.refresh_token);
};
const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// ─── Request interceptor — attach JWT ─────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─── Response interceptor — refresh on 401 ────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          const resp = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          setTokens(resp.data);
          originalRequest.headers.Authorization = `Bearer ${resp.data.access_token}`;
          return api(originalRequest);
        } catch {
          clearTokens();
          window.location.href = "/login";
        }
      } else {
        clearTokens();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export { api, setTokens, clearTokens, getAccessToken };
export default api;
