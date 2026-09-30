import json
import logging
import math
from collections import Counter, defaultdict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db.models import F
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView

from mathefragen.apps.core.utils import (
    create_default_hash,
    RepairImages
)
from mathefragen.apps.guardian.models import BlockedIP
from mathefragen.apps.guardian.tools import ip
from mathefragen.apps.hashtag.models import HashTag
from mathefragen.apps.question.forms import CreateQuestionForm
from mathefragen.apps.question.models import (
    Question,
    Answer,
    QuestionComment,
    AnswerComment,
)
from mathefragen.apps.question.utils import filter_questions
from mathefragen.apps.user.models import Profile
from mathefragen.apps.vote.models import Vote
from mathefragen.lib import validate_with_turnstile

logger = logging.getLogger(__name__)


def mathefragen_landing(request):
    return render(request, 'landing/www.mathefragen.de.html', {
        'no_left_sidebar': True,
        'show_nav': True
    })


def index(request):
    src = request.GET.get('src', '')

    user_id = request.GET.get('user', '').replace('/', '')
    answered_user_id = request.GET.get('answered_user', '').replace('/', '')
    question_filter = request.GET.get('filter', '')

    try:
        page = request.GET.get('page', 1)
        if isinstance(page, str):
            page = page.replace('/', '')
        page = int(page)
    except ValueError:
        page = 1

    page = 1 if page < 1 else page

    number_questions, questions, max_page, page = filter_questions(
        question_filter=question_filter,
        user_id=user_id,
        answered_user_id=answered_user_id,
        page=page
    )

    answered_user = ''
    if answered_user_id:
        try:
            answered_user = User.objects.get(id=answered_user_id)
        except User.DoesNotExist:
            pass

        if hasattr(answered_user, 'profile'):
            answered_user = answered_user.profile.get_full_name

    return render(request, 'index.html', {
        'questions': questions,
        'answered_user': answered_user,
        'number_of_questions': number_questions,
        'number_of_pages': math.ceil(number_questions / 20),
        'page': page,
        'next_page': True if page < max_page else False,
        'prev_page': True if page > 1 else False,
    })


