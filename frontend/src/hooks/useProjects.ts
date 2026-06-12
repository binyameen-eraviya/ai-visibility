import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../config/api";

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  website_url: string | null;
  description?: string | null;
  industry?: string | null;
  brand_identity?: string[] | null;
  products_services?: string[] | null;
  detected_location?: string | null;
  detected_language?: string | null;
  detected_timezone?: string | null;
  favicon_url?: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ProjectCreatePayload {
  name: string;
  website_url?: string;
  description?: string;
  industry?: string;
  brand_identity?: string[];
  products_services?: string[];
  detected_location?: string;
  detected_language?: string;
  detected_timezone?: string;
  favicon_url?: string;
}

export interface ProjectUpdatePayload extends Partial<ProjectCreatePayload> {}

export function useProjects() {
  return useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: async () => {
      const { data } = await api.get("/api/projects");
      return data;
    },
  });
}

export function useProject(id?: string) {
  return useQuery<Project>({
    queryKey: ["projects", id],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ProjectCreatePayload) => {
      const { data } = await api.post("/api/projects", payload);
      return data as Project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateProject(id?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ProjectUpdatePayload) => {
      const { data } = await api.put(`/api/projects/${id}`, payload);
      return data as Project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["projects", id] });
    },
  });
}
