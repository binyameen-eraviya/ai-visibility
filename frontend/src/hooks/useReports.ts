import { useQuery } from "@tanstack/react-query";
import api from "../config/api";

export interface DailyMetric {
  id: string;
  project_id: string;
  brand_id: string;
  platform_id: string;
  country_id: string;
  date: string;
  visibility_pct: number;
  avg_position: number | null;
  avg_sentiment: number | null;
  share_of_voice: number;
  total_runs: number;
  mention_count: number;
}

export interface SourceMetric {
  id: string;
  project_id: string;
  domain: string;
  source_type: string;
  date: string;
  citation_count: number;
}

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0];
}

export function useDailyMetrics(projectId?: string, days = 30) {
  const end = formatDate(new Date());
  const start = formatDate(new Date(Date.now() - days * 24 * 60 * 60 * 1000));
  return useQuery<DailyMetric[]>({
    queryKey: ["projects", projectId, "reports", "daily-metrics", start, end],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/reports/daily-metrics`, {
        params: { start_date: start, end_date: end },
      });
      return data;
    },
    enabled: !!projectId,
  });
}

export function useSourceMetrics(projectId?: string, days = 30) {
  const end = formatDate(new Date());
  const start = formatDate(new Date(Date.now() - days * 24 * 60 * 60 * 1000));
  return useQuery<SourceMetric[]>({
    queryKey: ["projects", projectId, "reports", "source-metrics", start, end],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/reports/source-metrics`, {
        params: { start_date: start, end_date: end },
      });
      return data;
    },
    enabled: !!projectId,
  });
}
