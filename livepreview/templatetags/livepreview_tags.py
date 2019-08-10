"""Live preview template tags."""
from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("livepreview_javascript_tags.html", takes_context=True)
def livepreview_js(context):
    """Include the template file that will add the relevant JS to your page."""
    return context


@register.simple_tag
def livepreview_interval_time():
    """Get the LIVEPREVIEW_TIMEOUT setting. Default is 1000ms.

    The lowest value possible is 1000ms as to not DDoS ourselves.
    """
    use_file_rendering = getattr(settings, "LIVEPREVIEW_USE_FILE_RENDERING", True)
    timeout = getattr(settings, "LIVEPREVIEW_TIMEOUT", 1000)
    if not use_file_rendering:
        # Not using file-based rendering: Minimum 1 second timeout
        return 1000 if timeout < 1000 else timeout
    else:
        # Using file-based rendering. Minimum 250ms timeout.
        return 250 if timeout < 250 else timeout

