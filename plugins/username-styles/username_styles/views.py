import os

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from misago.users.models import Group

from .models import RoleStyle

STYLES_DIR = os.path.join(os.path.dirname(__file__), 'styles')
os.makedirs(STYLES_DIR, exist_ok=True)


def get_style_files():
    files = []

    for f in os.listdir(STYLES_DIR):
        if f.endswith('.css'):
            files.append(f[:-4])

    return files


@staff_member_required
def admin_index(request):

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            name = request.POST.get('name', '').strip()
            content = request.POST.get('content', '').strip()

            if name and content:

                filepath = os.path.join(STYLES_DIR, f"{name}.css")

                if not os.path.exists(filepath):
                    with open(filepath, 'w') as f:
                        f.write(content)
                    messages.success(request, f"Style '{name}' created.")

                else:
                    messages.error(request, f"Style '{name}' already exists.")

            else:
                messages.error(request, "Name and CSS content are required.")

            return redirect('misago:admin:plugins:username-styles:index')

        elif action == 'delete':

            name = request.POST.get('name', '').strip()

            if name:
                filepath = os.path.join(STYLES_DIR, f"{name}.css")

                if os.path.exists(filepath):
                    os.remove(filepath)
                    RoleStyle.objects.filter(style_name=name).update(style_name=None)
                    messages.success(request, f"Style '{name}' deleted.")
                else:
                    messages.error(request, f"Style '{name}' not found.")

            return redirect('misago:admin:plugins:username-styles:index')

        elif action == 'update_roles':

            for key, value in request.POST.items():
                if key.startswith('role_'):
                    role_id = key.split('_')[1]
                    style = value.strip() or None
                    try:
                        role = Group.objects.get(id=role_id)
                        obj, created = RoleStyle.objects.get_or_create(role=role)
                        obj.style_name = style
                        obj.save()
                    except Group.DoesNotExist:
                        pass

            messages.success(request, "Role assignments saved.")

            return redirect('misago:admin:plugins:username-styles:index')

    styles = get_style_files()
    groups = Group.objects.all().order_by('name')
    groups_with_style = []

    for group in groups:

        style_name = None

        if hasattr(group, 'style'):
            style_name = group.style.style_name

        groups_with_style.append({'group': group, 'style': style_name})

    return render(request, 'username_styles/admin/index.html', {
        'styles': styles,
        'groups_with_style': groups_with_style,
    })