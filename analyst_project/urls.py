from django.contrib import admin
from django.urls import path
from analyzer import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.upload_and_analyze, name='upload_and_analyze'),
    path('download-report/', views.download_pdf_report, name='download_pdf_report'),
]