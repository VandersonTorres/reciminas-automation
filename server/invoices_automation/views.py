import threading
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .forms import CustomUserCreationForm, EntryInvoiceForm
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
def entry_invoice(request):
    if request.method == "POST":
        if automation_lock.locked():
            messages.error(request, "Outra automação já está em andamento. Aguarde finalizar.")
            return redirect("dashboard")

        form = EntryInvoiceForm(request.POST)
        if form.is_valid():

            def run_automation():
                with automation_lock:
                    automation = EntryInvoicesAutomation(
                        provider=form.cleaned_data["provider"],
                        material_code=form.cleaned_data["material_code"],
                        material_quantity=form.cleaned_data["material_quantity"],
                        material_price=form.cleaned_data["material_price"],
                        discount=form.cleaned_data.get("discount", 0),
                        job_id=str(uuid.uuid4()),
                    )
                    request.session["job_id"] = automation.job_id
                    automation.run()

            threading.Thread(target=run_automation, daemon=True).start()
            return redirect("automation_logs")

    else:
        form = EntryInvoiceForm()

    return render(request, "invoices_automation/entry_invoice.html", {"form": form})


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
