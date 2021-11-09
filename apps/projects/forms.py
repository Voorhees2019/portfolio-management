from django import forms
from django_select2.forms import Select2MultipleWidget
from apps.accounts.models import User
from import_export.forms import ImportForm, ConfirmImportForm
from .models import Project


class CustomImportForm(ImportForm):
    author = forms.ModelChoiceField(queryset=User.objects.all(), required=True)


class CustomConfirmImportForm(ConfirmImportForm):
    author = forms.ModelChoiceField(queryset=User.objects.all(), required=True, widget=forms.HiddenInput())


class ProjectForm(forms.ModelForm):
    description = forms.CharField(label="Description", widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Project
        fields = ['title', 'description', 'industries', 'technologies', 'url', 'url_is_active', 'is_private']
        widgets = {
            'industries': Select2MultipleWidget,
            'technologies': Select2MultipleWidget,
        }
