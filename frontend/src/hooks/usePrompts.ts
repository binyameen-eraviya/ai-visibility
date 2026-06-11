import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../config/api";

export interface Topic {
  id: string;
  project_id: string;
  name: string;
  created_at: string;
}

export interface Tag {
  id: string;
  project_id: string;
  name: string;
  created_at: string;
}

export interface Prompt {
  id: string;
  project_id: string;
  text: string;
  status: string;
  topic: Topic | null;
  tags: Tag[];
  created_at: string;
  updated_at: string | null;
}

export interface PromptCreatePayload {
  text: string;
  topic_id?: string;
  tag_ids?: string[];
}

export function usePrompts(projectId?: string) {
  return useQuery<Prompt[]>({
    queryKey: ["projects", projectId, "prompts"],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/prompts`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useCreatePrompt(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PromptCreatePayload) => {
      const { data } = await api.post(`/api/projects/${projectId}/prompts`, payload);
      return data as Prompt;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "prompts"] });
    },
  });
}

export function useDeletePrompt(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (promptId: string) => {
      await api.delete(`/api/projects/${projectId}/prompts/${promptId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "prompts"] });
    },
  });
}

export function useTopics(projectId?: string) {
  return useQuery<Topic[]>({
    queryKey: ["projects", projectId, "topics"],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/topics`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useTags(projectId?: string) {
  return useQuery<Tag[]>({
    queryKey: ["projects", projectId, "tags"],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/tags`);
      return data;
    },
    enabled: !!projectId,
  });
}
