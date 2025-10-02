from django.contrib.auth import views as auth_views
from django.urls import path

from invoices_automation.forms import CustomAuthenticationForm
from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html", authentication_form=CustomAuthenticationForm),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
