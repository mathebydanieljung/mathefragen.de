import json
from decimal import Decimal

from django.shortcuts import render, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.db.models import Count
from django.contrib.auth.decorators import login_required

from .models import Playlist, Unit
from .forms import PlaylistForm, UnitForm
from mathefragen.apps.user.models import Profile
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.guardian.tools import ip


def all_playlists(request):
    playlists = Playlist.objects.annotate(units=Count('playlist_units')).filter(
        units__gt=0, is_active=True
    ).order_by('-id')
    return render(request, 'playlist/index.html', {
        'playlists': playlists
    })


@login_required
def profile_playlists(request, user_hash):
    try:
        profile = Profile.objects.get(hash_id=user_hash)
    except Profile.DoesNotExist:
        return redirect('/')

    user_playlists = Playlist.objects.filter(user_id=profile.user_id, is_active=True).order_by('-id')

    if request.user.id != profile.user_id:
        user_playlists = user_playlists.annotate(units=Count('playlist_units')).filter(units__gt=0).order_by('-id')

    return render(request, 'playlist/index.html', {
        'profile': profile,
        'playlists': user_playlists
    })


def playlist_detail(request, slug, pl_hash):

    try:
        playlist = Playlist.objects.get(hash_id=pl_hash)
    except Playlist.DoesNotExist:
        return redirect('%s?deleted=1' % reverse('index'))

    playlist.increase_views_counter(request=request)

    publish_now = request.GET.get('publish_now')
    if publish_now == 'yes':
        playlist.is_active = True
        playlist.save()

    if request.user.is_authenticated:
        already_seen = request.user.user_seen_playlists.filter(playlist_id=playlist.id).count()
        if not already_seen:
            request.user.user_seen_playlists.create(playlist_id=playlist.id)

    unit = request.GET.get('unit')
    if unit:
        unit = Unit.objects.get(id=unit)

    return render(request, 'playlist/detail.html', {
        'playlist': playlist,
        'unit': unit
    })


class AddPlaylist(LoginRequiredMixin, CreateView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        playlist_hash = kwargs.get('pl_hash')
        user = request.user

        context = {
            'form': PlaylistForm()
        }

        # in this case, this question is being edited
        if playlist_hash:
            playlist = Playlist.objects.get(hash_id=playlist_hash)

            if user.id == playlist.user_id:
                form = PlaylistForm(initial={
                    'name': playlist.name,
                    'description': playlist.description,
                    'playlist_hash_id': playlist.hash_id,
                    'being_edited': 'yes'
                })
                context.update({
                    'form': form,
                    'profile': user.profile,
                    'playlist': playlist,
                    'tags': json.dumps(list(playlist.tags.values('id', 'name')))
                })

        return render(request, 'playlist/add.html', context)

    def post(self, request, *args, **kwargs):
        form = PlaylistForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            name = form_data.get('name')
            description = form_data.get('description')
            tags = form_data.get('tags')
            being_edited = form_data.get('being_edited')
            playlist_hash_id = form_data.get('playlist_hash_id')

            if len(name) < 10:
                context = {
                    'form': form,
                    'name_error': 'Titel der Playliste muss mindestens 10 Zeichen lang sein.'
                }
                return render(request, 'playlist/add.html', context)

            user = request.user

            if being_edited == 'yes':
                playlist = Playlist.objects.get(hash_id=playlist_hash_id)
                playlist.name = name
                playlist.description = description
                playlist.save()

                # remove reports, as we hope that user has edited his question to make it better
                playlist.playlist_reports.all().delete()

            else:
                source_ip = '192.168.0.1'
                found_ip = ip.IP(request=request).user_ip()
                if found_ip:
                    source_ip = found_ip

                playlist = Playlist.objects.create(
                    name=name,
                    description=description,
                    user_id=user.id,
                    source_ip=source_ip
                )

            new_tags = [tag_name.strip().lower() for tag_name in tags.split(',') if tag_name and tag_name.strip()]
            # clean out old hashtags
            playlist.tags.clear()

            for tag in new_tags:
                tag = tag.lower()

                if not HashTag.objects.filter(name=tag).count():
                    tag_ = HashTag.objects.create(name=tag)
                else:
                    tag_ = HashTag.objects.filter(name=tag).last()

                playlist.tags.add(tag_.id)

            return redirect(playlist.get_absolute_url())

        else:
            context = {
                'form': form,
                'error': 'Titel und Frage sind Pflichtfelder'
            }
            return render(request, 'playlist/add.html', context)


class AddPlaylistUnit(LoginRequiredMixin, CreateView):

    def post(self, request, *args, **kwargs):
        playlist = Playlist.objects.get(hash_id=kwargs.get('pl_hash'))

        name = request.POST.get('name').strip()
        unit_content = request.POST.get('unit_content', '').strip()
        order = request.POST.get('order')
        suggested_videos = request.POST.getlist('suggested_videos')
        existing_unit = request.POST.get('existing_unit')

        if existing_unit:
            unit = Unit.objects.get(hash_id=existing_unit)
            unit.name = name
            unit.description = unit_content
            unit.int_order = Decimal(order)
            unit.save()
        else:
            unit = playlist.playlist_units.create(
                name=name,
                description=unit_content,
                int_order=Decimal(order)
            )

        for youtube_id in suggested_videos:
            unit.unit_vid_recommendations.create(
                youtube_id=youtube_id
            )

        return redirect(playlist.get_absolute_url())


@login_required
def delete_playlist(request, pl_hash):
    playlist = Playlist.objects.get(hash_id=pl_hash)

    if request.user.id != playlist.user_id:
        return redirect(reverse('public_profile', kwargs={'pk': request.user.id}))

    playlist.delete()

    return redirect(reverse('profile_playlists', kwargs={'user_hash': request.user.profile.hash_id}))


@login_required
def delete_unit(request):
    unit_hash = request.POST.get('unit_hash')
    playlist_unit = Unit.objects.get(hash_id=unit_hash)

    playlist = playlist_unit.playlist

    if request.user.id != playlist_unit.playlist.user_id:
        return redirect(reverse('public_profile', kwargs={'pk': request.user.id}))

    playlist_unit.delete()

    return redirect(playlist.get_absolute_url())
