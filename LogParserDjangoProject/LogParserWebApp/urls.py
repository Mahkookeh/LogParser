from django.urls import path, re_path
from . import views
from rest_framework import permissions
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view as get_view
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/doc/', SpectacularSwaggerView.as_view(url_name='log_parser:schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='log_parser:schema'), name='redoc'),    
]