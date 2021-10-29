import json
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime
from apps.accounts.models import User


class Industry(models.Model):
    title = models.CharField(_('Title'), max_length=150)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name_plural = 'Industries'


class Technology(models.Model):
    title = models.CharField(_('Title'), max_length=80)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name_plural = 'Technologies'


class Project(models.Model):
    title = models.CharField(_('Project name'), max_length=150)
    description = models.TextField(_('Description'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_projects')
    industries = models.ManyToManyField(Industry)
    technologies = models.ManyToManyField(Technology)
    url = models.URLField(_('Project website'), null=True, blank=True)
    url_is_active = models.BooleanField(_('Website is active'), default=False)
    created_at = models.DateTimeField(_('Date created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date updated'), auto_now=True)
    is_private = models.BooleanField(_('Private'), default=True)

    def get_elasticsearch_document(self):
        doc = {
            'title': self.title,
            'description': self.description,
            'industries': list(self.industries.values_list("id", flat=True)),
            'technologies': list(self.technologies.values_list("id", flat=True)),
        }
        return json.dumps(doc)

    def save(self, *args, **kwargs):
        from .utils import update_elastic_document
        super().save(*args, **kwargs)
        update_elastic_document(self)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name_plural = 'Projects'


class Company(models.Model):
    name = models.CharField(_('Company name'), max_length=150)
    logo = models.ImageField(_('Company logo'), upload_to='company_logos/')
    founder = models.OneToOneField(User, on_delete=models.CASCADE, related_name='founder_company')
    year_founded = models.IntegerField(validators=[MinValueValidator(1950), MaxValueValidator(datetime.now().year)])
    website = models.URLField(_('Company website'))
    email = models.EmailField(_('Contact email'), max_length=255, unique=True)
    slogan = models.CharField(_('Company slogan'), max_length=255)
    description = models.TextField(_('Description'))

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name_plural = 'Companies'
