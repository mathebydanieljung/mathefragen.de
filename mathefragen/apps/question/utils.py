import math

from django.db.models import Count
from django.utils import timezone

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
