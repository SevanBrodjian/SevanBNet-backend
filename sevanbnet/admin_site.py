"""Control-panel pieces that aren't tied to one model: the environment badge, the
dashboard, the Rebuild site page, and the admin look for allauth's sign-in pages."""

from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.http import url_has_allowed_host_and_scheme

from . import rebuild
from .models import BlogPost, Media, Project, Publication


def environment(request):
    if settings.RAILWAY_ENV == "production":
        return ["Production", "danger"]
    if settings.ON_RAILWAY:
        return ["Sandbox", "warning"]
    if settings.USING_SANDBOX:
        return ["Local · sandbox data", "warning"]
    return ["Local", "info"]


def dashboard(request, context):
    def counts(model, **listed):
        return {
            "visible": model.objects.filter(visible=True, **listed).count(),
            "total": model.objects.count(),
        }

    context.update(
        {
            "cards": [
                ("Projects", "admin:sevanbnet_project_changelist", counts(Project)),
                ("Papers", "admin:sevanbnet_publication_changelist", counts(Publication)),
                ("Writing", "admin:sevanbnet_blogpost_changelist", counts(BlogPost)),
            ],
            "unlisted": Project.objects.filter(visible=True, listed=False).count(),
            "media_count": Media.objects.count(),
            "rebuild_ready": rebuild.configured(),
        }
    )
    return context


def rebuild_view(request):
    if request.method == "POST":
        if not rebuild.configured():
            messages.error(request, "Rebuilding isn't set up on this server.")
        else:
            try:
                rebuild.rebuild()
            except rebuild.RebuildError as error:
                messages.error(request, f"Couldn't start a rebuild. {error}")
            else:
                messages.success(
                    request, "Rebuild started. The site updates in a few minutes, when it's done."
                )
        target = request.POST.get("next", "")
        if url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
            return redirect(target)
        return redirect("admin:index")
    context = {
        **admin.site.each_context(request),
        "title": "Rebuild site",
        "rebuild_ready": rebuild.configured(),
    }
    return TemplateResponse(request, "admin/rebuild.html", context)


def sign_in_pages(request):
    """allauth's pages (sign-in, passkeys, backup codes) and the lockout page wear the
    control panel's look, which needs the admin site's template context."""
    if request.path.startswith(("/accounts/", "/admin/login/")):
        return admin.site.each_context(request)
    return {}
