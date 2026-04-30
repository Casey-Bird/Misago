
from django.http import HttpRequest
from django.template import Context
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from misago.plugins.outlets import PluginOutlet, append_outlet_action, prepend_outlet_action




@mark_safe
def landing_page(request: HttpRequest, context: Context):
    return render_to_string(
        "landing_page_plugin/landing_page.html"
    )


prepend_outlet_action(PluginOutlet.BODY_START, landing_page)

