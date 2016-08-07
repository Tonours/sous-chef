from .settings import *


SECRET_KEY = "SecretKeyForUseOnTravis"

DEBUG = False
TEMPLATE_DEBUG = False

DATABASES = {
    'default': {
        'HOST': 'localhost',
    }
}
