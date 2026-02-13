import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin

from invoices_automation.services import TO_PDF_APPROVAL


@login_required
@require_POST
def approve_pdf(request):
    task_id = request.POST.get("task_id")
    action = request.POST.get("action")

    if task_id in TO_PDF_APPROVAL:
        if action == "approve":
            TO_PDF_APPROVAL[task_id]["status"] = "approved"
        elif action == "cancel":
            TO_PDF_APPROVAL[task_id]["status"] = "cancelled"
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error", "message": "Job não encontrado"}, status=404)


@login_required
def get_pending_pdfs(request):
    job_id = request.GET.get("job_id")
    results = [
        {"task_id": task_id, "pdf_path": info["path"], "status": info["status"]}
        for task_id, info in TO_PDF_APPROVAL.items()
        if info.get("job_id") == job_id and info["status"] == "pending"
    ]
    return JsonResponse({"results": results})


@login_required
@xframe_options_sameorigin
def serve_pdf(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if not os.path.exists(file_path):
        raise Http404("Arquivo não encontrado")
    return FileResponse(open(file_path, "rb"), content_type="application/pdf")
