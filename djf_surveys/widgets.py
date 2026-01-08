from django import forms
from django.db.models import Count
from djf_surveys.models import Survey, SurveySelection


class CheckboxSelectMultipleSurvey(forms.CheckboxSelectMultiple):
    option_template_name = 'djf_surveys/widgets/multiselect.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        return context
    

class RadioSelectSurvey(forms.RadioSelect):
    option_template_name = 'djf_surveys/widgets/radio_option.html'


class DateSurvey(forms.DateTimeInput):
    template_name = 'djf_surveys/widgets/datepicker.html'


class RatingSurvey(forms.HiddenInput):
    template_name = 'djf_surveys/widgets/star_rating.html'
    stars = 8

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['num_ratings'] = self.num_ratings
        return context


class InlineChoiceField(forms.HiddenInput):
    template_name = 'djf_surveys/widgets/inline_choices.html'
    extra = 3

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if context['widget']['value']:
            context['widget']['choice_value'] = [x.strip() for x in context['widget']['value'].split(',')]
        else:
            context['widget']['choice_value'] = []

        choices_count = len(context['widget']['choice_value'])
        context['widget']['extra'] = range(1 + choices_count, self.extra + 1 + choices_count)
        return context


class InlineChoiceSelectField(forms.HiddenInput):
    template_name = 'djf_surveys/widgets/inline_choices_select.html'
    extra = 1

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        surveys_with_selection = Survey.objects.annotate(surveyselection_count=Count('survey_selection'))
        surveys_filtered = surveys_with_selection.filter(surveyselection_count__lt=1)
        context['widget']['all_surveys'] = surveys_filtered
        survey_count = Survey.objects.count()
        context['widget']['surveys'] = (SurveySelection.objects.get(id=self.attrs['instance']).surveys.all() 
                                            if self.attrs.get('instance', None) else None)
        context['widget']['extra'] = range(1 + survey_count, self.extra + 1 + survey_count)
        return context
