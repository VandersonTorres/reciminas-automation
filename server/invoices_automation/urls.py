from django.contrib.auth import views as auth_views
from django.urls import path

from invoices_automation.forms import CustomAuthenticationForm
from invoices_automation.views.core import dashboard, register
from invoices_automation.views.manage_emission_approval import approve_pdf, get_pending_pdfs, serve_pdf
from invoices_automation.views.crud_invoices import (
    create_invoice_registry,
    invoice_queue,
    edit_invoice,
    delete_invoice,
)
from invoices_automation.views.manage_automation import (
    start_batch_automation,
    cancel_automation,
    automation_logs,
    get_logs,
    clear_logs,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html", authentication_form=CustomAuthenticationForm),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("registro/", register, name="register"),
    path("dashboard/", dashboard, name="dashboard"),
    path("gerenciamento-nf-de-entrada/", create_invoice_registry, name="create_invoice_registry"),
    path("emissoes-nf-de-entrada/", start_batch_automation, name="start_batch_automation"),
    path("fila-de-nfs/", invoice_queue, name="invoice_queue"),
    path("fila/excluir/<int:pk>/", delete_invoice, name="delete_invoice"),
    path("fila/editar/<int:pk>/", edit_invoice, name="edit_invoice"),
    path("logs-automacao/", automation_logs, name="automation_logs"),
    path("get-logs/", get_logs, name="get_logs"),
    path("cancelar-processo/", cancel_automation, name="cancel_automation"),
    path("pegar-pdfs-pendentes/", get_pending_pdfs, name="get_pending_pdfs"),
    path("aprovar-nota/", approve_pdf, name="approve_pdf"),
    path("downloads/<path:filename>", serve_pdf, name="serve_pdf"),
    path("clear_logs/", clear_logs, name="clear_logs"),
]
