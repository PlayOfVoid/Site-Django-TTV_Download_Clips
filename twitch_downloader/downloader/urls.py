from django.urls import path
from . import views

urlpatterns = [
    path('', views.download_clip, name='download_clip'),  # Главная страница
    path('download/<str:filename>/', views.serve_download, name='serve_download'), # URL для отдачи файла
]