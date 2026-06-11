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

export function useRuns(projectId?: string) {
  return useQuery<ScrapeRun[]>({
    queryKey: ["projects", projectId, "runs"],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/runs`);
      return data;
    },
    enabled: !!projectId,
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
