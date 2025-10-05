import time
import threading
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt

from .forms import CustomUserCreationForm, EntryInvoiceForm
from .models import EntryInvoiceQueue
from .services.invoices_generator import EntryInvoicesAutomation, CANCEL_FLAGS
from .services.lock_manager import automation_lock
from .services.log_buffer import current_logs


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # noqa: F841
            messages.success(request, "Cadastro enviado! Aguarde a aprovação do administrador.")
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, "core/register.html", {"form": form})


@login_required
def dashboard(request):
    return render(request, "invoices_automation/dashboard.html")


@login_required
def invoice_queue(request):
    queue = EntryInvoiceQueue.objects.filter(user=request.user).order_by("created_at")
    paginator = Paginator(queue, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "invoices_queue": page_obj.object_list,
    }

    return render(request, "invoices_automation/invoice_queue.html", context)


@login_required
def start_batch_automation(request):
    if automation_lock.locked():
        messages.error(request, "Outra automação já está em andamento. Aguarde finalizar.")
        return redirect("invoice_queue")

    queue_items = EntryInvoiceQueue.objects.filter(user=request.user, status="pending")
    if not queue_items:
        messages.info(request, "Nenhuma nota pendente para emitir.")
        return redirect("invoice_queue")

    job_id = str(uuid.uuid4())
    request.session["job_id"] = job_id

    def run_batch():
        with automation_lock:
            for idx, item in enumerate(queue_items):
                current_iter = f"{idx + 1}/{len(queue_items)}"
                if CANCEL_FLAGS.get(job_id) or CANCEL_FLAGS.get("__GLOBAL_CANCEL__"):
                    item.status = "cancelled"
                    item.save()
                    messages.warning(request, "Automação cancelada pelo usuário — interrompendo o lote.")
                    break

                item.status = "processing"
                item.save()
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
                    automation.run()
                    # TODO: Aqui salva o resultado em EntryInvoiceResult (PDF/screenshot)
                    # EntryInvoiceResult.objects.create(
                    #     queue_item=item,
                    #     user=request.user,
                    #     # pdf_file="path/to/pdf.pdf",
                    #     # screenshot="path/to/screenshot.png",
                    # )
                    item.status = "done"
                except RuntimeError:
                    item.status = "cancelled"
                except Exception as e:
                    item.status = "cancelled"
                    automation.logger.error(f"Erro ao emitir NF {item.id}: {e}")
                finally:
                    item.save()
                    time.sleep(2)

            CANCEL_FLAGS.pop(job_id, None)
            CANCEL_FLAGS.pop("__GLOBAL_CANCEL__", None)

    threading.Thread(target=run_batch, daemon=True).start()
    return redirect("automation_logs")


@login_required
def entry_invoices_management(request):
    if request.method == "POST":
        form = EntryInvoiceForm(request.POST)
        action = request.POST.get("action")  # Get which button was pressed
        if form.is_valid():
            invoice_data = {
                "provider": form.cleaned_data["provider"],
                "material_code": form.cleaned_data["material_code"],
                "material_quantity": form.cleaned_data["material_quantity"],
                "material_price": form.cleaned_data["material_price"],
                "discount": form.cleaned_data.get("discount", 0.0),
            }

            # Action: Emit now
            if action == "emit_now":
                if automation_lock.locked():
                    messages.error(request, "Outra automação já está em andamento. Aguarde finalizar.")
                    return redirect("dashboard")

                def run_automation():
                    with automation_lock:
                        automation = EntryInvoicesAutomation(**invoice_data, job_id=str(uuid.uuid4()))
                        request.session["job_id"] = automation.job_id
                        automation.run()

                threading.Thread(target=run_automation, daemon=True).start()
                return redirect("automation_logs")

            # Action: Add to queue
            elif action == "add_to_queue":
                EntryInvoiceQueue.objects.create(user=request.user, **invoice_data)
                messages.success(request, "Nota adicionada à fila com sucesso!")
                return redirect("entry_invoices_management")

            # Action: Go to queue
            elif action == "go_to_queue":
                return redirect("invoice_queue")
    else:
        form = EntryInvoiceForm()

    return render(request, "invoices_automation/entry_invoices_management.html", {"form": form})


@login_required
def delete_invoice(request, pk):
    invoice = get_object_or_404(EntryInvoiceQueue, pk=pk, user=request.user)
    invoice.delete()
    messages.success(request, "Nota removida da fila com sucesso!")
    return redirect("invoice_queue")


@login_required
def edit_invoice(request, pk):
    invoice = get_object_or_404(EntryInvoiceQueue, pk=pk, user=request.user)
    if request.method == "POST":
        form = EntryInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, "Nota atualizada com sucesso!")
            return redirect("invoice_queue")
    else:
        form = EntryInvoiceForm(instance=invoice)
    return render(request, "invoices_automation/entry_invoices_management.html", {"form": form, "is_edit": True})


@login_required
def automation_logs(request):
    return render(request, "invoices_automation/automation_logs.html")


@login_required
def get_logs(request):
    return JsonResponse({"logs": current_logs})


@csrf_exempt
@login_required
def cancel_automation(request):
    if request.method == "POST":
        job_id = request.POST.get("job_id")
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
