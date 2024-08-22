from django import forms

from .models import UserReview


class ReviewForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '6',
            'autofocus': 'autofocus'
        }),
        label='Deine Bewertung',
        help_text='max. 400 Zeichen',
        max_length=400
    )

    relation_source = forms.CharField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control w-50'
        }, choices=UserReview.RELATION_SOURCES),
        label='Woher kennst du '
    )

    class Meta:
        model = UserReview
        exclude = ('given_to', 'given_by')
        fields = (
            'text', 'relation_source'
        )
