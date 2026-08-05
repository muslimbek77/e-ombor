import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createTicket, exportTickets, getTicket, getTickets, ticketQueryKey, ticketsQueryKey, updateTicket } from "../api/tickets";
import { downloadBlob } from "../lib/downloadFile";

export function useTickets() {
  return useQuery({
    queryKey: ticketsQueryKey,
    queryFn: getTickets,
    select: (response) => response.results,
  });
}

export function useTicket(ticketId: number) {
  return useQuery({
    queryKey: ticketQueryKey(ticketId),
    queryFn: () => getTicket(ticketId),
    enabled: Number.isInteger(ticketId) && ticketId > 0,
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTicket,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ticketsQueryKey }),
  });
}

export function useUpdateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTicket,
    onSuccess: (ticket) => {
      queryClient.setQueryData(ticketQueryKey(ticket.id), ticket);
      return queryClient.invalidateQueries({ queryKey: ticketsQueryKey });
    },
  });
}

export function useExportTickets() {
  return useMutation({
    mutationFn: exportTickets,
    onSuccess: (blob) => downloadBlob(blob, "murojaatlar.csv"),
  });
}
