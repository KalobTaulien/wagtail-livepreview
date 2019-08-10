from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _


class LivePreviewRevision(models.Model):
    """Live Preview Revision History."""

    page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name=_("page"),
        related_name="live_preview_updates",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(db_index=True, verbose_name=_("created at"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    content_json = models.TextField(verbose_name=_("content JSON"))

    def save(self, *args, **kwargs):
        # Set default value for created_at to now
        # We cannot use auto_now_add as that will override
        # any value that is set before saving
        if self.created_at is None:
            self.created_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return '"' + str(self.page) + '" at ' + str(self.created_at)

    class Meta:
        verbose_name = _("page live preview")
        verbose_name_plural = _("page live previews")
