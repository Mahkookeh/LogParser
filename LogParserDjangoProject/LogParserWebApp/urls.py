from django.urls import path, re_path
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Log Parser API",
        default_version='v1',
        description="API for parsing data from Elite Insight logs of Guild Wars 2 encounters.",
        contact=openapi.Contact(email="tmanju9067@gmail.com"),
        license=openapi.License(name="Apache 2.0", url="http://www.apache.org/licenses/LICENSE-2.0"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^doc(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),  
    path('doc/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),  
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),  
]