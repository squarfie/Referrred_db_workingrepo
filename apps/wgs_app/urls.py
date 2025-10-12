
# apps/wgs_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('data_center/', views.upload_wgs_view, name='upload_wgs_view'),
    path('show/wgs', views.show_wgs_projects, name='show_wgs_projects'),
    path('delete/wgs/<int:pk>', views.delete_wgs, name='delete_wgs'),

    path('referred', views.upload_combined_table, name='upload_combined_table'),
    
    path('fastq', views.upload_fastq, name='upload_fastq'),
    path('show/fastq', views.show_fastq, name='show_fastq'),
    path('delete/fastq/<int:pk>/', views.delete_fastq, name='delete_fastq'),
    
    path('gambit', views.upload_gambit, name='upload_gambit'),
    path('show/gambit/', views.show_gambit, name='show_gambit'),
    path('delete/gambit/<int:pk>/', views.delete_gambit, name='delete_gambit'),
    
    path('mlst', views.upload_mlst, name='upload_mlst'),
    path('show/mlst/', views.show_mlst, name='show_mlst'),
    path('delete/mlst/<int:pk>/', views.delete_mlst, name='delete_mlst'),

    path('checkm2', views.upload_checkm2, name='upload_checkm2'),
    path('show/checkm2', views.show_checkm2, name='show_checkm2'),
    path('delete/checkm2/<int:pk>/', views.delete_checkm2, name='delete_checkm2'),

    path('assembly', views.upload_assembly, name='upload_assembly'),
    path('show/assembly', views.show_assembly, name='show_assembly'),
    path('delete/assembly/<int:pk>/', views.delete_assembly, name='delete_assembly'),


    path('amrfinder', views.upload_amrfinder, name='upload_amrfinder'),
    path('show/amrfinder', views.show_amrfinder, name='show_amrfinder'),
    path('delete/amrfinder/<int:pk>/', views.delete_amrfinder, name='delete_amrfinder'),


    path('del_all/gambit/', views.delete_all_gambit, name='delete_all_gambit'),
    path('del_all/fastq/', views.delete_all_fastq, name='delete_all_fastq'),
    path('del_all/mlst/', views.delete_all_mlst, name='delete_all_mlst'),
    path('del_all/checkm2/', views.delete_all_checkm2, name='delete_all_checkm2'),
    path('del_all/assembly/', views.delete_all_assembly, name='delete_all_assembly'),
    path('del_all/amrfinder/', views.delete_all_amrfinder, name='delete_all_amrfinder'),

    path('wgs/data-overview', views.view_wgs_overview, name='view_wgs_overview'),
    path('wgs/download-wgs/', views.download_all_wgs_data, name='download_all_wgs_data'),
    path('wgs/download_matched/', views.download_matched_wgs_data, name='download_matched_wgs_data'),

    path("amrfinder/delete_by_date/", views.delete_amrfinder_by_date, name="delete_amrfinder_by_date"),
    path("fastq/delete_by_date/", views.delete_fastq_by_date, name="delete_fastq_by_date"),

    # path('overview/', views.view_data_overview, name='view_data_overview'),

]
