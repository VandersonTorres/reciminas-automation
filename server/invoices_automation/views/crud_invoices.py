import threading
import uuid

from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from invoices_automation.forms import EntryInvoiceForm
from invoices_automation.models import EntryInvoiceQueue
from invoices_automation.services.invoices_generator import EntryInvoicesAutomation
from invoices_automation.services.lock_manager import automation_lock


# Create invoice entry
@login_required
def create_invoice(request, invoice_pk=None):
    if request.method == "POST":
        action = request.POST.get("action")  # Get which button was pressed
        form = EntryInvoiceForm(request.POST)
        invoice_data = {}
        if form.is_valid():
            invoice_data = {
                "provider": form.cleaned_data["provider"],
                "material_code": form.cleaned_data["material_code"],
                "material_quantity": form.cleaned_data["material_quantity"],
                "material_price": form.cleaned_data["material_price"],
                "discount": form.cleaned_data.get("discount", 0.0),
            }
        elif invoice_pk:
            invoice = get_object_or_404(EntryInvoiceQueue, pk=invoice_pk)
            action = "emit_now"
            invoice_data = {
                "provider": invoice.provider,
                "material_code": invoice.material_code,
                "material_quantity": invoice.material_quantity,
                "material_price": invoice.material_price,
                "discount": invoice.discount,
            }

        if invoice_data:
            # Action: Emit now
            if action == "emit_now":
                if automation_lock.locked():
                    messages.error(request, "Outra automação já está em andamento. Aguarde finalizar.")
                    return redirect("dashboard")

                job_id = str(uuid.uuid4())
                request.session["job_id"] = job_id
                queue_item = EntryInvoiceQueue.objects.create(
                    user=request.user,
                    status="processing",
                    **invoice_data,
                )

                def run_unique_automation():
                    with automation_lock:
                        automation = EntryInvoicesAutomation(**invoice_data, job_id=job_id)
                        try:
                            invoice = automation.run()
                            if invoice:
                                queue_item.status = "done"
                                queue_item.invoice_path = invoice.replace("downloads/", "")
                            else:
                                queue_item.status = "cancelled"
                        except Exception:
                            queue_item.status = "cancelled"
                        finally:
                            queue_item.save()

                threading.Thread(target=run_unique_automation, daemon=True).start()
                return redirect("follow_automation_logs")

            # Action: Add to queue
            elif action == "add_to_queue":
                EntryInvoiceQueue.objects.create(user=request.user, **invoice_data)
                messages.success(request, "Nota adicionada à fila com sucesso!")
                return redirect("create_invoice")

            # Action: Go to queue
            elif action == "go_to_queue":
                return redirect("access_invoices_queue")
    else:
        form = EntryInvoiceForm()

    return render(request, "invoices_automation/entry_invoices_management.html", {"form": form})


# Read invoices
@login_required
def access_invoices_queue(request):
    queue = EntryInvoiceQueue.objects.filter(user=request.user).order_by("created_at")
    paginator = Paginator(queue, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "invoices_queue": page_obj.object_list,
    }

    return render(request, "invoices_automation/access_invoices_queue.html", context)


# Update invoice
@login_required
def edit_invoice(request, pk):
    invoice = get_object_or_404(EntryInvoiceQueue, pk=pk, user=request.user)
    if request.method == "POST":
        form = EntryInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, "Nota atualizada com sucesso!")
            return redirect("access_invoices_queue")
    else:
        form = EntryInvoiceForm(instance=invoice)
    return render(request, "invoices_automation/entry_invoices_management.html", {"form": form, "is_edit": True})


# Delete Invoice
@login_required
def delete_invoice(request, pk):
    invoice = get_object_or_404(EntryInvoiceQueue, pk=pk, user=request.user)
    invoice.delete()
    messages.success(request, "Nota removida da fila com sucesso!")
    return redirect("access_invoices_queue")
