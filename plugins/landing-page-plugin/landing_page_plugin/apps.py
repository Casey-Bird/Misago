
from django.apps import AppConfig


class MisagoUsersOnlinePlugin(AppConfig):
    name = "landing_page_plugin"

    def ready(self):
        from . import landing_page