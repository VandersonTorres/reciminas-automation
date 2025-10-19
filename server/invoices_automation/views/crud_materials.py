from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from invoices_automation.models import Material
from invoices_automation.forms import MaterialForm


@login_required
def list_materials(request):
    materials = Material.objects.all().order_by("name")
    return render(request, "materials/materials_list.html", {"materials": materials})


@login_required
def add_new_material(request):
    if request.method == "POST":
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Material adicionado com sucesso!")
            return redirect("list_materials")
    else:
        form = MaterialForm()
    return render(request, "materials/add_material.html", {"form": form})


@login_required
def delete_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    try:
        material.delete()
        messages.success(request, "🗑️ Material excluído com sucesso!")
    except Exception:
        messages.error(request, "❌ Não foi possível excluir este material, ele provavelmente está em uso.")
    return redirect("list_materials")