class CreateQuestion(FormView):

    def get(self, request, *args, **kwargs):
        question_id = kwargs.get('question_id')

        context = {
            'question_form': CreateQuestionForm()
        }

        # in this case, this question is being edited
        if question_id and request.user.is_authenticated:
            question = Question.objects.get(id=question_id)

            if request.user.id == question.user_id or request.user.profile.can_edit_questions():
                initial_data = {
                    'title': question.title,
                    'question_text': question.text,
                    'question_id': question_id,
                    'being_edited': 'yes'
                }
                if not question.can_be_edited() and not request.user.profile.is_moderator():
                    initial_data['question_text'] = ''

                question_form = CreateQuestionForm(initial=initial_data)

                context.update({
                    'can_be_edited': question.can_be_edited() or request.user.profile.is_moderator(),
                    'question_form': question_form,
                    'question': question,
                    'tags': json.dumps(list(question.question_hashtags.values('id', 'name')))
                })

        return render(request, 'question/create.html', context)

    def post(self, request, *args, **kwargs):
        question_form = CreateQuestionForm(request.POST)
        if question_form.is_valid():
            question_form_data = question_form.cleaned_data

            title = question_form_data.get('title')
            is_article = question_form_data.get('is_article')
            question_text = question_form_data.get('question_text')
            tags = question_form_data.get('question_tags')
            being_edited = question_form_data.get('being_edited')
            question_id = question_form_data.get('question_id')

            being_edited = being_edited == 'yes'

            turnstile_validation = validate_with_turnstile(request.POST.get('cf-turnstile-response'))
            if not turnstile_validation.get('success'):
                return render(request, 'question/create.html', {
                    'question_form': question_form,
                    'error': 'Bitte bestätige, dass du kein Roboter bist.',
                })

            found_ip = ip.IP(request=request).user_ip()
            if found_ip and BlockedIP.objects.filter(ip=found_ip).count() > 0:
                return render(request, 'question/create.html', {
                    'question_form': question_form,
                    'error': 'Sorry, die Registrierung ist temporär nicht möglich.',
                })

            if len(title) < 10 and not question_id:
                context = {
                    'question_form': question_form,
                    'title_error': 'Titel der Frage muss mindestens 10 Zeichen lang sein.'
                }
                return render(request, 'question/create.html', context)

            if not being_edited:
                already_asked = Question.question_already_asked(question_title=title.strip())
                if already_asked:
                    return redirect('%s?already_asked=1' % reverse('create_question'))

            device = '%s,%s,%s' % (
                request.user_agent.device.family,
                request.user_agent.device.brand,
                request.user_agent.device.model
            )

            if being_edited and request.user.is_authenticated:
                question = Question.objects.get(id=question_id)
                if question.can_be_edited() or request.user.profile.is_moderator():
                    question.title = title
                    question.text = question_text
                else:
                    edit_separator = '<p class="font15 font-weight-600 mt-3">EDIT vom %s:</p>' % timezone.now().strftime(
                        '%d.%m.%Y um %H:%M')
                    question.text += edit_separator
                    question.text += question_text

                # todo: offload out these small things into separate module
                # remove reports, as we hope that user has edited his question to make it better
                question.question_reports.all().delete()
                # set question visible again
                question.is_active = True

                question.edited_by_id = request.user.id
                question.edited_at = timezone.now()
                question.save()

            else:
                source_ip = '192.168.0.1'
                found_ip = ip.IP(request=request).user_ip()
                if found_ip:
                    source_ip = found_ip

                question_type = 'article' if is_article == 'True' else 'question'
                question = Question.objects.create(
                    title=title,
                    text=question_text,
                    device=device,
                    type=question_type,
                    source_ip=source_ip,
                    is_active=False
                )
                if request.user.is_authenticated:
                    question.go_online(user=request.user)
                    # update stats
                    stats = request.stats
                    stats.update_total_questions()

            question.repair_images()

            new_tags = [tag_name.strip().lower() for tag_name in tags.split(',') if tag_name and tag_name.strip()]

            if question.can_be_edited():
                # clean out old hashtags & (re)set tags
                question.question_hashtags.clear()

            for tag in new_tags:
                tag = tag.lower()

                if not HashTag.objects.filter(name=tag).count():
                    hashtag = HashTag.objects.create(name=tag)
                else:
                    hashtag = HashTag.objects.filter(name=tag).last()

                hashtag.questions.add(question.id)

            # re-rank in index page
            if request.user.is_authenticated:
                if being_edited:
                    question.re_rank(reason='geändert', last_acted_user=request.user)
                else:
                    if is_article != 'False':
                        question.re_rank(reason='geschrieben', last_acted_user=request.user)
                    else:
                        question.re_rank(reason='gefragt', last_acted_user=request.user)

                return redirect('%s?newquestion=1' % question.get_absolute_url())

            # not logged in, so redirect to register
            return redirect('%s?nqh=%s' % (reverse('join_with_question'), question.hash_id))

        else:
            context = {
                'question_form': question_form,
                'error': 'Titel und Beschreibung sind Pflichtfelder'
            }
            return render(request, 'question/create.html', context)


def question_detail(request, question_id, slug):
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return redirect('%s?deleted=1' % reverse('index'))

    # 301 redirect to new url
    return redirect(question.get_absolute_url(), permanent=True)


@login_required
def reload_tags(request, question_id, slug):
    question = Question.objects.get(id=question_id)
    return render(request, 'question/includes/edit_tags.html', {
        'tags': json.dumps(list(question.question_hashtags.values('id', 'name'))),
        'question': question
    })


