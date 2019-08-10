"""LivePreview Views."""
import re
import os

from django.conf import settings

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.views.generic import View

from wagtail.core import hooks
from wagtail.core.models import Page

from .models import LivePreviewRevision


class LivePreviewOnEdit(View):
    """Live Preview Views.

    Only GET and POST are allowed.
    """

    http_method_names = ("post", "get")

    def get_live_preview_file_name(self, page_id, user_id):
        """Name a LivePreview file.

        Creates a directory in the media dir called /livepreview/page-#/
        with a file called user-#.html.
        """
        media_dir = settings.MEDIA_ROOT
        preview_dir = "{}/livepreview".format(media_dir)
        page_dir = "{}/page-{}".format(preview_dir, page_id)
        if not os.path.isdir(preview_dir):
            os.mkdir(preview_dir)
        if not os.path.isdir(page_dir):
            os.mkdir(page_dir)
        return "{}/livepreview/page-{}/user-{}.html".format(media_dir, page_id, user_id)

    def post(self, request, *args, **kwargs):
        """When a live preview is saved."""
        page_id = self.args[0]

        page = get_object_or_404(Page, id=page_id).specific
        parent = page.get_parent()

        content_type = ContentType.objects.get_for_model(page)
        page_class = content_type.model_class()

        page_perms = page.permissions_for_user(request.user)
        if not page_perms.can_edit():
            raise PermissionDenied

        edit_handler = page_class.get_edit_handler()
        edit_handler = edit_handler.bind_to(instance=page, request=request)
        form_class = edit_handler.get_form_class()

        form = form_class(
            request.POST, request.FILES, instance=page, parent_page=parent
        )

        json_response = {"is_valid": True}

        if form.is_valid() and not page.locked:
            # Create a new LivePreviewRevision
            page = form.save(commit=False)

            for fn in hooks.get_hooks("before_live_preview_save"):
                fn(request, page)

            # Get or create a LivePreviewRevision
            live_preview_revision, created = LivePreviewRevision.objects.get_or_create(page=page, user=request.user)
            live_preview_revision.content_json = page.to_json()
            live_preview_revision.save()

            # If file based rendering is enabled, save the rendered template to
            # a file so the GET requests can use those instead of having to
            # re-render the template on every request.
            use_file_rendering = getattr(settings, "LIVEPREVIEW_USE_FILE_RENDERING", True)
            if use_file_rendering:
                context = page.get_context(request, *args, **kwargs)
                context["livepreview"] = True
                request.livepreview = True
                template = TemplateResponse(
                    request,
                    page.template,  # Purposely bypassing the get_template() method to avoid using the ajax_template property
                    context,
                )
                rendered = template.render()
                content = rendered.content.decode("utf-8")
                file_name = self.get_live_preview_file_name(page.id, request.user.id)
                with open(file_name, 'w') as the_file:
                    the_file.write(content.strip())

            # Hook to execute after the live preview was saved
            for fn in hooks.get_hooks("after_live_preview_save"):
                fn(request, page)

        elif page.locked:
            # Page is locked
            raise PermissionDenied
        else:
            # Invalid form.
            raise HttpResponseBadRequest

        return JsonResponse(json_response)

    def get(self, request, *args, **kwargs):
        """Get the latest live preview and render the page with it.

        Checks for a file first. If the rendered template exists in a file
        then serve that file. This prevents expensive queries form happening as
        often as every second.
        """
        page_id = self.args[0]

        # Always look for the file first.
        # If there's a LivePreview file, serve that. This will reduce the number of DB queries hitting the server
        file_name = self.get_live_preview_file_name(page_id, request.user.id)
        use_file_rendering = getattr(settings, "LIVEPREVIEW_USE_FILE_RENDERING", True)
        if use_file_rendering and os.path.isfile(file_name):
            with open(file_name, 'r') as file:
                page_content = file.read()
                return HttpResponse(page_content)

        # Attempt to get the page.
        try:
            page = LivePreviewRevision.objects.get(id=page_id, user=request.user)
        except LivePreviewRevision.DoesNotExist:
            page = get_object_or_404(Page, id=page_id).specific

        if request.GET.get("from_revision", None):
            # Load page from the latest revision
            page = page.get_latest_revision_as_page()
        else:
            # Load page from a Live Preview
            # Revisions order_by -created_at, but since that value always
            # increments and the PK always increments, we can simply order_by
            # the id DESC and get the same results.
            last_live_preview = (
                LivePreviewRevision.objects.filter(page_id=page.id).order_by("-id").first()
            )
            if last_live_preview:
                content_json = last_live_preview.content_json
                page = page.specific_class.from_json(content_json)
        context = page.get_context(request, *args, **kwargs)
        context["livepreview"] = True
        request.livepreview = True
        return TemplateResponse(
            request,
            page.template,  # Purposely bypassing the get_template() method to avoid using the ajax_template property
            context,
        )
