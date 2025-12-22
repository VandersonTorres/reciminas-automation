from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from invoices_automation.forms import EntryInvoiceForm, EntryInvoiceItemFormSet
from invoices_automation.models import EntryInvoiceQueue
from invoices_automation.services.lock_manager import automation_lock


# Create invoice entry
@login_required
def create_invoice(request, invoice_pk=None):
    invoice = None
    if invoice_pk:
        invoice = get_object_or_404(EntryInvoiceQueue, pk=invoice_pk)

    is_edit = invoice is not None

    if request.method == "POST":
        action = request.POST.get("action")

        invoice_form = EntryInvoiceForm(request.POST, instance=invoice)
        material_formset = EntryInvoiceItemFormSet(
            request.POST,
            instance=invoice if is_edit else None,
            prefix="items",
        )

        if invoice_form.is_valid() and material_formset.is_valid():
            valid_materials = [
                f
                for f in material_formset
                if not f.cleaned_data.get("DELETE", False) and f.cleaned_data.get("material")
            ]

            if not valid_materials:
                material_formset.non_form_errors = "Adicione pelo menos um material"
                # re-render template
                return render(
                    request,
                    "invoices_automation/entry_invoices_management.html",
                    {
                        "form": invoice_form,
                        "formset": material_formset,
                        "is_edit": invoice is not None,
                    },
                )

            # Create Invoice
            invoice = invoice_form.save(commit=False)
            invoice.user = request.user
            invoice.status = "pending"
            invoice.save()

            # Store invoice materials
            material_formset.instance = invoice
            material_formset.save()

            if action == "emit_now":
                return redirect("emit_invoice", invoice_pk=invoice.pk)

            elif action == "add_to_queue":
                messages.success(request, "Nota adicionada à fila!")
                return redirect("create_invoice")
        else:
            if material_formset.error_messages.get("missing_management_form"):
                material_formset.non_form_errors = "Material sem especificações"
                # re-render template
                return render(
                    request,
                    "invoices_automation/entry_invoices_management.html",
                    {
                        "form": invoice_form,
                        "formset": material_formset,
                        "is_edit": is_edit,
                    },
                )

    else:
        invoice_form = EntryInvoiceForm(instance=invoice)
        material_formset = EntryInvoiceItemFormSet(
            instance=invoice if is_edit else None,
            prefix="items",
        )

    return render(
        request,
        "invoices_automation/entry_invoices_management.html",
        {
            "form": invoice_form,
            "formset": material_formset,
            "is_edit": is_edit,
        },
    )


# Read invoices
@login_required
def access_invoices_queue(request):
    # Check if there are any invoices with status "processing" and automation is not running
    processing_invoices = EntryInvoiceQueue.objects.filter(status="processing")
    if not automation_lock.locked():
        for invoice in processing_invoices:
            invoice.status = "cancelled"
            invoice.save()

    queue = EntryInvoiceQueue.objects.all().order_by("created_at")
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
    invoice = get_object_or_404(EntryInvoiceQueue, pk=pk)
    if request.method == "POST":
        form = EntryInvoiceForm(request.POST, instance=invoice)
        formset = EntryInvoiceItemFormSet(request.POST, instance=invoice, prefix="items")

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Nota atualizada com sucesso!")
            return redirect("access_invoices_queue")
        else:
            messages.error(request, "Corrija os erros do formulário e tente novamente.")
    else:
        form = EntryInvoiceForm(instance=invoice)
        formset = EntryInvoiceItemFormSet(instance=invoice, prefix="items")

    return render(
        request,
        "invoices_automation/entry_invoices_management.html",
        {
            "form": form,
            "formset": formset,
            "is_edit": True,
        },
    )


# Delete Invoice
@login_required
def delete_invoice(request, pk):
    invoice = get_object_or_404(EntryInvoiceQueue, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para excluir notas.")
        return redirect("access_invoices_queue")

    invoice.delete()
    messages.success(request, "Nota removida da fila com sucesso!")
    return redirect("access_invoices_queue")
