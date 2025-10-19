from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from invoices_automation.forms import CustomUserCreationForm
from invoices_automation.services.lock_manager import automation_lock


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
    lock_status = "Bloqueada. Aguarde alguns minutos" if automation_lock.locked() else "Disponível"
    return render(request, "invoices_automation/dashboard.html", {"lock_status": lock_status})
