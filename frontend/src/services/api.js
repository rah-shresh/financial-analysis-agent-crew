import axios from "axios";
import { useAuthStore } from "../store/authStore";
 
export const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
 
export const api = axios.create({ baseURL: API_BASE, timeout: 30000 });
 
// One place that attaches the login token to every request.
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
 
// A 401 on any normal call means the token expired / was revoked: log out, and
// ProtectedRoute (which watches the store) sends the user to the login page.
// A 401 from login/register itself just means "wrong credentials" -- leave it alone.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const url = err.config?.url || "";
    const isAuthCall = url.includes("/api/auth/login") || url.includes("/api/auth/register");
    if (err.response?.status === 401 && !isAuthCall && useAuthStore.getState().token) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(err);
  }
);
 
export const register = (body) => api.post("/api/auth/register", body).then((r) => r.data);
export const login = (body) => api.post("/api/auth/login", body).then((r) => r.data);
export const startRun = (ticker) => api.post("/api/analysis/run", { ticker }).then((r) => r.data);
export const getRun = (id) => api.get(`/api/analysis/${id}`).then((r) => r.data);
export const listReports = ({ limit = 20, skip = 0 } = {}) =>
  api.get("/api/reports", { params: { limit, skip } }).then((r) => r.data);
export const getReport = (id) => api.get(`/api/reports/${id}`).then((r) => r.data);
 












