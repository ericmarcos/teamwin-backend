"""
Django settings for teamwin project.

Generated by 'django-admin startproject' using Django 1.8b2.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's_+3wxw#a86nsx@y(7yjcya#rt7eek3j)&^hcpi(s25lqy4#41'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'dareyoo.herokuapp.com',
    'dareyoo2.herokuapp.com',
    'dareyoo-pro.herokuapp.com',
    'dareyoo-pre.herokuapp.com',
    'teamwin.herokuapp.com',
    '.dareyoo.com',
    '.dareyoo.net',
    '.dareyoo.es',
    '.dareyoo.dev',
    '.teamwinapp.com',
    '.teamwinapp.es',
    '.teamwinapp.dev'
]

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'storages',
    'oauth2_provider',
    'social.apps.django_app.default',
    'rest_framework_social_oauth2',
    'rest_framework',
    'users',
    'game',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'dareyoo2.urls'

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
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'teamwin.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

import dj_database_url


DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = os.environ.get('STATIC_URL', '/static/')

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.environ.get('PROJECT_HOME', '') + '/static/',
)

#CELERY
REDIS_URL = os.environ.get('REDISTOGO_URL', os.environ.get('REDIS_URL', 'redis://localhost:6379'))

CELERY_TIMEZONE = 'UTC'
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

# SOCIAL AUTH

AUTHENTICATION_BACKENDS = (
    # Facebook OAuth2
    'social.backends.facebook.FacebookAppOAuth2',
    'social.backends.facebook.FacebookOAuth2',

    # django-rest-framework-social-oauth2
    'rest_framework_social_oauth2.backends.DjangoOAuth2',

    # Django
    'django.contrib.auth.backends.ModelBackend',
)

# Facebook configuration
SOCIAL_AUTH_FACEBOOK_KEY = os.environ.get('FACEBOOK_APP_ID')
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get('FACEBOOK_API_SECRET')

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'user_friends']
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = ['username', 'first_name', 'middle_name', 'last_name', 'locale', 'gender', 'location', 'timezone']

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'users.pipelines.save_profile',
    'users.pipelines.save_profile_picture',
    'users.pipelines.save_friends'
)


# REST FRAMEWORK

REST_FRAMEWORK = {
    
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # OAuth
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework_social_oauth2.authentication.SocialAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

### STORAGES ###

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_HOST = os.environ.get('AWS_S3_HOST')
AWS_QUERYSTRING_AUTH = False

### CORS ###
CORS_URLS_REGEX = r'^(/api/.*|/auth/.*)$'
CORS_ORIGIN_ALLOW_ALL = True

# IONIC

IONIC_APP_ID = os.environ.get('IONIC_APP_ID')
IONIC_API_KEY = os.environ.get('IONIC_API_KEY')


# DAREYOO

DEFAULT_PROFILE_PIC_URL = STATIC_URL + 'default_profile_pics/profile_%s.png'
DEFAULT_TEAM_PIC_URL = STATIC_URL + 'default_team_pics/team_%s.png'

DAREYOO_MAX_PLAYERS = 11 # Max players per team
DAREYOO_MAX_TEAMS = 5 # Max teams per player
DAREYOO_MAX_LEAGUES = 3 # Max leagues per team
