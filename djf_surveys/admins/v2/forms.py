from django import forms
from django.utils.translation import gettext_lazy as _
from djf_surveys.models import Question, Survey, SurveySelection
from djf_surveys.widgets import InlineChoiceField, InlineChoiceSelectField
from tinymce.widgets import TinyMCE
from djf_surveys.app_settings import SURVEY_TINYMCE_DEFAULT_CONFIG
from djf_surveys.app_settings import field_validators


class QuestionForm(forms.ModelForm):
    
    class Meta:
        model = Question
        fields = ['label', 'key', 'help_text', 'required']


class QuestionWithChoicesForm(forms.ModelForm):
    
    class Meta:
        model = Question
        fields = ['label', 'key', 'choices', 'help_text', 'required']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['choices'].widget = InlineChoiceField()
        self.fields['choices'].help_text = _("Click Button Add to adding choice")


class QuestionFormRatings(forms.ModelForm):
    
    class Meta:
        model = Question
        fields = ['label', 'key', 'choices', 'help_text', 'required']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['choices'].widget = forms.NumberInput(attrs={'max':10, 'min':1})
        self.fields['choices'].help_text = _("Must be between 1 and 10")
        self.fields['choices'].label = _("Number of ratings")
        self.fields['choices'].initial = 5


class QuestionEmailForm(forms.ModelForm):
    type_filter = forms.ChoiceField(
        label=_("Type Filter"),
        choices=(
            ('', _('--- Choices ---')),
            ('whitelist', 'Whitelist'),
            ('blacklist', 'Blacklist'),
        ),
        widget=forms.Select(),
        required=False,
        help_text=_("Filter type to accept allowed email domains"),
    )
    email_domain = forms.CharField(
        label='Email Domains', help_text=_('Click Button Add to adding data'),
        widget=InlineChoiceField()
    )

    class Meta:
        model = Question
        fields = ['label', 'key', 'help_text', 'required', 'type_filter', 'email_domain']


class QuestionTextForm(forms.ModelForm):
    max_length = forms.IntegerField(
        label=_("Max. Length"),
        min_value=3, max_value=250,
        initial=field_validators['max_length']['text'], help_text=_("Max. Length: Text input"),
    )
    min_length = forms.IntegerField(
        label=_("Min. Length"),
        min_value=3, max_value=200,
        initial=field_validators['min_length']['text'], help_text=_("Min. Length: Text input"),
    )

    class Meta:
        model = Question
        fields = ['label', 'key', 'help_text', 'required', 'max_length', 'min_length']


class QuestionNumberForm(forms.ModelForm):
    max_value = forms.IntegerField(
        label=_("Max. Value"), min_value=1, initial=1000, help_text=_("Max. value: Number"),
    )
    min_value = forms.IntegerField(
        label=_("Min. Value"), min_value=1, initial=1, help_text=_("Min. value: Number"),
    )

    class Meta:
        model = Question
        fields = ['label', 'key', 'help_text', 'required', 'max_value', 'min_value']


class QuestionTextAreaForm(forms.ModelForm):
    max_length = forms.IntegerField(
        label=_("Max. Length"),
        min_value=10, max_value=1000,
        initial=field_validators['max_length']['text_area'],
        help_text=_("Max. Length: Text input"),
    )
    min_length = forms.IntegerField(
        label=_("Min. Length"),
        min_value=3, max_value=100,
        initial=field_validators['min_length']['text_area'],
        help_text=_("Min. Length: Text input"),
    )

    class Meta:
        model = Question
        fields = ['label', 'key', 'help_text', 'required', 'max_length', 'min_length']


class SurveyForm(forms.ModelForm):  
    survey_selection = forms.ModelChoiceField(
        label=_("Survey Selection to Return to..."),
        empty_label=_("No Survey Selection"),
        queryset=SurveySelection.objects.all(),
        required=False,
        help_text=_("Select Survey Selection associated with this survey"),
    )

    class Media:
        js = ('djf_surveys/js/admin_survey_form.js',)
        css = {
            'all': ('djf_surveys/css/admin_survey_form.css',)
        }

    class Meta:
        model = Survey
        fields = [
            'name', 'slug', 'description', 'editable', 'deletable',
            'duplicate_entry', 'cancel_button','cycle_survey', 
            'survey_selection', 'private_response', 
            'can_anonymous_user', 'gdpr_compliant', 'notification_to',
            'success_page_content'
        ]
        widgets = {
            'description': TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG),
            'success_page_content': TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG)
        }
        help_texts = {
            'slug': _("Leave the field blank if you want the slug to be generated automatically"),
        }

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if self.instance and self.instance.slug != slug and Survey.objects.filter(slug=slug).exists():
            raise forms.ValidationError(_('Slug already exists'))
        if not self.instance and slug and Survey.objects.filter(slug=slug).exists():
            raise forms.ValidationError(_('Slug already exists'))
        return slug

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notification_to'].widget = InlineChoiceField()
        self.fields['slug'].required = False


class CustomChoiceField(forms.ChoiceField):
    def clean(self, value):
        if value:
            value = value.split(',')
            value.pop(value.index('0')) if '0' in value else None
            value =[int(x) for x in value ]
            return value
        else:
            return []


class SurveySelectionListForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Name"), max_length=200,
        help_text=_("Name for this survey selection")
    )
    surveys=CustomChoiceField(
        label=_("Allowed Surveys"), help_text=_("Click Button Add Data"),
        widget=InlineChoiceSelectField()
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        survey_choices = ""
        if kwargs.get('instance'):   # Editing existing SurveySelection
            survey_ids = kwargs['instance'].surveys
            self.fields['surveys'].widget.attrs.update({'instance': kwargs['instance'].id})
            self.fields['surveys'].choices = \
                [(s.id, s.name) for s in SurveySelection.objects.get(id=kwargs['instance'].id).surveys.all()]
        else: # Creating new SurveySelection
            self.fields['surveys'].initial = None

    class Meta:
        model = SurveySelection
        fields = ['name', 
                  'description',
                  'surveys',
                  'can_anonymous_user',
                  'success_page_content']
        widgets = {
            'description': TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG),
            'success_page_content': TinyMCE(mce_attrs=SURVEY_TINYMCE_DEFAULT_CONFIG)
        }    

    def clean_surveys(self):
        surveys = self.cleaned_data['surveys']
        if not surveys or len(surveys) < 2:
            raise forms.ValidationError(_("At least two surveys must be selected."))
        return surveys
    

