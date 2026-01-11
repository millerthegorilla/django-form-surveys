import uuid

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.text import capfirst
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView
from django.contrib.auth import get_user_model

from djf_surveys import app_settings
from djf_surveys.forms import EditSurveyForm, RespondToSurveyForm, WithdrawResponseForm
from djf_surveys.mixin import ContextTitleMixin
from djf_surveys.models import (
    TYPE_FIELD,
    BaseModel,
    Question,
    Survey,
    SurveySelection,
    UserAnswer,
)
from djf_surveys.utils import NewPaginator
from djf_surveys.app_settings import SURVEY_SINGLE_USE_PASSWORDS

User = get_user_model()

class IndexView(ContextTitleMixin, View):
    template_name = "djf_surveys/home.html"
    title_page = _("Survey Home")
    paginate_by = app_settings.SURVEY_PAGINATION_NUMBER["survey_list"]
    paginator_class = NewPaginator

    def get(self, request, *args, **kwargs):
        filter = {}
        if (
            app_settings.SURVEY_ANONYMOUS_VIEW_LIST
            and not self.request.user.is_authenticated
        ):
            filter["can_anonymous_user"] = True
        query = self.request.GET.get("q")

        if query:
            surveys = Survey.objects.filter(name__icontains=query, **filter)
        else:
            surveys = Survey.objects.filter(**filter)

        if query:
            survey_selections = SurveySelection.objects.filter(
                name__icontains=query, **filter
            )
        else:
            survey_selections = SurveySelection.objects.filter(**filter)

        # # Paginate surveys
        # survey_paginator = self.paginator_class(surveys, self.paginate_by)
        # survey_page_number = request.GET.get('page', 1)
        # survey_page_obj = survey_paginator.get_page(survey_page_number)

        # # Paginate survey selections
        # selection_paginator = self.paginator_class(survey_selections, self.paginate_by)
        # selection_page_number = request.GET.get('page', 1)
        # selection_page_obj = selection_paginator.get_page(selection_page_number)
        context = self.get_context_data(
            surveys=surveys,
            survey_selections=survey_selections,
            reason="search" if query else "display",
            search_query=query if query else "",
        )
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        # page_number = self.request.GET.get('page', 1)
        context = super().get_context_data(**kwargs)
        #  page_range = context['survey_page_obj'].paginator.get_elided_page_range(number=page_number)
        # context['page_range'] = page_range
        context["welcome_message_title"] = app_settings.SURVEY_WELCOME_MESSAGE_TITLE
        context["welcome_message_tagline"] = app_settings.SURVEY_WELCOME_MESSAGE_TAGLINE
        return context


# base class for survey list view
class SurveyList(ContextTitleMixin, UserPassesTestMixin, ListView):
    paginate_by = app_settings.SURVEY_PAGINATION_NUMBER["survey_list"]
    paginator_class = NewPaginator

    def test_func(self):
        return (
            app_settings.SURVEY_ANONYMOUS_VIEW_LIST
            or self.request.user.is_authenticated
        )

    def get_queryset(self):
        filter = {}
        if (
            app_settings.SURVEY_ANONYMOUS_VIEW_LIST
            and not self.request.user.is_authenticated
        ):
            filter["can_anonymous_user"] = True
        query = self.request.GET.get("q")
        if query:
            object_list = self.model.objects.filter(name__icontains=query, **filter)
        else:
            object_list = self.model.objects.filter(**filter)
        return object_list

    def get_context_data(self, **kwargs):
        page_number = self.request.GET.get("page", 1)
        context = super().get_context_data(**kwargs)
        page_range = context["page_obj"].paginator.get_elided_page_range(
            number=page_number
        )
        query = self.request.GET.get("q")
        context["reason"] = "search" if query else "display"
        context["page_range"] = page_range
        context["welcome_message_title"] = app_settings.SURVEY_WELCOME_MESSAGE_TITLE
        context["welcome_message_tagline"] = app_settings.SURVEY_WELCOME_MESSAGE_TAGLINE
        return context


class SurveySelectionListView(SurveyList):
    model = SurveySelection
    title_page = "Survey Selection List"
    template_name = "djf_surveys/survey_selection_list.html"


class SurveyListView(SurveyList):
    model = Survey
    title_page = "Survey List"


