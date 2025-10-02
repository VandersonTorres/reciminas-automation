from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


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


# Entry Invoices Emission Form
class EntryInvoiceForm(forms.Form):
    provider = forms.CharField(
        label="Fornecedor",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome completo"}),
    )
    material_code = forms.ChoiceField(
        label="Material",
        choices=[
            ("", "Selecione"),
            ("50", "Sucata de Cobre"),
            ("51", "Sucata de Latão"),
            ("52", "Sucata de Alumínio"),
            ("64", "Sucata de Ferro"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    material_quantity = forms.DecimalField(
        label="Quantidade (Kg)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ex: 10.2"}),
    )
    material_price = forms.DecimalField(
        label="Preço Unitário (R$)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ex: 50.10"}),
    )
    discount = forms.DecimalField(
        label="Desconto (R$)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ex: 0"}),
    )
