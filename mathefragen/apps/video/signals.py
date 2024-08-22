from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Video


@receiver(pre_delete, sender=Video)
def remove_file_from_s3(sender, **kwargs):
    instance = kwargs['instance']
    instance.file.delete(save=False)
    instance.original_size.delete(save=False)
