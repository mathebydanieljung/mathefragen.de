from django import forms

from .models import Playlist, Unit


class PlaylistForm(forms.Form):
    name = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Titel deiner Playliste',
            'autofocus': 'true'
        }),
        help_text='Mindestens 10 Zeichen.'
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control wmd-input',
            'rows': '10',
            'id': 'wmd-input',
            'placeholder': 'Beschreibung deiner Playliste'
        })
    )
    tags = forms.CharField(
        label='Tags',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nach passendem Tag suchen'
        })
    )
    being_edited = forms.CharField(
        initial='no',
        widget=forms.TextInput(attrs={'type': 'hidden'})
    )
    playlist_hash_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'type': 'hidden'})
    )


class UnitForm(forms.ModelForm):
    name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': '',
            'placeholder': 'E-Mail oder Benutzername *'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control w-50',
            'rows': '5'
        }),
        label='Beschreibung',
        help_text='max. 140 Zeichen',
        max_length=140
    )
    link = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control w-50',
            'rows': '5'
        }),
        label='Beschreibung',
        help_text='max. 140 Zeichen',
        max_length=140
    )
    media = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        label='Datei hochladen'
    )

    class Meta:
        model = Unit
        exclude = (
            'playlist',
        )