@login_required
def update_questions_tags(request, question_id, slug):
    question = Question.objects.get(id=question_id)
    if request.method == 'POST':
        edited_q_tags = request.POST.get('edited_question_tags')

        new_tags = [tag_name.strip().lower() for tag_name in edited_q_tags.split(',') if tag_name and tag_name.strip()]

        question.question_hashtags.clear()

        for tag in new_tags:
            tag = tag.lower()

            if not HashTag.objects.filter(name=tag).count():
                hashtag = HashTag.objects.create(name=tag)
            else:
                hashtag = HashTag.objects.filter(name=tag).last()

            hashtag.questions.add(question.id)

        question.tag_names = ', '.join(new_tags)
        question.save()

    return redirect(question.get_absolute_url())


def question_detail_hashed(request, hash_id, slug):
    try:
        question = Question.objects.select_related('user__profile').get(hash_id=hash_id)
    except Question.DoesNotExist:
        return redirect('%s?deleted=1' % reverse('index'))

    if not question.confirmed:
        if not request.user.is_authenticated or question.user_id != request.user.id:
            return redirect(reverse('index'))

    # fresh question, set online and redirect to original url
    if slug == 'nqh-%s' % hash_id and not question.user_id:
        question.go_online(user=request.user)

        # update stats
        stats = request.stats
        stats.update_total_questions()

        return redirect('%s?newquestion=1' % question.get_absolute_url())

    question.increase_views_counter(request=request)

    # increase reach, in question and in answers
    # +1 per answer, so a user with several answers gets several; one UPDATE per distinct increment
    if hasattr(question.user, 'profile'):
        reach = Counter([question.user_id])
        reach.update(question.question_answers.filter(user_id__isnull=False).values_list('user_id', flat=True))
        user_ids_by_increment = defaultdict(list)
        for user_id, increment in reach.items():
            user_ids_by_increment[increment].append(user_id)
        for increment, user_ids in user_ids_by_increment.items():
            Profile.objects.filter(user_id__in=user_ids).update(reached_ppl=F('reached_ppl') + increment)

    answer = request.GET.get('answer')
    if answer:
        answer = Answer.objects.get(id=answer)

    show_ask_question_modal = False
    answered_by_this_user = False

    if not request.user.is_authenticated and settings.DOMAIN not in request.META.get('HTTP_REFERER', ''):
        show_ask_question_modal = True

    if 'mathefragen' not in settings.DOMAIN:
        show_ask_question_modal = False

    if request.user.is_authenticated and question.question_answers.filter(user_id=request.user.id).count():
        answered_by_this_user = True

    # todo: this was hotfix. Later think about better code.
    if not question.number_answers:
        question.sync_number_answers()

    return render(request, 'question/detail.html', {
        'question': question,
        'answer': answer,
        'show_ask_question_modal': show_ask_question_modal,
        'answered_by_this_user': answered_by_this_user
    })


@login_required
def delete_question(request, question_id):
    question = Question.objects.get(id=question_id)

    can_moderate = request.user.profile.can_moderate()
    can_be_deleted = question.can_be_deleted()

    delete_allowed = False
    if request.user.id == question.user_id and can_be_deleted:
        delete_allowed = True
    elif can_moderate:
        delete_allowed = True

    if delete_allowed:
        question.delete()
        # update stats
        stats = request.stats
        stats.update_total_questions()

        return redirect('%s?deleted=1' % reverse('index'))

    return redirect('%s?question_cant_be_deleted=1' % question.get_absolute_url())


@login_required
def toggle_question_visibility(request, question_id):
    question = Question.objects.get(id=question_id)

    if request.user.profile.can_moderate():
        question.is_active = not question.is_active
        question.save()

    return redirect(question.get_absolute_url())


