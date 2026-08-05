import type { Address } from "../../types/address";

export function formatAddressLine(address: Pick<Address, "district" | "street" | "building">) {
  return [address.district, address.street, address.building].filter(Boolean).join(", ") || "—";
}
