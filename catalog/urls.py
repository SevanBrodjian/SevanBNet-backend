from django.urls import path, re_path
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('projects/', views.ProjectListView.as_view(), name='projects'),
    re_path(r'^projects/(?P<stub>[-\w]+)$', views.project_detail_view, name='project-detail'),
]