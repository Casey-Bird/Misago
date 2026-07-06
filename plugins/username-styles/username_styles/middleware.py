import os
import re
from django.contrib.auth import get_user_model
from .models import RoleStyle

User = get_user_model()
STYLES_DIR = os.path.join(os.path.dirname(__file__), 'styles')

PLACEHOLDER_CLASS = '.username'

USERNAME_LINK_CLASSES = [
    'posts-feed-item-post-bit-side-poster-link',
]


def _build_username_link_pattern(classes):
    escaped = [re.escape(cls) for cls in classes]
    class_alternation = '|'.join(escaped)
    return re.compile(
        rf'<a\s+([^>]*class="[^"]*(?:{class_alternation})[^"]*"[^>]*)>',
        re.DOTALL
    )


def _extract_user_id_from_attributes(attributes):

    data_match = re.search(r'data-user-id="(\d+)"', attributes)
    if data_match:
        return int(data_match.group(1))

    href_match = re.search(r'href="([^"]*)"', attributes)
    if href_match:
        href = href_match.group(1)
        id_match = re.search(r'/(\d+)/?$', href)
        if id_match:
            return int(id_match.group(1))
    return None


def _fetch_users_by_ids(user_ids):
    users = User.objects.filter(id__in=user_ids).select_related('group', 'group__style')
    return {user.id: user for user in users}


def _load_css_templates(user_ids, user_map):
    css_by_user = {}
    for user_id in user_ids:
        user = user_map.get(user_id)
        if not (user and user.group and hasattr(user.group, 'style') and user.group.style.style_name):
            continue
        style_name = user.group.style.style_name
        css_file = os.path.join(STYLES_DIR, f"{style_name}.css")
        if os.path.exists(css_file):
            with open(css_file, 'r') as f:
                css_content = f.read().strip()
            if css_content:
                css_by_user[user_id] = css_content
    return css_by_user


def _inject_style_block_into_html(html, style_block):
    style_tag = f"<style>\n{style_block}\n</style>"
    if '</head>' in html:
        return html.replace('</head>', f'{style_tag}\n</head>')
    elif '</body>' in html:
        return html.replace('</body>', f'{style_tag}\n</body>')
    return html + f'\n{style_tag}'


class UsernameStyleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.link_pattern = _build_username_link_pattern(USERNAME_LINK_CLASSES)

    def __call__(self, request):
        response = self.get_response(request)

        if response is None:
            return response

        if not response.get('Content-Type', '').startswith('text/html'):
            return response

        try:
            html = response.content.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            return response

        if not any(cls in html for cls in USERNAME_LINK_CLASSES):
            return response

        matches = list(self.link_pattern.finditer(html))
        if not matches:
            return response

        user_ids = set()
        for match in matches:
            uid = _extract_user_id_from_attributes(match.group(1))
            if uid:
                user_ids.add(uid)

        if not user_ids:
            return response

        def add_class_to_link(match):
            attrs = match.group(1)
            uid = _extract_user_id_from_attributes(attrs)
            if uid is None:
                return match.group(0)
            if 'class=' in attrs:
                new_attrs = re.sub(r'class="([^"]*)"', f'class="\\1 user-{uid}"', attrs)
            else:
                new_attrs = f'class="user-{uid}" {attrs}'
            return f'<a {new_attrs}>'

        html = self.link_pattern.sub(add_class_to_link, html)

        user_map = _fetch_users_by_ids(user_ids)
        css_by_user = _load_css_templates(user_ids, user_map)

        if css_by_user:
            all_css = []
            for user_id, css_template in css_by_user.items():
                css_for_user = css_template.replace(PLACEHOLDER_CLASS, f'.user-{user_id}')
                all_css.append(css_for_user)

            style_block = "\n".join(all_css)
            html = _inject_style_block_into_html(html, style_block)

        response.content = html.encode('utf-8')
        return response