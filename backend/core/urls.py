"""
URL configuration for Resume Classifier API.
"""

import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.generic import TemplateView
from django.conf import settings as django_settings
from api import views as api_views
from api import admin_views
from api.admin_views import FirstAdminSetupView, DashboardLoginView
from rest_framework_simplejwt.views import TokenRefreshView
import mimetypes
import logging
from urllib.parse import unquote

from django.views.decorators.clickjacking import xframe_options_exempt

logger = logging.getLogger(__name__)

@xframe_options_exempt
def serve_media_file(request, path):
    """Serve media files for download. Preview is handled by rendered text in the frontend."""
    decoded_path = unquote(path)
    
    # Normalize the path and prevent directory traversal attacks
    file_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, decoded_path))
    if not file_path.startswith(os.path.normpath(settings.MEDIA_ROOT)):
        raise Http404("Invalid path")
    
    if not os.path.exists(file_path):
        logger.error(f"Media file not found: requested={path}, decoded={decoded_path}, full_path={file_path}")
        raise Http404("File not found")
    
    is_download = request.GET.get('download') == '1'
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # If downloading a DOCX file, convert to PDF using pure python (fpdf2)
    if is_download and file_ext in ['.docx', '.doc']:
        pdf_path = file_path.rsplit('.', 1)[0] + '.pdf'
        
        if not os.path.exists(pdf_path):
            try:
                import docx
                from fpdf import FPDF
                
                doc = docx.Document(file_path)
                pdf = FPDF()
                pdf.add_page()
                # Use standard font
                pdf.set_font("Helvetica", size=11)
                
                for para in doc.paragraphs:
                    text = para.text.strip()
                    if text:
                        # Replace common unsupported characters
                        text = text.replace('\u2022', '-') # bullet
                        text = text.replace('\u2013', '-') # en dash
                        text = text.replace('\u2014', '-') # em dash
                        text = text.replace('\u2018', "'") # single quote left
                        text = text.replace('\u2019', "'") # single quote right
                        text = text.replace('\u201c', '"') # double quote left
                        text = text.replace('\u201d', '"') # double quote right
                        
                        # Encode to latin-1 and replace unknown chars with ?
                        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 7, clean_text)
                
                pdf.output(pdf_path)
                logger.info(f"Generated PDF with fpdf2: {pdf_path}")
            except Exception as e:
                logger.error(f"fpdf2 conversion failed for {file_path}: {e}")
                pdf_path = None
                
        if pdf_path and os.path.exists(pdf_path):
            file_path = pdf_path
            
    with open(file_path, 'rb') as f:
        data = f.read()
        
    content_type, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(data, content_type=content_type or 'application/octet-stream')
    
    if is_download:
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    else:
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
        
    response['Content-Length'] = len(data)
    
    # Explicit CORS headers for cross-origin fetch
    origin = request.META.get('HTTP_ORIGIN', '')
    allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    if origin in allowed_origins:
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition, Content-Type'
        
    return response

api_patterns = [
    path('auth/signup', api_views.RegisterView.as_view(), name='auth_signup'),
    path('auth/signin', api_views.LoginView.as_view(), name='auth_signin'),
    path('auth/google', api_views.GoogleLoginView.as_view(), name='auth_google'),
    path('auth/otp/request/', api_views.ForgotPasswordView.as_view(), name='otp_request'),
    path('auth/reset-password/', api_views.ResetPasswordView.as_view(), name='reset_password'),
    path('auth/profile', api_views.ProfileDetailAPIView.as_view(), name='auth_profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('classify', api_views.ResumeClassifyAPIView.as_view(), name='resume_classify'),
    path('optimize', api_views.ResumeOptimizeAPIView.as_view(), name='resume_optimize'),
    
    # --- Job Portal Endpoints ---
    path('jobs/', api_views.JobCreateListView.as_view(), name='job_list_create'),
    path('jobs/my/', api_views.MyJobsView.as_view(), name='my_jobs'),
    path('jobs/apply/', api_views.ApplyJobView.as_view(), name='job_apply'),
    path('jobs/<str:job_id>/applications/', api_views.JobApplicationsListView.as_view(), name='job_applications'),
    path('jobs/<str:job_id>/analyze/', api_views.AnalyzeJobApplicantsView.as_view(), name='job_analyze'),
    path('jobs/<str:job_id>/delete/', api_views.JobDeleteView.as_view(), name='job_delete'),
    # ----------------------------
    path('media/<path:path>', serve_media_file, name='media_serve'),
    path('', api_views.APIInfoAPIView.as_view(), name='api_info'),
    # --- Admin / Master Control Panel Endpoints ---
    path('master/status', admin_views.AdminStatusView.as_view(), name='admin_status'),
    path('master/toggle-server', admin_views.AdminToggleServerView.as_view(), name='admin_toggle'),
    path('master/setup', FirstAdminSetupView.as_view(), name='admin_setup'),
    path('master/login', DashboardLoginView.as_view(), name='dashboard_login'),
    path('master/users', admin_views.AdminUsersView.as_view(), name='admin_users'),
    path('master/users/<int:user_id>', admin_views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('master/jobs', admin_views.AdminJobsView.as_view(), name='admin_jobs'),
    path('master/jobs/<str:job_id>', admin_views.AdminJobDetailView.as_view(), name='admin_job_detail'),
    path('master/applications', admin_views.AdminApplicationsView.as_view(), name='admin_applications'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', TemplateView.as_view(
        template_name='index.html',
        extra_context={'STATIC_PUBLIC_URL': django_settings.STATIC_PUBLIC_URL}
    ), name='dashboard'),
    path('media/<path:path>', serve_media_file, name='media_serve_root'),
    
    # Include API patterns both with and without 'api/' prefix to support
    # both local development and cPanel Phusion Passenger (which strips /api)
    path('api/', include(api_patterns)),
    path('', include(api_patterns)),
]
