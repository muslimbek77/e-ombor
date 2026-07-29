import { AtSign, MapPin, Phone, UserRound } from "lucide-react";
import { Link } from "react-router-dom";
import type { Supplier } from "../../types/supplier";

export function SupplierCard({ supplier }: { supplier: Supplier }) {
  return (
    <Link to={`/suppliers/${supplier.id}`} className="block rounded-2xl bg-white p-5 shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500">
      <div className="mb-4 flex items-start justify-between gap-3"><div className="min-w-0"><h2 className="truncate text-base font-bold text-gray-900">{supplier.name}</h2><p className="mt-1 text-xs font-medium text-gray-400">{supplier.code}</p></div><span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${supplier.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>{supplier.is_active ? "Faol" : "Nofaol"}</span></div>
      <div className="space-y-2.5 border-t border-gray-100 pt-3 text-sm text-gray-700"><Info icon={<UserRound size={14} />} value={supplier.contact_person} /><Info icon={<Phone size={14} />} value={supplier.phone} /><Info icon={<AtSign size={14} />} value={supplier.email} /><Info icon={<MapPin size={14} />} value={supplier.address} /></div>
    </Link>
  );
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
