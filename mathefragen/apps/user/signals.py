from django.contrib.auth.models import User
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


@receiver(pre_delete, sender=Profile)
def delete_user_traces(sender, instance=None, **kwargs):
    # delete all IP Addresses of this user from his entries.
    instance.remove_ip_trace()
    instance.update_question_speed_fields(reset=True)

    # remove questions of this user from main feed, to make space for active questions
    instance.close_user_questions()


@receiver(pre_delete, sender=User)
def delete_user_socials(sender, instance=None, **kwargs):
    # delete old social auth if exists
    # UserSocialAuth.objects.filter(user=instance).delete()
    pass
