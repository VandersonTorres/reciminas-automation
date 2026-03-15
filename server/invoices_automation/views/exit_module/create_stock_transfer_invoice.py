from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from invoices_automation.forms import ExitInvoiceForm, ExitInvoiceItemFormSet
from invoices_automation.models import ExitInvoiceQueue


# Create invoice Exit - Stock Transfer
@login_required
def create_stock_transfer_invoice(request, invoice_pk=None):
    invoice = None
    if invoice_pk:
        invoice = get_object_or_404(ExitInvoiceQueue, pk=invoice_pk)

    is_edit = invoice is not None

    if request.method == "POST":
        action = request.POST.get("action")

        post_data = request.POST.copy()
        # Stock Transfer is always between the same owner (provider)
        post_data["provider"] = "RECIMINAS - RJ"
        if not post_data.get("modality"):
            post_data["modality"] = "exit_stock_transfer"

        invoice_form = ExitInvoiceForm(post_data, instance=invoice)
        material_formset = ExitInvoiceItemFormSet(
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
                    "invoices_automation/exit_module/exit_invoices_stock_transfer_management.html",
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
                url = reverse("emit_invoice", kwargs={"invoice_pk": invoice.pk})
                emission_url = (
                    f"{url}?"
                    "invoice_model=ExitInvoiceQueue&"
                    "service_class=StockTransferInvoiceService&"
                    "access_invoices_view=access_exit_invoices_queue"
                )
                return redirect(emission_url)

            elif action == "add_to_queue":
                messages.success(request, "Nota adicionada à fila!")
                return redirect("create_stock_transfer_invoice")
        else:
            if not material_formset.is_valid():
                material_formset.non_form_errors = "Material sem especificações"
            elif not invoice_form.is_valid():
                invoice_form.non_field_errors = "Dados da nota inválidos"

            # re-render template
            return render(
                request,
                "invoices_automation/exit_module/exit_invoices_stock_transfer_management.html",
                {
                    "form": invoice_form,
                    "formset": material_formset,
                    "is_edit": is_edit,
                },
            )

    else:
        initial_data = {"modality": "exit_stock_transfer"}
        invoice_form = ExitInvoiceForm(instance=invoice, initial=initial_data)
        material_formset = ExitInvoiceItemFormSet(
            instance=invoice if is_edit else None,
            prefix="items",
        )

    return render(
        request,
        "invoices_automation/exit_module/exit_invoices_stock_transfer_management.html",
        {
            "form": invoice_form,
            "formset": material_formset,
            "is_edit": is_edit,
        },
    )
