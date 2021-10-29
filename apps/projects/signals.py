from django.db.models.signals import post_delete, m2m_changed
from .models import Project
from django.dispatch import receiver


@receiver(post_delete, sender=Project)
def delete_document(sender, instance, **kwargs):
    from .utils import delete_elastic_document
    delete_elastic_document(instance)


@receiver(m2m_changed, sender=Project.industries.through)
def update_document(sender, instance, **kwargs):
    from .utils import update_elastic_document
    update_elastic_document(instance)


@receiver(m2m_changed, sender=Project.technologies.through)
def update_document(sender, instance, **kwargs):
    from .utils import update_elastic_document
    update_elastic_document(instance)
