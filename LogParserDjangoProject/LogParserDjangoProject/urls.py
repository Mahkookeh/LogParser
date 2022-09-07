"""LogParserDjangoProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from LogParserWebApp.views import DataViewSet, PlayersViewSet, LogsViewSet, LogsWithDataView


# Data router
data_router = routers.SimpleRouter()
data_router.register(
    r'data',
    DataViewSet,
    basename='data',
)

# Players router
players_router = routers.SimpleRouter()
players_router.register(
    r'players',
    PlayersViewSet,
    basename='players',
)

# Logs router
logs_router = routers.SimpleRouter()
logs_router.register(
    r'logs',
    LogsViewSet,
    basename='logs',
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(('LogParserWebApp.urls', 'log_parser'), namespace='log_parser')),
    path('api/', include(data_router.urls)),
    path('api/', include(players_router.urls)),
    path('api/', include(logs_router.urls)),
    path('api/logs-with-data/', LogsWithDataView.as_view()),
]
