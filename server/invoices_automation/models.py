from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


# Material Support Model
class Material(models.Model):
    code = models.CharField(
        max_length=50, unique=True, validators=[RegexValidator(r"^\d+$", "O código deve conter apenas números.")]
    )
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.code})"


# Invoice Model Base
class BaseInvoiceModel(models.Model):

    class Meta:
        abstract = True

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


# Entry Invoice
class EntryInvoiceQueue(BaseInvoiceModel):
    items = GenericRelation("InvoiceItem")

    def __str__(self):
        return f"{self.provider} - {self.id} (Entrada)"


# Exit Invoice
class ExitInvoiceQueue(BaseInvoiceModel):
    items = GenericRelation("InvoiceItem")

    freight = models.CharField(
        max_length=255,
        choices=[
            ("0", "Contratado p/ conta Remetente (CIF)"),
            ("1", "Contratado p/ conta Destinatário (FOB)"),
            ("2", "Contratado p/ conta Terceiros"),
            ("3", "Próprio p/ conta Remetente"),
            ("4", "Próprio p/ conta Destinatário"),
            ("9", "Sem Frete"),
        ],
    )
    search_carrier_by = models.CharField(
        max_length=50,
        choices=[
            ("code", "Código"),
            ("name", "Nome"),
        ],
        default="code",
    )
    carrier_name = models.CharField(max_length=255, null=True, blank=True)
    carrier_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        validators=[RegexValidator(r"^\d+$", "O código deve conter apenas números.")],
    )
    observation = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.provider} - {self.id} (Saída)"

    def clean(self):
        super().clean()
        if self.search_carrier_by == "code" and not self.carrier_code:
            raise ValidationError({"carrier_code": "Informe o código do transportador."})
        if self.search_carrier_by == "name" and not self.carrier_name:
            raise ValidationError({"carrier_name": "Informe o nome do transportador."})


# Generic Invoice Item
class InvoiceItem(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    invoice = GenericForeignKey("content_type", "object_id")
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    material_quantity = models.FloatField()
    material_price = models.FloatField()
    discount = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.material.name} - {self.material_quantity}kg"
