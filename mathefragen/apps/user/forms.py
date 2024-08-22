from django import forms

from .models import Social, Profile


class LoginForm(forms.Form):

    login_id = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': '',
            'placeholder': 'E-Mail oder Benutzername *'
        })
    )

    password = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Passwort *'
        })
    )


class RegisterForm(forms.Form):

    username = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Benutzername * (max. 16 Zeichen)',
            'autofocus': 'yes'
        }),
        help_text='Du kannst Buchstaben, Ziffern und Punkte verwenden. Max. 16 Zeichen.'
    )

    email = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-Mail *'
        })
    )

    password = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Passwort *'
        })
    )


class BasicInfoForm(forms.Form):
    username = forms.CharField(
        max_length=200,
        required=False,
        label='Benutzername',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Benutzername'
        })
    )
    email = forms.CharField(
        max_length=200,
        required=False,
        label='E-Mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-Mail'
        })
    )
    first_name = forms.CharField(
        max_length=200,
        required=False,
        label='Vorname',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Vorname'
        })
    )

    last_name = forms.CharField(
        max_length=200,
        required=False,
        label='Nachname',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nachname'
        })
    )
    phone_number = forms.CharField(
        max_length=200,
        required=False,
        label='Handynummer',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '+4917612345678'
        })
    )
    bio = forms.CharField(
        max_length=200,
        required=False,
        label='Über mich',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Beschreib\' dich in einem Satz'
        })
    )
    skills = forms.CharField(
        max_length=300,
        required=False,
        label='Ich bin gut in:',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Worin bist du besonders gut?'
        })
    )
    status = forms.ChoiceField(
        required=False,
        label='Status',
        choices=(('', 'Status auswählen'),) + Profile.STATUS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    other_status = forms.CharField(
        required=False,
        label='Eigene Beschreibung (Status)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Eigene Beschreibung'
        })
    )


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        max_length=200,
        required=True,
        label='Aktuelles Passwort',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Aktuelles Passwort',
        })
    )
    password1 = forms.CharField(
        max_length=200,
        required=True,
        label='Neues Passwort',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Neues Passwort'
        })
    )
    password2 = forms.CharField(
        max_length=200,
        required=True,
        label='Neues Passwort wiederholen',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wiederholen'
        })
    )


class PasswordSetForm(forms.Form):
    password1 = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Neues Passwort'
        })
    )
    password2 = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Neues Passwort wiederholen'
        })
    )


class ImageChangeForm(forms.Form):
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'style': 'font-size: 12px'
        })
    )


class ApplyVerificationForm(forms.Form):

    reason = forms.CharField(
        max_length=300,
        required=False,
        label='Grund',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Warum sollten wir deinen Account verifizieren?'
        })
    )


class AddSocialsForm(forms.ModelForm):
    type = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'form-control w-50'
        }, choices=Social.TYPES),
        label='Typ'
    )
    link = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control w-50',
            'rows': '2'
        }),
        help_text='Bitte absoluten Link mit https://.. eingeben',
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

    class Meta:
        model = Social
        exclude = ('user',)
        fields = (
            'type',
            'link',
            'description'
        )


class CompleteProfileForm(forms.Form):
    """
    one random chunk will be shown in completeProfileForm until profile is complete.
    """

    CHUNKS = {
        'name': ['first_name', 'last_name'],
        'postal_code': ['postal_code'],
        'phone_number': ['phone_number'],
        'degree_course': ['degree_course'],
        'status': ['status', 'other_status'],
        'institution': ['institution'],
        'gender': ['gender'],
        'birth_year': ['birth_year'],
        'degree_grade': ['degree_grade']
    }
    first_name = forms.CharField(
        max_length=200,
        required=False,
        label='Vorname',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Vorname'
        })
    )
    last_name = forms.CharField(
        max_length=200,
        required=False,
        label='Nachname',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nachname'
        })
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Telefonnummer'
        }),
        label='Telefonnummer'
    )
    degree_course = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'z.B. Angewannte Mathematik'
        }),
        label='Studiengang'
    )
    status = forms.ChoiceField(
        required=False,
        choices=(('', 'Status auswählen'),) + Profile.STATUS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Status'
    )
    other_status = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Eigene Beschreibung'
        }),
        label='Eigene Beschreibung (Status)'
    )
    institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name deiner Uni / Hochschule / Schule'
        }),
        label='Name deiner Uni / Hochschule / Schule'
    )
    gender = forms.ChoiceField(
        required=False,
        choices=(('', 'Geschlecht auswählen'),) + Profile.GENDER,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Geschlecht (nicht öffentlich)'
    )
    birth_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'z.B. 1990',
            'max': '2020',
            'min': '1912'
        }),
        label='Dein Geburtsjahr (nicht öffentlich)'
    )
    degree_grade = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'z.B. 2. Semester oder 10. Klasse'
        }),
        label='Deine Jahrgangsstufe (Semester, Klasse)'
    )
    postal_code = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'PLZ'
        }),
        label='PLZ (z.B. 94339)'
    )


class PrivacySettings(forms.Form):
    pass


class NotificationSettingsForm(forms.Form):
    email_notification = forms.CharField(
        required=False,
        widget=forms.CheckboxInput()
    )
    # later also push notification
