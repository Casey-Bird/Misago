
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def index(request):
    context = {
        'title': 'Username Styles',
    }
    return render(request, 'username_styles/admin/index.html', context)