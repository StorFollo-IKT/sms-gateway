# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your_secret_key'
ALLOWED_HOSTS = ['127.0.0.1']
# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'smsgateway',
        'USER': 'smsgateway',
        'PASSWORD': 'asdf',
        'HOST': '127.0.0.1',
        'TEST': {
            'COLLATION': 'utf8_general_ci',
        }
    }
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
