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
        path("edit_final", views.edit_final_data, name="edit_final_data"),

]
