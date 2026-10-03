from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from . import qr_api, qr_views, views

router = DefaultRouter()
router.register(r"blogposts", views.BlogPostViewSet)
router.register(r"projects", views.ProjectViewSet)
router.register(r"publications", views.PublicationViewSet)

urlpatterns = [
    path("", RedirectView.as_view(url=settings.SITE_URL)),
    path("healthz/", lambda request: HttpResponse("ok")),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    # QR code manager
    path("r/<slug:code>/", qr_views.qr_redirect, name="qr-redirect"),
    path("qr/", qr_views.qr_dashboard, name="qr-dashboard"),
    path("api/qr/image/<int:redirect_id>/", qr_views.qr_code_image, name="qr-image"),
    path("api/qr/redirects/", qr_api.redirects_list, name="qr-api-list"),
    path("api/qr/redirects/<int:pk>/", qr_api.redirect_detail, name="qr-api-detail"),
    path("api/qr/redirects/<int:pk>/scans/", qr_api.redirect_scans, name="qr-api-scans"),
]