@login_required(login_url='/user/register/')
def answer_question(request, question_id):
    answer_text = request.POST.get('answer_text')
    existing_answer = request.POST.get('existing_answer')
    suggested_videos = request.POST.getlist('suggested_videos')

    question = Question.objects.get(id=question_id)
    get_param_for_ga = '?newanswer=1'

    if answer_text:

        # repairs image rotation in background
        RepairImages(text=answer_text).start()

        if existing_answer:
            answer = Answer.objects.get(id=existing_answer)
            answer.text = answer_text

            # re-activate answer if it was inactive (blocked, reported, etc)
            if not answer.is_active:
                answer.is_active = True
                answer.answer_reports.all().delete()

            answer.edited_by_id = request.user.id
            answer.edited_at = timezone.now()
            answer.save()

            get_param_for_ga = '?answer_edited=1'
        else:
            source_ip = '192.168.0.1'
            found_ip = ip.IP(request=request).user_ip()
            if found_ip:
                source_ip = found_ip

            new_answer = question.question_answers.create(
                user_id=request.user.id,
                text=answer_text,
                question_id=question_id,
                source_ip=source_ip
            )
            new_answer.user.profile.update_number_answers(question_id=question_id)
            # todo: give 15 points if user is new and his first question.
            answer = new_answer

            question.sync_number_answers()

            # update stats
            stats = request.stats
            stats.update_total_answers()

        # update helped tags
        answer.user.profile.update_most_helped_tags()

        # update video recommendations
        # clear the list to add new ones and delete old ones.
        answer.answer_recommendations.all().delete()
        for youtube_id in suggested_videos:
            answer.answer_recommendations.create(youtube_id=youtube_id)

        # re-rank in index page
        if existing_answer:
            question.re_rank(reason='Antwort bearbeitet', last_acted_user=request.user)
        else:
            question.re_rank(reason='beantwortet', last_acted_user=request.user)

        # inform the questioner about new answer
        if not existing_answer:
            question.inform_questioner(answer=answer)

    new_question_url = '%s%s' % (question.get_absolute_url(), get_param_for_ga)
    return redirect(new_question_url)


@login_required
def accept_answer(request):
    answer_id = request.POST.get('answer_id')
    grasp_level = request.POST.get('grasp_level')

    answer = Answer.objects.get(id=answer_id)

    if answer.question.user_id != request.user.id:
        return HttpResponse('not_allowed_to_accept')

    # undo already accepted answer
    answer.question.question_answers.filter(accepted=True).update(accepted=False)

    answer.set_accepted(grasp_level=grasp_level)

    # reward user who answered
    if answer.user:
        user_who_answered = answer.user.profile
        user_who_answered.increase_points(points=15, reason='helped')

    # reward accepted user
    user_profile = request.user.profile

    # and increase his knowledge, todo: later we test his knowledge by quiz.
    user_profile.increase_knowledge(more_knowledge=15)
    # give 2 credits because he accepted
    user_profile.increase_points(points=2, reason='accepted')

    return HttpResponse('ok')


@login_required
def delete_answer(request):
    answer_id = request.POST.get('answer_id')
    answer = Answer.objects.get(id=answer_id)
    question = answer.question

    is_moderator = request.user.profile.is_moderator()
    can_be_deleted = answer.can_be_deleted()

    delete_allowed = False
    if request.user.id == answer.user_id and can_be_deleted:
        delete_allowed = True
    elif is_moderator:
        delete_allowed = True

    if delete_allowed:
        answer_owner = answer.user.profile

        # soft delete answer
        answer.delete()

        answer_owner.update_number_answers(counter=-1)
        answer_owner.update_most_helped_tags()

        question.sync_number_answers()

        # update stats
        stats = request.stats
        stats.update_total_answers()

        return redirect(question.get_absolute_url())

    return redirect('%s?answer_cant_be_deleted=1' % question.get_absolute_url())


