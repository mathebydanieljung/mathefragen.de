import json
import math

from django.shortcuts import render, HttpResponse

from mathefragen.apps.question.models import Question
from mathefragen.apps.hashtag.models import HashTag


def questions_with_tag(request):
    tag_name = request.GET.get('tag')
    if not tag_name:
        tag_name = 'mathematik'

    hashtag_object = HashTag.objects.filter(name__iexact=tag_name).last()
    questions = Question.objects.all()

    if hashtag_object:
        questions = hashtag_object.questions.filter(type='question').order_by('-rank_date')

    number_of_questions = questions.count()

    try:
        page = request.GET.get('page', 1)
        if isinstance(page, str):
            page = page.replace('/', '')
        page = int(page)
    except ValueError:
        page = 1

    page = 1 if page < 1 else page

    max_page = int(math.ceil(questions.count() / 15.0))
    max_page = 1 if max_page < 1 else max_page

    if page > max_page:
        page = max_page

    questions = questions[15 * (page - 1): 15 * page]

    return render(request, 'index.html', {
        'tag': hashtag_object,
        'questions': questions,
        'number_of_questions': number_of_questions,
        'number_of_pages': math.ceil(number_of_questions / 15),
        'page': page,
        'next_page': True if page < max_page else False,
        'prev_page': True if page > 1 else False,
    })


def search_for_hashtag(request):

    query = request.GET.get('q')

    if not query:
        return HttpResponse(
            json.dumps([]),
            content_type='application/json'
        )

    found_hashtags = HashTag.objects.filter(name__icontains=query).values('id', 'name')

    return HttpResponse(
        json.dumps(list(found_hashtags)),
        content_type='application/json'
    )
