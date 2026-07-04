"""
Service for tracking usernames
"""

from datetime import timedelta

from django.utils import timezone


from ..categories.models import Category
from ..legal.models import Agreement
from ..notifications.models import Notification
from ..postedits.models import PostEdit
from ..threadupdates.models import ThreadUpdate
from ..threads.models import Post, Thread
from ..likes.models import Like


def get_username_options(settings, user, user_acl):
    changes_left = get_left_namechanges(user, user_acl)
    next_on = get_next_available_namechange(user, user_acl, changes_left)

    return {
        "changes_left": changes_left,
        "next_on": next_on,
        "length_min": settings.username_length_min,
        "length_max": settings.username_length_max,
    }


def get_left_namechanges(user, user_acl):
    name_changes_allowed = user_acl["name_changes_allowed"]
    if not name_changes_allowed:
        return 0

    valid_changes = get_valid_changes_queryset(user, user_acl)
    used_changes = valid_changes.count()
    if name_changes_allowed <= used_changes:
        return 0
    return name_changes_allowed - used_changes


def get_next_available_namechange(user, user_acl, changes_left):
    name_changes_expire = user_acl["name_changes_expire"]
    if changes_left or not name_changes_expire:
        return None

    valid_changes = get_valid_changes_queryset(user, user_acl)
    name_last_changed_on = valid_changes.latest().changed_on
    return name_last_changed_on + timedelta(days=name_changes_expire)


def get_valid_changes_queryset(user, user_acl):
    name_changes_expire = user_acl["name_changes_expire"]
    queryset = user.namechanges.filter(changed_by=user)
    if user_acl["name_changes_expire"]:
        cutoff = timezone.now() - timedelta(days=name_changes_expire)
        return queryset.filter(changed_on__gte=cutoff)
    return queryset


def record_name_change(self, changed_by, new_username, old_username):
    return self.namechanges.create(
        new_username=new_username,
        old_username=old_username,
        changed_by=changed_by,
        changed_by_username=changed_by.username,
    )


def update_username_references(self, user):
    user.user_renames.update(changed_by_username=user.username)

    Category.objects.filter(last_poster=user).update(last_poster_name=user.username, last_poster_slug=user.slug)

    Agreement.objects.filter(created_by=user).update(created_by_name=user.username)
    Agreement.objects.filter(last_modified_by=user).update(last_modified_by_name=user.username)

    Notification.objects.filter(actor=user).update(actor_name=user.username)

    Thread.objects.filter(starter=user).update(starter_name=user.username, starter_slug=user.slug)
    Thread.objects.filter(last_poster=user).update(last_poster_name=user.username, last_poster_slug=user.slug)
    Thread.objects.filter(solution_by=user).update(solution_by_name=user.username, solution_by_slug=user.slug)
    Thread.objects.filter(solution_selected_by=user).update(solution_selected_by_name=user.username, solution_selected_by_slug=user.slug)

    ThreadUpdate.objects.filter(actor=user).update(actor_name=user.username)
    ThreadUpdate.objects.filter(hidden_by=user).update(hidden_by_name=user.username)
    ThreadUpdate.objects.context_object(user).update(context=user.username)

    Post.objects.filter(poster=user).update(poster_name=user.username)
    Post.objects.filter(last_editor=user).update(last_editor_name=user.username, last_editor_slug=user.slug)
    Post.objects.filter(hidden_by=user).update(hidden_by_name=user.username, hidden_by_slug=user.slug)

    PostEdit.objects.filter(user=user).update(user_name=user.username, user_slug=user.slug)
    PostEdit.objects.filter(hidden_by=user).update(hidden_by_name=user.username, hidden_by_slug=user.slug)

    Like.objects.filter(user=user).update(user_name=user.username, user_slug=user.slug)
