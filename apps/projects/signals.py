from django.db.models.signals import post_delete, pre_delete, m2m_changed
from .models import Project, CSVFile, Set
from django.dispatch import receiver


@receiver(post_delete, sender=Project)
def delete_document(sender, instance, **kwargs):
    from .utils import delete_elastic_document
    delete_elastic_document(instance)


@receiver(m2m_changed, sender=Project.industries.through)
@receiver(m2m_changed, sender=Project.technologies.through)
def update_document(sender, instance, action, **kwargs):
    if action == 'post_add':
        refresh_index = getattr(instance, '_refresh_index', True)
        dry_index_update = getattr(instance, '_dry_index_update', False)
        instance.save(refresh_index=refresh_index, dry_index_update=dry_index_update)


@receiver(pre_delete, sender=CSVFile)
def delete_csv_file(sender, instance, **kwargs):
    """Must delete .csv file from storage here but not in model's `delete()` method because when deleting objects
    from admin panel, django uses `bulk_delete()` on a queryset and doesn't call `delete()` method for each instance"""
    instance.csv_file.delete()


@receiver(pre_delete, sender=Set)
def delete_set(sender, instance, **kwargs):
    for project in instance.projects.all():
        if not project.original:
            project.delete()
