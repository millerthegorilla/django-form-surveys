from typing import List, Tuple
import uuid
from shortener import shortener

from django import forms
from django.core.mail import BadHeaderError, send_mail
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from djf_surveys.app_settings import (
    DATE_INPUT_FORMAT,
    SURVEY_EMAIL_FROM,
    SURVEY_FIELD_VALIDATORS,
    SURVEY_GDPR_REFERENCE_MESSAGE,
)
from djf_surveys.models import TYPE_FIELD, Answer, Question, UserAnswer
from djf_surveys.validators import (
    RatingValidator,
    SurveyEmailValidator,
    TermsEmailValidator,
    TermsNumberValidator,
    TermsTextAreaValidator,
    TermsTextValidator,
)
from djf_surveys.widgets import (
    Title,
    CheckboxSelectMultipleSurvey,
    DateSurvey,
    RadioSelectSurvey,
    RatingSurvey,
)

def make_choices(question: Question) -> List[Tuple[str, str]]:
    choices = []
    for choice in question.choices.split(","):
        choice = choice.strip()
        choices.append((choice.replace(" ", "_").lower(), choice))
    return choices

# required, label, initial, widget, help_text
class TitleField(forms.Field):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self, value):
        return value
    

class BaseSurveyForm(forms.Form):
    def __init__(self, survey, user, *args, **kwargs):
        self.survey = survey
        self.user = user if user.is_authenticated else None
        self.field_names = []
        self.questions = self.survey.questions.all().order_by("ordering")
        super().__init__(*args, **kwargs)

        for question in self.questions:
            # to generate field name
            field_name = f"field_survey_{question.id}"

            if question.type_field == TYPE_FIELD.title:
                self.fields[field_name] = TitleField(
                    required=False,
                    label=question.label,
                    widget=Title(attrs={"value": question.label}),
                )
            elif question.type_field == TYPE_FIELD.multi_select:
                choices = make_choices(question)
                self.fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    label=question.label,
                    widget=CheckboxSelectMultipleSurvey,
                )
            elif question.type_field == TYPE_FIELD.radio:
                choices = make_choices(question)
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices, label=question.label, widget=RadioSelectSurvey
                )
            elif question.type_field == TYPE_FIELD.select:
                choices = make_choices(question)
                empty_choice = [("", _("Choose"))]
                choices = empty_choice + choices
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices, label=question.label
                )
            elif question.type_field == TYPE_FIELD.number:
                # add other terms validator
                validators = []
                if hasattr(question, "termsvalidators"):
                    terms = TermsNumberValidator.to_object(
                        question.termsvalidators.terms
                    )
                    validators.append(MinValueValidator(terms.min_value))
                    validators.append(MaxValueValidator(terms.max_value))
                else:
                    terms = TermsNumberValidator()
                    validators.append(MinValueValidator(terms.min_value))
                    validators.append(MaxValueValidator(terms.max_value))

                self.fields[field_name] = forms.IntegerField(
                    label=question.label, validators=validators
                )
            elif question.type_field == TYPE_FIELD.url:
                self.fields[field_name] = forms.URLField(
                    label=question.label,
                    validators=[
                        MaxLengthValidator(SURVEY_FIELD_VALIDATORS["max_length"]["url"])
                    ],
                )
            elif question.type_field == TYPE_FIELD.email:
                validators = [
                    MaxLengthValidator(SURVEY_FIELD_VALIDATORS["max_length"]["email"])
                ]

                # add other terms validator
                if hasattr(question, "termsvalidators"):
                    terms = TermsEmailValidator.to_object(
                        question.termsvalidators.terms
                    )
                    validators.append(SurveyEmailValidator(terms))

                self.fields[field_name] = forms.EmailField(
                    label=question.label, validators=validators
                )

            elif question.type_field == TYPE_FIELD.date:
                self.fields[field_name] = forms.DateField(
                    label=question.label,
                    widget=DateSurvey(),
                    input_formats=DATE_INPUT_FORMAT,
                )
            elif question.type_field == TYPE_FIELD.text_area:
                # add other terms validator
                validators = []
                if hasattr(question, "termsvalidators"):
                    terms = TermsTextAreaValidator.to_object(
                        question.termsvalidators.terms
                    )
                    validators.append(MinLengthValidator(terms.min_length))
                    validators.append(MaxLengthValidator(terms.max_length))
                else:
                    terms = TermsTextAreaValidator()
                    validators.append(MinLengthValidator(terms.min_length))
                    validators.append(MaxLengthValidator(terms.max_length))

                self.fields[field_name] = forms.CharField(
                    label=question.label, widget=forms.Textarea, validators=validators
                )

            elif question.type_field == TYPE_FIELD.rating:
                if not question.choices:  # use 5 as default for backward compatibility TODO
                    question.choices = 5
                self.fields[field_name] = forms.CharField(
                    label=question.label,
                    widget=RatingSurvey,
                    validators=[
                        MaxLengthValidator(len(str(int(question.choices)))),
                        RatingValidator(
                            int(question.choices), required=question.required
                        ),
                    ],
                )
                self.fields[field_name].widget.num_ratings = int(question.choices)
            else:
                # add other terms validator
                validators = []
                if hasattr(question, "termsvalidators"):
                    terms = TermsTextValidator.to_object(question.termsvalidators.terms)
                    validators.append(MinLengthValidator(terms.min_length))
                    validators.append(MaxLengthValidator(terms.max_length))
                else:
                    terms = TermsTextValidator()
                    validators.append(MinLengthValidator(terms.min_length))
                    validators.append(MaxLengthValidator(terms.max_length))

                self.fields[field_name] = forms.CharField(
                    label=question.label, validators=validators
                )

            self.fields[field_name].required = question.required
            self.fields[field_name].widget.is_required = question.required
            self.fields[field_name].help_text = question.help_text
            self.field_names.append(field_name)
        
        self.has_multiselect = any(
            isinstance(field, forms.MultipleChoiceField)
            for field in self.fields.values()
        )
        self.has_rating = any(
            isinstance(field, forms.CharField) and isinstance(field.widget, RatingSurvey)
            for field in self.fields.values()
        )

    def clean(self):
        cleaned_data = super().clean()

        for field_name in self.field_names:
            try:
                field = cleaned_data[field_name]
            except KeyError:
                raise forms.ValidationError("You must enter valid data")

            if self.fields[field_name].required and not field:
                self.add_error(field_name, "This field is required")

        return cleaned_data


