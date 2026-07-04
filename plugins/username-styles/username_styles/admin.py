
from django.urls import path, include
from django.utils.translation import pgettext_lazy

from . import views


class MisagoAdminExtension:
    def register_urlpatterns(self, urlpatterns):
        urlpatterns.patterns(
            "plugins",
            path("username-styles/", include(("username_styles.admin_urls", "username-styles")))
        )

    def register_navigation_nodes(self, site):
        site.add_node(
            name=pgettext_lazy("admin node", "Username Styles"),
            icon="fa fa-cog",
            parent="plugins",
            namespace="username-styles",
        )