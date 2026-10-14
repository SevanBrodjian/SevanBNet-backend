from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.urls import reverse

PANEL_PATHS = ("/admin/", "/accounts/")

# Content Security Policy for the control panel. Unfold's Alpine.js needs 'unsafe-eval';
# inline scripts stay blocked (allauth and our pages load scripts from /static/ only).
PANEL_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'unsafe-eval'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "media-src 'self' https://cdn.jsdelivr.net",
        "connect-src 'self'",
        "font-src 'self'",
        "form-action 'self'",
        "frame-ancestors 'self'",
        "base-uri 'none'",
        "object-src 'none'",
    ]
)
PANEL_PERMISSIONS = (
    "camera=(), microphone=(), geolocation=(), "
    "publickey-credentials-get=(self), publickey-credentials-create=(self)"
)


def noindex(get_response):
    """Keep every backend host (API, admin, QR redirects) out of search results.

    The backend is never a page a visitor should land on from a search engine;
    only the frontend at www.sevanb.net should be indexed. A header (rather than
    a robots.txt Disallow) lets crawlers fetch the URL and see the instruction,
    which is what gets already-indexed pages dropped.
    """

    def middleware(request):
        response = get_response(request)
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    return middleware


def admin_hosts(get_response):
    """The control panel exists only on its own hosts (admin.sevanb.net, dev-admin...).

    There, the root opens the panel and responses get strict headers. On every other
    host (go.sevanb.net, *.up.railway.app) the panel's paths are a plain 404, so only
    the API, QR short links and old-URL redirects are served.
    """

    def middleware(request):
        on_panel_host = request.get_host().partition(":")[0] in settings.ADMIN_HOSTS
        if not on_panel_host:
            if request.path.startswith(PANEL_PATHS):
                return HttpResponseNotFound("Not found")
            return get_response(request)
        if request.path == "/":
            return HttpResponseRedirect("/admin/")
        response = get_response(request)
        response.setdefault("Content-Security-Policy", PANEL_CSP)
        response.setdefault("Permissions-Policy", PANEL_PERMISSIONS)
        return response

    return middleware


def require_passkey(get_response):
    """On Railway, staff must register a passkey before they can use the panel."""
    from allauth.mfa.models import Authenticator

    def middleware(request):
        user = request.user
        if (
            settings.REQUIRE_PASSKEY
            and request.path.startswith("/admin/")
            and user.is_authenticated
            and user.is_staff
            and not Authenticator.objects.filter(
                user=user, type=Authenticator.Type.WEBAUTHN
            ).exists()
        ):
            return HttpResponseRedirect(reverse("mfa_add_webauthn"))
        return get_response(request)

    return middleware
