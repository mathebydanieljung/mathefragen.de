import json
from datetime import datetime
from decimal import Decimal

import jwt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import render, HttpResponse, redirect, reverse
from django.utils import timezone
from django.views.generic import FormView
from paypalcheckoutsdk.orders import OrdersGetRequest

from mathefragen.apps.core.models import random_five_digits
from mathefragen.apps.core.utils import send_email_in_template
from mathefragen.apps.question.models import Question
from mathefragen.apps.user.models import Profile
from mathefragen.apps.video.models import Video
from . import PAYMENT_SUCCESS_TEXT
from .forms import (
    PriceSettingForm,
    TargetGroupForm,
    PaymentMethodForm,
    PaymentConfirmForm,
    TutorStatusForm,
    VideoForm
)
from .models import HelpRequest, TutorSetting, Payment, PayoutRequest
from .paypal import PayPalClient


class AskTutors(LoginRequiredMixin, FormView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        question_hash = request.GET.get('question')

        question = None
        if question_hash:
            try:
                question = Question.objects.get(hash_id=question_hash)
            except Exception:
                pass

        # fullname must be entered
        if not all([request.user.first_name, request.user.last_name]):
            return redirect('%s?fullname_missing=1&next=%s' % (
                reverse('profile_settings', args=(request.user.id,)), '%s?question=%s' % (
                    reverse('ask_tutors'), question_hash
                )
            ))

        if 'confirmed' not in request.user.profile.confirm_hash:
            return redirect('%s?email_confirmation_missing=1&next=%s' % (
                reverse('profile_settings', args=(request.user.id,)), '%s?question=%s' % (
                    reverse('ask_tutors'), question_hash
                )
            ))

        user_hash_id = kwargs.get('user_hash_id')
        pre_select = user_hash_id
        if user_hash_id:
            top_tutors = Profile.objects.filter(hash_id=user_hash_id)
        else:
            top_tutors = Profile.objects.filter(can_tutor=True)

        final_tutors = list()
        for tutor in top_tutors:
            # all checks happen in can_give_tutoring() function
            if not tutor.can_give_tutoring() or tutor.user_id == request.user.id:
                continue
            final_tutors.append(tutor)

        return render(request, 'tutoring/ask_tutor.html', {
            'question': question,
            'tutors': final_tutors,
            'pre_select': pre_select
        })

    def post(self, request, *args, **kwargs):

        question_hash = request.POST.get('question_hash')
        duration = request.POST.get('duration')
        request_message = request.POST.get('request_message')
        date_time1 = request.POST.get('date_time1', '').replace('Uhr', '').strip()
        date_time2 = request.POST.get('date_time2', '').replace('Uhr', '').strip()
        date_time3 = request.POST.get('date_time3', '').replace('Uhr', '').strip()

        selected_tutors = request.POST.getlist('selected_tutors')

        single_session = None

        if not selected_tutors:
            return redirect('%s%s' % (
                reverse('ask_tutors'), '?question=' + question_hash if question_hash else ''
            ))

        if not date_time1:
            return redirect('%s%s' % (
                reverse('ask_tutors'), '?question=' + question_hash if question_hash else ''
            ))

        question = None
        if question_hash:
            question = Question.objects.get(hash_id=question_hash)
            question.number_tutor_pings += 1
            question.save()

        try:
            date_time1 = datetime.strptime(date_time1, '%d.%m.%Y %H:%M')
        except ValueError:
            return redirect('%s%s' % (
                reverse('ask_tutors'), '?question=' + question_hash if question_hash else ''
            ))

        if date_time2:
            try:
                date_time2 = datetime.strptime(date_time2, '%d.%m.%Y %H:%M')
            except ValueError:
                return redirect('%s%s' % (
                    reverse('ask_tutors'), '?question=' + question_hash if question_hash else ''
                ))

        if date_time3:
            try:
                date_time3 = datetime.strptime(date_time3, '%d.%m.%Y %H:%M')
            except ValueError:
                return redirect('%s%s' % (
                    reverse('ask_tutors'), '?question=' + question_hash if question_hash else ''
                ))

        for tutor_hash in selected_tutors:
            tutor = Profile.objects.get(hash_id=tutor_hash)
            amount_to_pay = tutor.get_time_price(duration=duration)

            help_request = HelpRequest.objects.create(
                date_time1=date_time1,
                date_time2=date_time2,
                date_time3=date_time3,
                question=question,
                user_id=request.user.id,
                tutor_id=tutor.user_id,
                last_acted_user_id=request.user.id,
                duration=int(duration),
                amount_to_pay=amount_to_pay
            )
            single_session = help_request

            help_request.request_messages.create(
                sender=request.user,
                message=request_message
            )
            help_request.notify_tutor()

            send_email_in_template(
                'neue Nachhilfe Session Anfrage',
                settings.ADMINS_TO_REPORT,
                **{
                    'text': '<p>neue Nachhilfe Session Anfrage reingekommen.</p>'
                            '<p>%s -> %s</p>'
                            '<p>Message: %s</p>' % (request.user.username, tutor.username, request_message)
                }
            )

        if len(selected_tutors) == 1:
            return redirect(single_session.get_absolute_url())

        return redirect(reverse('tutoring_sessions', args=(request.user.profile.hash_id,)))


class TutoringSessions(LoginRequiredMixin, FormView):

    def get(self, request, *args, **kwargs):
        user_hash = kwargs.get('user_hash_id')

        if user_hash != request.user.profile.hash_id:
            return redirect(reverse('tutoring_sessions', args=(request.user.profile.hash_id,)))

        received_help_requests = request.user.received_help_requests.all()
        sent_help_requests = request.user.sent_help_requests.all()

        sessions = (received_help_requests | sent_help_requests).order_by('-idate')

        return render(request, 'tutoring/sessions.html', {
            'sessions': sessions
        })


class RequestDetail(LoginRequiredMixin, FormView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        request_hash = kwargs.get('request_hash')
        try:
            help_request = HelpRequest.objects.get(hash_id=request_hash)
        except HelpRequest.DoesNotExist:
            return redirect(reverse('index'))

        if request.user.id not in [help_request.tutor_id, help_request.user_id]:
            return redirect(reverse('index'))

        if help_request.declined_at:
            return redirect(reverse('declined_tutoring_request', args=(help_request.hash_id,)))

        # check if completed
        status = request.GET.get('status', '')
        if 'completed' in status:

            if request.user.id == help_request.user_id:
                help_request.student_completed_at = timezone.now()
                help_request.save()
                # redirect to profile, so helper can get a review
                return redirect(
                    '%s?finished_session=%s' % (
                        help_request.tutor.profile.get_absolute_url(), help_request.hash_id
                    )
                )

            help_request.tutor_completed_at = timezone.now()
            help_request.save()

            # todo: tutor should also review the student? probably yes
            return redirect('/')

        if 'review_given' in status:
            if help_request.question_id:
                return redirect(
                    '%s?ask_if_settled=%s' % (
                        help_request.question.get_absolute_url(), help_request.hash_id
                    )
                )
            return redirect(
                '%s?ask_if_settled=%s' % (
                    reverse('index'), help_request.hash_id
                )
            )

        # track click on "start conference"
        # WIP
        if 'start' in status and help_request.can_begin():
            # In the past, here was a session initiated with Jitsi. This was removed.
            pass

        google_cal_link = 'https://calendar.google.com/calendar/r/eventedit?text=Nachhilfe (%s-%s) auf mathefragen.de&dates=%sT%s00/%sT%s00&details=Nachhilfe (%s-%s) auf mathefragen.de. Mehr infos: %s' % (
            # noqa
            help_request.tutor.username,
            help_request.user.username,
            help_request.date_time1.strftime('%Y%m%d'),
            help_request.date_time1.strftime('%H%M'),
            (help_request.date_time1 + timezone.timedelta(minutes=help_request.duration)).strftime('%Y%m%d'),
            (help_request.date_time1 + timezone.timedelta(minutes=help_request.duration)).strftime('%H%M'),
            help_request.tutor.username,
            help_request.user.username,
            'https://%s%s' % (settings.DOMAIN, help_request.get_absolute_url())
        )

        remaining_secs = 0
        if help_request.accepted_date_time:
            duration = help_request.accepted_date_time - timezone.now()
            duration = duration - timezone.timedelta(minutes=5)
            remaining_secs = max(0, int(duration.total_seconds()))

        return render(request, 'tutoring/request_detail.html', {
            'remaining_secs': remaining_secs,
            'help_request': help_request,
            'session_id': request_hash,
            'google_cal_link': google_cal_link
        })

    def post(self, request, *args, **kwargs):
        # in post, either date-time will be changed or whole deal is confirmed
        confirmed_date_time = request.POST.get('confirmed_date_time')
        date_time1 = request.POST.get('date_time1', '').replace('Uhr', '').strip()
        date_time2 = request.POST.get('date_time2', '').replace('Uhr', '').strip()
        date_time3 = request.POST.get('date_time3', '').replace('Uhr', '').strip()

        request_hash = kwargs.get('request_hash')
        help_request = HelpRequest.objects.get(hash_id=request_hash)

        if date_time1:
            try:
                date_time1 = datetime.strptime(date_time1, '%d.%m.%Y %H:%M')
            except ValueError:
                return redirect(reverse('request_detail', args=(help_request.hash_id,)))

            if date_time2:
                try:
                    date_time2 = datetime.strptime(date_time2, '%d.%m.%Y %H:%M')
                except ValueError:
                    return redirect(reverse('request_detail', args=(help_request.hash_id,)))

            if date_time3:
                try:
                    date_time3 = datetime.strptime(date_time3, '%d.%m.%Y %H:%M')
                except ValueError:
                    return redirect(reverse('request_detail', args=(help_request.hash_id,)))

            help_request.date_time1 = date_time1
            help_request.date_time2 = date_time2
            help_request.date_time3 = date_time3
            help_request.last_acted_user = request.user
            help_request.save()

            message = 'Wie wäre es mit: %s um %s Uhr?' % (
                date_time1.strftime('%d.%m.%Y'), date_time1.strftime('%H:%M')
            )
            if date_time2:
                message += '\n oder: %s um %s Uhr' % (date_time2.strftime('%d.%m.%Y'), date_time2.strftime('%H:%M'))
            if date_time3:
                message += '\n oder: %s um %s Uhr' % (date_time3.strftime('%d.%m.%Y'), date_time3.strftime('%H:%M'))

            help_request.request_messages.create(
                sender_id=request.user.id,
                message=message
            )
            student_is_changing = request.user.id == help_request.user_id
            help_request.notify_about_time_change(student_is_changing)

        elif confirmed_date_time:
            help_request.accepted_date_time = getattr(help_request, confirmed_date_time)
            help_request.accepted_at = timezone.now()
            help_request.last_acted_user = request.user
            help_request.save()

            help_request.notify_on_deal()

            message = 'Super! Bis dann :)'
            if request.user.id == help_request.tutor_id:
                message = 'Okay, passt. Bis dann :)'

            help_request.request_messages.create(
                sender_id=request.user.id,
                message=message
            )

        return redirect(reverse('request_detail', args=(help_request.hash_id,)))


@login_required
def message_send(request, request_hash):
    message = request.POST.get('message-to-send')
    help_request = HelpRequest.objects.get(hash_id=request_hash)

    if request.user.id not in [help_request.tutor_id, help_request.user_id]:
        return redirect(reverse('index'))

    help_request.request_messages.create(
        sender_id=request.user.id,
        message=message
    )
    if help_request.tutor_id == request.user.id:
        receiver = help_request.user
    else:
        receiver = help_request.tutor

    help_request.notify_on_message(sender=request.user, receiver=receiver)

    return redirect('%s#message-to-send' % help_request.get_absolute_url())


@login_required
def decline_tutoring_request(request, request_hash):
    help_request = HelpRequest.objects.get(hash_id=request_hash)

    if request.user.id not in [help_request.tutor_id, help_request.user_id]:
        return redirect(reverse('index'))

    decline_tutoring_request_msg = request.POST.get('decline_tutoring_request_msg')
    if not help_request.declined_at and request.user.id == help_request.tutor_id and not help_request.accepted_at:
        help_request.declined_at = timezone.now()
        help_request.decline_reason = decline_tutoring_request_msg
        help_request.save()

        send_email_in_template(
            'Deine Anfrage für private Nachhilfe abgelehnt',
            [help_request.user.email],
            **{
                'text': '<p>Deine Anfrage für Nachhilfe wurde von %s abgelehnt.</p>'
                        '<p>Nachricht von %s:</p>'
                        '<p><b>%s</b></p>' % (
                            help_request.tutor.username,
                            help_request.tutor.username,
                            decline_tutoring_request_msg
                        )
            }
        )

    return redirect(reverse('declined_tutoring_request', args=(help_request.hash_id,)))


@login_required
def declined_tutoring_request(request, request_hash):
    help_request = HelpRequest.objects.get(hash_id=request_hash)

    if request.user.id not in [help_request.tutor_id, help_request.user_id]:
        return redirect(reverse('index'))

    return render(request, 'tutoring/declined_request.html', {
        'help_request': help_request
    })


@login_required
def pay_and_join(request, session_id):
    help_request = HelpRequest.objects.get(hash_id=session_id)

    if request.user.id not in [help_request.tutor_id, help_request.user_id]:
        return redirect(reverse('index'))

    if help_request.is_paid:
        return redirect(reverse('request_detail', args=(help_request.hash_id,)))

    amount_to_pay = None
    amount_to_show = ''

    if help_request.duration == 30:
        amount_to_pay = help_request.amount_to_pay
        amount_to_show = ('30 Minuten Nachhilfe - %s EUR' % amount_to_pay).replace('.', ',')

    elif help_request.duration == 60:
        amount_to_pay = help_request.amount_to_pay
        amount_to_show = ('60 Minuten Nachhilfe - %s EUR' % amount_to_pay).replace('.', ',')

    if help_request.duration == 90:
        amount_to_pay = help_request.amount_to_pay
        amount_to_show = ('90 Minuten Nachhilfe - %s EUR' % amount_to_pay).replace('.', ',')

    return render(request, 'tutoring/pay_and_join.html', {
        'session_id': session_id,
        'help_request': help_request,
        'amount_to_show': amount_to_show,
        'amount_to_pay': str(amount_to_pay).replace(',', '.'),
        'paypal_client_id': settings.PAYPAL_CLIENT_ID
    })


@login_required
def process_payment(request, session_id):
    paypal = PayPalClient()

    payload = json.loads(request.body)
    order_id = payload.get('order_id')

    help_request = HelpRequest.objects.get(hash_id=session_id)

    if request.user.id not in [help_request.tutor_id, help_request.user_id]:
        return redirect(reverse('index'))

    paypal_request = OrdersGetRequest(order_id)
    response = paypal.client.execute(paypal_request)

    if response.status_code == 200:
        paid_amount = Decimal(response.result.purchase_units[0].amount.value)
        commission = paid_amount * settings.TUTORING_COMPANY_SHARE / 100
        users_share = paid_amount - commission

        # save payment details
        user_payment = Payment.objects.create(
            request_id=help_request.id,
            paypal_order_id=response.result.id,
            paid_amount=paid_amount,
            commission=commission,
            users_share=users_share
        )
        user_payment.user_id = request.user.id
        user_payment.save()

        help_request.users_share = users_share
        help_request.paid_at = timezone.now()
        help_request.save()

        help_request.inform_about_payment_success()

        # send email to user
        send_email_in_template(
            'Deine Zahlung in %s' % settings.DOMAIN,
            [request.user.email],
            **{
                'text': PAYMENT_SUCCESS_TEXT % (
                    request.user.username or request.user.username,
                    str(user_payment.paid_amount).replace('.', ','),
                    help_request.duration,
                    help_request.tutor.username
                )
            }
        )

        http_response = HttpResponse(json.dumps({
            'payment_hash_id': user_payment.hash_id
        }), content_type='application/json')

        return http_response

    return HttpResponse(response.result.status, status=response.status_code)


@login_required
def payment_success(request, session_id):
    help_request = HelpRequest.objects.get(hash_id=session_id)

    if request.user.id not in [help_request.tutor_id, help_request.user_id]:
        return redirect(reverse('index'))

    return redirect(reverse('request_detail', args=(help_request.hash_id,)))


@login_required
def save_tutor_review(request, session_id):
    help_request = HelpRequest.objects.get(hash_id=session_id)

    if request.user.id not in [help_request.tutor_id, help_request.user_id]:
        return HttpResponse('bad')

    tutor_feedback_text = request.POST.get('tutor_feedback_text')
    review = help_request.request_reviews.create(
        tutor_id=help_request.tutor_id,
        given_by_id=request.user.id,
        text=tutor_feedback_text,
        public=False
    )

    send_email_in_template(
        'Neue Nachhilfe-Bewertung ist eingegangen.',
        settings.ADMINS_TO_REPORT,
        **{
            'text': 'hey Leute, eine neue Nachhilfe-Bewertung ist eingegangen. '
                    'Bitte prüfen und freischalten.',
            'link_name': 'Jetzt Bewertung ansehen',
            'link': 'https://%s%stutoring/review/%s/change/' % (
                settings.DOMAIN, settings.ADMIN_URL, review.id
            )
        }
    )

    return HttpResponse('okay')


@login_required
def tutor_settings(request, pk):
    if request.user.id != pk:
        return redirect(reverse('public_profile', args=(request.user.id,)))

    user = request.user
    profile = user.profile

    if not hasattr(user, 'tutor_setting'):
        tutor_setting = TutorSetting.objects.create(
            user_id=user.id
        )
    else:
        tutor_setting = user.tutor_setting

    tutor_setting_form = PriceSettingForm(instance=tutor_setting)
    target_group_form = TargetGroupForm(instance=tutor_setting)
    if 'change_payment' in request.GET:
        payment_method_form = PaymentMethodForm()
    else:
        payment_method_form = PaymentMethodForm(instance=tutor_setting)

    given_sessions = HelpRequest.objects.filter(tutor_id=user.id).order_by('-id')

    number_mins_given_tutoring = given_sessions.aggregate(hours=Sum('duration')).get('hours', 0)
    if number_mins_given_tutoring:
        number_hours_given_tutoring = round(number_mins_given_tutoring / 60, 2)
    else:
        number_hours_given_tutoring = 0.0

    return render(request, 'user/tutor_settings.html', {
        'profile': profile,
        'tutor_setting': tutor_setting,
        'tutor_setting_form': tutor_setting_form,
        'target_group_form': target_group_form,
        'payment_method_form': payment_method_form,
        'payment_confirm_form': PaymentConfirmForm(),
        'video_form': VideoForm(),
        'payout_requests': PayoutRequest.objects.filter(user_id=user.id).order_by('-id'),
        'sessions': given_sessions,
        'number_hours_given_tutoring': number_hours_given_tutoring
    })


@login_required
def tutor_videos(request, pk):
    user = User.objects.get(id=pk)

    if not request.user.is_superuser:
        return redirect(reverse('public_profile', args=(request.user.id,)))

    profile = user.profile

    all_videos = Video.objects.filter(owner='daniel').order_by('-id')[:12]

    return render(request, 'user/videos.html', {
        'profile': profile,
        'all_videos': all_videos
    })


@login_required
def video_watch_view(request, hash_id):
    video = Video.objects.get(hash_id=hash_id)

    return render(request, 'user/video_detail.html', {
        'profile': User.objects.get(username='danieljung').profile,
        'video': video
    })


@login_required
def update_tutoring_status(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    form = TutorStatusForm(request.POST)
    if form.is_valid():
        is_active = form.cleaned_data.get('is_active')
        tutor_setting = user.tutor_setting
        tutor_setting.is_active = is_active
        tutor_setting.save()

    return redirect('%s?tutor_status_updated=1' % reverse('tutor_settings', args=(user.id,)))


@login_required
def update_video(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    tutor_setting = user.tutor_setting

    form = VideoForm(request.POST, request.FILES)
    if form.is_valid():
        delete_video = form.cleaned_data.get('delete_video')
        video_file = request.FILES.get('video')
        if video_file:
            tutor_setting.video = video_file
            tutor_setting.save()
        elif delete_video:
            # todo: delete the file also from aws
            tutor_setting.video = ''
            tutor_setting.save()

    return redirect('%s?video_saved=1' % reverse('tutor_settings', args=(user.id,)))


@login_required
def update_tutor_price(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    form = PriceSettingForm(request.POST)
    if form.is_valid():
        half_hourly_rate = form.cleaned_data.get('half_hourly_rate')
        hourly_rate = form.cleaned_data.get('hourly_rate')
        ninety_min_rate = form.cleaned_data.get('ninety_min_rate')

        tutor_setting = user.tutor_setting
        tutor_setting.half_hourly_rate = half_hourly_rate
        tutor_setting.hourly_rate = hourly_rate
        tutor_setting.ninety_min_rate = ninety_min_rate
        tutor_setting.save()

        return redirect('%s?tutor_price_updated=1' % reverse('tutor_settings', args=(user.id,)))

    return redirect('%s?tutor_price_error=1' % reverse('tutor_settings', args=(user.id,)))


@login_required
def update_target_group(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    form = TargetGroupForm(request.POST)
    if form.is_valid():
        university_modules = request.POST.getlist('uni_module')
        university_modules = ','.join(university_modules)

        sek_1 = form.cleaned_data.get('sek_1')
        sek_2 = form.cleaned_data.get('sek_2')
        note = form.cleaned_data.get('note')

        tutor_setting = user.tutor_setting
        tutor_setting.sek_1 = sek_1
        tutor_setting.sek_2 = sek_2
        tutor_setting.note = note
        tutor_setting.university_modules = university_modules
        tutor_setting.save()
        return redirect('%s?target_updated=1#target_settings' % reverse('tutor_settings', args=(user.id,)))

    return redirect('%s?target_error=1#target_settings' % reverse('tutor_settings', args=(user.id,)))


@login_required
def change_payment_type(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    form = PaymentMethodForm(request.POST)
    if form.is_valid():
        payment_type = form.cleaned_data.get('payment_type')
        paypal_email = form.cleaned_data.get('paypal_email')
        iban = form.cleaned_data.get('iban')
        bic = form.cleaned_data.get('bic')

        if not paypal_email and not iban and not bic:
            return redirect('%s?payment_type_error=1#payouts' % reverse('tutor_settings', args=(user.id,)))

        tutor_setting = user.tutor_setting
        tutor_setting.payment_type = payment_type
        tutor_setting.paypal_email = paypal_email
        tutor_setting.iban = iban
        tutor_setting.bic = bic

        tutor_setting.payment_changed_to = payment_type
        tutor_setting.payment_changed_at = timezone.now()
        tutor_setting.payment_confirm_code = random_five_digits()
        # reset this field
        tutor_setting.payment_confirmed_at = None

        tutor_setting.inform_admin_about_new_payment_details()
        tutor_setting.inform_user_about_new_payment_details()

        tutor_setting.save()
        return redirect('%s?payment_type_updated=1#payouts' % reverse('tutor_settings', args=(user.id,)))

    return redirect('%s?payment_type_code_error=1#payouts' % reverse('tutor_settings', args=(user.id,)))


@login_required
def confirm_payment_type(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    form = PaymentConfirmForm(request.POST)
    if form.is_valid():
        payment_confirm_code = form.cleaned_data.get('payment_confirm_code')

        tutor_setting = user.tutor_setting
        if tutor_setting.payment_confirm_code == payment_confirm_code:
            tutor_setting.payment_confirmed_at = timezone.now()
            tutor_setting.payment_confirm_code = ''
            tutor_setting.payment_changed_to = ''
            tutor_setting.save()

            # todo: inform user and admin about it

            return redirect('%s?payment_type_updated=1#payouts' % reverse('tutor_settings', args=(user.id,)))

    return redirect('%s?payment_type_code_error=1#payouts' % reverse('tutor_settings', args=(user.id,)))


@login_required
def delete_payment_type(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    setting_hash = request.POST.get('setting_hash')

    setting = TutorSetting.objects.get(hash_id=setting_hash)
    setting.payment_change_cancelled_at = timezone.now()
    setting.payment_changed_at = None
    setting.payment_confirm_code = ''
    setting.payment_type = ''
    setting.paypal_email = ''
    setting.iban = ''
    setting.bic = ''
    setting.payment_changed_to = ''
    setting.save()

    return redirect('%s?payment_type_updated=1#payouts' % reverse('tutor_settings', args=(user.id,)))


@login_required
def request_payout(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return redirect(reverse(request.user.profile.get_absolute_url()))

    payout_amount = request.POST.get('payout_amount')
    if not payout_amount:
        return redirect('%s?payout_amount_error=1#payouts' % reverse('tutor_settings', args=(user.id,)))

    try:
        payout_amount = Decimal(payout_amount)
    except Exception:
        return redirect('%s?payout_amount_error=1#payouts' % reverse('tutor_settings', args=(user.id,)))

    if payout_amount > user.profile.current_earnings_as_tutor():
        return redirect('%s?payout_amount_error=1#payouts' % reverse('tutor_settings', args=(user.id,)))

    if user.profile.current_earnings_as_tutor() < payout_amount:
        return redirect('%s?payout_amount_error=1#payouts' % reverse('tutor_settings', args=(user.id,)))

    new_payout_request = PayoutRequest.objects.create(
        user_id=user.id,
        amount=payout_amount,
        status='pending'
    )
    send_email_in_template(
        '%s hat Auszahlung angefragt' % user.username,
        settings.ADMINS_TO_REPORT,
        **{
            'text': '%s hat Auszahlung angefragt. Link:\n\n'
                    'https://%s%stutoring/payoutrequest/%s/change/' % (
                        user.username, settings.DOMAIN, settings.ADMIN_URL, new_payout_request.id
                    )
        }
    )
    return redirect('%s?payout_request_created=1#payouts' % reverse('tutor_settings', args=(user.id,)))
