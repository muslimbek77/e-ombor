import api from "../lib/axios";
import type { Ticket, TicketCreatePayload, TicketUpdatePayload, TicketsResponse } from "../types/ticket";

export const ticketsQueryKey = ["tickets"] as const;
export const ticketQueryKey = (ticketId: number) => [...ticketsQueryKey, ticketId] as const;

export async function getTickets(): Promise<TicketsResponse> {
  const { data } = await api.get<TicketsResponse>("/tickets/");
  return data;
}

export async function getTicket(ticketId: number): Promise<Ticket> {
  const { data } = await api.get<Ticket>(`/tickets/${ticketId}/`);
  return data;
}

export async function createTicket(payload: TicketCreatePayload): Promise<Ticket> {
  const { data } = await api.post<Ticket>("/tickets/", payload);
  return data;
}

export async function updateTicket({ ticketId, payload }: { ticketId: number; payload: TicketUpdatePayload }): Promise<Ticket> {
  const { data } = await api.put<Ticket>(`/tickets/${ticketId}/`, payload);
  return data;
}

export interface TicketFilters {
  status?: string;
  priority?: string;
  category?: string;
}

export async function exportTickets(filters?: TicketFilters): Promise<Blob> {
  const { data } = await api.get<Blob>("/tickets/export/", { params: filters, responseType: "blob" });
  return data;
}
