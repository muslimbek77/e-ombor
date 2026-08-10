"""Hujjatlar: ro'yxat, zanjir amallari, arxiv, izohlar, fayllar, eksport."""


from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import exceptions, generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..audit import create_audit_log
from ..exports import export_to_csv
from ..freeze import ensure_document_editable
from ..models import (
    Document,
    DocumentApproval,
    DocumentComment,
    DocumentFile,
    User,
)
from ..notifications import notify_branch_roles, notify_users
from ..numbering import build_document_number, save_with_unique_number
from ..roles import ARCHIVE_ROLES, DOCUMENT_MANAGE_ROLES, has_any_role, is_admin
from ..scope import branch_scope, filter_by_query_params
from ..serializers import (
    DocumentCommentSerializer,
    DocumentFileSerializer,
    DocumentSerializer,
    DocumentWorkflowSerializer,
)
from ..stock import ReceiptError, receive_purchase_items
from ..workflow import COMMENT_REQUIRED_ACTIONS, WORKFLOW_RULES


# --- Document Views ---
class DocumentListCreateView(generics.ListCreateAPIView):
    """Hujjatlar ro'yxati va yaratish."""
    serializer_class = DocumentSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = branch_scope(
            Document.objects.select_related("created_by", "site", "branch").prefetch_related("approvals"),
            user,
        ).order_by("-created_at")
        archived_filter = self.request.query_params.get("archived", "false")
        if archived_filter == "true":
            queryset = queryset.filter(is_archived=True)
        elif archived_filter != "all":
            queryset = queryset.filter(is_archived=False)
        queryset = filter_by_query_params(
            queryset,
            self.request,
            {"status": "status", "doc_type": "doc_type", "site": "site_id"},
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(doc_number__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        site = serializer.validated_data.get("site")
        branch = site.branch if site else self.request.user.branch
        if site and not is_admin(self.request.user) and self.request.user.branch_id and site.branch_id != self.request.user.branch_id:
            raise serializers.ValidationError("Siz faqat o'z filiali obyektiga hujjat yarata olasiz")
        document = save_with_unique_number(
            lambda: serializer.save(
                created_by=self.request.user,
                branch=branch,
                doc_number=build_document_number(serializer.validated_data["doc_type"]),
            )
        )
        create_audit_log(
            self.request,
            "document_created",
            "Document",
            document.id,
            {"doc_number": document.doc_number, "status": document.status},
        )
        notify_branch_roles(
            branch,
            # Xaridlar bo'limi so'rovni boshidanoq kuzatadi — arxitektura
            # javobini kutmasdan filial rahbariga tuzatish aytishi uchun.
            {"architecture", "procurement", "branch_manager", "admin"},
            "Yangi hujjat yaratildi",
            f"{document.doc_number} raqamli hujjat yaratildi va ko'rib chiqishni kutmoqda.",
            "info",
            related_type="document",
            related_id=document.id,
        )


class DocumentWorkflowActionView(APIView):
    """Hujjat workflow amallari."""

    # Nazorat rolining yozish taqiqidan yagona ish-mazmunli istisno: o'z
    # bosqichida qaror qabul qilish uning asosiy vazifasi. Kim qaysi amalni
    # bajara olishi baribir `WORKFLOW_RULES` bilan tekshiriladi — ya'ni bu
    # istisno nazoratga zanjirning boshqa bosqichini ochib bermaydi.
    control_role_may_write = True

    def post(self, request, pk):
        serializer = DocumentWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = branch_scope(
            Document.objects.select_related("created_by", "branch", "site"),
            request.user,
        ).filter(pk=pk).first()
        if not document:
            return Response({"error": "Hujjat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        action = serializer.validated_data["action"]
        comment = serializer.validated_data.get("comment", "").strip()
        rule = WORKFLOW_RULES.get(document.status, {}).get(action)
        if not rule:
            return Response({"error": "Bu holatda ushbu amal mavjud emas"}, status=status.HTTP_400_BAD_REQUEST)

        if not (is_admin(request.user) or bool(set(request.user.roles or []).intersection(rule["roles"]))):
            return Response({"error": "Bu amal uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        if action in COMMENT_REQUIRED_ACTIONS and not comment:
            return Response(
                {"error": COMMENT_REQUIRED_ACTIONS[action]}, status=status.HTTP_400_BAD_REQUEST
            )

        previous_status = document.status
        previous_status_label = document.get_status_display()
        # `send_back` — yagona `next_status` i yo'q amal: nishonni foydalanuvchi
        # tanlaydi. Tanlov qoidadagi ro'yxat bilan tekshiriladi, ya'ni faqat
        # o'zidan oldingi tasdiqlash bosqichi bo'la oladi — aks holda bu amal
        # zanjirdan sakrab o'tishning yo'liga aylanardi.
        target_status = serializer.validated_data.get("target_status", "").strip()
        if action == "send_back":
            if target_status not in rule["targets"]:
                return Response(
                    {"error": "Bu bosqichga qaytarib bo'lmaydi"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            next_status = target_status
        else:
            target_status = ""
            next_status = rule["next_status"]

        try:
            with transaction.atomic():
                # Qabul — statusning yon ta'siri emas, uning mazmuni: tovar
                # omborga kiradi. Ikkalasi bitta transaksiyada, aks holda
                # status o'zgarib qoldiq o'zgarmay qolishi mumkin edi.
                movements = (
                    receive_purchase_items(
                        document, request.user, serializer.validated_data.get("warehouse")
                    )
                    if next_status == "received"
                    else []
                )
                document.status = next_status
                document.save(update_fields=["status", "updated_at"])
                DocumentApproval.objects.create(
                    document=document,
                    approver=request.user,
                    action=action,
                    target_status=target_status,
                    comment=comment,
                )
        except ReceiptError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        create_audit_log(
            request,
            "document_workflow_changed",
            "Document",
            document.id,
            {
                "from": previous_status,
                "to": document.status,
                "action": action,
                "target_status": target_status,
                "comment": comment,
            },
        )
        if movements:
            create_audit_log(
                request,
                "document_stock_received",
                "Document",
                document.id,
                {
                    "doc_number": document.doc_number,
                    "warehouse_id": movements[0].warehouse_id,
                    "movement_ids": [movement.id for movement in movements],
                    "branch_id": document.branch_id,
                },
            )
        if previous_status == "revision":
            self._notify_returners(document, request.user)

        recipients = [document.created_by]
        # Bosqichga qaytarish umumiy "holat yangilandi" xabari ostida
        # yo'qolmasligi kerak: nishon bosqichdan qayta qaror kutilmoqda va
        # sababi aynan izohda.
        if action == "send_back":
            branch_title = "Hujjat qayta ko'rib chiqishga qaytarildi"
            branch_body = (
                f"{document.doc_number} hujjati {previous_status_label} dan "
                f"{document.get_status_display()} ga qayta ko'rib chiqish uchun "
                f"qaytarildi. Sabab: {comment}"
            )
        else:
            branch_title = "Hujjat holati yangilandi"
            branch_body = (
                f"{document.doc_number} hujjati {previous_status_label} dan "
                f"{document.get_status_display()} ga o'tdi."
            )
        notify_branch_roles(
            document.branch,
            {
                "architecture",
                "ceo",
                "procurement",
                "anticorruption",
                "accountant",
                "warehouse",
                "branch_manager",
                "admin",
            },
            branch_title,
            branch_body,
            "info" if document.status not in {"rejected"} and action != "send_back" else "warning",
            related_type="document",
            related_id=document.id,
        )
        if recipients:
            notify_users(
                recipients,
                "Hujjat holati yangilandi",
                f"{document.doc_number} hujjatingizning yangi holati: {document.get_status_display()}",
                "info" if document.status != "rejected" else "warning",
                related_type="document",
                related_id=document.id,
            )

        return Response(DocumentSerializer(document, context={"request": request}).data, status=status.HTTP_200_OK)

    @staticmethod
    def _notify_returners(document, actor):
        """
        Hujjatni tuzatishga qaytargan foydalanuvchilarga qayta yuborilgani
        haqida xabar beradi.

        Qaytargan odam zanjirning boshiga qaytgan hujjatni o'z navbatida yana
        ko'radi, lekin bu bir necha bosqichdan keyin bo'ladi — u vaqtgacha
        so'rov unutilib qolmasin. Filial bo'yicha umumiy xabar bu yerda
        yetarli emas: qaytargan rol markaziy bo'lishi mumkin.
        """
        returner_ids = set(
            DocumentApproval.objects.filter(document=document, action="return")
            .exclude(approver__isnull=True)
            .exclude(approver_id=actor.id)
            .values_list("approver_id", flat=True)
        )
        if not returner_ids:
            return

        notify_users(
            list(User.objects.filter(id__in=returner_ids, is_active=True)),
            "Qaytarilgan hujjat qayta yuborildi",
            f"{document.doc_number} hujjati tuzatilib qayta jo'natildi — zanjir arxitekturadan boshlanadi.",
            "info",
            related_type="document",
            related_id=document.id,
        )


class DocumentArchiveToggleView(APIView):
    """Hujjatni arxivlash yoki arxivdan chiqarish."""

    def post(self, request, pk):
        document = branch_scope(
            Document.objects.select_related("created_by", "branch", "site"),
            request.user,
        ).filter(pk=pk).first()
        if not document:
            return Response({"error": "Hujjat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if not (is_admin(request.user) or bool(set(request.user.roles or []).intersection(ARCHIVE_ROLES))):
            return Response({"error": "Arxivlash uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        archive = request.data.get("archive", True)
        if isinstance(archive, str):
            archive = archive.lower() == "true"

        document.is_archived = archive
        document.archived_at = timezone.now() if archive else None
        document.save(update_fields=["is_archived", "archived_at", "updated_at"])

        create_audit_log(
            request,
            "document_archived" if archive else "document_unarchived",
            "Document",
            document.id,
            {
                "doc_number": document.doc_number,
                "is_archived": document.is_archived,
                "branch_id": document.branch_id,
            },
        )
        return Response(DocumentSerializer(document, context={"request": request}).data, status=status.HTTP_200_OK)


class DocumentsExportView(APIView):
    """Hujjatlarni CSV eksport qilish."""

    def get(self, request):
        queryset = branch_scope(
            Document.objects.select_related("created_by", "site", "branch"),
            request.user,
        ).order_by("-created_at")

        archived_filter = request.query_params.get("archived", "all")
        if archived_filter == "true":
            queryset = queryset.filter(is_archived=True)
        elif archived_filter == "false":
            queryset = queryset.filter(is_archived=False)

        queryset = filter_by_query_params(
            queryset,
            request,
            {"status": "status", "doc_type": "doc_type", "site": "site_id"},
        )

        rows = [
            {
                "doc_number": document.doc_number,
                "doc_type": document.get_doc_type_display(),
                "status": document.get_status_display(),
                "title": document.title,
                "branch": document.branch.name if document.branch else "",
                "site": document.site.name if document.site else "",
                "created_by": document.created_by.full_name if document.created_by else "",
                "total_amount": document.total_amount,
                "is_archived": "Ha" if document.is_archived else "Yo'q",
                "created_at": timezone.localtime(document.created_at).strftime("%Y-%m-%d %H:%M"),
            }
            for document in queryset
        ]
        return export_to_csv(
            "documents-export.csv",
            [
                "doc_number",
                "doc_type",
                "status",
                "title",
                "branch",
                "site",
                "created_by",
                "total_amount",
                "is_archived",
                "created_at",
            ],
            rows,
        )


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Hujjat tahrirlash va o'chirish."""
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return branch_scope(
            Document.objects.select_related("created_by", "site", "branch").prefetch_related("approvals"),
            self.request.user,
        ).order_by("-created_at")

    def _ensure_can_manage(self, document):
        """
        Ikki mustaqil shart: KIM va QAYSI HOLATDA.

        Kim — muallifi yoki `DOCUMENT_MANAGE_ROLES`; ilgari o'z filialidagi
        istalgan xodim begona hujjatni o'chirib yubora olardi. Holat —
        `ensure_document_editable`: zanjir boshlangach hujjat muzlaydi.
        Ikkalasi alohida javob beradi (403 va 409), chunki foydalanuvchi
        uchun bular boshqa-boshqa muammo.
        """
        user = self.request.user
        if not (document.created_by_id == user.id or has_any_role(user, DOCUMENT_MANAGE_ROLES)):
            raise exceptions.PermissionDenied("Bu hujjatni o'zgartirish uchun sizda ruxsat yo'q")
        ensure_document_editable(document)

    def update(self, request, *args, **kwargs):
        self._ensure_can_manage(self.get_object())
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        self._ensure_can_manage(document)

        create_audit_log(
            request,
            "document_deleted",
            "Document",
            document.id,
            {"doc_number": document.doc_number, "branch_id": document.branch_id},
        )
        return super().destroy(request, *args, **kwargs)


class DocumentCommentListCreateView(generics.ListCreateAPIView):
    """
    Hujjat bo'yicha yozishma — ro'yxat va yangi izoh.

    Muzlatish bu yerga TEGISHLI EMAS. Aynan muzlagan hujjat haqida gaplashish
    kerak bo'ladi: xaridlar bo'limi kamchilikni ko'radi, tuzatishni esa filial
    rahbari kiritadi. Izoh hujjat mazmunini o'zgartirmaydi, shuning uchun
    `ensure_document_editable` chaqirilmaydi.
    """

    serializer_class = DocumentCommentSerializer
    # Nazorat roli uchun istisno: kuzatuvini qayd eta olmaydigan nazoratning
    # ma'nosi qolmaydi. SoD buzilmaydi — izoh qaror emas, hujjat mazmunini
    # o'zgartirmaydi va muallifi bilan birga audit izi qoldiradi.
    control_role_may_write = True

    def get_queryset(self):
        return branch_scope(
            DocumentComment.objects.select_related("author", "document", "document__branch"),
            self.request.user,
            "document__branch",
        ).filter(document_id=self.kwargs["pk"])

    def perform_create(self, serializer):
        # Ro'yxat filial bo'yicha filtrlanadi; yozish ham shunday cheklanishi
        # kerak, aks holda begona filial hujjatiga izoh yozib bo'lardi.
        document = branch_scope(
            Document.objects.select_related("branch", "created_by"), self.request.user
        ).filter(pk=self.kwargs["pk"]).first()
        if not document:
            raise exceptions.NotFound("Hujjat topilmadi")

        comment = serializer.save(document=document, author=self.request.user)
        create_audit_log(
            self.request,
            "document_comment_created",
            "Document",
            document.id,
            {"doc_number": document.doc_number, "branch_id": document.branch_id},
        )
        notify_branch_roles(
            document.branch,
            {"branch_manager", "procurement", "admin"},
            "Hujjatga yangi izoh",
            f"{document.doc_number} hujjatiga izoh yozildi: {comment.text[:120]}",
            "info",
            related_type="document",
            related_id=document.id,
        )
        if document.created_by_id and document.created_by_id != self.request.user.id:
            notify_users(
                [document.created_by],
                "Hujjatingizga izoh yozildi",
                f"{document.doc_number}: {comment.text[:120]}",
                "info",
                related_type="document",
                related_id=document.id,
            )


# --- Document File Views ---
class DocumentFileListView(generics.ListAPIView):
    """Hujjat fayllari ro'yxati."""
    serializer_class = DocumentFileSerializer
    
    def get_queryset(self):
        doc_id = self.kwargs.get('doc_pk')
        return branch_scope(
            DocumentFile.objects.select_related("document", "uploaded_by", "document__branch"),
            self.request.user,
            "document__branch",
        ).filter(document_id=doc_id).order_by("-created_at")


class DocumentFileUploadView(APIView):
    """Hujjatga fayl yuklash."""
    
    def post(self, request, doc_pk):
        # Fayllar ro'yxati filial bo'yicha filtrlanadi; yuklash ham shunday
        # cheklanishi kerak, aks holda begona filial hujjatiga fayl ilib
        # qo'yish mumkin edi.
        document = branch_scope(
            Document.objects.select_related("branch"), request.user
        ).filter(id=doc_pk).first()
        if not document:
            return Response({'error': 'Hujjat topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'Fayl tanlanmadi'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Max 10MB
        if file.size > 10 * 1024 * 1024:
            return Response({'error': 'Fayl hajmi 10MB dan oshmasligi kerak'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_extensions = {".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png"}
        suffix = ""
        if "." in file.name:
            suffix = file.name[file.name.rfind("."):].lower()
        if suffix not in allowed_extensions:
            return Response(
                {"error": "Faqat PDF, XLSX, XLS, JPG, JPEG va PNG fayllariga ruxsat beriladi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = DocumentFile.objects.create(
            document=document,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            uploaded_by=request.user
        )

        create_audit_log(
            request,
            "document_file_uploaded",
            "DocumentFile",
            created.id,
            {"document_id": document.id, "filename": file.name},
        )
        return Response({'message': 'Fayl muvaffaqiyatli yuklandi'}, status=status.HTTP_201_CREATED)
