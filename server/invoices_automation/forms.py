from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import EntryInvoiceQueue, Material


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
        fields = ["provider", "material", "material_quantity", "material_price", "discount"]
        labels = {
            "provider": "Fornecedor",
            "material": "Material",
            "material_quantity": "Quantidade (Kg)",
            "material_price": "Preço Unitário (R$)",
            "discount": "Desconto (R$)",
        }
        widgets = {
            "provider": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome completo"}),
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

    def clean_material_quantity(self):
        value = self.cleaned_data["material_quantity"]
        if value < 0:
            raise forms.ValidationError("A quantidade não pode ser negativa.")
        return value

    def clean_material_price(self):
        value = self.cleaned_data["material_price"]
        if value < 0:
            raise forms.ValidationError("O preço não pode ser negativo.")
        return value

    def clean_discount(self):
        value = self.cleaned_data.get("discount", 0)
        if value < 0:
            raise forms.ValidationError("O desconto não pode ser negativo.")
        return value
