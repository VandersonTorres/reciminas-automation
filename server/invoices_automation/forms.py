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
