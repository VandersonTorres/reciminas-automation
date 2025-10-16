import time
import threading
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from invoices_automation.models import EntryInvoiceQueue
from invoices_automation.services.invoices_generator import EntryInvoicesAutomation, CANCEL_FLAGS
from invoices_automation.services.lock_manager import automation_lock
from invoices_automation.services.log_buffer import current_logs


@login_required
def start_batch_automation(request):
    if automation_lock.locked():
        messages.error(request, "Outra automação já está em andamento. Aguarde finalizar.")
        return redirect("dashboard")

    queue_items = EntryInvoiceQueue.objects.filter(user=request.user, status="pending")
    if not queue_items:
        messages.info(request, "Nenhuma nota pendente para emitir.")
        return redirect("access_invoices_queue")

    job_id = str(uuid.uuid4())
    request.session["job_id"] = job_id

    def run_batch_automation():
        with automation_lock:
            for idx, item in enumerate(queue_items):
                if CANCEL_FLAGS.get(job_id) or CANCEL_FLAGS.get("__GLOBAL_CANCEL__"):
                    # Keep monitoring through the loop to cancel all items if needed
                    item.status = "cancelled"
                    item.save()
                    messages.warning(request, "Automação cancelada pelo usuário — interrompendo o lote.")
                    break
                item.status = "processing"
                item.save()

                current_iter = f"{idx + 1}/{len(queue_items)}"
                automation = EntryInvoicesAutomation(
                    provider=item.provider,
                    material_code=item.material_code,
                    material_quantity=item.material_quantity,
                    material_price=item.material_price,
                    discount=item.discount,
                    job_id=job_id,
                    current_iter=current_iter,
                )

                try:
                    invoice = automation.run()
                    if invoice:
                        item.status = "done"
                        item.invoice_path = invoice.replace("downloads/", "")
                    else:
                        item.status = "cancelled"
                except Exception:
                    item.status = "cancelled"
                finally:
                    item.save()
                    time.sleep(2)

            CANCEL_FLAGS.pop(job_id, None)
            CANCEL_FLAGS.pop("__GLOBAL_CANCEL__", None)

    threading.Thread(target=run_batch_automation, daemon=True).start()
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


@csrf_exempt
@login_required
def cancel_automation(request):
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
        # Release lock
        if automation_lock.locked():
            try:
                automation_lock.release()
                messages.info(request, "Fila liberada com sucesso.")
            except RuntimeError as err:
                messages.warning(request, f"Erro ao liberar fila: {err}")

        return JsonResponse({"status": "cancelling"})
