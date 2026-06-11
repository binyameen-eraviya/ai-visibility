import { create } from "zustand";
import api, { TOKEN_STORAGE_KEY } from "../config/api";

const USER_STORAGE_KEY = "aiscope_user";

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  verified_at: string | null;
}

interface SignupData {
  user_name: string;
  email: string;
  password: string;
  organization_name: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (userData: SignupData) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: async (email, password) => {
    const { data } = await api.post("/api/login", { email, password });
    localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));
    set({ user: data.user, token: data.access_token, isAuthenticated: true });
  },

  signup: async (userData) => {
    await api.post("/api/signup", userData);
    const { data } = await api.post("/api/login", {
      email: userData.email,
      password: userData.password,
    });
    localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));
    set({ user: data.user, token: data.access_token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    set({ user: null, token: null, isAuthenticated: false });
    window.location.href = "/login";
  },

  loadFromStorage: () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
      let user: User | null = null;
      const stored = localStorage.getItem(USER_STORAGE_KEY);
      if (stored) {
        try {
          user = JSON.parse(stored) as User;
        } catch {
          user = null;
        }
      }
      set({ token, user, isAuthenticated: true });
    }
  },
}));
