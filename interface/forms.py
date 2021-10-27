"""
forms.py: describes the strucutre and definition of the forms used in the application
"""
from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import userModel
from .helper import get_or_none, validate_password

import pandas as pd

## Registration form for new users
class RegisterForm(forms.Form):
    first_name = forms.CharField(label=_('First Name'), widget=forms.TextInput())
    last_name = forms.CharField(label=_('Last Name'), widget=forms.TextInput())
    works_at = forms.CharField(label=_('Organization'), widget=forms.TextInput())
    email = forms.EmailField(widget=forms.EmailInput())
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(), help_text=mark_safe("Passwords are to be atleast 7 characters long and containing 1 letter and 1 number"))

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        self._validate_password_strength(self.cleaned_data.get('password'))
        return password

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user = get_or_none(userModel, email=email)
        if user is not None:
            raise ValidationError(_("User with the same email is already registered"))
        return email

    def _validate_password_strength(self, value):
        validate_password(value)

    def save(self, commit=True):
        user = userModel.objects.create_user(
                first_name=self.cleaned_data.get('first_name'),
                last_name=self.cleaned_data.get('last_name'),
                email=self.cleaned_data.get('email'),
                works_at=self.cleaned_data.get('works_at'),
                password=self.cleaned_data.get('password'))
        if commit:
            user.save()
        return user


## User login form
class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': '', 'autofocus': ''}))
    password = forms.CharField(
        widget=forms.PasswordInput()
        )

## Form for users to update their account information
class EditUserForm(forms.ModelForm):
    class Meta:
        model = userModel
        fields = ('first_name', 'last_name')
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'works_at': 'Organization',
        }

