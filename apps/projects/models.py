import json
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import ArrayField
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
    industries = models.ManyToManyField(Industry, related_name='projects_containing_industry')
    technologies = models.ManyToManyField(Technology, related_name='projects_containing_technology')
    url = models.URLField(_('Project website'), null=True, blank=True)
    url_is_active = models.BooleanField(_('Website is active'), default=False)
    created_at = models.DateTimeField(_('Date created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date updated'), auto_now=True)
    is_private = models.BooleanField(_('Project is private'), default=True)
    is_original = models.BooleanField(_('Project is original'), default=True)

    def get_elasticsearch_document(self):
        doc = {
            'title': self.title,
            'description': self.description,
            'author': self.author.id,
            'project_id': self.id,
            'is_private': self.is_private,
            'industries': list(self.industries.values_list("id", flat=True)),
            'technologies': list(self.technologies.values_list("id", flat=True)),
        }
        return json.dumps(doc)

    def save(self, *args, **kwargs):
        refresh_index = kwargs.pop('refresh_index', True)
        # Control admin import csv. Do not create elastic documents if
        # transaction will rollback (first dry_run import to preview changes)
        dry_index_update = kwargs.pop('dry_index_update', False)

        self._refresh_index = refresh_index
        self._dry_index_update = dry_index_update  # to control signal m2m_changed

        super().save(*args, **kwargs)

        if not dry_index_update:
            from .utils import update_elastic_document
            update_elastic_document(self, refresh_index=refresh_index)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name_plural = 'Projects'


class CSVFile(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('Date created'), auto_now_add=True)
    csv_file = models.FileField(upload_to="csv_files")

    def __str__(self):
        return f'CSV file #{self.id}'

    class Meta:
        verbose_name_plural = 'CSV Files'


class Set(models.Model):
    name = models.CharField(_('Set name'), max_length=150)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_sets')
    projects = models.ManyToManyField(Project, related_name='sets_containing_project')
    created_at = models.DateTimeField(_('Date created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date updated'), auto_now=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name_plural = 'Sets'
        unique_together = ('name', 'author')
        ordering = ['-id']


class SetSharedLink(models.Model):
    set = models.ForeignKey(Set, on_delete=models.CASCADE, related_name='set_shared_link')
    token = models.CharField(_('Shared link'), max_length=255, unique=True)
    ip_addresses = ArrayField(models.CharField(max_length=255, blank=True), default=list)
    opening_counter = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(_('Date created'), auto_now_add=True)

    def __str__(self):
        return f'Shared link for Set "{self.set.name}"'

    class Meta:
        verbose_name_plural = 'Sets Shared Links'
