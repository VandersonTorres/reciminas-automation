from django.db import models
from django.contrib.auth.models import User
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

    modality = models.CharField(
        max_length=50,
        choices=[
            ("entry", "Entrada"),
            ("exit_instate", "Venda Comum (Dentro do Estado)"),
            ("exit_outstate", "Venda Comum (Fora do Estado)"),
            ("exit_stock_transfer", "Saída (Transferência de Estoque)"),
            ("exit_triangular_sale", "Saída (Venda Triangular)"),
        ],
    )
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
    modality = "entry"

    def __str__(self):
        return f"{self.provider} - {self.id} (Entrada)"


class EntryInvoiceItem(models.Model):
    invoice = models.ForeignKey(EntryInvoiceQueue, related_name="items", on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    material_quantity = models.FloatField()
    material_price = models.FloatField()
    discount = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.material.name} - {self.material_quantity}kg"


# Exit Invoice
class ExitInvoiceQueue(BaseInvoiceModel):
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
        default="0",
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


class ExitInvoiceItem(models.Model):
    invoice = models.ForeignKey(ExitInvoiceQueue, related_name="items", on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    material_quantity = models.FloatField()
    material_price = models.FloatField()
    discount = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.material.name} - {self.material_quantity}kg"
