from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import CustomUserCreationForm, EntryInvoiceForm


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
def entry_invoice(request):
    if request.method == "POST":
        form = EntryInvoiceForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data  # noqa: F841
            # provider = data.get("provider")
            # material_code = data.get("material_code")
            # material_quantity = data.get("material_quantity")
            # material_price = data.get("material_price")
            # discount = data.get("discount", 0)
            # import pdb; pdb.set_trace()
            messages.success(request, "Iniciando emissão de NF de Entrada")
    else:
        form = EntryInvoiceForm()

    return render(request, "invoices_automation/entry_invoice.html", {"form": form})
