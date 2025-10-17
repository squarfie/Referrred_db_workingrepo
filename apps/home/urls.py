# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path, include
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    

    #the forms
    path('batch/', views.batch_create_view,name='batch_create_view'),
    # path('generate-accession/', views.generate_accession, name='generate_accession'),
    path("raw-data/<int:id>/", views.raw_data, name="raw_data"),  # edit existing
    path('show/', views.show_data,name='show_data'),
    path('batches/', views.show_batches,name='show_batches'),
    path('edit/<int:id>/', views.edit_data, name='edit_data'),
    path('delete/<int:id>/',views.delete_data,name='delete_data'),
  
    
    #--- done editing -- start
    path('site-add/', views.add_dropdown,name='add_dropdown'),
    path('site-view', views.site_view,name='site_view'),
    path('site-delete/<int:id>/',views.delete_dropdown,name='delete_dropdown'),
    
    #--- done editing --- finish


    path("search/", views.search, name="search"),
    path('clinic-code/', views.get_clinic_code, name='get_clinic_code'),
    path('breakpoints-view/', views.breakpoints_view, name='breakpoints_view'),
    path('breakpoints-delete/<int:id>', views.breakpoints_del, name='breakpoints_del'),
    path('breakpoints-add/', views.add_breakpoints, name='add_breakpoints'), 
    path('breakpoints-edit/<int:pk>/', views.add_breakpoints, name='edit_breakpoints'),  
    path('breakpoints-upload/', views.upload_breakpoints, name='upload_breakpoints'),
    path('breakpoints-deleteAll/', views.delete_all_breakpoints, name='delete_all_breakpoints'),
    path('breakpoints-export/', views.export_breakpoints, name='export_breakpoints'),
    path('test_results-view/', views.abxentry_view, name='abxentry_view'),
    path('specimens/', views.specimen_list, name='specimen_list'),
    path('specimens-add/', views.add_specimen, name='add_specimen'),
    path('specimens-edit/<int:pk>/', views.edit_specimen, name='edit_specimen'),
    path('specimens-delete/<int:pk>/', views.delete_specimen, name='delete_specimen'),
    path('generate_gs/<int:id>/', views.generate_gs, name='generate_gs'),
    path('antibioticentry-export/', views.export_Antibioticentry, name='export_Antibioticentry'),
    path('add_contact/', views.add_contact, name='add_contact'),
    path('delete_contact/<int:id>/', views.delete_contact, name='delete_contact'),
    path('contact_view/', views.contact_view, name='contact_view'),
    path('staff/', views.get_ars_staff_details, name='get_ars_staff_details'),
    path("add-location/", views.add_location, name="add_location"),
    path('upload-location/', views.upload_locations, name='upload_locations'),
    path('view-location/', views.view_locations, name='view_locations'),
    path('delete_cities/', views.delete_cities, name='delete_cities'),
    path('delete_city/<int:id>/', views.delete_city, name='delete_city'),
    path('download_combined_table/', views.download_combined_table, name='download_combined_table'),
    path('generate-pdf/<int:id>/', views.generate_pdf, name='generate_pdf'),
    path("delete_batch/<int:batch_id>/", views.delete_batch, name="delete_batch"),
    path("review_batches/", views.review_batches, name="review_batches"),
    path("clean_batch/<int:batch_id>/", views.clean_batch, name="clean_batch"),
    path('upload-sitecode/', views.upload_sitecode, name='site_upload'),
    path('delete_all_dropdown/', views.delete_all_dropdown, name='delete_all_dropdown'),

    path("copy_to_final/<int:id>/", views.copy_data_to_final, name="copy_data_to_final"),
    path("upload_raw/", views.upload_combined_table, name='upload_combined_table'),
    
    #include all app's urls
    path('upload/', include('apps.wgs_app.urls')),
    path('final/', include('apps.home_final.urls')),


    # path('batch/', views.show_accession, name="show_accession"),
 

    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
    re_path(r'^(?P<template>.*)\.html$', views.pages, name='pages'),

 
    

]