class RespondToSurveyForm(BaseSurveyForm):
    gdpr_reference = forms.CharField(
        label=_("GDPR Reference"),
        widget=forms.TextInput(attrs={"readonly": "readonly"})
    )

    def __init__(self, *args, **kwargs):
        host = kwargs.pop("host", None)
        scheme = kwargs.pop("scheme", "https")
        super().__init__(*args, **kwargs)
        #if UserAnswer.objects.filter(gdpr_reference=self.fields["gdpr_reference"].initial).exists():
         #   self.fields["gdpr_reference"].initial = str(uuid.uuid4())
        link = reverse("djf_surveys:withdraw_response", kwargs={"gdpr_reference": self.initial['gdpr_reference']})
        short_link = shortener.get_or_create(None, link, refresh=True)
        url_short = f"{scheme}://{host}/s/{short_link}"
        self.fields["gdpr_reference"].help_text = mark_safe(
            _(SURVEY_GDPR_REFERENCE_MESSAGE).format(url_short)
        )
       # self.fields["gdpr_reference"].short_link = short_link

    @transaction.atomic
    def save(self):
        cleaned_data = super().clean()
        user_answer = UserAnswer.objects.create(
            survey=self.survey,
            user=self.user,
            gdpr_reference=cleaned_data["gdpr_reference"],
        )
        for question in self.questions:
            field_name = f"field_survey_{question.id}"

            if question.type_field == TYPE_FIELD.multi_select:
                value = ",".join(cleaned_data[field_name])
            else:
                value = cleaned_data[field_name]
            
            if question.type_field == TYPE_FIELD.title:
                value = "Title"
                
            Answer.objects.create(
                question=question, value=value, user_answer=user_answer
            )

        if self.survey.notification_to and SURVEY_EMAIL_FROM:
            try:
                user_answer_count = UserAnswer.objects.filter(
                    survey=self.survey
                ).count()
                send_mail(
                    _("Notification {survey_name}").format(
                        survey_name=self.survey.name
                    ),
                    _(
                        "You have received one new response. "
                        "The total number of responses is currently {count}"
                    ).format(count=user_answer_count),
                    SURVEY_EMAIL_FROM,
                    self.survey.notification_to.split(","),
                    fail_silently=False,
                )
            except (BadHeaderError, ConnectionError) as e:
                print(e)


class EditSurveyForm(BaseSurveyForm):
    def __init__(self, user_answer, *args, **kwargs):
        self.survey = user_answer.survey
        self.user_answer = user_answer
        super().__init__(survey=self.survey, user=user_answer.user, *args, **kwargs)
        self._set_initial_data()

    def _set_initial_data(self):
        answers = self.user_answer.answer_set.all()

        for answer in answers:
            field_name = f"field_survey_{answer.question.id}"
            if answer.question.type_field == TYPE_FIELD.multi_select:
                self.fields[field_name].initial = answer.value.split(",")
            else:
                self.fields[field_name].initial = answer.value

    @transaction.atomic
    def save(self):
        cleaned_data = super().clean()
        self.user_answer.survey = self.survey
        self.user_answer.user = self.user
        self.user_answer.save()

        for question in self.questions:
            field_name = f"field_survey_{question.id}"

            if question.type_field == TYPE_FIELD.multi_select:
                value = ",".join(cleaned_data[field_name])
            else:
                value = cleaned_data[field_name]

            answer, created = Answer.objects.get_or_create(
                question=question,
                user_answer=self.user_answer,
                defaults={
                    "question_id": question.id,
                    "user_answer_id": self.user_answer.id,
                },
            )

            if not created and answer:
                answer.value = value
                answer.save()


class WithdrawResponseForm(forms.Form):
    gdpr_reference = forms.CharField(label=_("GDPR Reference"), max_length=100)

    def __init__(self, *args, **kwargs):
        gdpr_reference = kwargs.pop('gdpr_reference', "")
        super().__init__(*args, **kwargs)
        self.fields["gdpr_reference"].initial = gdpr_reference

    def clean_gdpr_reference(self):
        gdpr_reference = self.cleaned_data.get("gdpr_reference")
        if not UserAnswer.objects.filter(gdpr_reference=gdpr_reference).exists():
            raise forms.ValidationError(_("Invalid GDPR Reference"))
        return gdpr_reference
