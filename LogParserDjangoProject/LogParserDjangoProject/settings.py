"""
Django settings for LogParserDjangoProject project.

Generated by 'django-admin startproject' using Django 4.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import yaml

config = yaml.safe_load(open("djangoconfig.yml"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/



# Current list of files
SECRET_KEY = config["credentials"]["secretKey"]
DATABASE_NAME = config["credentials"]["database"]
DATABASE_HOST = config["credentials"]["host"]
DATABASE_USER = config["credentials"]["user"]
DATABASE_PASSWORD = config["credentials"]["password"]
DATABASE_PORT = config["credentials"]["port"]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config["credentials"]["secretKey"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
]

LOCAL_APPS = [
    'LogParserWebApp.apps.LogparserwebappConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'LogParserDjangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'LogParserDjangoProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT,

    }
}


# Rest Framework
REST_FRAMEWORK = {
    # Rendering
    # https://www.django-rest-framework.org/api-guide/renderers/
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],

    # Authentication
    # https://www.django-rest-framework.org/api-guide/authentication/
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Choose auth to use
        # 'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.RemoteUserAuthentication',
    ],

    # Permissions
    # https://www.django-rest-framework.org/api-guide/permissions/
    'DEFAULT_PERMISSION_CLASSES': [
        # Choose permissions to use
        # 'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        # 'rest_framework.permissions.IsAdminUser',
        # 'rest_framework.permissions.AllowAny',
    ],

    # Parsers
    # https://www.django-rest-framework.org/api-guide/parsers/
    'DEFAULT_PARSER_CLASSES': [
        # Choose parser to use
        'rest_framework.parsers.JSONParser',
        # 'rest_framework.parsers.FormParser',
        # 'rest_framework.parsers.MultiPartParser',
    ],

    # Filtering
    # https://www.django-rest-framework.org/api-guide/filtering/
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],

    # Pagination
    # https://www.django-rest-framework.org/api-guide/pagination/
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
        # Pagination options:
        # 'rest_framework.pagination.PageNumberPagination'
        # 'rest_framework.pagination.LimitOffsetPagination'
        # 'rest_framework.pagination.CursorPagination'
    'PAGE_SIZE': 20,

}

# Only use in DEBUG mode
if DEBUG:
    # Rendering
    # Disable in production because of security concerns
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

    # Authentication
    # Implies use of cookies and is not entirely stateless
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
        'rest_framework.authentication.SessionAuthentication',
    )


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = 'static'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
