from django import forms

from .models import TutorSetting, PayoutRequest


class TutorStatusForm(forms.Form):
    is_active = forms.CharField(
        required=False,
        widget=forms.CheckboxInput()
    )


class VideoForm(forms.ModelForm):
    video = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': "video/mp4"
        })
    )
    delete_video = forms.CharField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'd-none'}
        )
    )

    class Meta:
        model = TutorSetting
        fields = ('delete_video', 'video')


class PriceSettingForm(forms.ModelForm):
    half_hourly_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control w-50 d-inline',
            'min': '0.0'
        })
    )
    hourly_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control w-50 d-inline',
            'min': '0.0'
        })
    )
    ninety_min_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control w-50 d-inline',
            'min': '0.0'
        })
    )

    class Meta:
        model = TutorSetting
        fields = ('is_active', 'half_hourly_rate', 'hourly_rate', 'ninety_min_rate')


class TargetGroupForm(forms.ModelForm):
    sek_1 = forms.CharField(
        required=False,
        widget=forms.CheckboxInput()
    )
    sek_2 = forms.CharField(
        required=False,
        widget=forms.CheckboxInput()
    )
    university_modules = forms.CharField(
        required=False,
        widget=forms.Textarea()
    )
    note = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '2',
            'placeholder': 'Bemerkungen z.B. Uni nur bis 2. Semester'
        })
    )

    class Meta:
        model = TutorSetting
        fields = ('sek_1', 'sek_2', 'note')


class PaymentMethodForm(forms.ModelForm):
    payment_type = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        choices=(('', 'Zahlungsart auswählen'),) + TutorSetting.PAYMENT_TYPES
    )
    paypal_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control mt-3 d-none',
            'placeholder': 'Deine Paypal E-Mail'
        })
    )
    iban = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mt-3 d-none',
            'placeholder': 'Deine IBAN'
        })
    )
    bic = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mt-3 d-none',
            'placeholder': 'Deine BIC'
        })
    )

    class Meta:
        model = TutorSetting
        fields = ('payment_type', 'paypal_email', 'iban', 'bic')


class PaymentConfirmForm(forms.Form):
    payment_confirm_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mt-2',
            'placeholder': 'Code aus Verwendungszweck'
        })
    )


class PayoutForm(forms.Form):
    amount = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control mt-2',
            'placeholder': 'Betrag eingeben'
        })
    )
