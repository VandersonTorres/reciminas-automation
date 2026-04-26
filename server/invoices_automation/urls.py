from django.contrib.auth import views as auth_views
from django.urls import path

from invoices_automation.forms import CustomAuthenticationForm
from invoices_automation.views.core import dashboard, register
from invoices_automation.views.manage_emission_approval import approve_pdf, get_pending_pdfs, serve_pdf
from invoices_automation.views.entry_module.crud_entry_invoices import (
    create_entry_invoice,
    access_entry_invoices_queue,
    edit_entry_invoice,
    delete_entry_invoice,
)
from invoices_automation.views.exit_module.create_instate_invoice import create_instate_sale_invoice
from invoices_automation.views.exit_module.create_outstate_invoice import create_outstate_sale_invoice
from invoices_automation.views.exit_module.create_stock_transfer_invoice import create_stock_transfer_invoice
from invoices_automation.views.exit_module.crud_exit_invoices import (
    access_exit_invoices_queue,
    edit_exit_invoice,
    delete_exit_invoice,
)
from invoices_automation.views.manage_automation_process import (
    emit_invoice,
    start_batch_automation,
    cancel_automation,
    follow_automation_logs,
    get_logs,
    clear_logs,
)
from invoices_automation.views.crud_materials import (
    list_materials,
    add_new_material,
    delete_material,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html", authentication_form=CustomAuthenticationForm),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("cadastro/", register, name="register"),
    path("aprovar-nota/", approve_pdf, name="approve_pdf"),
    path("pdfs-pendentes/", get_pending_pdfs, name="get_pending_pdfs"),
    path("downloads/<path:filename>", serve_pdf, name="serve_pdf"),
    path("registro-nf-entrada/", create_entry_invoice, name="create_entry_invoice"),
    path("controle-nfs-entrada/", access_entry_invoices_queue, name="access_entry_invoices_queue"),
    path("fila/editar/entrada/<int:pk>/", edit_entry_invoice, name="edit_entry_invoice"),
    path("fila/excluir/entrada/<int:pk>/", delete_entry_invoice, name="delete_entry_invoice"),
    path("registro-nf-venda-dentro-do-estado/", create_instate_sale_invoice, name="create_instate_sale_invoice"),
    path("registro-nf-venda-fora-do-estado/", create_outstate_sale_invoice, name="create_outstate_sale_invoice"),
    path("registro-nf-transferencia-estoque/", create_stock_transfer_invoice, name="create_stock_transfer_invoice"),
    path("controle-nfs-saida/", access_exit_invoices_queue, name="access_exit_invoices_queue"),
    path("fila/editar/saida/<int:pk>/", edit_exit_invoice, name="edit_exit_invoice"),
    path("fila/excluir/saida/<int:pk>/", delete_exit_invoice, name="delete_exit_invoice"),
    path("cancelar-processo/", cancel_automation, name="cancel_automation"),
    path("emitir-nota/<int:invoice_pk>/", emit_invoice, name="emit_invoice"),
    path("emissoes-nfs/", start_batch_automation, name="start_batch_automation"),
    path("logs-automacao/", follow_automation_logs, name="follow_automation_logs"),
    path("get-logs/", get_logs, name="get_logs"),
    path("limpar-logs/", clear_logs, name="clear_logs"),
    path("materiais/", list_materials, name="list_materials"),
    path("materiais/cadastro/", add_new_material, name="add_new_material"),
    path("materiais/excluir/<int:pk>/", delete_material, name="delete_material"),
]
