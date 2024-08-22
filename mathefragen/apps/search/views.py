import requests
import json
import logging
import math

from django.shortcuts import render, HttpResponse
from django.contrib.postgres.search import SearchVector
from django.db.models import Q
from django.db.models import Count
from django.conf import settings

from mathefragen.apps.question.models import Question
from mathefragen.apps.playlist.models import Playlist

logger = logging.getLogger(__name__)


def search(request):
    search_term = request.GET.get('q', '')

    questions = Question.objects.order_by('-idate')

    if search_term:
        questions = questions.annotate(
            search=SearchVector('title'),
        ).filter(search=search_term)

    number_of_questions = questions.count()

    page = int(request.GET.get('page', 1))
    page = 1 if page < 1 else page

    max_page = int(math.ceil(questions.count() / 15.0))
    max_page = 1 if max_page < 1 else max_page

    if page > max_page:
        page = max_page

    questions = questions[15 * (page - 1): 15 * page]

    return render(request, 'index.html', {
        'questions': questions,
        'number_of_questions': number_of_questions,
        'number_of_pages': math.ceil(number_of_questions / 15),
        'page': page,
        'next_page': True if page < max_page else False,
        'prev_page': True if page > 1 else False,
    })


def playlist_search(request):
    search_term = request.GET.get('q', '')
    playlists = Playlist.objects.annotate(units=Count('playlist_units')).filter(units__gt=0).order_by('-id')

    if search_term:
        playlists = playlists.filter(
            Q(name__icontains=search_term) | Q(description__icontains=search_term)
        )

    return render(request, 'playlist/index.html', {
        'playlists': playlists
    })


def youtube_search(request):

    search_term = request.GET.get('search_term')

    response = requests.get(settings.YOUTUBE_SEARCH_URL, params={
        'part': 'snippet',
        'q': search_term,
        'type': 'video',
        'key': settings.YOUTUBE_API_KEY,
        'maxResults': 15
    })

    if response.json().get('error'):
        logger.debug(response.json())

    return HttpResponse(json.dumps(response.json()), content_type='application/json')
