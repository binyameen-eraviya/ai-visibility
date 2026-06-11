import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../config/api";

export interface Platform {
  id: string;
  name: string;
  display_name: string;
  adapter_type: string;
  is_active: boolean;
}

export interface Country {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
}

export interface TrackingConfig {
  id: string;
  project_id: string;
  prompt_id: string;
  platform_id: string;
  country_id: string;
  frequency: string;
  is_active: boolean;
  created_at: string;
}

export interface TrackingConfigCreatePayload {
  prompt_id: string;
  platform_id: string;
  country_id: string;
  frequency?: string;
}

export function usePlatforms() {
  return useQuery<Platform[]>({
    queryKey: ["platforms"],
    queryFn: async () => {
      const { data } = await api.get("/api/platforms");
      return data;
    },
  });
}

export function useCountries() {
  return useQuery<Country[]>({
    queryKey: ["countries"],
    queryFn: async () => {
      const { data } = await api.get("/api/countries");
      return data;
    },
  });
}

export function useTrackingConfigs(projectId?: string) {
  return useQuery<TrackingConfig[]>({
    queryKey: ["projects", projectId, "tracking-configs"],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/tracking-configs`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useCreateTrackingConfig(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TrackingConfigCreatePayload) => {
      const { data } = await api.post(`/api/projects/${projectId}/tracking-configs`, payload);
      return data as TrackingConfig;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "tracking-configs"] });
    },
  });
}

export function useToggleTrackingConfig(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (configId: string) => {
      const { data } = await api.patch(`/api/projects/${projectId}/tracking-configs/${configId}/toggle`);
      return data as TrackingConfig;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "tracking-configs"] });
    },
  });
}
