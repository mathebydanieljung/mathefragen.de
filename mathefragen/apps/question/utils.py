import re

import math
from django.db.models import Count
from django.utils import timezone
from google.cloud import vision

from mathefragen.apps.question.models import Answer, Question
from mathefragen.apps.settings.models import Performance


def filter_questions(question_filter, user_id, answered_user_id, page):
    def paginated_questions(questions_, page_):
        number_questions = questions_.count()
        max_page = int(math.ceil(number_questions / 20.0))
        max_page = 1 if max_page < 1 else max_page
        if page_ > max_page:
            page_ = max_page
        return number_questions, questions[20 * (page - 1): 20 * page], max_page, page_

    if user_id:
        questions = Question.objects.filter(user_id=int(user_id), soft_deleted=False).order_by('-rank_date')
        return paginated_questions(questions, page)

    if answered_user_id:
        question_ids = list(Answer.objects.filter(user_id=int(answered_user_id)).values_list('question_id', flat=True))
        questions = Question.objects.filter(id__in=question_ids, soft_deleted=False).order_by('-rank_date')
        return paginated_questions(questions, page)

    if question_filter == 'no_accept':
        # questions with no answer acceptance.
        questions = Question.objects.exclude(type='article').annotate(
            answers=Count('question_answers')
        ).filter(answers__gte=1, closed=False, soft_deleted=False).order_by('-rank_date')
        return paginated_questions(questions, page)

    if question_filter == 'article':
        questions = Question.objects.filter(type='article', soft_deleted=False).order_by('-rank_date')
        return paginated_questions(questions, page)

    if question_filter == 'no_answer':
        questions = Question.objects.filter(
            number_answers__lt=1,
            type='question',
            is_active=True,
            closed=False,
            soft_deleted=False
        ).order_by('-rank_date')
        return paginated_questions(questions, page)

    performance = Performance.objects.last()

    if performance and not performance.feed_3_days or question_filter == 'show_all':
        questions = Question.objects.filter(
            type='question', soft_deleted=False, is_active=True
        ).order_by('-rank_date')
    else:
        two_weeks = timezone.now() - timezone.timedelta(days=3)
        questions = Question.objects.filter(
            type='question', rank_date__gte=two_weeks, soft_deleted=False, is_active=True
        ).order_by('-rank_date')

    return paginated_questions(questions, page)


class ImageSafety:

    def __init__(self, text='', image_content=''):
        self.text = text
        self.image_content = image_content
        self.image_uris = list()
        if self.text:
            pattern = r'src="(.*?)"'
            image_urls = re.findall(pattern, self.text)
            for image_uri in image_urls:
                if 'http' in image_uri:
                    self.image_uris.append(image_uri)

    def check_for_safety(self):
        # if no image found, text should be safe. for now. Later we analyze text also.
        if not self.image_uris and not self.image_content:
            return True

        checklist = list()
        if self.image_uris:
            for uri in self.image_uris:
                is_safe = self._google_detect_safe_search(image_uri=uri)
                checklist.append(is_safe)

        if self.image_content:
            is_safe = self._google_detect_safe_search(image_content=self.image_content)
            checklist.append(is_safe)

        return all(checklist)

    @staticmethod
    def _google_detect_safe_search(image_uri='', image_content=''):
        """Google. Detects unsafe features in the file."""

        client = vision.ImageAnnotatorClient()
        if image_content:
            image = vision.Image(content=image_content)
        else:
            image = vision.Image()
            image.source.image_uri = image_uri

        response = client.safe_search_detection(image=image)
        if response.error.message:
            return False

        safe = response.safe_search_annotation

        adult = safe.adult.value
        medical = safe.medical.value
        spoof = safe.spoof.value
        violence = safe.violence.value
        racy = safe.racy.value

        # UNKNOWN = 0, VERY_UNLIKELY = 1, UNLIKELY = 2, POSSIBLE = 3, LIKELY = 4, VERY_LIKELY = 5
        image_is_fine = all([adult < 3, medical < 3, spoof < 3, violence < 3, racy < 3])

        if not image_is_fine:
            # capture_event('nsfw image detected')
            pass

        return image_is_fine
