from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, **kwargs):
    user = kwargs['instance']
    if kwargs['created']:
        profile = Profile(user=user)
        profile.points = 10
        profile.verified = False
        profile.save()


@receiver(post_delete, sender=Profile)
def delete_user(sender, instance=None, **kwargs):
    try:
        instance.user
    except User.DoesNotExist:
        pass
    else:
        # answers
        instance.user.delete()


@receiver(post_delete, sender=Profile)
def delete_profile_image(sender, instance=None, **kwargs):
    # Django löscht Dateien nicht mit dem Datensatz; erst nach Commit, damit ein Rollback das Bild nicht kostet.
    image = instance.profile_image
    if image:
        transaction.on_commit(lambda: image.storage.delete(image.name), robust=True)


@receiver(pre_delete, sender=Profile)
def delete_user_traces(sender, instance=None, **kwargs):
    # delete all IP Addresses of this user from his entries.
    instance.remove_ip_trace()
    instance.update_question_speed_fields(reset=True)

    # remove questions of this user from main feed, to make space for active questions
    instance.close_user_questions()
