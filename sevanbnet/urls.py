from contextlib import suppress

from allauth.account.decorators import secure_admin_login
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.exceptions import NotRegistered
from django.contrib.auth.models import Group
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from . import qr_api, qr_views, views
from .admin import QRDashboard
from .admin_site import rebuild_view
from .models import QRRedirect

# Keep the panel to what Sevan uses; allauth and Django register a few extra models.
for model in (Group, EmailAddress, Authenticator):
    with suppress(NotRegistered):
        admin.site.unregister(model)

admin.site.index_title = "Overview"

if settings.ON_RAILWAY:
    # Sign-in goes through allauth (password + passkey) instead of the admin's password form.
    admin.site.login = secure_admin_login(admin.site.login)

router = DefaultRouter(trailing_slash=True)
router.include_root_view = False
router.register(r"projects", views.ProjectViewSet)
router.register(r"papers", views.PaperViewSet)
router.register(r"posts", views.PostViewSet)

qr_admin = admin.site.get_model_admin(QRRedirect)
panel = admin.site.admin_view

urlpatterns = [
    path("", RedirectView.as_view(url=settings.SITE_URL, permanent=True)),
    # Pages from when this backend served the site; see views.legacy_*.
    path("home/", views.legacy_page("/")),
    path("projects/", views.legacy_page("/projects")),
    path("research/", views.legacy_page("/research")),
    path("blog/", views.legacy_page("/blog")),
    re_path(r"^projects/(?P<stub>[-\w]+)/?$", views.legacy_project),
    re_path(r"^blog/(?P<stub>[-\w]+)/?$", views.legacy_post),
    path("healthz/", lambda request: HttpResponse("ok")),
    # Public API (read-only)
    path("api/site/", views.site_settings),
    path("api/", include(router.urls)),
    # QR short links
    path("r/<slug:code>/", qr_views.qr_redirect, name="qr-redirect"),
    # Control panel (only on the admin hosts; see middleware.admin_hosts)
    path("admin/qr/", panel(QRDashboard.as_view(model_admin=qr_admin)), name="qr_dashboard"),
    path("admin/qr/image/<int:redirect_id>/", panel(qr_views.qr_code_image), name="qr-image"),
    path("admin/qr/api/redirects/", qr_api.redirects_list, name="qr-api-list"),
    path("admin/qr/api/redirects/<int:pk>/", qr_api.redirect_detail, name="qr-api-detail"),
    path("admin/qr/api/redirects/<int:pk>/scans/", qr_api.redirect_scans, name="qr-api-scans"),
    path("admin/rebuild/", panel(rebuild_view), name="rebuild"),
    path("admin/", admin.site.urls),
    # Accounts are never made or reset from the web.
    re_path(r"^accounts/(signup|password/reset)/", lambda request, *a: HttpResponseNotFound()),
    path("accounts/", include("allauth.urls")),
]
