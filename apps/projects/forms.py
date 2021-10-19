from django import forms
from apps.accounts.models import User
from import_export.forms import ImportForm, ConfirmImportForm


class CustomImportForm(ImportForm):
    author = forms.ModelChoiceField(queryset=User.objects.all(), required=True)


class CustomConfirmImportForm(ConfirmImportForm):
    author = forms.ModelChoiceField(queryset=User.objects.all(), required=True, widget=forms.HiddenInput())
