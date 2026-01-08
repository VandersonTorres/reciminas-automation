from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


# Material Support Model
class Material(models.Model):
    code = models.CharField(
        max_length=50, unique=True, validators=[RegexValidator(r"^\d+$", "O código deve conter apenas números.")]
    )
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.code})"


# Invoice Model
class EntryInvoiceQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255)
    close_popup = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pendente"),
            ("processing", "Processando"),
            ("cancelled", "Cancelada"),
            ("done", "Transmitida"),
        ],
        default="pending",
    )
    invoice_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.provider} - {self.id}"


class EntryInvoiceItem(models.Model):
    invoice = models.ForeignKey(EntryInvoiceQueue, related_name="items", on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    material_quantity = models.FloatField()
    material_price = models.FloatField()
    discount = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.material.name} - {self.material_quantity}kg"
