from djf_surveys import app_settings
from djf_surveys.utils import get_type_field

def surveys_context(request):
    context = {
        'get_master_template': app_settings.SURVEY_MASTER_TEMPLATE,
        'get_admin_master_template': app_settings.SURVEY_ADMIN_MASTER_TEMPLATE,
        'chart_js_src': app_settings.CHART_JS_SRC,
        'get_type_field': get_type_field,
        'link_back_on_success_page': app_settings.SURVEY_LINK_BACK_ON_SUCCESS_PAGE,
        'DEFAULT_THANK_YOU_MESSAGE': app_settings.SURVEY_DEFAULT_THANK_YOU_MESSAGE,
        'SURVEY_FORM_TIMEOUT': app_settings.SURVEY_FORM_TIMEOUT,
        'SURVEY_FORM_TIMEOUT_DIALOG': app_settings.SURVEY_FORM_TIMEOUT_DIALOG,
        'SURVEY_INCLUDE_NAVBAR': app_settings.SURVEY_INCLUDE_NAVBAR,
        'SURVEY_ANONYMOUS_VIEW_LIST': app_settings.SURVEY_ANONYMOUS_VIEW_LIST,
        'SURVEY_DEBUG': app_settings.SURVEY_DEBUG,
    }
    return context
