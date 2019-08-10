"""Live preview hooks."""
# from django.http import HttpResponse
import json
import os
import shutil

from django.conf import settings
from django.conf.urls import url
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.html import format_html

from wagtail.core import hooks

from . import views
from .models import LivePreviewRevision


@hooks.register("insert_global_admin_js", order=100)
def add_livepreview_js():
    """Add livepreview .js file."""
    js_settings = {
        "auto_save_as_revision": getattr(
            settings, "LIVEPREVIEW_SAVE_AS_REVISIONS", False
        ),
        "save_revision_count": getattr(settings, "LIVEPREVIEW_SAVE_REVISION_COUNT", 10),
    }
    js_settings = "<script>livepreviewSettings = {}</script>".format(
        json.dumps(js_settings)
    )
    js = js_settings + format_html(
        '<script src="{}"></script>', static("livepreview/js/livepreview.js")
    )
    return js


@hooks.register("insert_global_admin_js", order=99)
def add_split_js():
    """Add livepreview .js file."""
    return format_html(
        '<script src="{}"></script>', static("livepreview/js/split.min.js")
    )


@hooks.register("insert_global_admin_css", order=100)
def global_admin_css():
    """Add livepreview .css file."""
    return format_html(
        '<link rel="stylesheet" href="{}" type="text/css">',
        static("livepreview/css/livepreview.css"),
    )


@hooks.register("register_admin_urls")
def urlconf_time():
    """Add the live_preview urls."""
    return [
        url(
            r"^pages/(\d+)/edit/live_preview/$",
            views.LivePreviewOnEdit.as_view(),
            name="live_preview",
        )
    ]


@hooks.register("after_delete_page")
def before_edit_page(request, page_class):
    """Find all LivePreviews and remove them."""
    # Delete all LivePreview rows in the livepreviewrevision table.
    LivePreviewRevision.objects.filter(page_id=page_class.id).delete()
    # Remove all temporary Live Preview files matching this path: /{MEDIA}/livepreview/page-{#}
    # Do not check if LIVEPREVIEW_USE_FILE_RENDERING is enabled. This setting could have been enabled
    # for a while and then disabled, leaving dangling files. Instead, destroy the entire dir
    # regardless of this setting.
    page_dir = "{}/livepreview/page-{}".format(settings.MEDIA_ROOT, page_class.id)
    if os.path.isdir(page_dir):
        shutil.rmtree(page_dir)


# @hooks.register('after_live_preview_save')
# def after_live_preview_save(request, page):
#     """Sample live preview hooks."""
#     print(page.id)


# @hooks.register('before_live_preview_save')
# def before_live_preview_save(request, page):
#     """Sample live preview hooks."""
#     print(page.id)
