from django import forms


class CreateQuestionForm(forms.Form):

    title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Gib deiner Frage eine aussagekräftige Überschrift',
            'autofocus': 'true'
        }),
        help_text='min. 10 Zeichen, max. 100 Zeichen.'
    )
    question_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control wmd-input',
            'rows': '10',
            'id': 'wmd-input',
            'placeholder': 'Gib alle Informationen an, die jemand zur Beantwortung deiner Frage benötigt. '
                           'Lade deine bisherigen Ergebnisse und Ansätze hoch und erkläre konkret, wo du '
                           'nicht weiterkommst.'
        })
    )
    question_tags = forms.CharField(
        label='Tags',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nach passendem Tag suchen'
        })
    )
    is_article = forms.CharField(
        required=False,
        widget=forms.CheckboxInput(check_test=lambda x: False)
    )
    being_edited = forms.CharField(
        initial='no',
        widget=forms.TextInput(attrs={'type': 'hidden'})
    )
    question_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'type': 'hidden'})
    )
