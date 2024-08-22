from django.shortcuts import render

from mathefragen.apps.news.models import News, ReleaseNote


def detail_news(request, hash_id, slug):
    news = News.objects.get(hash_id=hash_id)

    return render(request, 'news/detail.html', {
        'news': news
    })


def details_release_note(request, hash_id, slug):
    other_release_notes = ReleaseNote.objects.exclude(hash_id=hash_id).filter(public=True).order_by('public_date')
    release_note = ReleaseNote.objects.get(hash_id=hash_id)

    # mark it as read
    if request.user.is_authenticated:
        already_seen = request.user.user_read_release_notes.filter(release_note_id=release_note.id).count()
        if not already_seen:
            request.user.user_read_release_notes.create(release_note_id=release_note.id)

    return render(request, 'release_notes/detail.html', {
        'release_note': release_note,
        'other_release_notes': other_release_notes
    })


def latest_release_note(request):
    release_note = ReleaseNote.objects.filter(public=True)
    other_release_notes = []
    if release_note and release_note.count():
        release_note = ReleaseNote.objects.filter(public=True).order_by('-id')[0]
        other_release_notes = ReleaseNote.objects.exclude(hash_id=release_note.hash_id).filter(public=True).order_by('public_date')

    # mark it as read
    if request.user.is_authenticated and release_note:
        already_seen = request.user.user_read_release_notes.filter(release_note_id=release_note.id).count()
        if not already_seen:
            request.user.user_read_release_notes.create(release_note_id=release_note.id)

    return render(request, 'release_notes/detail.html', {
        'release_note': release_note,
        'other_release_notes': other_release_notes
    })
