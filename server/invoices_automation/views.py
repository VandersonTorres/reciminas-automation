from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.shortcuts import render, redirect

from .forms import CustomUserCreationForm


class CustomLogoutView(LogoutView):
    template_name = "logout.html"


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # noqa: F841
            messages.success(request, "Cadastro enviado! Aguarde a aprovação do administrador.")
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})


@login_required
def dashboard(request):
    return render(request, "dashboard.html")
