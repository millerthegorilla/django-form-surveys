from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from tinymce.widgets import TinyMCE

from typing import List, Tuple

from djf_surveys.app_settings import (
    SURVEY_TINYMCE_DEFAULT_CONFIG,
    field_validators,
    SURVEY_TEXT_SIZE_CSS_MAP,
    SURVEY_TEXT_WEIGHT_CSS_MAP,
)

from djf_surveys.models import Question, Survey, SurveySelection
from djf_surveys.widgets import InlineChoiceField, InlineChoiceSelectField

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["label", "key", "help_text", "required"]


class QuestionWithChoicesForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["label", "key", "choices", "help_text", "required"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["choices"].widget = InlineChoiceField()
        self.fields["choices"].help_text = _("Click button Add to add choice")


class QuestionFormRatings(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["label", "key", "choices", "help_text", "required"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["choices"].widget = forms.NumberInput(attrs={"max": 10, "min": 1})
        self.fields["choices"].help_text = _("Must be between 1 and 10")
        self.fields["choices"].label = _("Number of ratings")
        self.fields["choices"].initial = 5


class QuestionEmailForm(forms.ModelForm):
    type_filter = forms.ChoiceField(
        label=_("Type Filter"),
        choices=(
            ("", _("--- Choices ---")),
            ("whitelist", "Whitelist"),
            ("blacklist", "Blacklist"),
        ),
        widget=forms.Select(),
        required=False,
        help_text=_("Filter type to accept allowed email domains"),
    )
    email_domain = forms.CharField(
        label="Email Domains",
        help_text=_("Click Button Add to adding data"),
        widget=InlineChoiceField(),
    )

    class Meta:
        model = Question
        fields = [
            "label",
            "key",
            "help_text",
            "required",
            "type_filter",
            "email_domain",
        ]


class QuestionTextForm(forms.ModelForm):
    max_length = forms.IntegerField(
        label=_("Max. Length"),
        min_value=3,
        max_value=250,
        initial=field_validators["max_length"]["text"],
        help_text=_("Max. Length: Text input"),
    )
    min_length = forms.IntegerField(
        label=_("Min. Length"),
        min_value=3,
        max_value=200,
        initial=field_validators["min_length"]["text"],
        help_text=_("Min. Length: Text input"),
    )
    class Meta:
        model = Question
        fields = ["label", "key", "help_text", "required", "max_length", "min_length"]


class QuestionTitleForm(forms.ModelForm):

    def make_choices(typeMap) -> List[Tuple[str, str]]:
        choices = []
        for key in typeMap:
            choices.append((typeMap[key], key))
        return choices

    font_size = forms.ChoiceField( 
        label=_("Font Size"),
        choices= make_choices(SURVEY_TEXT_SIZE_CSS_MAP),
        widget=forms.Select(attrs={"class": "tw:w-full tw:p-4 tw:pr-12 tw:text-sm tw:border tw:border-gray-500 tw:rounded-lg tw:shadow-sm"}),
    )

    font_weight = forms.ChoiceField(
        label=_("Font Weight"),
        choices= make_choices(SURVEY_TEXT_WEIGHT_CSS_MAP),
        widget=forms.Select(attrs={"class": "tw:w-full tw:p-4 tw:pr-12 tw:text-sm tw:border tw:border-gray-500 tw:rounded-lg tw:shadow-sm"}),
    )

    def save(self, commit=True):
        label = strip_tags(self.cleaned_data.get("label", ""))
        size = self.cleaned_data.get("font_size", "small")
        weight = self.cleaned_data.get("font_weight", "normal")
        self.instance.label = f'<span class="{size} {weight}">{label}</span>'
        return super().save(commit=commit)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['label'] = strip_tags(self.initial.get('label', ''))
    
    class Meta:
        model = Question
        fields = ["label"]


class QuestionNumberForm(forms.ModelForm):
    max_value = forms.IntegerField(
        label=_("Max. Value"),
        min_value=1,
        initial=1000,
        help_text=_("Max. value: Number"),
    )
    min_value = forms.IntegerField(
        label=_("Min. Value"),
        min_value=1,
        initial=1,
        help_text=_("Min. value: Number"),
    )

    class Meta:
        model = Question
        fields = ["label", "key", "help_text", "required", "max_value", "min_value"]


class QuestionTextAreaForm(forms.ModelForm):
    max_length = forms.IntegerField(
        label=_("Max. Length"),
        min_value=10,
        max_value=1000,
        initial=field_validators["max_length"]["text_area"],
        help_text=_("Max. Length: Text input"),
    )
    min_length = forms.IntegerField(
        label=_("Min. Length"),
        min_value=3,
        max_value=100,
        initial=field_validators["min_length"]["text_area"],
        help_text=_("Min. Length: Text input"),
    )

    class Meta:
        model = Question
        fields = ["label", "key", "help_text", "required", "max_length", "min_length"]


class SurveyForm(forms.ModelForm):

    class Media:
        js = ("djf_surveys/js/admin_survey_form.js",)
        css = {"all": ("djf_surveys/css/admin_survey_form.css",)}

    class Meta:
        model = Survey
        fields = [
            "name",
            "slug",
            "description",
            "editable",
            "deletable",
            "duplicate_entry",
            "cancel_button",
            "cycle_survey",
            "private_response",
            "private",
            "temp_user",
            "can_anonymous_user",
            "gdpr_compliant",
            "show_on_index",
            "bookmark",
            "fullscreen",
            "screensaver",
            "notification_to",
            "success_page_content",
        ]
        exclude = [
            "survey_selection",
        ]
        widgets = {
            "description": TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG),
            "success_page_content": TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG),
        }
        help_texts = {
            "slug": _(
                "Leave the field blank if you want the slug to be generated automatically"
            ),
        }

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if (
            self.instance
            and self.instance.slug != slug
            and Survey.objects.filter(slug=slug).exists()
        ):
            raise forms.ValidationError(_("Slug already exists"))
        if not self.instance and slug and Survey.objects.filter(slug=slug).exists():
            raise forms.ValidationError(_("Slug already exists"))
        return slug

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notification_to"].widget = InlineChoiceField()
        self.fields["slug"].required = False


class CustomChoiceField(forms.ChoiceField):
    def clean(self, value):
        if value:
            value = value.split(",")
            value.pop(value.index("0")) if "0" in value else None
            value = [int(x) for x in value]
            return value
        else:
            return []


class SurveySelectionListForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Name"), max_length=200, help_text=_("Name for this survey selection")
    )
    surveys = CustomChoiceField(
        label=_("Allowed Surveys"),
        help_text=_("Click Button Add Data"),
        widget=InlineChoiceSelectField(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get("instance"):  # Editing existing SurveySelection
            self.fields["surveys"].widget.attrs.update(
                {"instance": kwargs["instance"].id}
            )
            self.fields["surveys"].choices = [
                (s.id, s.name)
                for s in SurveySelection.objects.get(
                    id=kwargs["instance"].id
                ).surveys.all()
            ]
        else:  # Creating new SurveySelection
            self.fields["surveys"].initial = None

    class Meta:
        model = SurveySelection
        fields = [
            "name",
            "description",
            "surveys",
            "can_anonymous_user",
            "success_page_content",
            "show_on_index",
            "fullscreen",
            "screensaver",
            "private",
            "bookmark",
        ]
        widgets = {
            "description": TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG),
            "success_page_content": TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG),
        }

    def clean_surveys(self):
        surveys = self.cleaned_data["surveys"]
        if not surveys or len(surveys) < 2:
            raise forms.ValidationError(_("At least two surveys must be selected."))
        return surveys
