from django.contrib import admin
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from . import views
from . import qr_views, qr_api

router = DefaultRouter()
router.register(r'blogposts', views.BlogPostViewSet)
router.register(r'projects', views.ProjectViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='home/', permanent=True)),

    path('home/', views.home, name='home'),
    path('projects/', views.ProjectListView.as_view(), name='projects'),
    path('blog/', views.blog, name='blog'),
    path('research/', views.research, name='research'),

    re_path(r'^projects/(?P<stub>[-\w]+)$', views.project_detail_view, name='project-detail'),
    re_path(r'^blog/(?P<stub>[A-Za-z0-9-]+)$', views.blog_post, name='blog-post'),

    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^staticfiles/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),

    path('api/', include(router.urls)),

    # ── QR Code Manager ──────────────────────────────────────────────────────
    path('r/<slug:code>/',                          qr_views.qr_redirect,    name='qr-redirect'),
    path('qr/',                                     qr_views.qr_dashboard,   name='qr-dashboard'),
    path('api/qr/image/<int:redirect_id>/',         qr_views.qr_code_image,  name='qr-image'),
    path('api/qr/redirects/',                       qr_api.redirects_list,   name='qr-api-list'),
    path('api/qr/redirects/<int:pk>/',              qr_api.redirect_detail,  name='qr-api-detail'),
    path('api/qr/redirects/<int:pk>/scans/',        qr_api.redirect_scans,   name='qr-api-scans'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)