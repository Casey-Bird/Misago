
from django.urls import path, include

class MisagoAdminExtension:
    def register_urlpatterns(self, urlpatterns):
        urlpatterns.patterns(
            "plugins",
            path("username-styles/", include(("username_styles.admin_urls", "username-styles")))
        )

    def register_navigation_nodes(self, site):
        site.add_node(
            name="Username Styles",
            icon="fa fa-paint-brush",
            parent="plugins",
            namespace="username-styles",
        )