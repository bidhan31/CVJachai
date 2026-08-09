"""
Admin-only API views for the Master Control Dashboard.
All endpoints here require the requesting user to be is_staff=True.
"""
import os
import logging
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Job, Application, ServerConfig
from engine.groq import groq_base

logger = logging.getLogger(__name__)


class FirstAdminSetupView(APIView):
    """
    GET /api/master/setup?secret=SECRET_KEY&email=your@email.com
    Creates or updates a staff user and sets password to 'admin'.
    Protected by SETUP_SECRET in .env.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        secret = request.query_params.get('secret', '')
        email  = request.query_params.get('email', '').strip()
        expected_secret = os.getenv('SETUP_SECRET', '')

        if not expected_secret:
            return Response({"error": "SETUP_SECRET not set in .env."}, status=500)
        if secret != expected_secret:
            return Response({"error": "Invalid secret key."}, status=403)
        if not email:
            return Response({"error": "Provide ?email=your@gmail.com"}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email}
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password('admin')   # default password — change after first login
        user.save()

        logger.warning(f"[SETUP] Staff account set for {email}")

        return Response({
            "success": True,
            "message": f"✅ Staff account ready for {email}.",
            "login_url": "/api/dashboard/",
            "email": email,
            "password": "admin",
            "note": "Log in at /api/dashboard/ with email + password 'admin'."
        }, status=200)


class DashboardLoginView(APIView):
    """
    POST /api/master/login
    Body: { "email": "...", "password": "..." }
    Returns JWT tokens for staff users only.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get('email', '').strip()
        password = request.data.get('password', '').strip()

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=400)

        # Look up user by email
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or password."}, status=401)

        # Authenticate using Django's backend (checks hashed password)
        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            return Response({"error": "Invalid email or password."}, status=401)

        if not user.is_staff:
            return Response({"error": "Staff access required. Contact the administrator."}, status=403)

        # Issue JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email":     user.email,
                "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
                "is_staff":  user.is_staff,
            }
        }, status=200)


class AdminStatusView(APIView):
    """
    GET /api/admin/status
    Returns live server status, counts, and Groq engine state.
    Staff-only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        config = ServerConfig.get_config()

        # Groq health check
        groq_status = "unavailable"
        groq_model = "—"
        if groq_base.available:
            groq_status = "operational"
            groq_model = groq_base.ranker_model

        # Live counts
        total_users = User.objects.count()
        total_jobs = Job.objects.count()
        active_jobs = Job.objects.filter(is_active=True).count()
        total_applications = Application.objects.count()
        analyzed_applications = Application.objects.exclude(match_score__isnull=True).count()

        return Response({
            "api_enabled": config.api_enabled,
            "maintenance_message": config.maintenance_message,
            "last_toggled": config.updated_at,
            "groq": {
                "status": groq_status,
                "model": groq_model,
                "vision_model": groq_base.vision_model if groq_base.available else "—",
            },
            "stats": {
                "total_users": total_users,
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_applications": total_applications,
                "analyzed_applications": analyzed_applications,
            }
        }, status=status.HTTP_200_OK)


class AdminToggleServerView(APIView):
    """
    POST /api/admin/toggle-server
    Body: { "api_enabled": true/false, "maintenance_message": "optional" }
    Flips the API maintenance mode flag. Staff-only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        config = ServerConfig.get_config()

        api_enabled = request.data.get('api_enabled')
        if api_enabled is None:
            # If not provided, just flip it
            api_enabled = not config.api_enabled

        config.api_enabled = bool(api_enabled)

        msg = request.data.get('maintenance_message', '').strip()
        if msg:
            config.maintenance_message = msg

        config.save()

        logger.warning(
            f"[MASTER CONTROL] API {'ENABLED' if config.api_enabled else 'DISABLED'} "
            f"by {request.user.email}"
        )

        return Response({
            "success": True,
            "api_enabled": config.api_enabled,
            "message": f"API is now {'ONLINE' if config.api_enabled else 'IN MAINTENANCE MODE'}.",
            "toggled_by": request.user.email,
            "at": config.updated_at,
        }, status=status.HTTP_200_OK)


