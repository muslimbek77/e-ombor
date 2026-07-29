import { DOC_TYPE_OPTIONS, STATUS_FILTERS } from "../documents/documentUtils";
import { PRIORITY_OPTIONS, STATUS_OPTIONS as TICKET_STATUS_OPTIONS } from "../tickets/ticketUtils";

export const DOCUMENT_TYPE_ORDER = DOC_TYPE_OPTIONS;
export const DOCUMENT_STATUS_ORDER = STATUS_FILTERS.filter((filter) => filter.value !== "all");
export const TICKET_PRIORITY_ORDER = PRIORITY_OPTIONS;
export const TICKET_STATUS_ORDER = TICKET_STATUS_OPTIONS;

export function formatCappedCount(count: number, cap: number) {
  return count >= cap ? `${cap}+` : String(count);
}
