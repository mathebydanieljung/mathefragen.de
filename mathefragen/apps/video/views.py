import os
import re
import mimetypes
from wsgiref.util import FileWrapper

from django.views.decorators.clickjacking import xframe_options_exempt
from django.http.response import StreamingHttpResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required

from videos.apps.video.models import (
    Video,
    PlaylistCategory,
    Playlist
)
# from videos.apps.core.decorators import has_paid
from .utils import RangeFileWrapper


@login_required
# @has_paid
def category_detail(request, slug, category_hash):
    try:
        category = PlaylistCategory.objects.get(hash_id=category_hash)
    except PlaylistCategory.DoesNotExist:
        return redirect(reverse('start'))

    other_categories = PlaylistCategory.objects.exclude(id=category.id)

    return render(request, 'video/category.html', {
        'category': category,
        'other_categories': other_categories
    })


@login_required
def playlist_detail(request, slug, playlist_hash):
    try:
        playlist = Playlist.objects.get(hash_id=playlist_hash)
    except Playlist.DoesNotExist:
        return redirect(reverse('start'))

    other_playlist = Playlist.objects.exclude(id=playlist.id)

    return render(request, 'video/playlist.html', {
        'playlist': playlist,
        'other_playlist': other_playlist
    })


@xframe_options_exempt
def playlist_detail_iframe(request, slug, playlist_hash):
    try:
        playlist = Playlist.objects.get(hash_id=playlist_hash)
    except Playlist.DoesNotExist:
        return redirect(reverse('start'))

    return render(request, 'video/playlist-iframe.html', {
        'playlist': playlist,
        'hide_nav': True,
        'hide_footer': True
    })


@login_required
def video_detail(request, slug, video_hash):
    try:
        video = Video.objects.get(hash_id=video_hash)
    except Video.DoesNotExist:
        return render(request, '404.html')

    other_videos = Video.objects.exclude(id=video.id).filter(playlist_id=video.playlist_id).order_by('order')

    return render(request, 'video/detail.html', {
        'video': video,
        'other_videos': other_videos
    })


@xframe_options_exempt
def video_detail_iframe(request, slug, video_hash):
    try:
        video = Video.objects.get(hash_id=video_hash)
    except Video.DoesNotExist:
        return render(request, '404.html')

    return render(request, 'video/detail-iframe.html', {
        'video': video,
        'hide_nav': True,
        'hide_footer': True
    })


@xframe_options_exempt
def stream_video(request, slug, video_hash):
    video = Video.objects.get(hash_id=video_hash)

    path = video.file.path

    range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = range_re.match(range_header)
    size = os.path.getsize(path)
    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(
            RangeFileWrapper(open(path, 'rb'), offset=first_byte, length=length),
            status=206,
            content_type=content_type
        )
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
        resp['Content-Length'] = str(size)
    resp['Accept-Ranges'] = 'bytes'
    return resp

