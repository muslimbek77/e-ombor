import { MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import type { Address } from "../../types/address";
import { formatAddressLine } from "./addressUtils";

export function AddressCard({ address }: { address: Address }) {
  return (
    <Link to={`/addresses/${address.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500">
      <div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" />
      <div className="p-5">
        <div className="mb-3 flex items-start gap-3">
          <span className="mt-0.5 shrink-0 rounded-lg bg-green-50 p-2 text-green-700"><MapPin size={16} /></span>
          <div className="min-w-0">
            <h2 className="truncate text-base font-bold text-gray-900">{address.city}</h2>
            <p className="mt-1 text-sm text-gray-500">{formatAddressLine(address)}</p>
          </div>
        </div>
      </div>
    </Link>
  );
}
