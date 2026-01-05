from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.db.models import Case, When
from django.urls import include, path
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from urllib import parse

from faker import Faker
from .models import Survey, Question, Answer, UserAnswer, TermsValidators
User = get_user_model()

class AdminQuestion(admin.ModelAdmin):
    list_display = ('survey', 'label', 'type_field', 'help_text', 'required')
    search_fields = ('survey__name', )


class AdminAnswer(admin.ModelAdmin):
    list_display = ('question', 'get_label', 'value', 'user_answer')
    search_fields = ('question__label', 'value',)
    list_filter = ('question__survey',)

    def get_label(self, obj):
        return obj.question.label
    get_label.admin_order_field = 'question'
    get_label.short_description = 'Label'


class AdminUserAnswer(admin.ModelAdmin):
    list_display = ('survey', 'user', 'created_at', 'updated_at')


class AdminSurvey(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


class AdminTermsValidator(admin.ModelAdmin):
    list_display = ('question', 'terms')


class UserAdmin(AuthUserAdmin):
    change_list_template = "djf_surveys/admin/change_list.html"
    actions = ['user_printview']
    
    # def get_changeform_initial_data(self, request):
    #     return {'dave':'dave'}
    
    def user_printview(self, request, queryset):
        return redirect("admin:show_added_users", str(list(queryset.values_list('id', flat=True))))

    def add_10_random_users(self, request):
        fake = Faker()
        ids = []
        for index in range(10):
            user = User()
            user.username = fake.passport_number()
            user.password = fake.password()
            try:
                user.save()
                ids.append(user.id)
            except IntegrityError:
                index -= 1
                continue
        return redirect("admin:show_added_users", str(ids))

    def get_urls(self):
        urls = super(AuthUserAdmin, self).get_urls()
        my_urls = [
            path("addrand/", self.add_10_random_users),
            path("show_added_users/<str:added_users>/", AddedUser.as_view(), name="show_added_users")
        ]
        return my_urls + urls
    

class AddedUser(ListView):
    template_name = "djf_surveys/admin/show_added_users.html"

    def get_queryset(self):
        pk_list = [ int(id) for id in self.kwargs['added_users'][1:-1].split(',') ]
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pk_list)])
        queryset = User.objects.filter(pk__in=pk_list).order_by(preserved)
        return queryset

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Survey, AdminSurvey)
admin.site.register(Question, AdminQuestion)
admin.site.register(Answer, AdminAnswer)
admin.site.register(UserAnswer, AdminUserAnswer)
admin.site.register(TermsValidators, AdminTermsValidator)
