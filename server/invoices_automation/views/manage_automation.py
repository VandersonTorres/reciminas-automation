import threading
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt

from invoices_automation.models import EntryInvoiceQueue
from invoices_automation.services.invoices_service import CANCEL_FLAGS
from invoices_automation.services.lock_manager import automation_lock
from invoices_automation.services.log_buffer import current_logs

from invoices_automation.utils.invoices_processing import process_invoice_batch


@login_required
def emit_invoice(request, invoice_pk):
    if automation_lock.locked():
        messages.error(request, "Outra automação já está em andamento.")
        return redirect("dashboard")

    invoice = get_object_or_404(EntryInvoiceQueue, pk=invoice_pk)
    if invoice.status != "pending":
        messages.error(request, "Nota não está pendente.")
        return redirect("access_invoices_queue")

    job_id = str(uuid.uuid4())
    request.session["job_id"] = job_id

    threading.Thread(
        target=lambda: process_invoice_batch([invoice], job_id),
        daemon=True,
    ).start()

    return redirect("follow_automation_logs")


@login_required
def start_batch_automation(request):
    if automation_lock.locked():
        messages.error(request, "Outra automação já está em andamento.")
        return redirect("dashboard")

    invoices = list(EntryInvoiceQueue.objects.filter(user=request.user, status="pending"))

    if not invoices:
        messages.info(request, "Nenhuma nota pendente.")
        return redirect("access_invoices_queue")

    job_id = str(uuid.uuid4())
    request.session["job_id"] = job_id

    threading.Thread(
        target=lambda: process_invoice_batch(invoices, job_id),
        daemon=True,
    ).start()

    return redirect("follow_automation_logs")


@login_required
def follow_automation_logs(request):
    return render(request, "invoices_automation/follow_automation_logs.html", {"logs": current_logs})


@login_required
def get_logs(request):
    return JsonResponse({"logs": current_logs})


@login_required
@csrf_exempt
def clear_logs(request):
    current_logs.clear()
    return JsonResponse({"status": "cleared"})


@login_required
def cancel_automation(request):
    # Request for cancelling an ongoing automation
    job_id = request.POST.get("job_id") or request.GET.get("job_id")
    try:
        if job_id:
            if job_id in CANCEL_FLAGS:
                CANCEL_FLAGS[job_id] = True
                messages.info(request, f"Cancelando processo '{job_id}'.")
            else:
                # If job_id no longer exists, create a global flag as a fallback
                CANCEL_FLAGS["__GLOBAL_CANCEL__"] = True
                messages.warning(request, f"Job '{job_id}' não encontrado. Cancelamento global acionado.")
        else:
            # No job_id found - Cancel all for safety
            CANCEL_FLAGS["__GLOBAL_CANCEL__"] = True
            messages.warning(request, "Nenhum job_id informado — cancelamento global acionado.")
    except Exception as e:
        messages.error(request, f"Erro durante cancelamento: {str(e)}")
        # Even if it fails, Try to ensure the cancelling
        CANCEL_FLAGS["__GLOBAL_CANCEL__"] = True
        return JsonResponse({"status": "cancelling_with_error"})
    finally:
        return JsonResponse({"status": "cancelling"})
