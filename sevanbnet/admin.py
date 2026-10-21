from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.views.generic import TemplateView
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.views import UnfoldModelAdminViewMixin
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldAdminTextInputWidget

from . import media, rebuild
from .models import BlogPost, Media, Project, Publication, QRRedirect, SiteSettings


class MediaPicker(UnfoldAdminTextInputWidget):
    """A text box for a URL that also suggests every file in the media library."""

    def render(self, name, value, attrs=None, renderer=None):
        attrs = {**(attrs or {}), "list": f"{name}-library"}
        html = super().render(name, value, attrs, renderer)
        files = Media.objects.exclude(kind=Media.FILE).values_list("url", "path")
        options = format_html_join("", '<option value="{}">{}</option>', files)
        return format_html('{}<datalist id="{}-library">{}</datalist>', html, name, options)


class RebuildsSite:
    """Content the site's prerendered pages show: saving or deleting it rebuilds the site
    shortly after (see rebuild.soon), so nothing published lags behind the panel."""

    def rebuild_soon(self, request):
        if rebuild.soon() and not getattr(request, "_rebuild_noted", False):
            request._rebuild_noted = True
            messages.info(
                request,
                "The site rebuilds itself in about a minute; "
                "the change is live a few minutes after that.",
            )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.rebuild_soon(request)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        self.rebuild_soon(request)

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        self.rebuild_soon(request)


@admin.register(SiteSettings)
class SiteSettingsAdmin(RebuildsSite, ModelAdmin):
    """One row of site-wide text; the list page goes straight to it."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect("admin:sevanbnet_sitesettings_change", SiteSettings.load().pk)


@admin.register(Project)
class ProjectAdmin(RebuildsSite, ModelAdmin):
    list_display = ("title", "visible", "listed", "rank", "start", "end")
    list_editable = ("visible", "listed")
    list_filter = ("visible", "listed")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("linked_papers",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "visible",
                    "listed",
                    "standalone",
                    "rank",
                    ("start", "end"),
                    "source",
                )
            },
        ),
        ("Projects list", {"fields": ("summary", "thumbnail", "glow")}),
        (
            "Default page",
            {
                "description": "Ignored when the site's code has a hand-built page for this slug.",
                "fields": ("media_kind", "media", "description"),
            },
        ),
        (
            "Media details",
            {
                "classes": ["collapse"],
                "fields": ("media_poster", "media_alt", ("media_width", "media_height")),
            },
        ),
        ("Papers", {"fields": ("linked_papers",)}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in ("thumbnail", "media", "media_poster"):
            kwargs["widget"] = MediaPicker
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @display(description="Papers linking here")
    def linked_papers(self, obj):
        papers = obj.papers.all() if obj.pk else []
        if not papers:
            return "None"
        rows = (
            (
                reverse("admin:sevanbnet_publication_change", args=[p.pk]),
                p.title,
                "" if p.visible else " (hidden)",
            )
            for p in papers
        )
        return format_html_join(format_html("<br>"), '<a href="{}">{}</a>{}', rows)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and "visible" in form.changed_data and not obj.visible:
            titles = [p.title for p in obj.papers.filter(visible=True)]
            if titles:
                messages.warning(
                    request,
                    f"“{obj}” is hidden, so these papers no longer show a Site button: "
                    + "; ".join(titles),
                )


class ProjectChoice(forms.ModelChoiceField):
    def label_from_instance(self, project):
        return f"{project.title} (hidden)" if not project.visible else project.title


@admin.register(Publication)
class PaperAdmin(RebuildsSite, ModelAdmin):
    list_display = ("title", "visible", "rank", "status", "venue", "date", "project")
    list_editable = ("visible",)
    list_filter = ("visible",)
    search_fields = ("title", "authors", "venue")
    fieldsets = (
        (None, {"fields": ("title", "visible", "authors", "venue", "status", "date")}),
        ("Links", {"fields": ("paper_url", "project", "project_url")}),
        ("Papers page", {"fields": ("description", "bibtex", "key", "rank", "doi")}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "project":
            kwargs["form_class"] = ProjectChoice
            kwargs["queryset"] = Project.objects.order_by("title")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        paper = self.get_object(request, object_id)
        if request.method == "GET" and paper and paper.project and not paper.project.visible:
            messages.info(
                request,
                f"The linked project “{paper.project}” is hidden, "
                "so this paper shows no Project button.",
            )
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(BlogPost)
class PostAdmin(RebuildsSite, ModelAdmin):
    list_display = ("title", "visible", "date", "slug")
    list_editable = ("visible",)
    list_filter = ("visible",)
    search_fields = ("title",)
    ordering = ("-date",)
    prepopulated_fields = {"slug": ("title",)}
    fields = ("title", "slug", "visible", "date", "description")


class UploadForm(forms.Form):
    file = forms.FileField(widget=UnfoldAdminFileFieldWidget)
    folder = forms.CharField(
        required=False,
        max_length=100,
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "e.g. projects/learning-taichi"}),
        help_text="Optional. Where it goes in the media repo; defaults to uploads/.",
    )


@admin.register(Media)
class MediaAdmin(ModelAdmin):
    list_display = ("preview", "path", "kind", "file_size", "uploaded_at", "link")
    list_filter = ("kind",)
    search_fields = ("path",)
    readonly_fields = ("preview", "path", "url", "kind", "size", "uploaded_at")
    list_before_template = "admin/sevanbnet/media/note.html"

    def has_add_permission(self, request):
        return media.configured() and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), "uploads_ready": media.configured()}
        return super().changelist_view(request, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        if not self.has_add_permission(request):
            return redirect("admin:sevanbnet_media_changelist")
        form = UploadForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            try:
                item = media.upload(form.cleaned_data["file"], form.cleaned_data["folder"])
            except media.UploadError as error:
                form.add_error("file", str(error))
            else:
                messages.success(request, f"Uploaded {item.path}. Its URL: {item.url}")
                return redirect("admin:sevanbnet_media_changelist")
        context = {
            **self.admin_site.each_context(request),
            "title": "Upload media",
            "opts": self.opts,
            "form": form,
            "max_mb": media.MAX_BYTES // 2**20,
            "types": ", ".join(sorted(media.KINDS)),
        }
        return TemplateResponse(request, "admin/sevanbnet/media/upload.html", context)

    @display(description="")
    def preview(self, obj):
        if obj.kind == Media.IMAGE:
            return format_html('<img src="{}" alt="" class="media-thumb">', obj.url)
        return obj.get_kind_display()

    @display(description="Size")
    def file_size(self, obj):
        return f"{obj.size / 2**20:.1f} MB" if obj.size >= 2**20 else f"{obj.size // 1024} KB"

    @display(description="URL")
    def link(self, obj):
        return format_html(
            '<input class="media-url" type="text" readonly value="{}" aria-label="URL">', obj.url
        )


class QRDashboard(UnfoldModelAdminViewMixin, TemplateView):
    """The QR code manager: cards for every short link, with live previews and scan counts."""

    title = "QR codes"
    permission_required = ("sevanbnet.view_qrredirect",)
    template_name = "admin/qr_dashboard.html"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "qr_base_url": settings.QR_BASE_URL}


@admin.register(QRRedirect)
class QRRedirectAdmin(ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect("qr_dashboard")


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
