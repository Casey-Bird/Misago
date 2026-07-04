from django.dispatch import Signal, receiver

from ..users.signals import anonymize_user_data
from .models import Category


@receiver([anonymize_user_data])
def update_usernames(sender, **kwargs):
    Category.objects.filter(last_poster=sender).update(
        last_poster_name=sender.username, last_poster_slug=sender.slug
    )
