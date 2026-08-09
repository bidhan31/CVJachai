from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from rest_framework.permissions import AllowAny
from engine.groq import groq_base

class APIInfoAPIView(APIView):
    """API information endpoint."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return API information."""
        
        response_data = {
            "name": "CvJachai Resume Intelligence Engine",
            "version": "5.0.0 (Cloud-Native AI Release)",
            "status": "Operational",
            "authentication": "JWT Bearer Token Required",
            "architecture": "Cloud-Native AI Pipeline (Groq GPT-OSS 120B + Llama 4 Scout Vision)",
            "active_models": {
                "text_classifier": groq_base.ranker_model + " (Groq)",
                "optimizer": groq_base.optimizer_model + " (Groq)",
                "vision_ocr": groq_base.vision_model + " (Groq Vision)",
            },
            "endpoints": {
                "POST /api/auth/signup": "Create account",
                "POST /api/auth/signin": "Login & obtain JWT tokens",
                "GET/PATCH /api/auth/profile": "Professional profile management",
                "POST /api/jobs/": "Create a new job posting (HR)",
                "GET /api/jobs/my/": "View your job postings",
                "POST /api/jobs/apply/": "Public job application submission",
                "POST /api/jobs/<id>/analyze/": "AI-driven candidate screening (Top-K)",
                "POST /api/classify": "Massive resume ranking (Legacy)",
                "POST /api/optimize": "AI-powered ATS Resume Rewrite"
            },
            "security": {
                "protocol": "JWT + DRF Throttling",
                "environment": "Fully secured via environment variables",
                "storage": "Cloudinary (Persistent Media Storage)"
            },
            "supported_formats": ["PDF", "DOCX", "TXT", "ZIP", "PNG", "JPG", "JPEG"],
            "features": [
                "Massive Scale: Processes batches of resumes via Cloudinary pipeline",
                "AI Screening: Smart Top-K candidate selection using Groq GPT-OSS",
                "Persistent Storage: Resumes are safely stored in Cloudinary",
                "Zero Data Loss: Survives ephemeral disk wipes on Render/Heroku",
                "Premium Dashboard: Glassmorphism UI for HR management",
                "Short IDs: Unique 10-char alphanumeric job IDs"
            ]
        }
        
        return Response(response_data, status=HTTP_200_OK)
