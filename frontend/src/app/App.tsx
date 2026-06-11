import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { AppShell } from "./components/layout/AppShell";
import { LoginPage } from "./components/pages/LoginPage";
import { SignupPage } from "./components/pages/SignupPage";
import { OnboardingPage } from "./components/pages/OnboardingPage";
import { DashboardPage } from "./components/pages/DashboardPage";
import { PromptsPage } from "./components/pages/PromptsPage";
import { SourcesPage } from "./components/pages/SourcesPage";
import { CompetitorsPage } from "./components/pages/CompetitorsPage";
import { RunHistoryPage } from "./components/pages/RunHistoryPage";
import {
  ProjectSettingsPage,
  BrandsPage,
  TrackingPage,
  AccountSettingsPage,
  OrgSettingsPage,
} from "./components/pages/SettingsPages";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { Toaster } from "./components/ui/sonner";
import { useAuthStore } from "../store/authStore";

const queryClient = new QueryClient();

export default function App() {
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" />
      <BrowserRouter>
        <Routes>
          {/* Auth routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/onboarding" element={<OnboardingPage />} />

            {/* App routes — all wrapped in AppShell */}
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/prompts" element={<PromptsPage />} />
              <Route path="/sources" element={<SourcesPage />} />
              <Route path="/competitors" element={<CompetitorsPage />} />
              <Route path="/runs" element={<RunHistoryPage />} />
              <Route path="/settings/project" element={<ProjectSettingsPage />} />
              <Route path="/settings/brands" element={<BrandsPage />} />
              <Route path="/settings/tracking" element={<TrackingPage />} />
              <Route path="/settings/account" element={<AccountSettingsPage />} />
              <Route path="/settings/organization" element={<OrgSettingsPage />} />
            </Route>
          </Route>

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
