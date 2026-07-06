
from django.apps import AppConfig
from django.conf import settings

class UsernameStylesConfig(AppConfig):
    name = "username_styles"
    verbose_name = "Username Styles"

    def ready(self):
        from . import admin  # noqa: F401

        middleware = 'username_styles.middleware.UsernameStyleMiddleware'
        if middleware not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append(middleware)