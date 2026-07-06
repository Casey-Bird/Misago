
import os
import re
from django.contrib.auth import get_user_model
from .models import RoleStyle

User = get_user_model()
STYLES_DIR = os.path.join(os.path.dirname(__file__), 'styles')

def extract_keyframes(css):
    """Extract all @keyframes blocks from CSS by counting braces."""
    blocks = []
    i = 0
    n = len(css)
    while i < n:
        if css[i:i+10] == '@keyframes':
            start = i
            i += 10

            while i < n and css[i] != '{':
                i += 1
            if i < n and css[i] == '{':
                brace_count = 1
                i += 1
                while i < n and brace_count > 0:
                    if css[i] == '{':
                        brace_count += 1
                    elif css[i] == '}':
                        brace_count -= 1
                    i += 1

                blocks.append(css[start:i])
            else:
                i += 1
        else:
            i += 1
    return blocks

class UsernameStyleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response is None:
            return response

        if not response.get('Content-Type', '').startswith('text/html'):
            return response

        try:
            content = response.content.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            return response

        if 'posts-feed-item-post-bit-side-poster-link' not in content:
            return response

        pattern = r'<a\s+([^>]*class="[^"]*posts-feed-item-post-bit-side-poster-link[^"]*"[^>]*)>'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if not matches:
            return response

        user_ids = set()
        for match in matches:
            attrs = match.group(1)
            data_match = re.search(r'data-user-id="(\d+)"', attrs)
            if data_match:
                user_ids.add(int(data_match.group(1)))
                continue
            href_match = re.search(r'href="([^"]*)"', attrs)
            if href_match:
                href = href_match.group(1)
                id_match = re.search(r'/(\d+)/?$', href)
                if id_match:
                    user_ids.add(int(id_match.group(1)))

        if not user_ids:
            return response

        users = User.objects.filter(id__in=user_ids).select_related('group', 'group__style')
        user_map = {u.id: u for u in users}

        css_by_user = {}
        for uid in user_ids:
            user = user_map.get(uid)
            if user and user.group and hasattr(user.group, 'style') and user.group.style.style_name:
                style_name = user.group.style.style_name
                css_file = os.path.join(STYLES_DIR, f"{style_name}.css")
                if os.path.exists(css_file):
                    with open(css_file, 'r') as f:
                        css_content = f.read().strip()
                    css_by_user[uid] = css_content

        if not css_by_user:
            return response


        global_keyframes = []
        class_rules = []
        inline_colors = {}

        for uid, css_content in css_by_user.items():

            kf_blocks = extract_keyframes(css_content)
            if kf_blocks:
                global_keyframes.extend(kf_blocks)

                for kf in kf_blocks:
                    css_content = css_content.replace(kf, '')

            css_content = css_content.strip()
            if css_content:
                color_match = re.search(r'color\s*:\s*([^;]+);', css_content)
                if color_match:
                    inline_colors[uid] = color_match.group(1).strip()
                class_rules.append(f".user-{uid} {{ {css_content} }}")

        if not class_rules and not global_keyframes:
            return response

        style_block = ""
        if global_keyframes:
            style_block += "\n".join(global_keyframes) + "\n"
        if class_rules:
            style_block += "\n".join(class_rules) + "\n"
        style_block = style_block.strip()

        def replace_link(match):
            full_tag = match.group(0)
            attrs = match.group(1)
            data_match = re.search(r'data-user-id="(\d+)"', attrs)
            uid = None
            if data_match:
                uid = int(data_match.group(1))
            else:
                href_match = re.search(r'href="([^"]*)"', attrs)
                if href_match:
                    id_match = re.search(r'/(\d+)/?$', href_match.group(1))
                    if id_match:
                        uid = int(id_match.group(1))
            if not uid:
                return full_tag


            if 'class=' in attrs:
                new_attrs = re.sub(r'class="([^"]*)"', f'class="\\1 user-{uid}"', attrs)
            else:
                new_attrs = f'class="user-{uid}" {attrs}'

            # ermmmmm
            color = inline_colors.get(uid)
            if color:
                if 'style=' in new_attrs:
                    new_attrs = re.sub(r'style="([^"]*)"', f'style="\\1; color: {color};"', new_attrs)
                else:
                    new_attrs = f'style="color: {color};" {new_attrs}'

            return f'<a {new_attrs}>'

        new_content = re.sub(pattern, replace_link, content, flags=re.DOTALL)

        # style blocks
        if style_block:
            style_tag = f"<style>\n{style_block}\n</style>"
            head_close = '</head>'
            if head_close in new_content:
                new_content = new_content.replace(head_close, f'{style_tag}\n{head_close}')
            else:
                body_close = '</body>'
                if body_close in new_content:
                    new_content = new_content.replace(body_close, f'{style_tag}\n{body_close}')

        response.content = new_content.encode('utf-8')
        return response