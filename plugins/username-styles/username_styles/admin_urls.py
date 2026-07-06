

from django.urls import path
from . import views

app_name = "username-styles"

urlpatterns = [
    path("", views.admin_index, name="index"),
]