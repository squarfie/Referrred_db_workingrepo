
# apps/wgs_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_wgs_view, name='upload_wgs_view'),
    path('wgs/', views.show_wgs_projects, name='show_wgs_projects'),
    path('wgs/delete/<int:pk>', views.delete_wgs, name='delete_wgs'),
    
    path('fastq/upload', views.upload_fastq, name='upload_fastq'),
    path('fastq/show/', views.show_fastq, name='show_fastq'),
    path('fastq/delete/<int:pk>/', views.delete_fastq, name='delete_fastq'),
    
    path('gambit/upload', views.upload_gambit, name='upload_gambit'),
    path('gambit/show/', views.show_gambit, name='show_gambit'),
    path('gambit/delete/<int:pk>/', views.delete_gambit, name='delete_gambit'),
    
    path('mlst/upload', views.upload_mlst, name='upload_mlst'),
    path('mlst/show/', views.show_mlst, name='show_mlst'),
    path('mlst/delete/<int:pk>/', views.delete_mlst, name='delete_mlst'),

    path('checkm2/upload', views.upload_checkm2, name='upload_checkm2'),
    path('checkm2/show/', views.show_checkm2, name='show_checkm2'),
    path('checkm2/delete/<int:pk>/', views.delete_checkm2, name='delete_checkm2'),

    path('assembly/upload', views.upload_assembly, name='upload_assembly'),
    path('assembly/show/', views.show_assembly, name='show_assembly'),
    path('assembly/delete/<int:pk>/', views.delete_assembly, name='delete_assembly'),


    path('amrfinder/upload', views.upload_amrfinder, name='upload_amrfinder'),
    path('amrfinder/show/', views.show_amrfinder, name='show_amrfinder'),
    path('amrfinder/delete/<int:pk>/', views.delete_amrfinder, name='delete_amrfinder'),


    path('del_all/gambit/', views.delete_all_gambit, name='delete_all_gambit'),
    path('del_all/fastq/', views.delete_all_fastq, name='delete_all_fastq'),
    path('del_all/mlst/', views.delete_all_mlst, name='delete_all_mlst'),
    path('del_all/checkm2/', views.delete_all_checkm2, name='delete_all_checkm2'),
    path('del_all/assembly/', views.delete_all_assembly, name='delete_all_assembly'),
    path('del_all/amrfinder/', views.delete_all_amrfinder, name='delete_all_amrfinder'),
]
