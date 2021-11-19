from django import forms
from django_select2.forms import Select2MultipleWidget
from apps.accounts.models import User
from import_export.forms import ImportForm, ConfirmImportForm
from .models import Project, Set


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


class InSetEditProjectForm(ProjectForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'industries', 'technologies', 'url', 'url_is_active']
        widgets = {
            'industries': Select2MultipleWidget,
            'technologies': Select2MultipleWidget,
        }


class SetForm(forms.ModelForm):
    name = forms.CharField(label="", widget=forms.TextInput(attrs={'class': "form-control my-3"}))

    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        from django.core.exceptions import ValidationError
        cleaned_name = self.cleaned_data.get('name')
        if Set.objects.filter(name=cleaned_name, author=self.author).exists():
            raise ValidationError('Set with such name already exists')
        return cleaned_name

    class Meta:
        model = Set
        fields = ['name']
