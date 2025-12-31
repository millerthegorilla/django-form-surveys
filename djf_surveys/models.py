import random, string
from collections import namedtuple
import uuid
from tinymce.models import HTMLField
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.shortcuts import reverse
from django.db.models.functions import Length
from django.conf import settings

from djf_surveys import app_settings
from djf_surveys.utils import create_star

models.CharField.register_lookup(Length)

TYPE_FIELD = namedtuple(
    'TYPE_FIELD', 'text number radio select multi_select text_area url email date rating'
)._make(range(10))


def generate_unique_slug(klass, field, id, identifier='slug'):
    """
    Generate unique slug.
    """
    origin_slug = slugify(field)
    unique_slug = origin_slug
    numb = 1
    mapping = {
        identifier: unique_slug,
    }
    obj = klass.objects.filter(**mapping).first()
    while obj:
        if obj.id == id:
            break
        rnd_string = random.choices(string.ascii_lowercase, k=(len(unique_slug)))
        unique_slug = '%s-%s-%d' % (origin_slug, ''.join(rnd_string[:10]), numb)
        mapping[identifier] = unique_slug
        numb += 1
        obj = klass.objects.filter(**mapping).first()
    return unique_slug

def get_default_owner():
    return get_user_model().objects.get_or_create(first_name='Default', last_name="Owner", username="DefaultOwner")[0].id


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Survey(BaseModel):
    name = models.CharField(_("name"), max_length=200)
    description = HTMLField(_("description"), default='')
    slug = models.SlugField(_("slug"), max_length=225, default='')
    editable = models.BooleanField(_("editable"), default=True,
                                   help_text=_("If False, user " \
                                               "can't edit record."))
    deletable = models.BooleanField(_("deletable"), default=True,
                                    help_text=_("If False, user " \
                                                "can't delete record."))
    duplicate_entry = models.BooleanField(_("mutiple submissions"),
                                          default=False,
                                          help_text=_("If True, user " \
                                                      "can resubmit."))
    cancel_button = models.BooleanField(_("Show cancel button"),
                                        default=False, 
                                        help_text=_("If True, a button" \
                                                    " to cancel the " \
                                                    "survey is " \
                                                    "displayed."))
    cycle_survey = models.BooleanField(_("Cycle the survey"),
                                       default=False,
                                       help_text=_("If True, " \
                                       "success page returns to survey"))
    private_response = models.BooleanField(_("private response"),
                                           default=False,
                                           help_text=_("If True, only" \
                                           " admin and owner can " \
                                           "access."))
    can_anonymous_user = models.BooleanField(_("anonymous submission"),
                                             default=False,
                                             help_text=_("If True, " \
                                             "user without " \
                                             "authentatication can " \
                                             "submit."))
    notification_to = models.TextField(_("Notification To"), 
                                       blank=True, null=True,
                                       help_text=_("Enter your email" \
                                       " to be notified when the " \
                                       "form is submitted"))
    success_page_content = HTMLField(_("Success Page Content"),
                                     blank=True, null=True)
    survey_selection = models.ForeignKey('SurveySelection',
                                          verbose_name=_("survey " \
                                                         "selection"),
                                          related_name="surveys",
                                          on_delete=models.SET_NULL,
                                          blank=True,
                                          null=True,)
    gdpr_compliant = models.BooleanField(_("GDPR compliant"), default=False,
                                        help_text=_("If True, the " \
                                        "survey will include a " \
                                        "unique " \
                                        "identifier for GDPR compliance."))
    show_on_index = models.BooleanField(_("Show on index page"), default=False,
                                        help_text=_("If True, the " \
                                        "survey will be listed on " \
                                        "the index page."))   
    fullscreen = models.BooleanField(_("Show fullscreen"), default=False,
                                        help_text=_("If True then header/navbar " \
                                        "etc. is removed."))   
    private = models.BooleanField(_("Private Survey"), default=False,
                                        help_text=_("If True the survey will be " \
                                        "listed only on home page for user when " \
                                        "logged in."))
    bookmark = models.BooleanField(_("Bookmark Survey"), default=False,
                                        help_text=_("If True a link to the survey will be " \
                                        "listed in the user profile bookmark " \
                                        "list."))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("survey")
        verbose_name_plural = _("surveys")
        order_with_respect_to = 'survey_selection'
        
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Survey, 
                                             self.name, 
                                             self.id)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        selection = (self.survey_selection.slug
                     if self.survey_selection 
                     else "main")
        return reverse ('djf_surveys:respond',
                        kwargs={'slug': self.slug, 
                                'selection_slug': selection})


