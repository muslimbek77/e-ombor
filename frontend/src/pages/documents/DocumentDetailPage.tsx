import { Archive, ArrowLeft, Building2, Calendar, CheckCheck, Clock, FileText, Hash, History, MapPin, MessageSquare, Paperclip, Pencil, Send, Upload, Wallet } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useCreateDocumentComment, useDocument, useDocumentComments, useToggleArchive, useUpdateDocument, useWorkflowAction } from "../../hooks/useDocuments";
import { useDocumentFiles, useUploadDocumentFile } from "../../hooks/useDocuments";
import { useWarehouses } from "../../hooks/useWarehouses";
import { DocumentForm } from "./DocumentForm";
import { actionLabel, activityCardClass, activityDetailClass, activityIconClass, activityTitleClass, daysSince, docTypeLabel, formatFileSize, isDocumentEditable, isWaitingStatus, requiresComment, statusBadgeClass, waitingBadgeClass, waitingLabel } from "./documentUtils";
import { formatDateTime } from "../tickets/ticketUtils";
import { formatBudget, formatDate } from "../objects/siteUtils";
import { DOCUMENT_MANAGE_ROLES, useHasRole, useIsControlRole } from "../../lib/permissions";
import { useAuthStore } from "../../stores/authStore";
import { roleLabel } from "../users/usersUtils";
import type { DocStatus, DocumentUpdatePayload, WorkflowAction } from "../../types/document";

