from django.urls import path
from . import views
urlpatterns = [

        path("edit_final/<int:id>/", views.edit_final_data, name="edit_final_data"),
        path("show_final_table", views.show_final_table, name="show_final_table"),
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
        

        path("projects/wgs/classification/<int:pk>/",views.wgs_classification_view,name="wgs_classification_view"),  
        path("projects/wgs/classification/update/<str:accession_no>/", views.update_wgs_classification_inline, name="update_wgs_classification_inline"),

        ### add starting here for concordance analysis
        path("concordance_analysis/", views.concordance_analysis_view, name="concordance_analysis"),
        
        path("concordance/batch/generate/", views.concordance_generate_batch, name="concordance_generate_batch"),
        path("concordance/batch/<int:report_id>/", views.concordance_batch_detail, name="concordance_batch_detail"),
        
        path("concordance/accession/generate/", views.concordance_generate_accession, name="concordance_generate_accession"),
        path("concordance/accession/<int:report_id>/", views.concordance_accession_detail, name="concordance_accession_detail"),        
        # path("concordance/accession/<str:accession_no>/",views.concordance_accession_detail_view, name="concordance_accession_detail"),
        
        path("concordance_history/", views.concordance_history_view, name="concordance_history"),
        
        path("concordance_report/<int:report_id>/export/batch/",views.export_concordance_batch_excel,name="export_concordance_batch_excel",),
        path("concordance_report/<int:report_id>/export/accession/",views.export_concordance_accession_excel,name="export_concordance_accession_excel",),
        
        path("concordance_report/<int:report_id>/export_pdf/",views.export_concordance_report_pdf,name="export_concordance_report_pdf",),


]