class Question(BaseModel):
    TYPE_FIELD = [
        (TYPE_FIELD.text, _("Text")),
        (TYPE_FIELD.number, _("Number")),
        (TYPE_FIELD.radio, _("Radio")),
        (TYPE_FIELD.select, _("Select")),
        (TYPE_FIELD.multi_select, _("Multi Select")),
        (TYPE_FIELD.text_area, _("Text Area")),
        (TYPE_FIELD.url, _("URL")),
        (TYPE_FIELD.email, _("Email")),
        (TYPE_FIELD.date, _("Date")),
        (TYPE_FIELD.rating, _("Rating"))
    ]

    key = models.CharField(
        _("key"), max_length=225, unique=True, null=True, blank=True,
        help_text=_("Unique key for this question, fill in the blank"
                    " if you want to use for automatic generation.")
    )
    survey = models.ForeignKey(Survey, related_name='questions', 
                               on_delete=models.CASCADE, 
                               verbose_name=_("survey"))
    label = models.CharField(_("label"), max_length=500, 
                             help_text=_("Enter your question in here."))
    type_field = models.PositiveSmallIntegerField(_("type of " \
                                                    "input field"), 
                                                    choices=TYPE_FIELD)
    choices = models.TextField(
        _("choices"),
        blank=True, null=True,
        help_text=_(
            "If type of field is radio, select, or multi select, "
            "fill in the options separated "
            "by commas. Ex: Male, Female.")
    )
    help_text = models.CharField(
        _("help text"),
        max_length=200, blank=True, null=True,
        help_text=_("You can add a help text in here.")
    )
    required = models.BooleanField(_("required"), default=True,
                                   help_text=_("If True, the user "
                                   "must provide an answer to this "
                                   "question."))
    ordering = models.PositiveIntegerField(_("choices"), default=0,
                                           help_text=_("Defines the "
                                           "question order within " \
                                           "the surveys."))

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")
        ordering = ["ordering"]

    def __str__(self):
        return f"{self.label}-survey-{self.survey.id}"

    def save(self, *args, **kwargs):
        if self.key:
            self.key = generate_unique_slug(Question, 
                                            self.key, 
                                            self.id, 
                                            "key")
        else:
            self.key = generate_unique_slug(Question, 
                                            self.label, 
                                            self.id, 
                                            "key")

        super(Question, self).save(*args, **kwargs)


class UserAnswer(BaseModel):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, verbose_name=_("survey"))
    user = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.CASCADE, verbose_name=_("user"))
    gdpr_reference = models.UUIDField(_("GDPR reference"), default=None,
                                     blank=True, null=True)

    class Meta:
        verbose_name = _("user answer")
        verbose_name_plural = _("user answers")
        ordering = ["-updated_at"]

    def __str__(self):
        return str(self.id)

    def get_user_photo(self):
        default_photo = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
        if app_settings.SURVEY_USER_PHOTO_PROFILE:
            try:
                return eval(app_settings.SURVEY_USER_PHOTO_PROFILE)
            except:
                return default_photo
        return default_photo


class Answer(BaseModel):
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE, verbose_name=_("question"))
    value = models.TextField(_("value"), help_text=_("The value of the answer given by the user."))
    user_answer = models.ForeignKey(UserAnswer, on_delete=models.CASCADE, verbose_name=_("user answer"))

    class Meta:
        verbose_name = _("answer")
        verbose_name_plural = _("answers")
        ordering = ["question__ordering"]

    def __str__(self):
        return f"{self.question}: {self.value}"

    @property
    def get_value(self):
        if self.question.type_field == TYPE_FIELD.rating:
            if not self.question.choices:  # use 5 as default for backward compatibility
                self.question.choices = 5
            return create_star(active_star=int(self.value) if self.value else 0, num_stars=int(self.question.choices))
        elif self.question.type_field == TYPE_FIELD.url:
            return mark_safe(f'<a href="{self.value}" target="_blank">{self.value}</a>')
        elif self.question.type_field == TYPE_FIELD.radio or self.question.type_field == TYPE_FIELD.select or \
                self.question.type_field == TYPE_FIELD.multi_select:
            return self.value.strip().replace("_", " ").capitalize()
        else:
            return self.value

    @property
    def get_value_for_csv(self):
        if self.question.type_field == TYPE_FIELD.radio or self.question.type_field == TYPE_FIELD.select or \
                self.question.type_field == TYPE_FIELD.multi_select:
            return self.value.strip().replace("_", " ").capitalize()
        else:
            return self.value.strip()


class TermsValidators(BaseModel):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, verbose_name=_("question"))
    terms = models.JSONField(_("terms"), default=dict)

    def __str__(self):
        return f"{self.question}"


class SurveySelection(BaseModel):
    name = models.CharField(_("name"), max_length=200, null=False, blank=False)
    description = models.TextField(_("description"), blank=False, null=False)
    slug = models.SlugField(_("slug"), max_length=225, default='', unique=True)
    can_anonymous_user = models.BooleanField(_("anonymous submission"), default=False,
                                             help_text=_("If True, user without authentatication can view."))
    success_page_content = HTMLField(_("Success Page Content"), blank=True, null=True)
    show_on_index = models.BooleanField(_("Show on index page"), default=False,
                                        help_text=_("If True, the " \
                                        "survey selection will be " \
                                        "listed on the index page."))
    fullscreen = models.BooleanField(_("Show fullscreen"), default=False,
                                        help_text=_("Can be checked in " \
                                        "app template for removal of " \
                                        "header/navbar etc."))
    private = models.BooleanField(_("Private Survey Selection"), default=False,
                                        help_text=_("If True the survey will be " \
                                        "listed only on home page for user when " \
                                        "logged in.")) 
    bookmark = models.BooleanField(_("Bookmark Survey Selection"), default=False,
                                        help_text=_("If True a link to the survey selection will be " \
                                        "listed in the user profile bookmark " \
                                        "list."))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(name__length__gt=0), name="non_empty_name_survey_selection")
        ]
        verbose_name = _("survey selection")
        ordering = ['-created_at']
        #verbose_name_plural = _("survey selections")


    def __str__(self):
        return f"{self.name}"
    
    def get_absolute_url(self):
        return reverse ('djf_surveys:survey_selection' , kwargs={'slug': self.slug} )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(SurveySelection, self.name, self.id)
        super().save(*args, **kwargs)
