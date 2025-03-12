import json

import boto3
import cloudinary.uploader
import requests
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.core.validators import validate_email, ValidationError
from django.db import IntegrityError
from django.db.models import Count, Q, Sum
from django.http import StreamingHttpResponse
from django.shortcuts import render, reverse, redirect, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, CreateView

from mathefragen.apps.core.utils import (
    send_email_in_template,
    create_default_hash,
    RepairImages,
)
from mathefragen.apps.guardian.models import BlockedIP
from mathefragen.apps.guardian.tools import ip
from mathefragen.apps.messaging.models import Message
from mathefragen.apps.question.models import Answer, Question
from mathefragen.apps.tutoring.models import HelpRequest
from mathefragen.apps.user.forms import (
    LoginForm,
    RegisterForm,
    BasicInfoForm,
    PasswordChangeForm,
    ImageChangeForm,
    PasswordSetForm,
    ApplyVerificationForm,
    AddSocialsForm,
    CompleteProfileForm,
    NotificationSettingsForm
)
from mathefragen.apps.user.models import (
    Profile,
    Social,
    Institution,
    PostalCode
)
from mathefragen.lib import validate_with_turnstile


class Login(FormView):

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect('/')

        login_form = LoginForm()

        context = {
            'login_form': login_form,
            'no_left_sidebar': True,
            'new_question_hash': request.GET.get('nqh', '')
        }

        return render(request, 'user/login.html', context)

    def post(self, request, *args, **kwargs):
        login_form = LoginForm(request.POST or None)

        if login_form.is_valid():
            login_id = login_form.cleaned_data.get('login_id').lower()
            password = login_form.cleaned_data.get('password')
            next_page = request.POST.get('next_page')
            new_question_hash = request.POST.get('nqh')

            turnstile_validation = validate_with_turnstile(request.POST.get('cf-turnstile-response'))
            if not turnstile_validation.get('success'):
                return render(request, 'user/login.html', {
                    'login_form': login_form,
                    'error': 'Bitte bestätige, dass du kein Roboter bist.',
                    'no_left_sidebar': True,
                })

            try:
                validate_email(login_id)
                valid_email = True
            except ValidationError:
                valid_email = False

            if valid_email:
                # check if user already exists
                if not User.objects.filter(email=login_id).count():
                    return render(request, 'user/login.html', {
                        'login_form': login_form,
                        'error': 'Diese E-Mail existiert nicht',
                        'no_left_sidebar': True
                    })

                user = User.objects.filter(email=login_id).last()

            else:
                # check if user already exists
                if not User.objects.filter(username=login_id).count():
                    return render(request, 'user/login.html', {
                        'login_form': login_form,
                        'error': 'Dieser Benutzername existiert nicht',
                        'no_left_sidebar': True
                    })

                user = User.objects.filter(username=login_id).last()

            user = authenticate(username=user.username, password=password)
            if user is not None:

                if not user.profile.is_active:
                    return redirect('/user/login/?profile-inactive=1')

                login(request, user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')

                if new_question_hash:
                    try:
                        question = Question.objects.get(hash_id=new_question_hash)
                        if not question.user_id:
                            question.go_online(user=user)
                            # update stats
                            stats = request.stats
                            stats.update_total_questions()

                            return redirect('%s?newquestion=1' % question.get_absolute_url())

                    except Question.DoesNotExist:
                        pass

                if next_page:
                    return redirect(next_page)
                return redirect(reverse('index'))
            else:
                return render(request, 'user/login.html', {
                    'login_form': login_form,
                    'error': 'Zugangsdaten sind falsch.',
                    'no_left_sidebar': True
                })

        return render(request, 'user/login.html', {
            'login_form': login_form,
            'error': 'Ungültige Eingaben.',
            'no_left_sidebar': True
        })


class ConfirmMissingView(LoginRequiredMixin, FormView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        if request.user.profile.has_confirmed_email():
            return redirect(reverse('index'))

        return render(request, 'user/confirm_email.html', {
            'no_left_sidebar': True
        })


class PasswordForgotView(FormView):

    def get(self, request, *args, **kwargs):
        return render(request, 'user/password_forgot.html', {
            'no_left_sidebar': True
        })

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email').lower()
        question_hash = request.POST.get('qh').lower()

        if not User.objects.filter(email=email).count():
            return redirect('%s?email_not_found=1' % reverse('password_forgot'))

        user = User.objects.filter(email=email).last()
        pw_onetime_hash = create_default_hash(length=10)

        user.profile.pw_onetime_hash = pw_onetime_hash
        user.profile.save()

        password_reset_link = 'https://%s%s?qh=%s' % (
            settings.DOMAIN,
            reverse('set_password', kwargs={
                'pw_onetime_hash': pw_onetime_hash
            }),
            question_hash
        )

        send_email_in_template(
            'Passwort zurücksetzen - mathefragen.de',
            [email],
            **{
                'text': '<p>Hier kannst du nun dein Passwort zurücksetzen. Bitte klicke hierzu den Button an: </p>',
                'link': password_reset_link,
                'link_name': 'Passwort zurücksetzen'
            }
        )

        return redirect('%s?password_is_set=1' % reverse('password_forgot'))


class SetPasswordView(FormView):

    def get(self, request, *args, **kwargs):
        password_set_form = PasswordSetForm()
        pw_onetime_hash = kwargs.get('pw_onetime_hash')

        try:
            profile = Profile.objects.get(pw_onetime_hash=pw_onetime_hash)
        except Profile.DoesNotExist:
            return render(request, 'user/set_new_password.html', {
                'error': 'Dieser Link scheint nicht mehr gültig zu sein :/',
                'no_left_sidebar': True
            })

        clicked_date = '%s.%s.%s-%s:%s' % (
            timezone.now().day, timezone.now().month, timezone.now().year, timezone.now().hour, timezone.now().minute
        )
        profile.pw_onetime_hash = '%s-%s' % (
            pw_onetime_hash, clicked_date
        )

        return render(request, 'user/set_new_password.html', {
            'password_set_form': password_set_form,
            'user_id': profile.user_id,
            'no_left_sidebar': True
        })

    def post(self, request, *args, **kwargs):

        password_set_form = PasswordSetForm(request.POST)
        user_id = request.POST.get('user_id')
        question_hash = request.POST.get('qh')

        if password_set_form.is_valid():
            password1 = password_set_form.cleaned_data.get('password1')
            password2 = password_set_form.cleaned_data.get('password2')

            if password1 != password2:
                return render(request, 'user/set_new_password.html', {
                    'password_set_form': password_set_form,
                    'user_id': user_id,
                    'error': 'Passwörter stimmen nicht überein.',
                    'no_left_sidebar': True
                })

            if len(password2) < 8:
                return render(request, 'user/set_new_password.html', {
                    'password_set_form': password_set_form,
                    'user_id': user_id,
                    'error': 'Passwort muss mindestens 8 Zeichen enthalten.',
                    'no_left_sidebar': True
                })

            user = User.objects.get(id=user_id)
            user.set_password(raw_password=password2)
            user.save()

            if question_hash:
                try:
                    question = Question.objects.get(hash_id=question_hash)
                    question.go_online(user=user)
                    return redirect('%s?newquestion=1' % question.get_absolute_url())
                except Question.DoesNotExist:
                    pass

            return redirect('%s?password_is_set=1' % reverse('login'))

        return render(request, 'user/set_new_password.html', {
            'password_set_form': password_set_form,
            'user_id': user_id,
            'error': 'Eingaben sind ungültig',
            'no_left_sidebar': True
        })


class Register(FormView):
    form_class = RegisterForm

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect('/')

        context = {
            'register_form': self.get_form(),
            'no_left_sidebar': True,
            'new_question_hash': request.GET.get('nqh', '')
        }
        return render(request, 'user/register.html', context)

    def post(self, request, *args, **kwargs):
        register_form = RegisterForm(request.POST)
        next_url = request.POST.get('next')
        new_question_hash = request.POST.get('nqh')

        if register_form.is_valid():
            username = register_form.cleaned_data.get('username').lower()
            email = register_form.cleaned_data.get('email').lower()
            password = register_form.cleaned_data.get('password')

            # todo: this should be off, in case of company.
            found_ip = ip.IP(request=request).user_ip()
            if found_ip and BlockedIP.objects.filter(ip=found_ip).count() > 0:
                return render(request, 'user/register.html', {
                    'register_form': register_form,
                    'error': 'Sorry, die Registrierung ist temporär nicht möglich.',
                    'no_left_sidebar': True
                })

            # check if username exists
            if User.objects.filter(username=username).count():
                return render(request, 'user/register.html', {
                    'register_form': register_form,
                    'error': 'Dieser Benutzername existiert bereits',
                    'no_left_sidebar': True,
                    'new_question_hash': new_question_hash
                })

            # check if email exists
            if User.objects.filter(email=email).count():
                return render(request, 'user/register.html', {
                    'register_form': register_form,
                    'error': 'Diese E-Mail existiert bereits',
                    'no_left_sidebar': True,
                    'new_question_hash': new_question_hash
                })

            if len(password) < 8:
                return render(request, 'user/register.html', {
                    'register_form': register_form,
                    'error': 'Passwort muss mindestens aus 8 Zeichen bestehen',
                    'no_left_sidebar': True,
                    'new_question_hash': new_question_hash
                })

            if len(username) > 16:
                return render(request, 'user/register.html', {
                    'register_form': register_form,
                    'error': 'Benutzername ist zu lang',
                    'no_left_sidebar': True,
                    'new_question_hash': new_question_hash
                })

            turnstile_validation = validate_with_turnstile(request.POST.get('cf-turnstile-response'))
            if not turnstile_validation.get('success'):
                return render(request, 'user/register.html', {
                    'register_form': register_form,
                    'error': 'Bitte bestätige, dass du kein Roboter bist.',
                    'no_left_sidebar': True,
                    'new_question_hash': new_question_hash
                })

            try:
                user = User.objects.create(
                    username=username, email=email, is_active=False
                )
            except IntegrityError:
                # somehow this happens sometimes :/
                return render(request, 'user/register.html', {
                    'register_form': register_form,
                    'error': 'Dieser Benutzername existiert bereits',
                    'no_left_sidebar': True,
                    'new_question_hash': new_question_hash
                })

            user.set_password(raw_password=password)
            user.save()

            stats = request.stats
            stats.update_total_users()

            user.profile.send_email_confirmation()

            # login user already
            login(request, user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')

            if new_question_hash:
                try:
                    question = Question.objects.get(hash_id=new_question_hash)
                    if not question.user_id:
                        question.go_online(user=user)

                        # update stats
                        stats = request.stats
                        stats.update_total_questions()

                        return redirect('%s?newquestion=1' % question.get_absolute_url())

                except Question.DoesNotExist:
                    pass

            if next_url:
                next_url = next_url + '?newuser=1'
                return redirect(next_url)

            return redirect('%s?newuser=1' % reverse('index'))

        return render(request, 'user/register.html', {
            'register_form': register_form,
            'error': 'Ungültige Eingaben.',
            'no_left_sidebar': True
        })


class JoinWithQuestion(FormView):

    def get(self, request, *args, **kwargs):
        step = 1
        return render(request, 'user/join_with_question.html', {
            'no_left_sidebar': True,
            'step': step,
            'new_question_hash': request.GET.get('nqh', '')
        })

    def post(self, request, *args, **kwargs):
        new_user = True
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')
        final_step = request.POST.get('final_step')
        new_question_hash = request.POST.get('nqh')

        try:
            question = Question.objects.get(hash_id=new_question_hash)
            if question.confirmed and question.user_id:
                return redirect(reverse('create_question'))

        except Question.DoesNotExist:
            return redirect(reverse('create_question'))

        if final_step:
            # we login or create new account and redirect to question detail page and make question online.
            # inside question page, we ask user to confirm the email.
            if user_type == 'new':
                random_username = 'user%s' % create_default_hash(length=3)
                user = User.objects.create(
                    username=random_username,
                    email=email,
                    is_active=False
                )
                user.set_password(raw_password=password)
                user.save()

                question.go_online(user=user)

                # update stats
                stats = request.stats
                stats.update_total_questions()

                user.profile.send_email_confirmation()

                login(request, user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')

                return redirect('%s?newquestion=1' % question.get_absolute_url())

            else:
                # just login
                new_user = False

                user = User.objects.filter(email=email).last()
                if not user:
                    return render(request, 'user/join_with_question.html', {
                        'error': 'Zugangsdaten sind falsch.',
                        'no_left_sidebar': True,
                        'new_user': new_user,
                        'user_type': user_type,
                        'final_step': final_step,
                        'email': email,
                        'new_question_hash': new_question_hash
                    })

                user = authenticate(username=user.username, password=password)
                if user is not None:
                    login(request, user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')

                    if not question.user_id:
                        question.go_online(user=user)

                        # update stats
                        stats = request.stats
                        stats.update_total_questions()

                        return redirect('%s?newquestion=1' % question.get_absolute_url())

                    # this should not happen, just in case, question hash is wrong.
                    return redirect(reverse('index'))

                else:
                    return render(request, 'user/join_with_question.html', {
                        'error': 'Zugangsdaten sind falsch.',
                        'no_left_sidebar': True,
                        'new_user': new_user,
                        'user_type': user_type,
                        'final_step': final_step,
                        'email': email,
                        'new_question_hash': new_question_hash
                    })
        else:
            if User.objects.filter(email=email).count():
                new_user = False

        return render(request, 'user/join_with_question.html', {
            'no_left_sidebar': True,
            'new_user': new_user,
            'user_type': user_type,
            'email': email,
            'final_step': final_step,
            'new_question_hash': new_question_hash
        })


@csrf_exempt
def sync_new_user(request):
    # todo: move to DRF
    try:
        json_data = json.loads(request.body.decode('utf-8'))
    except json.decoder.JSONDecodeError:
        return HttpResponse('no payload, my friend')

    username = json_data.get('username')
    first_name = json_data.get('first_name')
    last_name = json_data.get('last_name')
    email = json_data.get('email')
    profile_image_url = json_data.get('profile_image_url')
    status = json_data.get('status')
    other_status = json_data.get('other_status')
    # already hashed password
    password = json_data.get('password')
    bio_text = json_data.get('bio_text')
    origin = json_data.get('origin')
    source_s3_bucket = json_data.get('source_s3_bucket')

    if not User.objects.filter(username__iexact=username).count():
        new_synced_user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_active=True
        )

        stats = request.stats
        stats.update_total_users()

        profile = new_synced_user.profile
        profile.status = status
        profile.other_status = other_status
        profile.bio_text = bio_text
        profile.origin = origin

        if profile_image_url:
            # copy s3 file from source bucket in this bucket
            s3 = boto3.resource('s3')
            profile_image_url = 'media/%s' % profile_image_url.split('media/')[1]
            source_to_copy = {'Bucket': source_s3_bucket, 'Key': profile_image_url}
            s3.meta.client.copy(
                source_to_copy,
                settings.AWS_STORAGE_BUCKET_NAME,
                profile_image_url
            )
            profile.profile_image = profile_image_url.replace('media/', '')

        profile.synced = True
        profile.save()

        return HttpResponse(json.dumps({'status': 'sync ok'}), content_type='application/json')

    user = User.objects.filter(username__iexact=username).last()
    user.profile.synced = True
    user.profile.save()

    return HttpResponse(json.dumps({'status': 'username exists already'}), content_type='application/json')


def register_confirm(request, confirm_hash):
    if not Profile.objects.filter(confirm_hash=confirm_hash).count():
        return redirect(reverse('index'))

    profile = Profile.objects.filter(confirm_hash=confirm_hash).last()
    clicked_date = '%s.%s.%s-%s:%s' % (
        timezone.now().day, timezone.now().month, timezone.now().year, timezone.now().hour, timezone.now().minute
    )
    profile.confirm_hash = '%s-%s-confirmed' % (
        confirm_hash, clicked_date
    )
    profile.save()

    profile.user.is_active = True
    profile.user.save()

    login(request, profile.user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')

    qh = request.GET.get('qh')
    try:
        question = Question.objects.get(hash_id=qh)
        question.go_online(user=profile.user)
        return redirect('%s?newquestion=1' % question.get_absolute_url())
    except Question.DoesNotExist:
        pass

    return redirect('%s?confirmed=1' % reverse('index'))


@login_required
def update_last_active(request, pk):
    if request.method != 'POST':
        return HttpResponse('I speak only POST')

    user = request.user

    if user.id != pk:
        return HttpResponse('this is not you')

    user.profile.last_active = timezone.now()
    user.profile.save()

    return HttpResponse('ok')


def all_users(request):
    users = Profile.objects.filter(reported__lt=3).order_by('-points')

    if request.GET.get('q', ''):
        users = users.filter(user__username__icontains=request.GET.get('q', ''))

    sort = request.GET.get('sort', '')

    if 'new' in sort:
        users = users.order_by('-id')

    if 'top_helping' in sort:
        users = users.order_by('-total_answers')

    if 'week_helper' in sort:
        users = users.order_by('-answers_this_week')

    if 'month_helper' in sort:
        users = users.order_by('-answers_this_month')

    if 'mods' in sort:
        users = users.annotate(questions=Count('user_questions')).order_by('-questions')

    paginator = Paginator(users, 40)

    page = request.GET.get('page')

    users = paginator.get_page(page)

    return render(request, 'user/index.html', {
        'users': users
    })


def public_profile(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return redirect(reverse('index'))

    if user.profile.reported > 2:
        return redirect(reverse('index'))

    given_answers = None
    if not user.profile.asked_questions().count():
        given_answers = Answer.objects.filter(user_id=user.id).order_by('-idate')[:5]

    return render(request, 'user/profile.html', {
        'profile': user.profile,
        'given_answers': given_answers
    })


def public_profile_hashed(request, hash_id):
    try:
        profile = Profile.objects.get(hash_id=hash_id)
    except Profile.DoesNotExist:
        return redirect(reverse('index'))

    if profile.reported > 2:
        return redirect(reverse('index'))

    given_answers = None
    if not profile.asked_questions().count():
        given_answers = Answer.objects.filter(user_id=profile.user_id).order_by('-idate')[:5]

    given_sessions = HelpRequest.objects.filter(tutor_id=profile.user_id).order_by('-id')

    number_mins_given_tutoring = given_sessions.aggregate(hours=Sum('duration')).get('hours', 0)
    if number_mins_given_tutoring:
        number_hours_given_tutoring = round(number_mins_given_tutoring / 60, 2)
    else:
        number_hours_given_tutoring = 0.0

    return render(request, 'user/profile.html', {
        'profile': profile,
        'given_answers': given_answers,
        'sessions': given_sessions,
        'number_hours_given_tutoring': number_hours_given_tutoring
    })


@login_required
def set_profile_image(request, hash_id):
    if request.method == 'POST':
        cloudinary_response = request.POST.get('cloudinary_response')
        json_response = json.loads(cloudinary_response)

        """
        asset_id: "97bbe63bc498bfc984a5dec3557bcd9b"
        batchId: "uw-batch2"
        bytes: 116234
        created_at: "2021-02-09T08:03:42Z"
        etag: "40cb3159cecbb19746c0be8b69cb4810"
        format: "png"
        height: 2000
        id: "uw-file3"
        original_filename: "icon_only"
        path: "v1612857822/ykrxlsbe7mouuwqdgaux.png"
        placeholder: false
        public_id: "ykrxlsbe7mouuwqdgaux"
        resource_type: "image"
        secure_url: "https://res.cloudinary.com/dqajvdtr3/image/upload/v1612857822/ykrxlsbe7mouuwqdgaux.png"
        signature: "d8a4464f66238e83fcc27835b6601303ec853c9b"
        tags: []
        thumbnail_url: "https://res.cloudinary.com/dqajvdtr3/image/upload/c_limit,h_60,w_90/v1612857822/ykrxlsbe7mouuwqdgaux.png"
        type: "upload"
        url: "http://res.cloudinary.com/dqajvdtr3/image/upload/v1612857822/ykrxlsbe7mouuwqdgaux.png"
        version: 1612857822
        version_id: "956db27d4a566afdca30cbf1a7566b7b"
        width: 2000
        """

        public_id = json_response.get('public_id')
        file_format = json_response.get('format')
        file_version = json_response.get('version')

        secure_url = json_response.get('secure_url')
        # scale to width 300
        secure_url = secure_url.replace('v%s' % file_version, 'w_300')

        final_path = 'user/%s/%s' % (
            request.user.profile.hash_id, '%s.%s' % (public_id, file_format)
        )

        with requests.get(secure_url, stream=True) as r:
            with default_storage.open(final_path, 'wb+') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

        request.user.profile.profile_image = final_path
        request.user.profile.save()

        # delete from cloudinary
        cloudinary.uploader.destroy(public_id, invalidate=True)

        return HttpResponse('okay')


@login_required
def download_certificate(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return redirect('/')

    certificate_url = user.profile.generate_certificate()

    pdf_file_response = requests.get('https://media.mathefragen.de/media/' + certificate_url, stream=True)

    response = StreamingHttpResponse(streaming_content=pdf_file_response.raw)
    response['Content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'attachment; filename="%s"' % certificate_url.split('/')[-1]
    return response


def public_profile_answers(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return redirect('/')

    given_answers = Answer.objects.filter(user_id=user.id).order_by('-idate')[:5]

    return render(request, 'user/profile.html', {
        'profile': user.profile,
        'given_answers': given_answers
    })


def public_profile_following_content(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return redirect('/')

    return render(request, 'user/profile.html', {
        'profile': user.profile
    })


def public_profile_articles(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return redirect('/')

    articles = user.user_questions.filter(type='article').order_by('-id')

    return render(request, 'user/profile.html', {
        'profile': user.profile,
        'written_articles': articles
    })


def profile_socials(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return redirect('/')

    return render(request, 'user/socials.html', {
        'profile': user.profile,
        'socials': user.user_socials.all()
    })


class EditSocials(LoginRequiredMixin, CreateView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        user = User.objects.get(id=kwargs.get('pk'))
        social = Social.objects.get(id=kwargs.get('social_pk'))

        form = AddSocialsForm(initial={
            'link': social.link,
            'type': social.type,
            'description': social.description
        })

        if request.user != user:
            return redirect(reverse('profile_socials', kwargs={'pk': request.user.id}))

        return render(request, 'user/add_socials.html', {
            'form': form,
            'profile': user.profile,
            'social': social
        })


@login_required
def delete_social(request, pk, social_pk):
    social = Social.objects.get(id=social_pk)

    if request.user.id != social.user_id:
        return redirect(reverse('profile_socials', kwargs={'pk': request.user.id}))

    social.delete()

    return redirect(reverse('profile_socials', kwargs={'pk': request.user.id}))


class AddSocials(LoginRequiredMixin, CreateView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        form = AddSocialsForm()
        user = User.objects.get(id=kwargs.get('pk'))

        if request.user != user:
            return redirect(reverse('profile_socials', kwargs={'pk': request.user.id}))

        return render(request, 'user/add_socials.html', {
            'form': form,
            'profile': user.profile
        })

    def post(self, request, *args, **kwargs):
        user = User.objects.get(id=kwargs.get('pk'))
        form = AddSocialsForm(request.POST)

        if form.is_valid():
            social_type = form.cleaned_data.get('type')
            link = form.cleaned_data.get('link')
            description = form.cleaned_data.get('description')
            social_id = request.POST.get('social_id')

            if 'http://' in link:
                link = link.replace('http://', 'https://')

            if 'https://' not in link:
                link = 'https://%s' % link

            if social_id:
                # editing
                social = Social.objects.get(id=social_id)

                social.link = link
                social.description = description
                social.type = social_type
                social.save()
            else:
                user.user_socials.create(
                    type=social_type, link=link, description=description
                )

            return redirect(reverse('profile_socials', kwargs={'pk': user.id}))

        return render(request, 'user/add_socials.html', {
            'form': form,
            'profile': user.profile,
            'errors': form.errors
        })


@login_required
def profile_settings(request, pk):
    if request.user.id != pk:
        return redirect(reverse('public_profile', args=(request.user.id,)))

    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return redirect('/')

    password_change_form = PasswordChangeForm()
    notification_settings_form = NotificationSettingsForm(initial={
        'email_notification': ''
    })

    basic_form = BasicInfoForm(initial={
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.profile.phone_number,
        'email': user.email,
        'bio': user.profile.bio_text,
        'skills': user.profile.skills,
        'status': user.profile.status,
        'other_status': user.profile.other_status
    })

    email_can_be_changed = True
    email_is_confirmed = True
    if 'confirmed' not in user.profile.confirm_hash:
        email_can_be_changed = False
        email_is_confirmed = False
        basic_form.fields['email'].widget.attrs.update({'disabled': 'disabled'})

    image_form = ImageChangeForm()

    return render(request, 'user/settings.html', {
        'basic_form': basic_form,
        'image_form': image_form,
        'email_can_be_changed': email_can_be_changed,
        'email_is_confirmed': email_is_confirmed,
        'profile': user.profile,
        'password_change_form': password_change_form
    })


@login_required
def resend_confirm_email(request, pk):
    profile = request.user.profile
    profile.send_email_confirmation()
    return HttpResponse('ok')


class ProfileReviews(FormView):

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return redirect('/')

        if user.received_user_reviews.count() < 1:
            return redirect(user.profile.get_absolute_url())

        return render(request, 'user/reviews.html', {
            'reviews': user.received_user_reviews.order_by('-id'),
            'profile': user.profile
        })


@login_required
def skip_profile_completion(request, pk):
    user = request.user
    user.profile.skipped_data_at = timezone.now()
    user.profile.save()
    return HttpResponse('ok')


@login_required
def fill_missing_data(request, pk):
    user = request.user

    url_to_return = '/'

    if request.method == 'POST':
        form = CompleteProfileForm(request.POST)
        fields_to_save = request.POST.get('fields_to_save', '')
        fields_to_save = [f for f in fields_to_save.split(',') if f.strip()]
        url_to_return = request.POST.get('url_to_return')
        if form.is_valid():
            for field in fields_to_save:
                if field == 'institution':
                    institution_name = form.cleaned_data.get(field)
                    if institution_name:
                        if Institution.objects.filter(name__iexact=institution_name).count():
                            institution = Institution.objects.filter(name__iexact=institution_name).last()
                        else:
                            institution = Institution.objects.create(name=institution_name)
                        user.profile.institution_id = institution.id

                elif field == 'postal_code':
                    postal_code = form.cleaned_data.get(field)
                    if postal_code:
                        if PostalCode.objects.filter(code=postal_code).count():
                            postal_code = PostalCode.objects.filter(code=postal_code).last()
                        else:
                            postal_code = PostalCode.objects.create(code=postal_code)
                        user.profile.postal_code_id = postal_code.id

                elif field == 'first_name':
                    user.first_name = form.cleaned_data.get(field)
                elif field == 'last_name':
                    user.last_name = form.cleaned_data.get(field)
                else:
                    setattr(user.profile, field, form.cleaned_data.get(field))

            user.save()
            user.profile.filled_data_at = timezone.now()
            user.profile.save()

    response = HttpResponseRedirect(url_to_return)

    return response


@login_required
def update_basic_info(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return render(request, 'user/profile.html', {
            'profile': request.user.profile
        })

    basic_form = BasicInfoForm(request.POST or None)

    if basic_form.is_valid():
        username = basic_form.cleaned_data.get('username').lower()
        email = basic_form.cleaned_data.get('email').lower()
        first_name = basic_form.cleaned_data.get('first_name')
        last_name = basic_form.cleaned_data.get('last_name')
        phone_number = basic_form.cleaned_data.get('phone_number')
        bio = basic_form.cleaned_data.get('bio')
        skills = basic_form.cleaned_data.get('skills')
        status = basic_form.cleaned_data.get('status')
        other_status = basic_form.cleaned_data.get('other_status')

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        profile = user.profile
        profile.bio_text = bio
        profile.phone_number = phone_number
        profile.skills = skills
        profile.status = status
        profile.other_status = other_status

        if email != profile.user.email:
            profile.user.is_active = False
            profile.confirm_hash = create_default_hash(length=12)

        if username and username != request.user.username:
            if not User.objects.filter(username=username).count():
                user.username = username
                user.save()
            else:
                return render(request, 'user/settings.html', {
                    'profile': user.profile,
                    'basic_form': basic_form,
                    'password_change_form': PasswordChangeForm(),
                    'basis_form_error': 'Dieser Benutzername existiert bereits.'
                })

        if email and email != request.user.email:
            if not User.objects.filter(email=email).count():
                user.email = email
                user.save()
                user.profile.send_email_confirmation()
            else:
                return render(request, 'user/settings.html', {
                    'profile': user.profile,
                    'basic_form': basic_form,
                    'password_change_form': PasswordChangeForm(),
                    'basis_form_error': 'Diese E-Mail Adresse existiert bereits.'
                })

        profile.save()
        profile.update_question_speed_fields()

        next_page = request.POST.get('next')
        if next_page:
            return redirect(next_page)

        return redirect('%s?basic_updated=1' % reverse('profile_settings', kwargs={'pk': pk}))

    return render(request, 'user/settings.html', {
        'profile': user.profile,
        'basic_form': basic_form,
        'password_change_form': PasswordChangeForm(),
        'basis_form_error': 'Ungültige Eingaben'
    })


@login_required
def change_pwd(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return render(request, 'user/profile.html', {
            'profile': request.user.profile
        })

    password_form = PasswordChangeForm(request.POST or None)

    basic_form = BasicInfoForm(initial={
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'bio': user.profile.bio_text
    })

    if password_form.is_valid():
        current_password = password_form.cleaned_data.get('current_password')
        password1 = password_form.cleaned_data.get('password1')
        password2 = password_form.cleaned_data.get('password2')

        if not user.password:
            # this is the case of login with phone number. Please check if this is not a security breach
            user.set_password(raw_password=current_password)
            user.save()

        if not user.check_password(raw_password=current_password):
            return render(request, 'user/settings.html', {
                'profile': user.profile,
                'basic_form': basic_form,
                'password_change_form': password_form,
                'pwd_error': 'Aktuelles Passwort falsch'
            })

        if password1 != password2:
            return render(request, 'user/settings.html', {
                'profile': user.profile,
                'basic_form': basic_form,
                'password_change_form': password_form,
                'pwd_error': 'Neue Passwörter stimmen nicht überein'
            })

        if len(password2) < 8:
            return render(request, 'user/settings.html', {
                'profile': user.profile,
                'basic_form': basic_form,
                'password_change_form': password_form,
                'pwd_error': 'Passwortlänge muss mindestens 8 sein'
            })

        user.set_password(raw_password=password2)
        user.save()

        # re-login user again
        login(request, user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')

        return redirect('%s?pwd_updated=1#security_card' % reverse('profile_settings', kwargs={'pk': pk}))

    return render(request, 'user/settings.html', {
        'profile': user.profile,
        'basic_form': basic_form,
        'password_change_form': password_form,
        'pwd_error': 'Ungültige Eingaben'
    })


@login_required
def change_image(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return render(request, 'user/profile.html', {
            'profile': request.user.profile
        })

    image = request.FILES.get('image')

    user.profile.profile_image = image
    user.profile.save(update_fields=['profile_image'])

    # repairs image rotation in background
    RepairImages(img_url=user.profile.profile_image.url).start()

    return redirect('%s?image_updated=1' % reverse('profile_settings', kwargs={'pk': pk}))


@login_required
def change_privacy(request, pk):
    user = User.objects.get(id=pk)

    if request.user.id != pk:
        return render(request, 'user/profile.html', {
            'profile': request.user.profile
        })

    hide_email = request.POST.get('hide_email')
    hide_full_name = request.POST.get('hide_full_name')
    hide_username = request.POST.get('hide_username')

    hide_email = hide_email == 'on'
    hide_full_name = hide_full_name == 'on'
    hide_username = hide_username == 'on'

    user.profile.hide_email = hide_email
    user.profile.hide_full_name = hide_full_name
    user.profile.hide_username = hide_username
    user.profile.save(
        update_fields=['hide_email', 'hide_full_name', 'hide_username']
    )

    return redirect('%s?privacy_updated=1#privacy_card' % reverse('profile_settings', kwargs={'pk': pk}))


@login_required
def inbox(request, pk):
    user = User.objects.get(id=pk)
    if request.user.id != pk:
        return redirect(user.profile.get_absolute_url())

    msg_type = request.GET.get('type')

    received_messages = Message.objects.filter(to_users__id=user.id).order_by('-idate')
    global_messages = Message.objects.filter(to_all=True).order_by('-idate')

    messages = received_messages | global_messages

    answer_types_count = messages.filter(type='Antwort').count()
    comment_types_count = messages.filter(type='Kommentar').count()
    review_types_count = messages.filter(type='Bewertung').count()
    upvote_types_count = messages.filter(type='upvote').count()
    downvote_types_count = messages.filter(type='downvote').count()
    accepted_answers = messages.filter(type='Akzeptiert').count()
    help_requests = messages.filter(type='Nachhilfe').count()

    if msg_type:
        if msg_type == 'vote':
            messages = messages.filter(Q(type='upvote') | Q(type='downvote'))
        else:
            messages = messages.filter(type=msg_type)

    paginator = Paginator(messages, 20)
    page = request.GET.get('page')
    messages = paginator.get_page(page)

    return render(request, 'messages.html', {
        'pk': pk,
        'messages': messages,
        'answer_types_count': answer_types_count,
        'comment_types_count': comment_types_count,
        'upvote_types_count': upvote_types_count,
        'downvote_types_count': downvote_types_count,
        'review_types_count': review_types_count,
        'help_requests': help_requests,
        'accepted_answers': accepted_answers
    })


@login_required
def delete_account(request):
    user = request.user

    # later do some other cleanups
    user.delete()

    stats = request.stats
    stats.update_total_users()

    return redirect('%s?account_deleted=1' % reverse('index'))


@login_required
def fetch_messages(request, pk):
    """
    fetches the latest 6 messages
    """
    three_weeks_ago = timezone.now() - timezone.timedelta(weeks=3)

    received_messages = Message.objects.filter(
        to_users__id=request.user.id,
        idate__gte=three_weeks_ago
    ).order_by('-idate')

    global_messages = Message.objects.filter(
        to_all=True,
        idate__gte=three_weeks_ago
    ).order_by('-idate')

    messages = received_messages | global_messages

    final_messages = []
    for msg in messages.order_by('-id'):
        msg_dict = {
            'title': '%s...' % msg.title[:50],
            'link': msg.link,
            'message': '%s...' % msg.message.replace('\n', '').replace('\r', '')[:50],
            'read': bool(request.user.user_read_messages.filter(message_id=msg.id).count()),
            'type': msg.type,
            'date': naturaltime(msg.idate)
        }
        final_messages.append(msg_dict)

    for msg in received_messages:
        if not request.user.user_read_messages.filter(message_id=msg.id).count():
            request.user.user_read_messages.create(
                message_id=msg.id
            )

    for msg in global_messages:
        if not request.user.user_read_messages.filter(message_id=msg.id).count():
            request.user.user_read_messages.create(
                message_id=msg.id
            )

    return HttpResponse(
        json.dumps(final_messages),
        content_type='application/json'
    )


class ApplyVerificationView(LoginRequiredMixin, FormView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        form = ApplyVerificationForm()

        return render(request, 'user/apply_verification.html', {
            'form': form
        })

    def post(self, request, *args, **kwargs):
        form = ApplyVerificationForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get('reason')
            user = request.user

            send_email_in_template(
                'Antrag auf Verifizierung - mathefragen.de',
                ['support@mathefragen.de'],
                **{
                    'text': '<p>User %s möchte ein Verification-Icon haben</p>'
                            '<p>Sein Grund: %s</p>' % (user.profile.id, reason)
                }
            )

            return redirect('%s?verification_applied=1' % reverse('apply_verification'))

        return redirect('%s?something_wrong=1' % reverse('apply_verification'))
