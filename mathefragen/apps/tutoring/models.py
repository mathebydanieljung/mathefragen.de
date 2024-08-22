from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from websocket import create_connection

from mathefragen.apps.core.models import Base
from mathefragen.apps.core.utils import send_email_in_template
from mathefragen.apps.messaging.models import Message as InboxMessage
from mathefragen.apps.question.models import Question
from . import (
    TUTOR_PING_TEXT,
    TUTOR_TIME_DEAL_TEXT,
    TUTOR_FIRST_TIME_DEAL,
    PAYOUT_SUCCESS_TEXT,
    TUTOR_TIME_OFFER_TEXT
)


class HelpRequest(Base):
    # user is taken via question object
    question = models.ForeignKey(
        Question,
        related_name='question_help_requests',
        on_delete=models.SET_NULL,
        null=True
    )
    user = models.ForeignKey(
        User,
        related_name='sent_help_requests',
        on_delete=models.SET_NULL,
        null=True
    )
    tutor = models.ForeignKey(
        User,
        related_name='received_help_requests',
        on_delete=models.SET_NULL,
        null=True
    )
    date_time1 = models.DateTimeField(null=True)
    date_time2 = models.DateTimeField(null=True)
    date_time3 = models.DateTimeField(null=True)
    duration = models.IntegerField(
        default=30
    )
    amount_to_pay = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    users_share = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    last_acted_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    accepted_at = models.DateTimeField(null=True)
    accepted_date_time = models.DateTimeField(null=True)

    paid_at = models.DateTimeField(null=True)
    started_at = models.DateTimeField(null=True)

    tutor_joined_at = models.DateTimeField(null=True)
    student_joined_at = models.DateTimeField(null=True)
    tutor_completed_at = models.DateTimeField(null=True)
    student_completed_at = models.DateTimeField(null=True)

    per_invoice = models.BooleanField(default=False)

    # only tutor can cancel the request for now.
    declined_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(default='', blank=True)

    class Meta:
        verbose_name = 'Nachhilfe Session'
        verbose_name_plural = 'Nachhilfe Sessions'

    def latest_message(self):
        return self.request_messages.latest().message

    def set_users_share(self):
        commission = self.amount_to_pay * settings.TUTORING_COMPANY_SHARE / 100
        self.users_share = self.amount_to_pay - commission
        self.save()

    def is_completed(self):
        return bool(self.tutor_completed_at) and bool(self.student_completed_at)

    def has_alternative_dates(self):
        return self.date_time2 or self.date_time3

    def can_begin(self):

        if self.is_completed():
            return False

        if not self.is_paid:
            return False

        return self.accepted_at and self.accepted_date_time <= (timezone.now() + timezone.timedelta(minutes=5))

    @property
    def is_paid(self):
        return bool(self.paid_at)

    @property
    def remaining_time_until_begin(self):
        if self.is_completed():
            return 'Die Videokonferenz wurde beendet.'

        if not self.is_paid:
            return 'Der ausgemachte Betrag ist noch offen.'

        return 'Die Videokonferenz ist 5 Minuten vor dem Start verfügbar'

    def inform_about_payment_success(self):
        send_email_in_template(
            'Dein Nachhilfe-Satz wurde bezahlt.',
            [self.tutor.email],
            **{
                'text': '%s hat den vereinbarten Betrag von %s € für %s Minuten bezahlt. '
                        'Dieser wird dir, nach erfolgriechem Abschluss der Nachhilfeeinhiet, auf deinem '
                        'mathefragen-Konto gutgeschrieben. Wir bedanken uns für deine Mithilfe im Forum und '
                        'wünschen dir viel Erfolg bei der Nachhilfe.' % (
                            self.user.username, self.amount_to_pay, self.duration
                        )
            }
        )
        send_email_in_template(
            'Eine Nachhilfe-Einheit wurde bezahlt',
            settings.ADMINS_TO_REPORT,
            **{
                'text': '%s hat für eine Nachhilfe Einheit mit %s EUR gezahlt.' % (
                    self.user.username, self.amount_to_pay
                )
            }
        )
        # inbox message
        msg = InboxMessage.objects.create(
            title='Nachhilfeunterricht bezahlt',
            message='%s hat für deine Nachhilfe %s EUR gezahlt.' % (
                self.user.username, self.amount_to_pay
            ),
            link=self.get_absolute_url(),
            type='Nachhilfe'
        )
        msg.to_users.add(self.tutor_id)

        # web push notification
        if settings.ENABLE_WEBSOCKETS:
            try:
                ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % self.tutor_id)
                ws.send('Nachhilfe')
                ws.close()
            except Exception:
                pass

    def notify_tutor(self):
        # email
        send_email_in_template(
            'Anfrage für Nachhilfeunterricht: %s' % self.user.username,
            [self.tutor.email],
            **{
                'text': TUTOR_PING_TEXT % (
                    self.tutor.username, self.user.username
                ),
                'link': 'https://%s%s' % (settings.DOMAIN, self.get_absolute_url()),
                'link_name': 'Anfrage ansehen'
            }
        )
        # inbox message
        msg = InboxMessage.objects.create(
            title='Anfrage für Nachhilfeunterricht: %s' % self.user.username,
            message='%s braucht dringend Hilfe und bittet '
                    'dich um eine private Unterrichtseinheit.\nNachricht: %s' % (
                        self.user.username, self.request_messages.first().message
                    ),
            link=self.get_absolute_url(),
            type='Nachhilfe'
        )
        msg.to_users.add(self.tutor_id)

        if settings.ENABLE_WEBSOCKETS:
            # web push notification
            try:
                ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % self.tutor_id)
                ws.send('Nachhilfe')
                ws.close()
            except Exception:
                pass

        if self.tutor.profile.phone_number:
            pass

    def notify_on_message(self, sender, receiver):
        send_email_in_template(
            '%s hat dir eine Nachricht geschickt - %s' % (sender.username, settings.DOMAIN),
            [receiver.email],
            **{
                'text': '%s hat dir eine Nachricht geschickt. ' % sender.username,
                'link': 'https://%s%s' % (settings.DOMAIN, self.get_absolute_url()),
                'link_name': 'Antworten'
            }
        )

    def notify_about_time_change(self, change_by_student=False):
        source_user = self.tutor
        target_user = self.user
        if change_by_student:
            source_user = self.user
            target_user = self.tutor

        send_email_in_template(
            'Nachhilfe - %s hat einen Vorschlag' % source_user.username,
            [target_user.email],
            **{
                'text': TUTOR_TIME_OFFER_TEXT % (
                    target_user.username, source_user.username
                ),
                'link': 'https://%s%s' % (settings.DOMAIN, self.get_absolute_url()),
                'link_name': 'Terminvorschlag ansehen'
            }
        )
        # inbox message
        msg = InboxMessage.objects.create(
            title='Nachhilfe - %s hat einen Vorschlag' % source_user.username,
            message='%s macht einen neuen Terminvorschlag' % (
                source_user.username
            ),
            link=self.get_absolute_url(),
            type='Nachhilfe'
        )
        msg.to_users.add(target_user.id)

        if settings.ENABLE_WEBSOCKETS:
            # web push notification
            try:
                ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % target_user.id)
                ws.send('Nachhilfe')
                ws.close()
            except Exception:
                pass

    def notify_on_deal(self):
        source_user = self.last_acted_user
        if self.last_acted_user_id == self.tutor_id:
            target_user = self.user
        else:
            target_user = self.tutor

        text = TUTOR_TIME_DEAL_TEXT % (
            target_user.username,
            source_user.username
        )
        # check if it is straight deal without messages:
        if self.request_messages.count() < 2:
            text = TUTOR_FIRST_TIME_DEAL % (
                self.user.username,
                self.tutor.username
            )

        send_email_in_template(
            'Nachhilfeunterricht mit %s steht fest' % source_user.username,
            [target_user.email],
            **{
                'text': text,
                'link': 'https://%s%s' % (settings.DOMAIN, self.get_absolute_url()),
                'link_name': 'Anfrage ansehen'
            }
        )

        # inbox message
        msg = InboxMessage.objects.create(
            title='Nachhilfeunterricht mit %s steht fest' % source_user.username,
            message='Klicke hier für weitere Details',
            link=self.get_absolute_url(),
            type='Nachhilfe'
        )
        msg.to_users.add(target_user.id)

        if settings.ENABLE_WEBSOCKETS:
            # web push notification
            try:
                ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % target_user.id)
                ws.send('Nachhilfe')
                ws.close()
            except Exception:
                pass

    def ordered_messages(self):
        return self.request_messages.order_by('id')

    def get_absolute_url(self):
        return reverse('request_detail', args=(self.hash_id,))

    def __str__(self):
        username = self.user.username if self.user_id else 'no user'
        tutor_username = self.tutor.username if self.tutor_id else 'no tutor'

        return 'Nachhilfe zwischen %s und %s' % (
            tutor_username, username
        )


