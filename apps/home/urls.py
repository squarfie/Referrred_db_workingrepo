# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path, include
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
     #include all app's urls
    path('upload/', include('apps.wgs_app.urls')),
    path('final/', include('apps.home_final.urls')),
    path("settings/", views.settings_page, name="settings_page"),


    #the forms
    path('batch/', views.batch_create_view,name='batch_create_view'),
    path('batch-edit/<int:pk>/', views.batch_edit_view, name='batch_edit_view'),
    # path('upload/', views.upload_referred_view, name="upload_referred_view"),

    # path('generate-accession/', views.generate_accession, name='generate_accession'),
    path("raw-data/<int:id>/", views.raw_data, name="raw_data"),  # edit existing
    path('show/', views.show_data,name='show_data'),

    path('batches/', views.show_batches,name='show_batches'),
    path('edit/<int:id>/', views.edit_data, name='edit_data'),
    path('delete/<int:id>/',views.delete_data,name='delete_data'),
  
    path('site-add/', views.add_dropdown,name='add_dropdown'),
    path('site-view', views.site_view,name='site_view'),
    path('site-delete/<int:id>/',views.delete_dropdown,name='delete_dropdown'),
    path('upload-sitecode/', views.upload_sitecode, name='site_upload'),
    path("sitecode/edit/<int:pk>/", views.edit_sitecode, name="edit_sitecode"),
    
    path("search/", views.search, name="search"),

    path('clinic-code/', views.get_clinic_code, name='get_clinic_code'),
    path('breakpoints-view/', views.breakpoints_view, name='breakpoints_view'),
    path('breakpoints-delete/<int:id>', views.breakpoints_del, name='breakpoints_del'),
    path('breakpoints-add/', views.add_breakpoints, name='add_breakpoints'), 
    path('breakpoints-edit/<int:pk>/', views.edit_breakpoints, name='edit_breakpoints'),  
    path('breakpoints-upload/', views.upload_breakpoints, name='upload_breakpoints'),
    path('breakpoints-delete-all/', views.delete_all_breakpoints, name='delete_all_breakpoints'),
    path('breakpoints-export/', views.export_breakpoints, name='export_breakpoints'),
    path('ajax/get-antibiotic-details/', views.get_antibiotic_details, name='get_antibiotic_details'),



    path('antibiotics-view/', views.antibiotics_view, name='antibiotics_view'),
    path('antibiotics-delete/<int:id>', views.antibiotics_del, name='antibiotics_del'),
    path('antibiotics-add/', views.add_antibiotics, name='add_antibiotics'), 
    path('antibiotics-edit/<int:pk>/', views.edit_antibiotics, name='edit_antibiotics'),  
    path('antibiotics-upload/', views.upload_antibiotics, name='upload_antibiotics'),
    path('antibiotics-delete-all/', views.delete_all_antibiotics, name='delete_all_antibiotics'),
    path('antibiotics-export/', views.export_antibiotics, name='export_antibiotics'),

    path('organism-add/', views.add_organism, name='add_organism'),
    path('organism-view/', views.view_organism, name='view_organism'),
    path('organism-edit/<int:pk>/', views.edit_organism, name='edit_organism'),  
    path('organism-delete/<int:id>', views.del_organism, name='del_organism'),
    path('organism-delete-all/', views.del_all_organism, name='del_all_organism'),
    path('organism-upload/', views.upload_organisms, name='upload_organisms'),
    path('organism-export/', views.export_organisms, name='export_organisms'),
    path("get_organism_name/", views.get_organism_name, name="get_organism_name"),



    path('test_results-view/', views.abxentry_view, name='abxentry_view'),
    path('specimens/', views.specimen_list, name='specimen_list'),
    path('specimens-add/', views.add_specimen, name='add_specimen'),
    path('specimens-edit/<int:pk>/', views.edit_specimen, name='edit_specimen'),
    path('specimens-delete/<int:pk>/', views.delete_specimen, name='delete_specimen'),
    path('specimens-upload/', views.upload_specimen_code, name='upload_specimen_code'),
    path('specimens-delete-all/', views.delete_all_specimens, name='delete_all_specimens'),

    # path('generate_gs/<int:id>/', views.generate_gs, name='generate_gs'),
    path('antibioticentry-export/', views.export_Antibioticentry, name='export_Antibioticentry'),
    path('add_contact/', views.add_contact, name='add_contact'),
    path('delete_contact/<int:id>/', views.delete_contact, name='delete_contact'),
    path('contact_view/', views.contact_view, name='contact_view'),
    path('staff/', views.get_ars_staff_details, name='get_ars_staff_details'),
    # path("add-location/", views.add_location, name="add_location"),
    # path('upload-location/', views.upload_locations, name='upload_locations'),
    # path('view-location/', views.view_locations, name='view_locations'),
    # path('delete_cities/', views.delete_cities, name='delete_cities'),
    # path('delete_city/<int:id>/', views.delete_city, name='delete_city'),
    path('download_combined_table/', views.download_combined_table, name='download_combined_table'),
    
    path('lab_result/<int:id>/', views.generate_pdf, name='generate_pdf'),
    path('lab_result_batch/<int:id>/', views.generate_batch_pdf, name='generate_batch_pdf'),
    
    path("delete_batch/<int:batch_id>/", views.delete_batch, name="delete_batch"),
    path("delete_record/<int:id>/", views.delete_record_in_batch, name="delete_record_in_batch"),
    path("review_batches/", views.review_batches, name="review_batches"),
    path("clean_batch/<int:batch_id>/", views.clean_batch, name="clean_batch"),

    path('delete_all_dropdown/', views.delete_all_dropdown, name='delete_all_dropdown'),
    
    path("copy_to_final/<int:id>/", views.copy_data_to_final, name="copy_data_to_final"),
    path("undo_copy/<int:id>/", views.undo_copy_to_final, name="undo_copy_to_final"),
    path("batch/<int:batch_id>/copy-to-final/", views.copy_batch_to_final, name="copy_batch_to_final"),
    path("batch/<int:batch_id>/undo-copy-to-final/",views.undo_copy_batch_to_final,name="undo_copy_batch_to_final"),


    
    path("upload_referred/", views.upload_combined_table, name='upload_combined_table'),
    path("field-mapper-tool/", views.field_mapper_tool, name="field_mapper_tool"),
    path("field-mapper/generate-mapped-excel/", views.generate_mapped_excel, name="generate_mapped_excel"),
    path("field-mapper/clear-mappings/", views.clear_mappings, name="clear_mappings"),
    path("field-mapper/mapping-summary/",views.download_mapping_summary,name="download_mapping_summary"),
    path("field-mapper/update-mapping/",views.update_field_mapping,name="update_field_mapping",),

    path("ajax/get-antibiotic-name/", views.get_antibiotic_name, name="get_antibiotic_name"),
    path("ajax/filter-antibiotics/", views.ajax_filter_antibiotics, name="ajax_filter_antibiotics"),

    # path('batch/', views.show_accession, name="show_accession"),
    path("Emerging/Criteria/View", views.view_eme_age, name="view_eme_age"),
    path("Emerging/Criteria/Add", views.add_emerging_age, name="add_emerging_age"),
    path("Emerging/Criteria/Edit", views.edit_eme_age, name="edit_eme_age"),

    path("phenotype-pre/add/", views.add_phenotype_pre, name="add_phenotype_pre"),
    path("phenotype-pre/upload/", views.upload_phenotype_pre, name="upload_phenotype_pre"),
    path("phenotype-pre/delete/<int:pk>/", views.delete_phenotype_pre, name="delete_phenotype_pre"),
    path("phenotype-pre/delete-all/", views.delete_all_phenotype_pre, name="delete_all_phenotype_pre"),
    path("phenotype-pre/edit/<int:pk>", views.edit_phenotype_pre, name="edit_phenotype_pre"),
    path("phenotype-pre/view/", views.view_phenotype_pre, name="view_phenotype_pre"),
    path("phenotype-pre/update/<int:pk>", views.update_phenotype_pre, name="update_phenotype_pre"),
   
    path("phenotype/post/view/",views.view_phenotype_post,name="view_phenotype_post"),
    path("add-phenotype-post/", views.add_phenotype_post, name="add_phenotype_post"),
    path("phenotype/post/upload/",views.upload_phenotype_post,name="upload_phenotype_post"),
    path("phenotype/post/edit/<int:pk>/",views.edit_phenotype_post,name="edit_phenotype_post"),
    path("phenotype/post/update/<int:pk>/",views.update_phenotype_post,name="update_phenotype_post"),
    path("phenotype/post/delete/<int:pk>/",views.delete_phenotype_post,name="delete_phenotype_post"),
    path("recommendation/add/",views.add_recommendation_item,name="add_recommendation_item"),
    path("recommendation/upload/",views.upload_recommendation_items,name="upload_recommendation_items"),
    path("recommendation/view/",views.view_recommendation_items,name="view_recommendation_items"),
    path("recommendation/edit/<int:pk>/", views.edit_recommendation_item, name="edit_recommendation_item"),
    path("recommendation/delete/<int:pk>/", views.delete_recommendation_item, name="delete_recommendation_item"),

    path("recommendation/get-description/", views.get_recommendation_description, name="get_recommendation_description"),
    path("projects/wgs/classification/<str:accession_no>/", views.wgs_classification_view, name="wgs_classification_view"),
    path("projects/wgs/classification/update/<str:accession_no>/", views.update_wgs_classification_inline, name="update_wgs_classification_inline"),

    path("tat/<int:batch_id>/", views.tat_monitoring_view, name="tat_monitoring_view"),
    path("tat/config/", views.add_tat_step_config, name="add_tat_step_config"),
    path("tat/config/edit/<int:pk>/", views.edit_tat_step_config, name="edit_tat_step_config"),
    path("tat/config/list/", views.tat_step_config_list, name="tat_step_config_list"),
    path("tat/upload/", views.upload_tat_step_config, name="upload_tat_step_config"),
    path("tat/delete-all/", views.delete_all_tat_process, name="delete_all_tat_process"),
    path("export/tat-report/", views.export_tat_excel, name="export_tat_excel"),
    path("tat/review/", views.tat_review_view, name="tat_review_view"),
    path("tat/analysis/", views.tat_analysis, name="tat_analysis"),
    path("settings/non-working/add/", views.add_non_working_day, name="add_non_working_day"),
    path("settings/non-working/delete/<int:pk>/", views.delete_non_working_day, name="delete_non_working_day"),
    path("batches/delete-all/",views.delete_all_batches,name="delete_all_batches"),
    path("batches/delete-all/",views.delete_blank_batches,name="delete_blank_batches"),
   





    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
    re_path(r'^(?P<template>.*)\.html$', views.pages, name='pages'),

 
    

]
