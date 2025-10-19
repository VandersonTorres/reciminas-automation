from django.apps import AppConfig
from django.db.models.signals import post_migrate


class InvoicesAutomationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "invoices_automation"

    def ready(self):
        from .models import Material

        def create_default_materials(sender, **kwargs):
            defaults = [
                ("50", "Sucata de Cobre"),
                ("51", "Sucata de Latão"),
                ("52", "Sucata de Alumínio"),
                ("64", "Sucata de Ferro"),
            ]
            for code, name in defaults:
                Material.objects.get_or_create(code=code, defaults={"name": name})

        post_migrate.connect(create_default_materials, sender=self)
