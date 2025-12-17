from django.urls import path, include
from djf_surveys import views
from djf_surveys.app_settings import SURVEYS_ADMIN_BASE_PATH

app_name = 'djf_surveys'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('survey_selection_list/', views.SurveySelectionListView.as_view(), name='survey_selection_list'),
    path('detail/<str:slug>/<str:selection_slug>/', views.DetailSurveyView.as_view(), name='detail'),
    path('edit/<int:pk>/', views.EditSurveyFormView.as_view(), name='edit'),
    path('detail/result/<int:pk>/', views.DetailResultSurveyView.as_view(), name='detail_result'),
    path('respond/<str:slug>/<str:selection_slug>/', views.RespondSurveyFormView.as_view(), name='respond'),
    path('delete/<int:pk>/', views.DeleteSurveyAnswerView.as_view(), name='delete'),
    path('share/<str:slug>/', views.share_link, name='share_link'),
    path('selection_share/<str:slug>/', views.selection_share_link, name='selection_share_link'),
    path('success/<str:slug>/<str:selection_slug>/', views.SuccessPageSurveyView.as_view(), name='success'),
    path('selection/<str:slug>/', views.SurveySelectionDetailView.as_view(), name='survey_selection'),
    path('withdraw_response/', views.WithdrawResponseView.as_view(), name='withdraw_response'),
    path(SURVEYS_ADMIN_BASE_PATH, include('djf_surveys.admins.urls')),
]
