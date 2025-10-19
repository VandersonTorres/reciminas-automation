from django.contrib.auth import views as auth_views
from django.urls import path

from invoices_automation.forms import CustomAuthenticationForm
from invoices_automation.views.core import dashboard, register
from invoices_automation.views.manage_emission_approval import approve_pdf, get_pending_pdfs, serve_pdf
from invoices_automation.views.crud_invoices import (
    create_invoice,
    access_invoices_queue,
    edit_invoice,
    delete_invoice,
)
from invoices_automation.views.crud_materials import (
    list_materials,
    add_new_material,
    delete_material,
)
from invoices_automation.views.manage_automation import (
    start_batch_automation,
    cancel_automation,
    follow_automation_logs,
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
    path("cadastro/", register, name="register"),
    path("dashboard/", dashboard, name="dashboard"),
    path("registro-nf-entrada/", create_invoice, name="create_invoice"),
    path("emissoes-nfs-entrada/", start_batch_automation, name="start_batch_automation"),
    path("controle-nfs/", access_invoices_queue, name="access_invoices_queue"),
    path("fila/excluir/<int:pk>/", delete_invoice, name="delete_invoice"),
    path("fila/editar/<int:pk>/", edit_invoice, name="edit_invoice"),
    path("logs-automacao/", follow_automation_logs, name="follow_automation_logs"),
    path("get-logs/", get_logs, name="get_logs"),
    path("cancelar-processo/", cancel_automation, name="cancel_automation"),
    path("pdfs-pendentes/", get_pending_pdfs, name="get_pending_pdfs"),
    path("aprovar-nota/", approve_pdf, name="approve_pdf"),
    path("downloads/<path:filename>", serve_pdf, name="serve_pdf"),
    path("limpar-logs/", clear_logs, name="clear_logs"),
    path("emitit-nota/<int:invoice_pk>/", create_invoice, name="create_invoice"),
    path("materiais/", list_materials, name="list_materials"),
    path("materiais/cadastro/", add_new_material, name="add_new_material"),
    path("materiais/excluir/<int:pk>/", delete_material, name="delete_material"),
]
