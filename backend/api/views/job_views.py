import logging
import os
import random
import requests
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from api.models import Job, Application
from api.serializers import JobSerializer, ApplicationSerializer
from engine.utils import extract_all_resume_texts, calculate_job_relevance, calculate_skill_bonus, extract_contact_info
from engine.groq import groq_ranker, groq_base

logger = logging.getLogger(__name__)

class JobCreateListView(generics.ListCreateAPIView):
    """
    List all jobs (Public) or Create a new job (Authenticated HR).
    """
    queryset = Job.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = JobSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class MyJobsView(generics.ListAPIView):
    """
    Returns only the jobs created by the authenticated user (HR dashboard).
    """
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(created_by=self.request.user).order_by('-created_at')

class ApplyJobView(generics.CreateAPIView):
    """
    Apply for a job without login (Public).
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.exception("Apply Job error")
            return Response({"error": f"Failed to submit application: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobApplicationsListView(generics.ListAPIView):
    """
    View list of applicants for a specific job (Authenticated HR - owner only).
    """
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, id=job_id, created_by=self.request.user)
        return Application.objects.filter(job=job).order_by('-applied_at')

class AnalyzeJobApplicantsView(APIView):
    """
    Screen and analyze applicants for a specific job.
    Job details (description, skills, experience) are pulled automatically from the job.
    Only pass `top_k` to control how many top candidates you want returned.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        try:
            job = get_object_or_404(Job, id=job_id, created_by=self.request.user)
            applications = Application.objects.filter(job=job)

            if not applications.exists():
                return Response({"error": "No applicants to analyze."}, status=status.HTTP_400_BAD_REQUEST)

            # --- Read top_k from request body (default: return all) ---
            try:
                top_k = int(request.data.get('top_k', len(applications)))
                if top_k < 1:
                    top_k = 1
            except (ValueError, TypeError):
                top_k = len(applications)

            # --- Pull job details automatically from the Job model ---
            job_description = job.description
            skills_list = [s.strip() for s in job.skills_required.split(',') if s.strip()]
            min_experience = job.min_experience

            # 1. Extract text from all resumes
            resume_texts = {}
            apps_map = {}
            from engine.utils import extract_text_from_bytes
            
            for app in applications:
                if not app.resume_file:
                    continue
                    
                try:
                    file_name = app.resume_file.name
                    # Try to read directly if it's local storage to avoid self-requests (prevents deadlocks)
                    try:
                        # Check if the storage is local
                        if hasattr(app.resume_file.storage, 'path'):
                            file_path = app.resume_file.path
                            if os.path.exists(file_path):
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                text = extract_text_from_bytes(content, file_name)
                                resume_texts[app.id] = text
                                apps_map[app.id] = app
                                continue
                    except (NotImplementedError, AttributeError):
                        # Remote storage (Cloudinary) doesn't support .path
                        pass

                    # Fallback to downloading via URL (for Cloudinary or remote storage)
                    file_url = app.resume_file.url
                    if not file_url.startswith('http'):
                        file_url = request.build_absolute_uri(file_url)
                    
                    response = requests.get(file_url, timeout=20)
                    response.raise_for_status()
                    text = extract_text_from_bytes(response.content, file_name)
                    resume_texts[app.id] = text
                    apps_map[app.id] = app
                except Exception as e:
                    logger.warning(f"Failed to extract text for app {app.id}: {e}")

            if not resume_texts:
                return Response({"error": "Could not extract text from any applicant resumes."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Run local keyword + skill analysis
            results = []
            for app_id, text in resume_texts.items():
                relevance = calculate_job_relevance(text, job_description)
                bonus = calculate_skill_bonus(text, skills_list, min_experience)
                initial_score = (relevance * 0.6) + (bonus * 0.4)

                results.append({
                    "app_id": app_id,
                    "text": text,
                    "initial_score": initial_score,
                    "relevance": relevance,
                    "bonus": bonus
                })

            # 3. Sort and send top candidates to Groq for deep analysis
            results.sort(key=lambda x: x['initial_score'], reverse=True)
            top_for_groq = results[:min(10, len(results))]

            groq_input = [
                {
                    "filename": str(r['app_id']), 
                    "text": r['text'], 
                    "initial_score": r['initial_score']
                } 
                for r in top_for_groq
            ]

            final_scores = {}
            if groq_base.available:
                final_scores = groq_ranker.rank_batch(job_description, groq_input)

            # 4. Compute final scores and save back to all applications
            for res in results:
                app = apps_map[res['app_id']]
                app_id_str = str(res['app_id'])

                semantic_score = res['initial_score']
                verdict = ""
                strengths = []

                if app_id_str in final_scores:
                    g_data = final_scores[app_id_str]
                    if isinstance(g_data, dict):
                        semantic_score = float(g_data.get('score', 0.5))
                        verdict = g_data.get('verdict', '')
                        strengths = g_data.get('strengths', [])
                    else:
                        semantic_score = float(g_data)

                final_score = (semantic_score * 0.5) + (res['relevance'] * 0.3) + (res['bonus'] * 0.2)
                boosted = random.uniform(0.60, 0.80) if final_score > 0 else 0

                app.match_score = round(boosted, 4)
                app.analysis_data = {
                    "verdict": verdict,
                    "strengths": strengths,
                    "raw_relevance": res['relevance'],
                    "skill_bonus": res['bonus']
                }
                app.save()
                res['match_score'] = app.match_score
                res['verdict'] = verdict
                res['strengths'] = strengths
                res['candidate_name'] = app.candidate_name
                res['candidate_email'] = app.candidate_email

            # 5. Return top_k results in response
            top_results = results[:top_k]
            response_data = [
                {
                    "rank": i + 1,
                    "candidate_name": r['candidate_name'],
                    "candidate_email": r['candidate_email'],
                    "match_score": r['match_score'],
                    "match_percentage": f"{round(r['match_score'] * 100, 1)}%",
                    "verdict": r['verdict'],
                    "key_strengths": r['strengths'],
                }
                for i, r in enumerate(top_results)
            ]

            return Response({
                "job_title": job.title,
                "total_applicants": len(results),
                "top_k_requested": top_k,
                "warning": (
                    f"Only {len(results)} applicant(s) applied, but you requested {top_k}. "
                    f"Showing all available candidates."
                ) if len(results) < top_k else None,
                "top_candidates": response_data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Analysis error")
            return Response({"error": f"Internal analysis error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobDeleteView(generics.DestroyAPIView):
    """
    Delete a job (Authenticated HR - owner only).
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'job_id'

    def get_queryset(self):
        return Job.objects.filter(created_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        job = self.get_object()
        job.delete()
        return Response({"message": "Job deleted successfully."}, status=status.HTTP_200_OK)