class SurveyFormView(FormMixin, DetailView):
    template_name = "djf_surveys/form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        # use url/get parameters as initial parameters
        if "create" in request.path:
            questions = Question.objects.filter(survey=self.object)
            for param in request.GET.keys():  # loop over all GET parameters
                for question in questions:
                    if question.key == param:  # find corresponding question
                        field_key = f"field_survey_{question.id}"
                        if field_key in context["form"].field_names:
                            if question.type_field == TYPE_FIELD.rating:
                                if not question.choices:
                                    question.choices = 5
                                context["form"][field_key].field.initial = max(
                                    0,
                                    min(
                                        int(request.GET[param]),
                                        int(question.choices) - 1,
                                    ),
                                )
                            elif question.type_field == TYPE_FIELD.multi_select:
                                context["form"][field_key].field.initial = request.GET[
                                    param
                                ].split(",")
                            else:
                                context["form"][field_key].field.initial = request.GET[
                                    param
                                ]
                        break
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            form.save()
            messages.success(
                self.request,
                gettext("%(page_action_name)s succeeded.")
                % dict(page_action_name=capfirst(self.title_page.lower())),
            )
            return self.form_valid(form)
        else:
            messages.error(self.request, gettext("Something went wrong."))
            return self.form_invalid(form)


class RespondSurveyFormView(ContextTitleMixin, SurveyFormView):
    model = Survey
    form_class = RespondToSurveyForm
    title_page = _("Respond To Survey")

    def dispatch(self, request, *args, **kwargs):
        survey = self.get_object()
        # handle if survey can_anonymous_user
        if not request.user.is_authenticated and not survey.can_anonymous_user:
            messages.warning(
                request, gettext("Sorry, you must be logged in to fill out the survey.")
            )
            return redirect("djf_surveys:index")

        # handle if user has already responded to survey and duplicate_entry is False
        if (
            request.user.is_authenticated
            and not survey.duplicate_entry
            and UserAnswer.objects.filter(survey=survey, user=request.user).exists()
        ):
            messages.warning(
                request, gettext("You have already completed this survey.")
            )
            return redirect("djf_surveys:index")

        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "survey": self.get_object(),
                "user": self.request.user,
                "initial": {"gdpr_reference": str(uuid.uuid4())},
            }
        )
        return kwargs

    def get_title_page(self):
        return self.get_object().name

    def get_sub_title_page(self):
        return self.get_object().description

    def get_success_url(self):
        return reverse("djf_surveys:success", kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = self.get_object()
        if survey.can_anonymous_user:
            context["gdpr_reference"] = uuid.uuid4()
        if survey.cycle_survey == True:
            if self.kwargs["selection_slug"] == "main":
                context["link_back_on_cancel"] = reverse_lazy(
                    "djf_surveys:respond",
                    kwargs={"slug": survey.slug, "selection_slug": "main"},
                )
            else:
                context["link_back_on_cancel"] = reverse_lazy(
                    "djf_surveys:survey_selection",
                    kwargs={"slug": self.kwargs["selection_slug"]},
                )
        else:
            context["link_back_on_cancel"] = reverse_lazy("djf_surveys:index")
        if survey.fullscreen == True:
            context["fullscreen"] = True
        return context


@method_decorator(login_required, name="dispatch")
class EditSurveyFormView(ContextTitleMixin, SurveyFormView):
    form_class = EditSurveyForm
    title_page = "Edit Survey"
    model = UserAnswer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object().survey
        return context

    def dispatch(self, request, *args, **kwargs):
        # handle if user not same
        user_answer = self.get_object()
        if user_answer.user != request.user or not user_answer.survey.editable:
            messages.warning(
                request,
                gettext("You can't edit this survey. You don't have permission."),
            )
            return redirect("djf_surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        user_answer = self.get_object()
        return form_class(user_answer=user_answer, **self.get_form_kwargs())

    def get_title_page(self):
        return self.get_object().survey.name

    def get_sub_title_page(self):
        return self.get_object().survey.description

    def get_success_url(self):
        survey = self.get_object().survey
        survey_slug = survey.slug
        selection_slug = (
            survey.survey_selection.slug if survey.survey_selection else "main"
        )
        messages.success(
            self.request,
            gettext("%(page_action_name)s succeeded.")
            % dict(page_action_name=capfirst(self.title_page.lower())),
        )
        return reverse(
            "djf_surveys:detail",
            kwargs={"slug": survey_slug, "selection_slug": selection_slug},
        )


@method_decorator(login_required, name="dispatch")
class DeleteSurveyAnswerView(DetailView):
    model = UserAnswer

    def dispatch(self, request, *args, **kwargs):
        # handle if user not same
        user_answer = self.get_object()
        if user_answer.user != request.user or not user_answer.survey.deletable:
            messages.warning(
                request,
                gettext("You can't delete this survey. You don't have permission."),
            )
            return redirect("djf_surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user_answer = self.get_object()
        survey = user_answer.survey
        surveyselection = survey.survey_selection or "main"
        user_answer.delete()
        messages.success(self.request, gettext("Answer succesfully deleted."))
        return redirect(
            "djf_surveys:detail",
            slug=user_answer.survey.slug,
            selection_slug=surveyselection,
        )


class DetailSurveyView(ContextTitleMixin, DetailView):
    model = Survey
    template_name = "djf_surveys/answer_list.html"
    title_page = _("Survey Detail")
    paginate_by = app_settings.SURVEY_PAGINATION_NUMBER["answer_list"]

    def dispatch(self, request, *args, **kwargs):
        survey = self.get_object()
        if not self.request.user.is_superuser and survey.private_response:
            messages.warning(
                request,
                gettext("You can't access this page. You don't have permission."),
            )
            return redirect("djf_surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user_answers = (
            UserAnswer.objects.filter(survey=self.get_object())
            .select_related("user")
            .prefetch_related("answer_set__question")
        )
        paginator = NewPaginator(user_answers, self.paginate_by)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number)
        context = super().get_context_data(**kwargs)
        context["page_obj"] = page_obj
        context["page_range"] = page_range
        return context


@method_decorator(login_required, name="dispatch")
class DetailResultSurveyView(ContextTitleMixin, DetailView):
    title_page = _("Survey Result")
    template_name = "djf_surveys/detail_result.html"
    model = UserAnswer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["on_detail"] = True
        return context

    def dispatch(self, request, *args, **kwargs):
        # handle if user not same
        user_answer = self.get_object()
        if user_answer.user != request.user:
            messages.warning(
                request,
                gettext("You can't access this page. You don't have permission."),
            )
            return redirect("djf_surveys:index")
        return super().dispatch(request, *args, **kwargs)

    def get_title_page(self):
        return self.get_object().survey.name

    def get_sub_title_page(self):
        return self.get_object().survey.description


def share_link(request, slug):
    # this func to handle link redirect to create form or edit form
    survey = get_object_or_404(Survey, slug=slug)
    if request.user.is_authenticated:
        return redirect(
            reverse_lazy(
                "djf_surveys:admin_summary_survey", kwargs={"slug": survey.slug}
            )
        )
    return redirect(reverse_lazy("djf_surveys:respond", kwargs={"slug": survey.slug, "selection_slug":"main"}))


def selection_share_link(request, slug):
    # this func to handle link redirect to create form or edit form
    survey_selection = get_object_or_404(SurveySelection, slug=slug)
    if request.user.is_authenticated:
        return redirect(
            reverse_lazy(
                "djf_surveys:admin_summary_survey_selection",
                kwargs={"slug": survey_selection.slug},
            )
        )
    return redirect(
        reverse_lazy(
            "djf_surveys:survey_selection", kwargs={"slug": survey_selection.slug}
        )
    )


class SuccessPageSurveyView(ContextTitleMixin, DetailView):
    model = BaseModel
    template_name = "djf_surveys/success-page.html"
    title_page = _("Submitted Successfully")

    def get_object(self, queryset=None):
        if self.kwargs["selection_slug"] == "main":
            return get_object_or_404(Survey, slug=self.kwargs["slug"])
        else:
            return get_object_or_404(
                SurveySelection, slug=self.kwargs["selection_slug"]
            )

    def get(self, request, *args, **kwargs):
        survey = get_object_or_404(Survey, slug=self.kwargs["slug"])
        if self.kwargs["temp_login"] == "True":
            logout(request)
        if SURVEY_SINGLE_USE_PASSWORDS:
            User.objects.filter(username=request.user.username).first().active = False
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        survey = get_object_or_404(Survey, slug=self.kwargs["slug"])
        if survey.cycle_survey == True:
            if self.kwargs["selection_slug"] == "main":
                context["link_back_on_success_page"] = reverse_lazy(
                    "djf_surveys:respond",
                    kwargs={"slug": survey.slug, "selection_slug": "main"},
                )
            else:
                context["link_back_on_success_page"] = reverse_lazy(
                    "djf_surveys:survey_selection",
                    kwargs={"slug": self.kwargs["selection_slug"]},
                )
        else:
            context["link_back_on_success_page"] = reverse_lazy("djf_surveys:index")
        return context


class SurveySelectionDetailView(ContextTitleMixin, DetailView):
    model = SurveySelection
    template_name = "djf_surveys/survey_selection_long_desc.html"
    title_page = _("Survey Selection")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs["slug"]
        context["survey_selection"] = get_object_or_404(SurveySelection, slug=slug)
        context["fullscreen"] = context["survey_selection"].fullscreen
        return context


class WithdrawResponseView(FormMixin, ContextTitleMixin, View):
    model = Survey
    template_name = "djf_surveys/form.html"  # withdraw_response.html"
    form_class = WithdrawResponseForm
    title_page = _("Withdraw Survey Response")

    def get_success_url(self):
        return reverse("djf_surveys:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def get_sub_title_page(self):
        return gettext(
            "Please provide your GDPR Reference to withdraw your survey response."
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            gdpr_reference = form.cleaned_data.get("gdpr_reference")
            user_response = get_object_or_404(UserAnswer, gdpr_reference=gdpr_reference)
            user_response.delete()
            messages.success(
                self.request,
                gettext("Your survey response has been successfully withdrawn."),
            )
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, gettext("Something went wrong."))
            return self.form_invalid(form)
