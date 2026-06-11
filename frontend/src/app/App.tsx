import { BrowserRouter, Routes, Route, Navigate } from "react-router";
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
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

        {/* Default redirect */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
