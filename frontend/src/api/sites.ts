import api from "../lib/axios";
import type { Site, SitePayload, SitesResponse } from "../types/site";

export const sitesQueryKey = ["sites"] as const;
export const siteQueryKey = (siteId: number) => [...sitesQueryKey, siteId] as const;

export async function getSites(): Promise<SitesResponse> {
  const { data } = await api.get<SitesResponse>("/sites/");
  return data;
}

export async function getSite(siteId: number): Promise<Site> {
  const { data } = await api.get<Site>(`/sites/${siteId}/`);
  return data;
}

export async function createSite(payload: SitePayload): Promise<Site> {
  const { data } = await api.post<Site>("/sites/", payload);
  return data;
}

export async function updateSite({ siteId, payload }: { siteId: number; payload: SitePayload }): Promise<Site> {
  const { data } = await api.put<Site>(`/sites/${siteId}/`, payload);
  return data;
}

export async function deleteSite(siteId: number): Promise<void> {
  await api.delete(`/sites/${siteId}/`);
}