class Message(Base):
    request = models.ForeignKey(
        HelpRequest,
        related_name='request_messages',
        on_delete=models.SET_NULL,
        null=True
    )
    sender = models.ForeignKey(
        User,
        related_name='tutoring_messages',
        on_delete=models.SET_NULL,
        null=True
    )
    message = models.TextField()

    class Meta:
        get_latest_by = ('idate',)

    def __str__(self):
        return self.message


class Payment(Base):
    request = models.ForeignKey(
        HelpRequest,
        related_name='tutoring_payment',
        on_delete=models.SET_NULL,
        null=True
    )
    user = models.ForeignKey(
        User,
        related_name='user_payments',
        on_delete=models.SET_NULL,
        null=True
    )
    paypal_order_id = models.CharField(
        max_length=50,
        default=''
    )
    paid_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    commission = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    users_share = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    voucher_file = models.FileField(
        upload_to='payment_voucher/',
        default='',
        blank=True,
        verbose_name='Rechnung (PDF)',
        help_text='Nutzer kann seine Rechnungen später im Profil herunterladen'
    )

    class Meta:
        verbose_name = 'Zahlung'
        verbose_name_plural = 'Zahlungen'


class TutorSetting(Base):
    PAYMENT_TYPES = (
        ('paypal', 'PayPal'),
        ('iban', 'Überweisung')
    )
    user = models.OneToOneField(
        User,
        related_name='tutor_setting',
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=False)
    half_hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    ninety_min_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    sek_1 = models.BooleanField(default=False, blank=True)
    sek_2 = models.BooleanField(default=False, blank=True)

    # university modules
    university_modules = models.TextField(default='')

    # extra note
    note = models.TextField(default='', blank=True)
    video = models.FileField(
        default='',
        blank=True,
        upload_to='tutor_profile_video/%Y/%m/'
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        blank=True
    )
    paypal_email = models.EmailField(
        max_length=200,
        blank=True,
        default=''
    )
    iban = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )
    bic = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )
    payment_changed_to = models.CharField(
        choices=PAYMENT_TYPES,
        blank=True,
        max_length=10,
        default=''
    )
    payment_confirm_code = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )
    payment_changed_at = models.DateTimeField(null=True, blank=True)
    payment_change_cancelled_at = models.DateTimeField(null=True, blank=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Tutor Profil'
        verbose_name_plural = 'Tutor Profile'

    def has_price(self):
        return any([self.half_hourly_rate, self.hourly_rate, self.ninety_min_rate])

    def current_payment_method(self):
        if self.payment_changed_to:
            return self.paypal_email if self.payment_changed_to == 'paypal' else '**%s' % self.iban[-4:]
        elif self.paypal_email:
            return self.paypal_email
        elif self.iban:
            return '**%s' % self.iban[-4:]
        return ''

    def inform_admin_about_new_payment_details(self):
        send_email_in_template(
            '%s hat seine/ihre Zahlungsart geändert' % self.user.username,
            settings.ADMINS_TO_REPORT,
            **{
                'text': '%s hat seine/ihre Zahlungsart geändert. Bitte Prüf-Code transferieren. Link:\n\n'
                        'https://%s%stutoring/tutorsetting/%s/change/' % (
                            self.user.username, settings.DOMAIN, settings.ADMIN_URL, self.id
                        )
            }
        )

    def inform_user_about_new_payment_details(self):
        send_email_in_template(
            'Zahlungsart geändert - %s' % settings.DOMAIN,
            [self.user.email],
            **{
                'text': 'Hi %s, \n\n du hast deine Zahlungsart auf %s auf %s geändert. In Kürze erhälst du von uns '
                        'eine Gutschrift i.H.v 1 Cent. Dort findest du im Verwendungszweck den 6-stelligen Code. Nutze diesen Code, '
                        'um diese neue Zahlungsart zu bestätigen, in dem du den Code in den Nachhilfe-Einstellungen '
                        'unter Abschnitt "Auszahlung" eingibst. '
                        'Bei Fragen kontaktiere uns unter support@mathefragen.de.' % (
                            self.user.username, settings.DOMAIN, self.get_payment_changed_to_display()
                        )
            }
        )

    def __str__(self):
        return 'tutor settings von %s' % self.user.username


class PayoutRequest(Base):
    STATUS = (
        ('pending', 'Ausstehend'),
        ('paid', 'Ausgezahlt')
    )
    user = models.ForeignKey(
        User,
        related_name='tutor_payouts',
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    status = models.CharField(
        choices=STATUS,
        default='',
        max_length=20
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        User,
        related_name='paid_payout_requests',
        on_delete=models.SET_NULL,
        null=True,
    )
    invoice_file = models.FileField(default='', blank=True)
    note = models.TextField(default='', blank=True)

    class Meta:
        verbose_name = 'Auszahlung'
        verbose_name_plural = 'Auszahlungen'

    def inform_tutor_about_payment(self):
        send_email_in_template(
            'Auszahlung - mathefragen.de',
            [self.user.email],
            **{
                'text': PAYOUT_SUCCESS_TEXT % (self.user.profile.username, self.amount)
            }
        )

    def __str__(self):
        return 'PayoutRequest von %s' % self.user.username


class Review(Base):
    given_by = models.ForeignKey(
        User,
        related_name='given_tutor_reviews',
        on_delete=models.CASCADE
    )
    tutor = models.ForeignKey(
        User,
        related_name='received_tutor_reviews',
        on_delete=models.CASCADE
    )
    request = models.ForeignKey(
        HelpRequest,
        related_name='request_reviews',
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField(default='', blank=True)
    public = models.BooleanField(
        default=True,
        help_text='Wenn aktiv, ist die Bewertung öffentlich.'
    )

    class Meta:
        verbose_name = 'Bewertung'
        verbose_name_plural = 'Bewertungen'

    def __str__(self):
        return self.text
