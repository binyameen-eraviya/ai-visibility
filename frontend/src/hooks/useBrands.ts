import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../config/api";

export interface Brand {
  id: string;
  project_id: string;
  name: string;
  aliases: string[];
  is_primary: boolean;
  website_url?: string | null;
  favicon_url?: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface BrandCreatePayload {
  name: string;
  aliases?: string[];
  is_primary?: boolean;
  website_url?: string;
  favicon_url?: string;
}

export function useBrands(projectId?: string) {
  return useQuery<Brand[]>({
    queryKey: ["projects", projectId, "brands"],
    queryFn: async () => {
      const { data } = await api.get(`/api/projects/${projectId}/brands`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useCreateBrand(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: BrandCreatePayload) => {
      const { data } = await api.post(`/api/projects/${projectId}/brands`, payload);
      return data as Brand;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "brands"] });
    },
  });
}

export function useDeleteBrand(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (brandId: string) => {
      await api.delete(`/api/projects/${projectId}/brands/${brandId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "brands"] });
    },
  });
}
