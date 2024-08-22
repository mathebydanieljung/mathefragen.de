import random
import re

from django import template
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template.defaultfilters import stringfilter
from django.utils import timezone
from django.utils.timesince import timesince

from mathefragen.apps.core.utils import generate_cool_number, utcisoformat
from mathefragen.apps.follow.models import UserFollow, QuestionFollow, HashTagFollow
from mathefragen.apps.guardian.models import ReportedPlaylist, ReportedQuestion, ReportedAnswer
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.messaging.models import Message
from mathefragen.apps.playlist.models import Playlist
from mathefragen.apps.promotion.models import RightPromotion
from mathefragen.apps.settings.models import Snippet, SEO
from mathefragen.apps.tips.models import QuestionTip, HelpTip
from mathefragen.apps.user.forms import CompleteProfileForm
from mathefragen.apps.user.models import Profile
from mathefragen.apps.vote.models import Vote, CommentVote

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Template filter to get a value from a dictionary.
    """
    return dictionary.get(key)


@register.filter
def naturaltime_v2(dt):
    if not dt:
        return 'vor langer Zeit'

    # if under a minute, show seconds.
    if dt > timezone.now() - timezone.timedelta(minutes=1):
        return naturaltime(dt)

    # if before a week, we show the date time. easy.
    if dt < timezone.now() - timezone.timedelta(weeks=1):
        return ' %s' % dt.strftime('%d.%m.%Y um %H:%M')

    dt_string = 'vor %s' % timesince(dt)
    return dt_string.replace('Tage', 'Tagen')


@register.filter
def convert_utc_iso(dt):
    return utcisoformat(dt)


@register.simple_tag
def render_favicons():
    site_domain = settings.DOMAIN
    prefix = f"images/favicons/{site_domain}"

    favicon = f"{prefix}/favicon.ico"
    apple_icon = f"{prefix}/apple-touch-icon.png"
    favicon_32 = f"{prefix}/favicon-32x32.png"
    favicon_16 = f"{prefix}/favicon-16x16.png"
    mask_icon = f"{prefix}/safari-pinned-tab.svg"

    return favicon, apple_icon, favicon_32, favicon_16, mask_icon


@register.simple_tag
def render_snippets():
    return Snippet.objects.filter(is_active=True).order_by('-id')


@register.simple_tag
def render_seo():
    return SEO.objects.last()


@register.simple_tag
def define(value=None):
    return value


@register.filter
def concat(text):
    return '_'.join(text.lower().split())


@register.filter
def better_list(text):
    return ', '.join(text.split(','))


@register.filter
def listify(text):
    if not text:
        return []
    return [e.strip() for e in text.split(',') if e.strip()]


@register.simple_tag
def top_week_helpers():
    return Profile.top_helpers()


@register.simple_tag
def top_playlists():
    return Playlist.objects.filter(is_active=True).order_by('?')[:5]


@register.simple_tag
def unread_messages(user):
    # messages from the last 3 weeks ago
    three_weeks_ago = timezone.now() - timezone.timedelta(weeks=3)
    user_read_messages = list(user.user_read_messages.values_list('message_id', flat=True))

    personal_msgs = Message.objects.filter(
        idate__gte=three_weeks_ago,
        to_users__id=user.id
    ).exclude(id__in=user_read_messages).count()

    global_msgs = Message.objects.filter(
        idate__gte=three_weeks_ago,
        to_all=True
    ).exclude(id__in=user_read_messages).count()

    return personal_msgs + global_msgs


@register.filter
@stringfilter
def count_list(words):
    words_list = words.split(',')
    return len(words_list)


@register.filter
@stringfilter
def first_letter(word):
    return word[:1]


@register.filter
@stringfilter
def remove_hash(tag_name):
    return tag_name.replace('#', '')


@register.filter
@stringfilter
def remove_empty_p_tag(html_text):
    cleaned_text = re.sub('<p>&nbsp;</p>', '', html_text)
    cleaned_text = re.sub('<p></p>', '', cleaned_text)
    return cleaned_text


@register.filter
@stringfilter
def toint(value):
    return int(value)


@register.simple_tag
def latest_tags():
    return HashTag.objects.order_by('-id')[:5]


@register.simple_tag
def right_promotions():
    return RightPromotion.objects.all()


@register.simple_tag
def random_question_tip():
    random_queryset = QuestionTip.objects.order_by('?')
    if random_queryset:
        return random_queryset[0].text
    return 'Vergiss nicht, die beste Antwort zu akzeptieren ;)'


@register.filter
def cool_number(value, num_decimals=2):
    """
    Django template filter to convert regular numbers to a
    cool format (ie: 2K, 434.4K, 33M...)
    :param value: number
    :param num_decimals: Number of decimal digits
    """
    final_cool_number = generate_cool_number(value, num_decimals)

    return final_cool_number


@register.simple_tag
def random_helper_tip():
    random_queryset = HelpTip.objects.order_by('?')
    if random_queryset:
        return random_queryset[0].text
    return 'Jeder kann Helfer werden!'


@register.simple_tag
def question_already_up_voted(question_id, user_id):
    if not user_id:
        return False

    if not question_id:
        return False

    return bool(Vote.objects.filter(user_id=user_id, question_id=question_id, type='up').count())


@register.simple_tag
def question_already_down_voted(question_id, user_id):
    if not user_id:
        return False
    if not question_id:
        return False
    return bool(Vote.objects.filter(user_id=user_id, question_id=question_id, type='down').count())


@register.simple_tag
def playlist_already_up_voted(playlist_id, user_id):
    if not user_id:
        return False

    if not playlist_id:
        return False

    return bool(Vote.objects.filter(user_id=user_id, playlist_id=playlist_id, type='up').count())


@register.simple_tag
def playlist_already_down_voted(playlist_id, user_id):
    if not user_id:
        return False
    if not playlist_id:
        return False
    return bool(Vote.objects.filter(user_id=user_id, playlist_id=playlist_id, type='down').count())


@register.simple_tag
def answer_already_up_voted(answer_id, user_id):
    if not user_id:
        return False
    if not answer_id:
        return False
    return bool(Vote.objects.filter(user_id=user_id, answer_id=answer_id, type='up').count())


@register.simple_tag
def comment_voted(comment_id, user_id, object_type):
    if not user_id:
        return False
    if not comment_id:
        return False

    if 'question' in object_type:
        return bool(CommentVote.objects.filter(user_id=user_id, question_comment_id=comment_id).count())
    else:
        return bool(CommentVote.objects.filter(user_id=user_id, answer_comment_id=comment_id).count())


@register.simple_tag
def answer_already_down_voted(answer_id, user_id):
    if not user_id:
        return False
    if not answer_id:
        return False
    return bool(Vote.objects.filter(user_id=user_id, answer_id=answer_id, type='down').count())


@register.simple_tag
def already_question_reported(question_id, user_id):
    if not user_id:
        return True
    if not question_id:
        return False
    return bool(ReportedQuestion.objects.filter(question_id=question_id, reported_by_id=user_id).count())


@register.simple_tag
def already_playlist_reported(playlist_id, user_id):
    if not user_id:
        return True
    if not playlist_id:
        return False
    return bool(ReportedPlaylist.objects.filter(playlist_id=playlist_id, reported_by_id=user_id).count())


@register.simple_tag
def already_answer_reported(answer_id, user_id):
    if not user_id:
        return True
    if not answer_id:
        return False
    return bool(ReportedAnswer.objects.filter(answer_id=answer_id, reported_by_id=user_id).count())


@register.simple_tag
def already_follow_user(request_user, user_to_follow_id):
    if request_user.is_authenticated:
        return bool(UserFollow.objects.filter(follower_id=request_user.id, following_id=user_to_follow_id).count())
    return False


@register.simple_tag
def already_follow_question(request_user, question_id):
    if request_user.is_authenticated:
        return bool(QuestionFollow.objects.filter(follower_id=request_user.id, question_id=question_id).count())
    return False


@register.simple_tag
def already_follow_hashtag(request_user, hashtag_id):
    if request_user.is_authenticated:
        return bool(HashTagFollow.objects.filter(follower_id=request_user.id, hashtag_id=hashtag_id).count())
    return False


@register.simple_tag
def already_reviewed(request_user, given_to_user_id):
    if request_user.is_authenticated:
        return bool(request_user.given_user_reviews.filter(given_to_id=given_to_user_id).count())
    return False


@register.simple_tag
def has_unread_release_notes(request_user):
    if not request_user.is_authenticated:
        return False
    return request_user.profile.has_unread_updates()


@register.simple_tag
def has_read_release_note(request_user, release_note_id):
    if not request_user.is_authenticated:
        return True
    return request_user.user_read_release_notes.filter(release_note_id=release_note_id).count() > 0


@register.simple_tag
def has_new_playlists(request_user):
    if not request_user.is_authenticated:
        return False
    return request_user.profile.has_unseen_playlists()


@register.simple_tag
def number_playlists():
    return Playlist.objects.filter(is_active=True).count()


@register.simple_tag
def has_seen_playlist(request_user, playlist_id):
    if not request_user.is_authenticated:
        return True
    return request_user.profile.has_seen_playlist(playlist_id=playlist_id)


@register.simple_tag
def render_complete_profile_form(request):
    if not request.user.is_authenticated:
        return

    incomplete_fields = request.user.profile.incomplete_fields
    if not incomplete_fields:
        return

    random_field = random.choice(incomplete_fields)
    fields_to_save = CompleteProfileForm.CHUNKS.get(random_field)

    form = CompleteProfileForm()
    for name, field in form.fields.items():
        if name not in fields_to_save:
            field.widget = field.hidden_widget()

    return form, ','.join(fields_to_save)


@register.simple_tag
def uni_module_selected(user, module_name):
    if not user.is_authenticated:
        return False

    if not hasattr(user, 'tutor_setting'):
        return False

    university_modules = user.tutor_setting.university_modules.split(',')
    return module_name in university_modules
