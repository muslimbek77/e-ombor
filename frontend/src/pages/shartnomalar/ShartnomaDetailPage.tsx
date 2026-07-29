import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Building2,
  Calendar,
  Wallet,
  Hash,
  FileText,
  Info,
} from "lucide-react";
import { useContract } from "../../hooks/useContracts";
import { Field } from "./ShartnomaUtilis";
import { formatBudget, formatDate } from "../objects/siteUtils";

const ShartnomaDetailPage = () => {
  const { id } = useParams();

  const navigate = useNavigate();

  const { data: contract, isLoading: loading, error } = useContract(Number(id));

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto space-y-5">
        <button
          onClick={() => navigate("/shartnomalar")}
          className="flex items-center gap-1.5 text-sm font-semibold text-gray-500 hover:text-gray-800 transition-colors cursor-pointer"
        >
          <ArrowLeft size={15} />
          Orqaga
        </button>

        {/* ── Hero card ── */}
        <div
          className="rounded-2xl overflow-hidden"
          style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
        >
          <div
            className="h-28 relative"
            style={{
              background:
                "linear-gradient(135deg, #0f1c14 0%, #16a34a 60%, #22c55e 100%)",
            }}
          >
            <div
              className="absolute inset-0 opacity-15"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(0deg,transparent,transparent 24px,rgba(255,255,255,0.3) 24px,rgba(255,255,255,0.3) 25px),repeating-linear-gradient(90deg,transparent,transparent 24px,rgba(255,255,255,0.3) 24px,rgba(255,255,255,0.3) 25px)",
              }}
            />
          </div>

          <div className="bg-white px-6 pb-5 py-5 relative">
            <div className="flex items-end gap-4 -mt-8 mb-1">
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center text-white flex-shrink-0 border-4 border-white"
                style={{
                  background:
                    "linear-gradient(135deg, #16a34a 0%, #0f1c14 100%)",
                  boxShadow: "0 2px 12px rgba(22,163,74,0.3)",
                }}
              >
                <FileText size={28} />
              </div>
              <div className="pb-1 min-w-0">
                <h2 className="text-gray-900 text-xl font-bold leading-tight truncate">
                  {contract?.supplier_name}
                </h2>
                <p className="text-gray-400 text-xs font-medium mt-1">
                  {contract?.contract_number}
                </p>
              </div>
            </div>

            {contract?.description && (
              <div className="flex items-start gap-2 mt-4 pt-4 border-t border-gray-100">
                <Info
                  size={14}
                  className="text-gray-400 flex-shrink-0 mt-0.5"
                />
                <p className="text-sm text-gray-600">{contract?.description}</p>
              </div>
            )}
          </div>
        </div>

        {/* ── Info cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div
            className="bg-white rounded-2xl px-5 py-4"
            style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
          >
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
              Hujjat
            </p>
            <Field
              icon={<Hash size={15} />}
              label="Shartnoma raqami"
              value={contract?.contract_number}
            />
            <Field
              icon={<FileText size={15} />}
              label="Hujjat raqami"
              value={contract?.document_doc_number}
            />
            <Field
              icon={<Building2 size={15} />}
              label="Yetkazib beruvchi"
              value={contract?.supplier_name}
            />
          </div>

          <div
            className="bg-white rounded-2xl px-5 py-4"
            style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
          >
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
              Muddat va summa
            </p>
            <Field
              icon={<Calendar size={15} />}
              label="Imzolangan sana"
              value={formatDate(contract?.signed_date)}
            />
            <Field
              icon={<Calendar size={15} />}
              label="Amal qilish muddati"
              value={`${formatDate(contract?.start_date)} — ${formatDate(contract?.end_date)}`}
            />
            <Field
              icon={<Wallet size={15} />}
              label="Umumiy summa"
              value={formatBudget(contract?.total_amount)}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShartnomaDetailPage;
