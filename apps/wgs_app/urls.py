
# apps/wgs_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('data_center/', views.upload_wgs_view, name='upload_wgs_view'),
    path('show/wgs', views.show_wgs_projects, name='show_wgs_projects'),
    path('delete/wgs/<int:pk>', views.delete_wgs, name='delete_wgs'),
    
    
    path("sample-info", views.upload_sample_information, name="upload_sample_information"),
    path("sample-info/relink-matches/", views.relink_sample_information_matches, name="relink_sample_information_matches"),
    path("show/sample-info/", views.show_sample_information, name="show_sample_information"),
    path("delete/sample-info/<int:pk>/", views.delete_sample_information, name="delete_sample_information"),
    path("del_all/sample-info/", views.delete_all_sample_information, name="delete_all_sample_information"),
    path("delete_by_date/sample-info", views.delete_sample_information_by_date, name="delete_sample_information_by_date"),

    path("bactscout", views.upload_bactscout, name="upload_bactscout"),
    path("show/bactscout/", views.show_bactscout, name="show_bactscout"),
    path("delete/bactscout/<int:pk>/", views.delete_bactscout, name="delete_bactscout"),
    path("del_all/bactscout/", views.delete_all_bactscout, name="delete_all_bactscout"),
    path("delete_by_date/bactscout/", views.delete_bactscout_by_date, name="delete_bactscout_by_date"),


    path("gtdbtk", views.upload_gtdbtk, name="upload_gtdbtk"),
    path("show/gtdbtk/", views.show_gtdbtk, name="show_gtdbtk"),
    path("delete/gtdbtk/<int:pk>/", views.delete_gtdbtk, name="delete_gtdbtk"),
    path("del-all/gtdbtk/", views.delete_all_gtdbtk, name="delete_all_gtdbtk"),
    path("delete_by_date/gtdbtk/", views.delete_gtdbtk_by_date, name="delete_gtdbtk_by_date"),


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
    path('del_all/mlst/', views.delete_all_mlst, name='delete_all_mlst'),
    path('del_all/checkm2/', views.delete_all_checkm2, name='delete_all_checkm2'),
    path('del_all/assembly/', views.delete_all_assembly, name='delete_all_assembly'),
    path('del_all/amrfinder/', views.delete_all_amrfinder, name='delete_all_amrfinder'),
    


    path('wgs/data-overview', views.view_wgs_overview, name='view_wgs_overview'),
    path('wgs/download_matched/', views.download_matched_wgs_data, name='download_matched_wgs_data'),
    path("wgs/export/<str:pipeline_key>/", views.export_builtin_wgs_pipeline, name="export_builtin_wgs_pipeline"),
    path("wgs/pipelines/", views.custom_pipeline_list, name="custom_pipeline_list"),
    path("wgs/pipelines/new/", views.custom_pipeline_create, name="custom_pipeline_create"),
    path("wgs/pipelines/<slug:slug>/edit/", views.custom_pipeline_edit, name="custom_pipeline_edit"),
    path("wgs/pipelines/<slug:slug>/deactivate/", views.custom_pipeline_deactivate, name="custom_pipeline_deactivate"),
    path("wgs/pipelines/<slug:slug>/delete/", views.custom_pipeline_delete, name="custom_pipeline_delete"),
    path("wgs/pipelines/<slug:slug>/fields/", views.custom_pipeline_fields, name="custom_pipeline_fields"),
    path("wgs/pipelines/<slug:slug>/fields/<int:field_id>/edit/", views.custom_pipeline_field_edit, name="custom_pipeline_field_edit"),
    path("wgs/pipelines/<slug:slug>/fields/<int:field_id>/delete/", views.custom_pipeline_field_delete, name="custom_pipeline_field_delete"),
    path("wgs/pipelines/<slug:slug>/upload/", views.custom_pipeline_upload, name="custom_pipeline_upload"),
    path("wgs/pipelines/<slug:slug>/records/", views.custom_pipeline_records, name="custom_pipeline_records"),
    path("wgs/pipelines/<slug:slug>/export/", views.custom_pipeline_export, name="custom_pipeline_export"),

    
    path("delete_by_date/gambit", views.delete_gambit_by_date, name="delete_gambit_by_date"),
    path("delete_by_date/mlst", views.delete_mlst_by_date, name="delete_mlst_by_date"),
    path("delete_by_date/checkm2", views.delete_checkm2_by_date, name="delete_checkm2_by_date"),
    path("delete_by_date/assembly", views.delete_assembly_by_date, name="delete_assembly_by_date"),
    path("delete_by_date/amrfinder", views.delete_amrfinder_by_date, name="delete_amrfinder_by_date"),
  

    path('get-details/<str:accession>/', views.get_wgs_details, name='get_wgs_details'),
    path('final/upload/', views.upload_final_data, name='upload_final_data'),
    path("projects/", views.projects_page, name="projects_page"),

    # path('upload/demogs', views.upload_final_combined_table, name='upload_final_combined_table'),
    path('upload/demogs', views.upload_referred_table, name='upload_referred_table'),
    path("upload/final_antibiotics", views.upload_final_antibiotics, name="upload_final_antibiotics"),
    path('final/show', views.show_final_data, name='show_final_data'),
    path('final/show_abx', views.show_final_antibiotic, name='show_final_antibiotic'),
    path('final/export-final/', views.export_Final_Antibioticentry, name='export_Final_Antibioticentry'),
    path('final/delete/<int:pk>/', views.delete_final_data, name='delete_final_data'),
    path('final/del-abx/<int:pk>/', views.delete_final_antibiotic, name='delete_final_antibiotic'),
    path('final/del_all', views.delete_all_final_data, name='delete_all_final_data'),
    path('final/del_abx_all', views.delete_all_final_antibiotic, name='delete_all_final_antibiotic'),
    path("final/delete_range", views.delete_finaldata_by_date, name="delete_finaldata_by_date"),
    path("final/delete_abx_date", views.delete_finalantibiotic_by_date, name="delete_finalantibiotic_by_date"),
    
    path("batch-generator", views.create_batch_from_referred, name="create_batch_from_referred"),
    path('auto-batch', views.create_batch_from_referred, name="generate_batches_from_referred"),

    path('raw/export-raw', views.export_raw_Antibioticentry, name="export_raw_Antibioticentry"),
    path('raw/del_abx_date', views.delete_rawantibiotic_by_date, name="delete_rawantibiotic_by_date"),
    path('raw/del_abx_all', views.delete_all_raw_antibiotic, name="delete_all_raw_antibiotic"),
    path('raw/del-abx/<int:pk>/', views.delete_raw_antibiotic, name='delete_raw_antibiotic'),
    path('raw/show_abx', views.show_raw_antibiotic, name='show_raw_antibiotic'),
    path("upload/raw_antibiotics", views.upload_raw_antibiotics, name="upload_raw_antibiotics"),
    
    path("raw/delete_range", views.delete_referreddata_by_date, name="delete_referreddata_by_date"),
    path("raw/delete_all", views.delete_all_referred_data, name="delete_all_referred_data"),
    path('raw/delete/<int:pk>/', views.delete_referred_data, name='delete_referred_data'),
    path('raw/show', views.show_referred_data, name='show_referred_data'),
    # path('overview/', views.view_data_overview, name='view_data_overview'),

]
