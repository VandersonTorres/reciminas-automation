from django.contrib.auth import views as auth_views
from django.urls import path

from invoices_automation.forms import CustomAuthenticationForm
from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html", authentication_form=CustomAuthenticationForm),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("registro/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("gerenciamento-nf-de-entrada/", views.entry_invoices_management, name="entry_invoices_management"),
    path("emissoes-nf-de-entrada/", views.start_batch_automation, name="start_batch_automation"),
    path("fila-de-nfs/", views.invoice_queue, name="invoice_queue"),
    path("fila/excluir/<int:pk>/", views.delete_invoice, name="delete_invoice"),
    path("fila/editar/<int:pk>/", views.edit_invoice, name="edit_invoice"),
    path("logs-automacao/", views.automation_logs, name="automation_logs"),
    path("get-logs/", views.get_logs, name="get_logs"),
    path("cancelar-processo/", views.cancel_automation, name="cancel_automation"),
]
