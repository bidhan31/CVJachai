from .classify_view import ResumeClassifyAPIView
from .info_view import APIInfoAPIView
from .optimize_view import ResumeOptimizeAPIView
from .auth_views import RegisterView, LoginView, ForgotPasswordView, ResetPasswordView, GoogleLoginView
from .profile_view import ProfileDetailAPIView
from .job_views import JobCreateListView, ApplyJobView, JobApplicationsListView, AnalyzeJobApplicantsView, JobDeleteView, MyJobsView

__all__ = [
    'ResumeClassifyAPIView', 
    'APIInfoAPIView', 
    'ResumeOptimizeAPIView', 
    'RegisterView', 
    'LoginView', 
    'ProfileDetailAPIView',
    'ForgotPasswordView',
    'ResetPasswordView',
    'JobCreateListView',
    'ApplyJobView',
    'JobApplicationsListView',
    'AnalyzeJobApplicantsView',
    'JobDeleteView',
    'MyJobsView',
    'GoogleLoginView'
]