@login_required
def save_question_comment(request):
    question_id = request.POST.get('question')

    comment_text = request.POST.get('comment_text')
    comment_id = request.GET.get('comment-id')
    user = request.user

    question = Question.objects.get(id=question_id)

    if comment_text:
        if comment_id:
            comment = question.question_comments.get(id=comment_id)
            comment.text = comment_text
            comment.save()

        else:
            source_ip = '192.168.0.1'
            found_ip = ip.IP(request=request).user_ip()
            if found_ip:
                source_ip = found_ip

            question.question_comments.create(
                user_id=user.id,
                text=comment_text,
                source_ip=source_ip
            )

        # re-rank in index page
        question.re_rank(reason='kommentiert', last_acted_user=request.user)

    return HttpResponse('ok')


@login_required
def save_answer_comment(request):
    answer_id = request.POST.get('answer')
    comment_text = request.POST.get('comment_text')
    comment_id = request.GET.get('comment-id')
    user = request.user

    try:
        answer = Answer.objects.get(id=answer_id)
    except Answer.DoesNotExist:
        return redirect('/')

    question = answer.question

    if comment_text:
        if comment_id:
            comment = answer.answer_comments.get(id=comment_id)
            comment.text = comment_text
            comment.save()

        else:
            source_ip = '192.168.0.1'
            found_ip = ip.IP(request=request).user_ip()
            if found_ip:
                source_ip = found_ip

            answer.answer_comments.create(
                user_id=user.id,
                text=comment_text,
                source_ip=source_ip
            )

        # re-rank in index page
        question.re_rank(reason='Antwort kommentiert', last_acted_user=request.user)

    return HttpResponse('ok')


@login_required
def delete_answer_comment(request):
    comment_id = request.POST.get('comment_id')
    answer_comment = AnswerComment.objects.get(id=comment_id)

    if answer_comment.user_id != request.user.id:
        return HttpResponse('bad')

    answer_comment.delete()

    return HttpResponse('ok')


@login_required
def delete_question_comment(request):
    comment_id = request.POST.get('comment_id')
    question_comment = QuestionComment.objects.get(id=comment_id)

    if question_comment.user_id != request.user.id:
        return HttpResponse('bad')

    question_comment.delete()

    return HttpResponse('ok')


@login_required
def convert(request):
    convert_direction = request.POST.get('convert_direction', '')
    convert_object_id = request.POST.get('convert_object_id')

    if 'to_answer' in convert_direction:
        try:
            comment = QuestionComment.objects.get(id=convert_object_id)
        except QuestionComment.DoesNotExist:
            return redirect(reverse('index'))

        question = comment.question

        new_answer = Answer.objects.create(
            question_id=comment.question_id,
            user_id=comment.user_id,
            text=comment.text
        )

        # copy votes from comment to new answer
        new_answer_votes = 0
        for vote in comment.question_comment_votes.all():
            Vote.objects.create(
                user_id=vote.user_id,
                answer_id=new_answer.id,
                type='up'
            )
            new_answer_votes += 5
            vote.delete()

        new_answer.update_votes(new_points=new_answer_votes)

        question.sync_number_answers()

        new_answer.idate = comment.idate
        new_answer.save()

        # inform the questioner about new answer
        question.inform_questioner(answer=new_answer)

        # delete comment
        comment.delete()

        return redirect(question.get_absolute_url())


@csrf_exempt
def upload_image(request):
    uploaded_file = request.FILES.get('file')

    if not uploaded_file:
        return HttpResponse(json.dumps({'location': ''}))

    date_folder = '%s/%s/%s/' % (
        timezone.now().year, timezone.now().month, timezone.now().day
    )
    filename = '%s.%s' % (create_default_hash(length=12), uploaded_file.name.split('.')[-1])
    final_path = '%s%s' % (
        date_folder, filename
    )

    # dont eat up memory if file is too big
    with default_storage.open(final_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    file_path = 'https://%s/media/%s%s' % (settings.AWS_STORAGE_BUCKET_NAME, date_folder, filename)

    response = json.dumps({
        'location': file_path
    })

    return HttpResponse(response)
