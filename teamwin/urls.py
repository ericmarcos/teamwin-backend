from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auth/', include('rest_framework_social_oauth2.urls')),
    url(r'^api/', include('game.urls')),
    url(r'^$', TemplateView.as_view(template_name="landing.html"), name='landing'),
    url(r'^terms_conditions$', TemplateView.as_view(template_name="terms_conditions.html"), name='terms_conditions'),
]
