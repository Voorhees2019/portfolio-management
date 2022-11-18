from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Company


@receiver(pre_delete, sender=Company)
def delete_company_logo_image(sender, instance, **kwargs):
    """
    Must delete company logo images from storage here but not in model's `delete()` method because
    when deleting objects from admin panel, django uses `bulk_delete()` on a queryset
    and doesn't call `delete()` method for each instance.
    """
    instance.logo.delete()
