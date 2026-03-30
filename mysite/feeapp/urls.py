from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
urlpatterns = [

    path('', views.role_select_view, name='role_select'),
    
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('challan/download/', views.download_challan, name='download_challan'),
    path('challan/view/', views.view_challan, name='view_challan'),
    path('api/search-challans-by-cnic/', views.search_challans_by_cnic, name='search_challans_by_cnic'),
    path('api/view-challan-html/<str:challan_number>/', views.view_challan_html, name='view_challan_html'),
    path('api/get-my-challans/', views.get_my_challans, name='get_my_challans'),
    path('preview/', views.challan_preview, name='challan_preview'),
    path('api/get-active-logo/', views.get_active_logo_api, name='get_active_logo_api'),
    
    path('clerk/login/', views.clerk_login, name='clerk_login'),
    path('clerk/dashboard/', views.clerk_dashboard, name='clerk_dashboard'), 

    path('api/clerk/login/', views.clerk_login_api, name='clerk_login_api'),
    path('api/clerk/forgot-password/', views.clerk_forgot_password_api, name='clerk_forgot_password_api'),
    path('api/clerk/resend-otp/', views.clerk_resend_otp_api, name='clerk_resend_otp_api'),
    path('api/clerk/verify-otp/', views.clerk_verify_otp_api, name='clerk_verify_otp_api'),
    path('api/clerk/reset-password/', views.clerk_reset_password_api, name='clerk_reset_password_api'),
    
    path('logout/', views.logout_confirmation, name='logout_confirmation'),
    path('logout_action/', views.logout_action, name='logout_action'),
    path('api/save-auto-logout-time/', views.save_auto_logout_time, name='save_auto_logout_time'),
    path('challan-form/', views.challan_form, name='challan_form'),
   
    path('api/get-programs/', views.get_programs, name='get_programs'),
    path('api/get-program-details/<int:program_id>/', views.get_program_details, name='get_program_details'),
    path('api/save-session/', views.save_session, name='save_session'),
    path('api/get-bs-disciplines/<str:category>/', views.get_bs_disciplines, name='get_bs_disciplines'),
    path('api/add-fee-head/', views.add_fee_head, name='add_fee_head'),
    path('api/generate-challan/', views.generate_challan, name='generate_challan'),
    path('api/get-students/', views.get_students, name='get_students'),
    path('api/get-challan/<str:challan_number>/', views.get_challan, name='get_challan'),
    path('api/check-challan-saved/<str:challan_number>/', views.check_challan_saved, name='check_challan_saved'),
    path('api/download-challan-pdf/<str:challan_number>/', views.download_challan_pdf, name='download_challan_pdf'),
    path('api/get-active-logo/', views.get_active_logo_api, name='get_active_logo_api'),
    path('api/download-challan/', views.download_challan_api, name='download_challan_api'),
  
    path('manage-installment/', views.manage_installment, name='manage_installment'),
    path('save-installment/', views.save_installment, name='save_installment'), 
    
    path('search_challan/', views.search_challan, name='search_challan'),
    path('api/search-challans-by-cnic/', views.search_challans_by_cnic, name='search_challans_by_cnic'),
    path('api/view-challan-html/<str:challan_number>/', views.view_challan_html, name='view_challan_html'),
    
    path('update_challan/', views.update_challan, name='update_challan'), 
    path('api/get_challan/<str:challan_number>/', views.get_challan_data, name='get_challan_data'),
    path('api/update-challan/', views.update_challan_api, name='update_challan_api'),
    path('challan-summary/', views.challan_summary, name='challan_summary'),
    path('fund-report/', views.fund_report_api, name='fund_report_api'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)