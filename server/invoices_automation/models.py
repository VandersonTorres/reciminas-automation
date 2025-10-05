from django.db import models
from django.contrib.auth.models import User


# Invoices waiting to emit.
class EntryInvoiceQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255)
    material_code = models.CharField(
        max_length=50,
        choices=[
            ("", "Selecione"),
            ("50", "Sucata de Cobre"),
            ("51", "Sucata de Latão"),
            ("52", "Sucata de Alumínio"),
            ("64", "Sucata de Ferro"),
        ],
    )
    material_quantity = models.FloatField()
    material_price = models.FloatField()
    discount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pendente"),
            ("processing", "Processando"),
            ("cancelled", "Cancelada"),
            ("done", "Emitida"),
        ],
        default="pending",
    )

    def __str__(self):
        return f"{self.provider} ({self.material_code})"


# TODO: Emitted Invoices
# class EntryInvoiceResult(models.Model):
#     queue_item = models.OneToOneField(EntryInvoiceQueue, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     pdf_file = models.FileField(upload_to="invoices/pdfs/", null=True, blank=True)
#     screenshot = models.ImageField(upload_to="invoices/screenshots/", null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