export default function DocumentDetailPage() {
  const { id } = useParams();
  const documentId = Number(id);
  const [isEditing, setIsEditing] = useState(false);
  // Izoh so'raydigan amal (`reject` yoki `return`) tasdiqlash panelini ochadi.
  const [pendingAction, setPendingAction] = useState<WorkflowAction | null>(null);
  const [comment, setComment] = useState("");
  // `send_back` da qaysi bosqichga qaytarilishi — ro'yxatni server beradi
  // (`send_back_targets`), bu yerda faqat tanlov saqlanadi.
  const [sendBackTarget, setSendBackTarget] = useState("");
  const [receiptWarehouse, setReceiptWarehouse] = useState("");
  const [newComment, setNewComment] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: document, isPending, isError } = useDocument(documentId);
  const updateDocument = useUpdateDocument();
  const workflowAction = useWorkflowAction();
  const toggleArchive = useToggleArchive();
  const { data: files = [], isPending: isFilesPending } = useDocumentFiles(documentId);
  const uploadFile = useUploadDocumentFile();
  const { data: comments = [], isPending: isCommentsPending } = useDocumentComments(documentId);
  const createComment = useCreateDocumentComment();
  const { data: warehouses = [] } = useWarehouses();
  const isReadOnly = useIsControlRole();
  const currentUser = useAuthStore((state) => state.user);
  const canManageDocuments = useHasRole(DOCUMENT_MANAGE_ROLES);

  // Uch bo'lakka bo'lingan tarixni (tasdiqlash / izoh / fayl) bitta ko'zdan
  // kechirish uchun xronologik lentaga birlashtiradi — pastdagi batafsil
  // bo'limlar shu manbalarning o'zidan, faqat qayta guruhlangan.
  const activity = useMemo(() => {
    const approvalEntries = (document?.approvals ?? []).map((approval) => ({
      key: `approval-${approval.id}`,
      time: approval.created_at,
      icon: <CheckCheck size={14} />,
      // Bosqichga qaytarishda nishonsiz yozuv tushunarsiz: "kim qaytardi" dan
      // ko'ra "qayerga qaytardi" muhimroq.
      title: `${actionLabel(approval.action as WorkflowAction)}${approval.target_status_display ? ` → ${approval.target_status_display}` : ""} — ${approval.approver_name || "—"}`,
      subtitle: approval.approver_roles?.length > 0 ? approval.approver_roles.map(roleLabel).join(", ") : undefined,
      detail: approval.comment,
      action: approval.action as WorkflowAction,
    }));
    const commentEntries = comments.map((comment) => ({
      key: `comment-${comment.id}`,
      time: comment.created_at,
      icon: <MessageSquare size={14} />,
      title: `Izoh — ${comment.author_name || "—"}`,
      subtitle: undefined as string | undefined,
      detail: comment.text,
      action: undefined as WorkflowAction | undefined,
    }));
    const fileEntries = files.map((file) => ({
      key: `file-${file.id}`,
      time: file.created_at,
      icon: <Paperclip size={14} />,
      title: `Fayl yuklandi — ${file.uploaded_by_name || "—"}`,
      subtitle: undefined as string | undefined,
      detail: file.original_filename,
      action: undefined as WorkflowAction | undefined,
    }));
    return [...approvalEntries, ...commentEntries, ...fileEntries].sort(
      (a, b) => new Date(b.time).getTime() - new Date(a.time).getTime(),
    );
  }, [document?.approvals, comments, files]);

  if (!Number.isInteger(documentId) || documentId < 1) return <DetailState>Hujjat ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !document) return <DetailState>Hujjatni yuklashda xatolik yuz berdi.</DetailState>;

  // Zanjirga kirgan hujjat muzlaydi (server: 409), nazorat roli esa umuman
  // yozmaydi (server: 403). Muallif yoki DOCUMENT_MANAGE_ROLES bo'lmasa ham
  // yo'q (server: 403) — server tekshiruvi bilan bir xil (`documents.py:
  // _ensure_can_manage`), aks holda bosilganda 403 beradigan tugma ko'rinardi.
  const canEdit =
    !isReadOnly &&
    isDocumentEditable(document.status) &&
    (document.created_by === currentUser?.id || canManageDocuments);
  // Qabulda xarid qatorlari omborga kirim bo'ladi va ombor taxmin qilinmaydi —
  // filialda bittasi bo'lsa ham omborchi o'zi ko'rsatadi (server: 400).
  // Qatorlari yo'q hujjatda ombor kerak emas, lekin buni bu yerdan bilib
  // bo'lmaydi: shuning uchun tanlov taklif qilinadi, o'tkazib yuborsa ham
  // bo'ladi.
  const branchWarehouses = warehouses.filter((warehouse) => warehouse.branch === document.branch);
  const isChoosingWarehouse = pendingAction === "advance";
  const isSendingBack = pendingAction === "send_back";
  // Uch xil qaytarish uch xil rangda: rad etish qizil, tuzatishga qaytarish
  // sariq, bosqichga qaytarish to'q sariq. Ular bir-biriga o'xshamasligi
  // kerak — oqibatlari ham har xil.
  const panelTone = pendingAction === "reject"
    ? { box: "border-red-100 bg-red-50", label: "text-red-700", note: "text-red-700", field: "border-red-200 focus:border-red-500 focus:ring-red-500/20", confirm: "bg-red-600 hover:bg-red-700" }
    : isSendingBack
      ? { box: "border-orange-100 bg-orange-50", label: "text-orange-800", note: "text-orange-700", field: "border-orange-200 focus:border-orange-500 focus:ring-orange-500/20", confirm: "bg-orange-600 hover:bg-orange-700" }
      : { box: "border-yellow-100 bg-yellow-50", label: "text-yellow-800", note: "text-yellow-700", field: "border-yellow-200 focus:border-yellow-500 focus:ring-yellow-500/20", confirm: "bg-yellow-600 hover:bg-yellow-700" };

  function resetActionPanel() {
    setPendingAction(null);
    setComment("");
    setSendBackTarget("");
    setReceiptWarehouse("");
  }

  function runAction(action: WorkflowAction, actionComment?: string, warehouse?: number, targetStatus?: DocStatus) {
    workflowAction.mutate(
      { documentId, payload: { action, comment: actionComment, warehouse, target_status: targetStatus } },
      { onSuccess: resetActionPanel },
    );
  }

  function handleActionClick(action: WorkflowAction) {
    // Izoh majburiy bo'lgan amallar va qabuldagi ombor tanlovi — ikkalasi ham
    // avval panel ochadi, so'ng yuboriladi.
    if (requiresComment(action) || action === "advance") {
      setPendingAction(action);
      return;
    }
    runAction(action);
  }

  function confirmPendingAction() {
    if (!pendingAction) return;
    if (pendingAction === "advance") {
      runAction(pendingAction, undefined, receiptWarehouse ? Number(receiptWarehouse) : undefined);
      return;
    }
    if (pendingAction === "send_back") {
      runAction(pendingAction, comment.trim(), undefined, sendBackTarget as DocStatus);
      return;
    }
    runAction(pendingAction, comment.trim());
  }

  function handleCommentSubmit(event: React.FormEvent) {
    event.preventDefault();
    const text = newComment.trim();
    if (!text) return;
    createComment.mutate({ documentId, text }, { onSuccess: () => setNewComment("") });
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
                {isWaitingStatus(document.status) && <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${waitingBadgeClass(daysSince(document.updated_at))}`}><Clock size={11} /> {waitingLabel(daysSince(document.updated_at))}</span>}
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
          {/* Server sababini aytadi ("ombor ko'rsatilishi shart" va h.k.) —
              uni yashirib "amal bajarilmadi" deyish foydalanuvchini nima
              qilish kerakligidan mahrum qiladi. */}
          {workflowAction.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">{workflowErrorMessage(workflowAction.error)}</p>}

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
              Hujjat tasdiqlash zanjiriga kirgan va tahrirlanmaydi. Tuzatish kerak bo'lsa bosqichdagi mas'ul uni tuzatishga qaytaradi — izoh esa istalgan holatda yoziladi.
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
                    className={`rounded-xl px-3 py-2 text-sm font-semibold disabled:opacity-60 ${action === "reject" ? "bg-red-50 text-red-700 hover:bg-red-100" : action === "return" ? "bg-yellow-50 text-yellow-800 hover:bg-yellow-100" : action === "send_back" ? "bg-orange-50 text-orange-800 hover:bg-orange-100" : "bg-green-600 text-white hover:bg-green-700"}`}
                  >
                    {actionLabel(action)}
                  </button>
                ))}
              </div>
              {pendingAction && requiresComment(pendingAction) && (
                <div className={`mt-3 space-y-2 rounded-xl border p-3 ${panelTone.box}`}>
                  {isSendingBack && (
                    <>
                      <label className={`block text-xs font-semibold ${panelTone.label}`}>Qaysi bosqich qayta ko'rib chiqsin</label>
                      {/* Ro'yxatni frontend o'zi tuzmaydi — serverdan keladi,
                          aks holda zanjir tartibi o'zgarganda eskirardi. */}
                      <select value={sendBackTarget} onChange={(event) => setSendBackTarget(event.target.value)} className={`w-full rounded-xl border bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 ${panelTone.field}`}>
                        <option value="">Bosqich tanlanmagan</option>
                        {document.send_back_targets.map((target) => (
                          <option key={target.value} value={target.value}>{target.label}</option>
                        ))}
                      </select>
                    </>
                  )}
                  <label className={`block text-xs font-semibold ${panelTone.label}`}>
                    {pendingAction === "reject" ? "Rad etish sababi (majburiy)" : isSendingBack ? "Nima qayta ko'rilishi kerak (majburiy)" : "Nima tuzatilishi kerak (majburiy)"}
                  </label>
                  {pendingAction === "return" && (
                    <p className={`text-xs ${panelTone.note}`}>
                      Diqqat: hujjat tuzatishga qaytariladi va qayta yuborilganda zanjir arxitekturadan boshdan boshlanadi — hozirgacha berilgan barcha tasdiqlar qayta so'raladi.
                    </p>
                  )}
                  {isSendingBack && (
                    <p className={`text-xs ${panelTone.note}`}>
                      Hujjat mazmuni o'zgarmaydi va muzlagan holicha qoladi — tanlangan bosqich faqat o'z qarorini qayta ko'radi. Undan keyin zanjir odatdagidek oldinga yuradi, ya'ni nazorat va buxgalteriya qaytadan o'tiladi. Mazmunning o'zi xato bo'lsa "Tuzatishga qaytarish" kerak.
                    </p>
                  )}
                  <textarea rows={2} value={comment} onChange={(event) => setComment(event.target.value)} className={`w-full rounded-xl border bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 ${panelTone.field}`} />
                  <div className="flex justify-end gap-2">
                    <button type="button" onClick={resetActionPanel} className="rounded-xl px-3 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
                    <button type="button" disabled={!comment.trim() || (isSendingBack && !sendBackTarget) || workflowAction.isPending} onClick={confirmPendingAction} className={`rounded-xl px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-60 ${panelTone.confirm}`}>
                      {actionLabel(pendingAction)}
                    </button>
                  </div>
                </div>
              )}
              {isChoosingWarehouse && (
                <div className="mt-3 space-y-2 rounded-xl border border-green-100 bg-green-50 p-3">
                  <label className="block text-xs font-semibold text-green-800">Qaysi omborga qabul qilindi</label>
                  <select value={receiptWarehouse} onChange={(event) => setReceiptWarehouse(event.target.value)} className="w-full rounded-xl border border-green-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20">
                    <option value="">Ombor tanlanmagan</option>
                    {branchWarehouses.map((warehouse) => (
                      <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>
                    ))}
                  </select>
                  <p className="text-xs text-green-700">Xarid qatorlari shu ombor qoldig'iga kirim qilinadi — xato ombor keyin faqat teskari harakat bilan tuzatiladi. Hujjatda material qatorlari bo'lmasa ombor kerak emas.</p>
                  <div className="flex justify-end gap-2">
                    <button type="button" onClick={resetActionPanel} className="rounded-xl px-3 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
                    <button type="button" disabled={workflowAction.isPending} onClick={confirmPendingAction} className="rounded-xl bg-green-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60">Qabul qilish</button>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {activity.length > 0 && (
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-gray-900"><History size={18} className="text-gray-400" /> Faoliyat tarixi</h2>
            <div className="space-y-3">
              {activity.map((entry) => (
                <div key={entry.key} className={`flex items-start gap-3 rounded-xl border p-4 ${activityCardClass(entry.action)}`}>
                  <span className={`mt-0.5 shrink-0 ${activityIconClass(entry.action)}`}>{entry.icon}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <p className={`text-sm font-semibold ${activityTitleClass(entry.action)}`}>{entry.title}</p>
                      <p className="shrink-0 text-xs text-gray-400">{formatDateTime(entry.time)}</p>
                    </div>
                    {entry.subtitle && <p className="mt-0.5 text-xs text-gray-400">{entry.subtitle}</p>}
                    {entry.detail && <p className={`mt-1.5 whitespace-pre-line ${activityDetailClass(entry.action)}`}>{entry.detail}</p>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-gray-900"><MessageSquare size={18} className="text-gray-400" /> Izohlar</h2>
          {isCommentsPending && <p className="text-sm text-gray-400">Yuklanmoqda...</p>}
          {!isCommentsPending && comments.length === 0 && <p className="text-sm text-gray-400">Hozircha izoh yo'q</p>}
          {comments.length > 0 && (
            <div className="space-y-3">
              {comments.map((item) => (
                <div key={item.id} className="rounded-xl bg-gray-50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-gray-800">{item.author_name || "—"}</p>
                    <p className="text-xs text-gray-400">{formatDateTime(item.created_at)}</p>
                  </div>
                  <p className="mt-1 whitespace-pre-line text-sm text-gray-700">{item.text}</p>
                </div>
              ))}
            </div>
          )}
          {/* Muzlatish izohga tegishli emas: aynan muzlagan hujjat haqida
              gaplashish kerak bo'ladi. Nazorat roli ham yoza oladi. */}
          <form onSubmit={handleCommentSubmit} className="mt-4 space-y-2">
            <textarea rows={2} value={newComment} onChange={(event) => setNewComment(event.target.value)} placeholder="Izoh yozing..." className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20" />
            {createComment.isError && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">Izohni saqlab bo'lmadi.</p>}
            <div className="flex justify-end">
              <button type="submit" disabled={!newComment.trim() || createComment.isPending} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60">
                <Send size={15} /> {createComment.isPending ? "Yuborilmoqda..." : "Izoh qoldirish"}
              </button>
            </div>
          </form>
        </section>

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

function workflowErrorMessage(error: unknown) {
  const serverError = (error as { response?: { data?: { error?: unknown } } })?.response?.data?.error;
  return typeof serverError === "string" && serverError ? serverError : "Amalni bajarib bo'lmadi.";
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
