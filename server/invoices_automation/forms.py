from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import EntryInvoiceQueue, EntryInvoiceItem, Material, ExitInvoiceQueue, ExitInvoiceItem


# Login Form
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Nome do usuário", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={"class": "form-control"}))


# Sign Up Form
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Digite seu e-mail"}),
    )

    password1 = forms.CharField(
        label="Senha", widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Digite sua senha"})
    )

    password2 = forms.CharField(
        label="Confirme a senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirme sua senha"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "Nome de usuário",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Digite seu nome de usuário"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False  # Will be active after approval
        if commit:
            user.save()
        return user


# Material Form
class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["code", "name"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Código"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome do material"}),
        }


# Entry Invoices Emission Form
class EntryInvoiceForm(forms.ModelForm):
    class Meta:
        model = EntryInvoiceQueue
        fields = ["provider"]
        labels = {"provider": "Fornecedor"}
        widgets = {
            "provider": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome completo"}),
        }


class EntryInvoiceItemForm(forms.ModelForm):
    class Meta:
        model = EntryInvoiceItem
        fields = ["material", "material_quantity", "material_price", "discount"]
        labels = {
            "material": "Material",
            "material_quantity": "Quantidade (Kg)",
            "material_price": "Preço Unitário (R$)",
            "discount": "Desconto (R$)",
        }
        widgets = {
            "material": forms.Select(attrs={"class": "form-select"}),
            "material_quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "Ex: 10.2"}
            ),
            "material_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "Ex: 50.10"}
            ),
            "discount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "Ex: 0"}
            ),
        }

    def clean(self):
        cleaned = super().clean()

        material = cleaned.get("material")
        q = cleaned.get("material_quantity")
        p = cleaned.get("material_price")
        d = cleaned.get("discount") or 0

        if any(v in [None, ""] for v in [material, q, p]):
            raise forms.ValidationError("Preencha todos os campos do material.")

        if any(v <= 0 for v in [q, p]):
            raise forms.ValidationError("Quantidade e preço devem ser maiores que zero.")

        if d < 0:
            raise forms.ValidationError("O desconto não pode ser negativo.")

        return cleaned


EntryInvoiceItemFormSet = inlineformset_factory(
    EntryInvoiceQueue,
    EntryInvoiceItem,
    form=EntryInvoiceItemForm,
    extra=1,
    can_delete=True,
)


# Exit Invoices Emission Form
class ExitInvoiceForm(forms.ModelForm):
    freight = forms.CharField(required=False, initial="0")
    search_carrier_by = forms.CharField(required=False, initial="code")

    CARRIER_CODE_CHOICES = [
        ("18", "18 - RECIMINAS"),
        ("25", "25 - SUCATRANS"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get("modality") == "exit_stock_transfer" or (
            self.instance and getattr(self.instance, "modality", None) == "exit_stock_transfer"
        ):
            self.fields["carrier_code"].widget = forms.Select(
                choices=self.CARRIER_CODE_CHOICES, attrs={"class": "form-select"}
            )
            self.observation = forms.CharField(required=False, initial="")

    class Meta:
        model = ExitInvoiceQueue
        fields = [
            "modality",
            "provider",
            "freight",
            "search_carrier_by",
            "carrier_name",
            "carrier_code",
            "observation",
        ]
        labels = {
            "modality": "Modalidade",
            "provider": "Fornecedor",
            "freight": "Tipo de Frete",
            "search_carrier_by": "Buscar Transportador por",
            "carrier_name": "Nome do Transportador",
            "carrier_code": "Código do Transportador",
            "observation": "Observação",
        }
        widgets = {
            "modality": forms.Select(attrs={"class": "form-select"}),
            "provider": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome completo"}),
            "freight": forms.Select(attrs={"class": "form-select"}),
            "search_carrier_by": forms.Select(attrs={"class": "form-select"}),
            "carrier_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome do transportador"}),
            "carrier_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Código do transportador"}),
            "observation": forms.Textarea(attrs={"class": "form-control", "placeholder": "Observações", "rows": 2}),
        }


class ExitInvoiceItemForm(forms.ModelForm):
    discount = forms.FloatField(required=False, initial=0)

    class Meta:
        model = ExitInvoiceItem
        fields = ["material", "material_quantity", "material_price", "discount"]
        labels = {
            "material": "Material",
            "material_quantity": "Quantidade (Kg)",
            "material_price": "Preço Unitário (R$)",
            "discount": "Desconto (R$)",
        }
        widgets = {
            "material": forms.Select(attrs={"class": "form-select"}),
            "material_quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "Ex: 10.2"}
            ),
            "material_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "Ex: 50.10"}
            ),
            "discount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "Ex: 0"}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        material = cleaned.get("material")
        q = cleaned.get("material_quantity")
        p = cleaned.get("material_price")
        d = cleaned.get("discount") or 0
        if any(v in [None, ""] for v in [material, q, p]):
            raise forms.ValidationError("Preencha todos os campos do material.")
        if any(v <= 0 for v in [q, p]):
            raise forms.ValidationError("Quantidade e preço devem ser maiores que zero.")
        if d < 0:
            raise forms.ValidationError("O desconto não pode ser negativo.")
        return cleaned


ExitInvoiceItemFormSet = inlineformset_factory(
    ExitInvoiceQueue,
    ExitInvoiceItem,
    form=ExitInvoiceItemForm,
    extra=1,
    can_delete=True,
)
