import { Archive, ArrowLeft, Building2, Calendar, FileText, Hash, MapPin, Paperclip, Pencil, Upload, Wallet } from "lucide-react";
import { useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useDocument, useToggleArchive, useUpdateDocument, useWorkflowAction } from "../../hooks/useDocuments";
import { useDocumentFiles, useUploadDocumentFile } from "../../hooks/useDocuments";
import { DocumentForm } from "./DocumentForm";
import { actionLabel, docTypeLabel, formatFileSize, isDocumentEditable, statusBadgeClass } from "./documentUtils";
import { formatDateTime } from "../tickets/ticketUtils";
import { formatBudget, formatDate } from "../objects/siteUtils";
import { useIsControlRole } from "../../lib/permissions";
import type { DocumentUpdatePayload, WorkflowAction } from "../../types/document";

export default function DocumentDetailPage() {
  const { id } = useParams();
  const documentId = Number(id);
  const [isEditing, setIsEditing] = useState(false);
  const [rejectingAction, setRejectingAction] = useState<WorkflowAction | null>(null);
  const [comment, setComment] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: document, isPending, isError } = useDocument(documentId);
  const updateDocument = useUpdateDocument();
  const workflowAction = useWorkflowAction();
  const toggleArchive = useToggleArchive();
  const { data: files = [], isPending: isFilesPending } = useDocumentFiles(documentId);
  const uploadFile = useUploadDocumentFile();
  const isReadOnly = useIsControlRole();

  if (!Number.isInteger(documentId) || documentId < 1) return <DetailState>Hujjat ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !document) return <DetailState>Hujjatni yuklashda xatolik yuz berdi.</DetailState>;

  // Zanjirga kirgan hujjat muzlaydi (server: 409), nazorat roli esa umuman
  // yozmaydi (server: 403). Ikkalasida ham tugmani ko'rsatishning ma'nosi yo'q.
  const canEdit = !isReadOnly && isDocumentEditable(document.status);

  function runAction(action: WorkflowAction, actionComment?: string) {
    workflowAction.mutate(
      { documentId, payload: { action, comment: actionComment } },
      { onSuccess: () => { setRejectingAction(null); setComment(""); } },
    );
  }

  function handleActionClick(action: WorkflowAction) {
    if (action === "reject") {
      setRejectingAction(action);
      return;
    }
    runAction(action);
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    uploadFile.mutate({ documentId, file });
    event.target.value = "";
  }

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <Link to="/documents" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700">
          <ArrowLeft size={16} /> Hujjatlarga qaytish
        </Link>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{document.title}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(document.status)}`}>{document.status_display}</span>
                <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{docTypeLabel(document.doc_type)}</span>
                {document.is_archived && <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-500"><Archive size={11} /> Arxivlangan</span>}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {canEdit && (
                <button type="button" onClick={() => setIsEditing((value) => !value)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
                  <Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}
                </button>
              )}
              {document.can_archive && (
                <button
                  type="button"
                  disabled={toggleArchive.isPending}
                  onClick={() => toggleArchive.mutate({ documentId, archive: !document.is_archived })}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
                >
                  <Archive size={15} /> {document.is_archived ? "Arxivdan chiqarish" : "Arxivlash"}
                </button>
              )}
            </div>
          </div>

          {updateDocument.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">O'zgarishlarni saqlab bo'lmadi.</p>}
          {workflowAction.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Amalni bajarib bo'lmadi.</p>}

          {isEditing && canEdit ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">Hujjatni tahrirlash</h2>
              <DocumentForm
                initialDocument={document}
                submitLabel="Saqlash"
                isSubmitting={updateDocument.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) => updateDocument.mutate({ documentId, payload: payload as DocumentUpdatePayload }, { onSuccess: () => setIsEditing(false) })}
              />
            </>
          ) : (
            <DocumentInformation document={document} />
          )}

          {!canEdit && !isReadOnly && (
            <p className="mt-4 rounded-lg bg-gray-50 p-3 text-sm text-gray-500">
              Hujjat tasdiqlash zanjiriga kirgan va tahrirlanmaydi. Tuzatish kerak bo'lsa hujjat rad etiladi va qayta ochiladi.
            </p>
          )}

          {!isEditing && document.allowed_actions.length > 0 && (
            <div className="mt-6 border-t border-gray-100 pt-5">
              <p className="mb-3 text-xs font-semibold text-gray-400 uppercase tracking-widest">Amallar</p>
              <div className="flex flex-wrap items-center gap-2">
                {document.allowed_actions.map((action) => (
                  <button
                    key={action}
                    type="button"
                    disabled={workflowAction.isPending}
                    onClick={() => handleActionClick(action)}
                    className={`rounded-xl px-3 py-2 text-sm font-semibold disabled:opacity-60 ${action === "reject" ? "bg-red-50 text-red-700 hover:bg-red-100" : "bg-green-600 text-white hover:bg-green-700"}`}
                  >
                    {actionLabel(action)}
                  </button>
                ))}
              </div>
              {rejectingAction && (
                <div className="mt-3 space-y-2 rounded-xl border border-red-100 bg-red-50 p-3">
                  <label className="block text-xs font-semibold text-red-700">Rad etish sababi (majburiy)</label>
                  <textarea rows={2} value={comment} onChange={(event) => setComment(event.target.value)} className="w-full rounded-xl border border-red-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20" />
                  <div className="flex justify-end gap-2">
                    <button type="button" onClick={() => { setRejectingAction(null); setComment(""); }} className="rounded-xl px-3 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
                    <button type="button" disabled={!comment.trim() || workflowAction.isPending} onClick={() => runAction(rejectingAction, comment.trim())} className="rounded-xl bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">Rad etish</button>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {document.approvals.length > 0 && (
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-bold text-gray-900">Tasdiqlashlar tarixi</h2>
            <div className="space-y-3">
              {document.approvals.map((approval) => (
                <div key={approval.id} className="flex flex-wrap items-start justify-between gap-3 rounded-xl bg-gray-50 p-4">
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{actionLabel(approval.action as WorkflowAction)} — {approval.approver_name || "—"}</p>
                    {approval.comment && <p className="mt-1 text-xs text-gray-500">{approval.comment}</p>}
                  </div>
                  <p className="text-xs text-gray-400">{formatDateTime(approval.created_at)}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-lg font-bold text-gray-900">Fayllar</h2>
            {!isReadOnly && (
              <button type="button" onClick={() => fileInputRef.current?.click()} disabled={uploadFile.isPending} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60">
                <Upload size={15} /> {uploadFile.isPending ? "Yuklanmoqda..." : "Fayl yuklash"}
              </button>
            )}
            <input ref={fileInputRef} type="file" className="hidden" accept=".pdf,.xlsx,.xls,.jpg,.jpeg,.png" onChange={handleFileChange} />
          </div>
          {uploadFile.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Fayl yuklab bo'lmadi (PDF, XLSX, XLS, JPG, PNG, 10MB gacha).</p>}
          {isFilesPending && <p className="text-sm text-gray-400">Yuklanmoqda...</p>}
          {!isFilesPending && files.length === 0 && <p className="text-sm text-gray-400">Fayllar yo'q</p>}
          {!isFilesPending && files.length > 0 && (
            <div className="space-y-2">
              {files.map((file) => (
                <a key={file.id} href={file.file} target="_blank" rel="noreferrer" className="flex items-center justify-between gap-3 rounded-xl bg-gray-50 p-3 hover:bg-gray-100">
                  <div className="flex items-center gap-2.5 text-sm text-gray-700">
                    <Paperclip size={14} className="text-gray-400" />
                    <span className="font-medium">{file.original_filename}</span>
                    <span className="text-xs text-gray-400">{formatFileSize(file.file_size)}</span>
                  </div>
                  <span className="text-xs text-gray-400">{file.uploaded_by_name}</span>
                </a>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function DocumentInformation({ document }: { document: NonNullable<ReturnType<typeof useDocument>["data"]> }) {
  const details = [
    [<Hash size={17} />, "Hujjat raqami", document.doc_number],
    [<Building2 size={17} />, "Filial", document.branch_name || "—"],
    [<MapPin size={17} />, "Obyekt", document.site_name || "—"],
    [<FileText size={17} />, "Yaratuvchi", document.created_by_name || "—"],
    [<Wallet size={17} />, "Umumiy summa", formatBudget(document.total_amount)],
    [<Calendar size={17} />, "Yaratilgan sana", formatDate(document.created_at)],
  ] as const;

  return (
    <div className="space-y-4">
      <dl className="grid gap-4 sm:grid-cols-2">
        {details.map(([icon, label, value]) => (
          <div key={label} className="flex gap-3 rounded-xl bg-gray-50 p-4">
            <span className="mt-0.5 text-gray-400">{icon}</span>
            <div>
              <dt className="text-xs font-medium text-gray-500">{label}</dt>
              <dd className="mt-1 text-sm font-semibold text-gray-800">{value}</dd>
            </div>
          </div>
        ))}
      </dl>
      {document.description && (
        <div className="rounded-xl bg-gray-50 p-4">
          <p className="text-xs font-medium text-gray-500">Tavsif</p>
          <p className="mt-1 text-sm text-gray-800">{document.description}</p>
        </div>
      )}
      {document.notes && (
        <div className="rounded-xl bg-gray-50 p-4">
          <p className="text-xs font-medium text-gray-500">Izoh</p>
          <p className="mt-1 text-sm text-gray-800">{document.notes}</p>
        </div>
      )}
    </div>
  );
}

function DetailState({ children }: { children: React.ReactNode }) {
  return <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">{children}</main>;
}
