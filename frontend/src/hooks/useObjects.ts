import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSite,
  deleteSite,
  getSite,
  getSites,
  siteQueryKey,
  sitesQueryKey,
  updateSite,
} from "../api/sites";
import type { SitePayload } from "../types/site";

export function useSites() {
  return useQuery({
    queryKey: sitesQueryKey,
    queryFn: getSites,
    select: (response) => response.results,
  });
}

export function useSite(siteId: number) {
  return useQuery({
    queryKey: siteQueryKey(siteId),
    queryFn: () => getSite(siteId),
    enabled: Number.isInteger(siteId) && siteId > 0,
  });
}

export function useCreateSite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSite,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sitesQueryKey }),
  });
}

export function useUpdateSite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateSite,
    onSuccess: (site) => {
      queryClient.setQueryData(siteQueryKey(site.id), site);
      return queryClient.invalidateQueries({ queryKey: sitesQueryKey });
    },
  });
}

export function useDeleteSite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSite,
    onSuccess: (_, siteId) => {
      queryClient.removeQueries({ queryKey: siteQueryKey(siteId) });
      return queryClient.invalidateQueries({ queryKey: sitesQueryKey });
    },
  });
}

export type UpdateSiteVariables = {
  siteId: number;
  payload: SitePayload;
};
