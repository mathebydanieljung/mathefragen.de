from django.views.generic import FormView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, reverse, redirect

from .forms import ReviewForm
from .models import UserReview
from mathefragen.apps.question.models import Question


class CreateReview(LoginRequiredMixin, FormView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        given_to = kwargs.get('given_to')

        form = ReviewForm()

        coming_from_question = False
        helper = User.objects.get(id=given_to)
        if 'source_question' in request.GET:
            coming_from_question = True
            source_question = Question.objects.get(id=request.GET.get('source_question'))
            hashtag_ids = source_question.question_hashtags.values('id', 'name')
        else:
            hashtag_ids = helper.profile.helped_hashtag_ids()

        target_username = helper.profile.get_full_name

        return render(request, 'user/add_review.html', {
            'profile': request.user.profile,
            'form': form,
            'coming_from_question': coming_from_question,
            'given_to': given_to,
            'target_username': target_username,
            'hashtag_ids': hashtag_ids
        })

    def post(self, request, *args, **kwargs):
        form = ReviewForm(request.POST)
        given_to = kwargs.get('given_to')
        review_id = request.POST.get('review_id')
        selected_hashtags = request.POST.getlist('selected_hashtag')
        source_question_id = request.POST.get('source_question_id')

        given_to_user = User.objects.get(id=given_to)

        if form.is_valid():
            text = form.cleaned_data.get('text')
            relation_source = form.cleaned_data.get('relation_source')

            if review_id:
                review = UserReview.objects.get(id=review_id)
                review.text = text
                review.relation_source = relation_source
                review.save()
            else:
                review = request.user.given_user_reviews.create(
                    given_to_id=given_to_user.id,
                    text=text,
                    relation_source=relation_source
                )

                review.inform_about_review()

            if source_question_id:
                review.source_question_id = source_question_id
                review.save()

            if selected_hashtags:
                review.hashtags.clear()
                # remove duplicates
                selected_hashtags = list(set(selected_hashtags))
                for hashtag_id in selected_hashtags:
                    review.hashtags.add(hashtag_id)

        return redirect(given_to_user.profile.get_absolute_url())


class EditReview(LoginRequiredMixin, CreateView):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, *args, **kwargs):
        user = User.objects.get(id=kwargs.get('pk'))
        review = UserReview.objects.get(id=kwargs.get('review_id'))

        form = ReviewForm(initial={
            'text': review.text
        })

        return render(request, 'user/add_review.html', {
            'form': form,
            'profile': user.profile,
            'given_to': review.given_to_id,
            'review_id': review.id
        })


@login_required
def delete_review(request, pk, review_id):
    review = UserReview.objects.get(id=review_id)

    user = review.given_to

    if request.user.id != review.given_by_id:
        return redirect(request.user.profile.get_absolute_url())

    review.delete()

    return redirect(reverse('profile_reviews', kwargs={'pk': user.id}))