class AdminUsersView(APIView):
    """
    GET /api/admin/users  — list all users
    POST /api/admin/users — create or update staff user
    Staff-only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        data = []
        for u in users:
            data.append({
                "id": u.id,
                "email": u.email,
                "full_name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "is_staff": u.is_staff,
                "is_active": u.is_active,
                "date_joined": u.date_joined,
                "last_login": u.last_login,
                "job_count": u.jobs_created.count(),
            })
        return Response({"users": data, "total": len(data)}, status=status.HTTP_200_OK)

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({"error": "Provide an email address."}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email}
        )
        user.is_staff = True
        user.is_superuser = True
        # Set default password
        user.set_password('admin')
        user.save()

        action = "created" if created else "updated to"
        logger.warning(f"[DASHBOARD] Staff account {action} for {email} by {request.user.email}")

        return Response({
            "success": True,
            "message": f"Staff account ready for {email} (default password 'admin').",
            "email": email
        }, status=status.HTTP_201_CREATED)



class AdminUserDetailView(APIView):
    """
    DELETE /api/admin/users/<id>  — delete a user
    PATCH  /api/admin/users/<id>  — toggle is_staff / is_active
    Staff-only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, user_id):
        if user_id == request.user.id:
            return Response({"error": "You cannot delete yourself."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
            email = user.email
            user.delete()
            return Response({"success": True, "message": f"User '{email}' deleted."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, user_id):
        if user_id == request.user.id:
            return Response({"error": "You cannot modify yourself here."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
            if 'is_staff' in request.data:
                user.is_staff = bool(request.data['is_staff'])
            if 'is_active' in request.data:
                user.is_active = bool(request.data['is_active'])
            user.save()
            return Response({
                "success": True,
                "id": user.id,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class AdminJobsView(APIView):
    """
    GET /api/admin/jobs — all jobs in the system
    Staff-only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        jobs = Job.objects.all().select_related('created_by').order_by('-created_at')
        data = []
        for j in jobs:
            data.append({
                "id": j.id,
                "title": j.title,
                "company_name": j.company_name,
                "location": j.location,
                "is_active": j.is_active,
                "created_by_email": j.created_by.email,
                "created_at": j.created_at,
                "application_count": j.applications.count(),
            })
        return Response({"jobs": data, "total": len(data)}, status=status.HTTP_200_OK)


class AdminJobDetailView(APIView):
    """
    DELETE /api/admin/jobs/<id>  — force-delete any job
    PATCH  /api/admin/jobs/<id>  — toggle is_active
    Staff-only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            title = job.title
            job.delete()
            return Response({"success": True, "message": f"Job '{title}' deleted."}, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            if 'is_active' in request.data:
                job.is_active = bool(request.data['is_active'])
                job.save()
            return Response({
                "success": True,
                "id": job.id,
                "title": job.title,
                "is_active": job.is_active,
            }, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)


class AdminApplicationsView(APIView):
    """
    GET /api/admin/applications — all applications across all jobs
    Staff-only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        apps = Application.objects.all().select_related('job').order_by('-applied_at')
        data = []
        for a in apps:
            data.append({
                "id": a.id,
                "candidate_name": a.candidate_name,
                "candidate_email": a.candidate_email,
                "job_title": a.job.title,
                "job_id": a.job.id,
                "applied_at": a.applied_at,
                "match_score": a.match_score,
                "match_percentage": f"{round(a.match_score * 100, 1)}%" if a.match_score else "Not analyzed",
                "verdict": a.analysis_data.get("verdict", "") if a.analysis_data else "",
            })
        return Response({"applications": data, "total": len(data)}, status=status.HTTP_200_OK)
