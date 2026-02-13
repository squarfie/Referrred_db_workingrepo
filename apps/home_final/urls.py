from django.urls import path
from . import views
urlpatterns = [
        path('upload', views.upload_final_combined_table, name='upload_final_combined_table'),
        path('upload_antibiotic', views.upload_antibiotic_entries, name='upload_antibiotic_entries'),
        path('show', views.show_final_data, name='show_final_data'),
        path('show_abx', views.show_final_antibiotic, name='show_final_antibiotic'),
        path('delete/<int:pk>/', views.delete_final_data, name='delete_final_data'),
        path('delete_abx/<int:pk>/', views.delete_final_antibiotic, name='delete_final_antibiotic'),
        path('del_all', views.delete_all_final_data, name='delete_all_final_data'),
        path('del_abx', views.delete_all_final_antibiotic, name='delete_all_final_antibiotic'),
        path("delete_range", views.delete_finaldata_by_date, name="delete_finaldata_by_date"),
        path("delete_range_abx", views.delete_finalantibiotic_by_date, name="delete_finalantibiotic_by_date"),
        path("edit_final/<int:id>/", views.edit_final_data, name="edit_final_data"),
        path("show_final_table", views.show_final_table, name="show_final_table"),\
        path("final_lab_result/<int:id>/", views.generate_final_batch_pdf, name="generate_final_batch_pdf"),
       
        path('ajax/get-antibiotic-details/', views.get_antibiotic_details, name='get_antibiotic_details'),
        path("ajax/get-antibiotic-name/", views.get_antibiotic_name, name="get_antibiotic_name"),
        path("ajax/filter-antibiotics/", views.ajax_filter_antibiotics, name="ajax_filter_antibiotics"),
        path("get_organism_name/", views.get_organism_name, name="get_organism_name"),
        
        path("download/", views.download_combined_final_table, name="download_combined_final_table"),
        path("ast/", views.final_abxentry_view, name="final_abxentry_view"),
        path("download/abx_entries/", views.export_final_antibiotic_entries, name="export_final_antibiotic_entries"),

        path("recommendation/get-description/", views.get_recommendation_f_description, name="get_recommendation_f_description"),

        path("emerging/list/", views.emerging_list_view, name="emerging_list_view"),
        path("emerging/download/", views.download_emerging_list, name="download_emerging_list"),
        

        path("projects/wgs/classification/<int:pk>/",views.wgs_classification_view,name="wgs_classification_view"),  ######### add this !!!!!
        path("projects/wgs/classification/update/<str:accession_no>/", views.update_wgs_classification_inline, name="update_wgs_classification_inline"),





]
