import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../config/api";

export interface ScrapeRun {
  id: string;
  tracking_config_id: string;
  status: string;
  raw_storage_path: string | null;
  screenshot_path: string | null;
  error: string | null;
  account_id: string | null;
  duration_ms: number | null;
  scraped_at: string | null;
  created_at: string;
}

export interface ScrapeRunDetail extends ScrapeRun {
  raw: Record<string, any> | null;
}

export interface RunPromptPayload {
  platform_id: string;
  country_id?: string;
}

// Runs in these states are still being worked by Celery -> keep polling.
export const ACTIVE_STATUSES = new Set(["PENDING", "RUNNING", "RETRYING"]);
const POLL_MS = 5000;

export function useRuns(projectId?: string) {
  return useQuery<ScrapeRun[]>({
    queryKey: ["projects", projectId, "runs"],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/runs`);
      return data;
    },
    enabled: !!projectId,
    // Poll while any run is still in flight; stop once everything settled.
    refetchInterval: (query) => {
      const data = query.state.data as ScrapeRun[] | undefined;
      return data?.some((r) => ACTIVE_STATUSES.has(r.status)) ? POLL_MS : false;
    },
  });
}

export function useRunDetail(projectId?: string, runId?: string) {
  return useQuery<ScrapeRunDetail>({
    queryKey: ["projects", projectId, "runs", runId],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/runs/${runId}`);
      return data;
    },
    enabled: !!projectId && !!runId,
    refetchInterval: (query) => {
      const data = query.state.data as ScrapeRunDetail | undefined;
      return data && ACTIVE_STATUSES.has(data.status) ? POLL_MS : false;
    },
  });
}

export function useRunPrompt(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ promptId, payload }: { promptId: string; payload: RunPromptPayload }) => {
      const { data } = await api.post(
        `/api/projects/${projectId}/prompts/${promptId}/run`,
        payload
      );
      return data as ScrapeRun;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "runs"] });
    },
  });
}
