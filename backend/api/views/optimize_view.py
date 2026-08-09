import os
import shutil
import tempfile
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.status import (
    HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
)

from engine.groq import groq_optimizer, groq_base
from engine.utils import extract_text_from_file

logger = logging.getLogger(__name__)

class ResumeOptimizeAPIView(APIView):
    """
    API endpoint for ATS-optimizing a single resume.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        """
        Analyse and rewrite a resume for ATS compatibility.
        
        Parameters:
        - resume_file: The resume file to optimize.
        - job_description: (Optional) Target job to optimize against.
        """
        resume_file = request.FILES.get('resume_file')
        job_description = request.data.get('job_description', '').strip()

        if not resume_file:
            return Response(
                {"error": "Please provide a 'resume_file' to optimize."},
                status=HTTP_400_BAD_REQUEST
            )

        if not groq_base.available:
            return Response(
                {"error": "Groq AI Engine is currently unavailable. Check your API_KEY."},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        temp_path = None
        try:
            # 1. Save file to temporary storage
            suffix = os.path.splitext(resume_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in resume_file.chunks():
                    tmp.write(chunk)
                temp_path = tmp.name

            # 2. Extract Text
            resume_text = extract_text_from_file(temp_path)
            if not resume_text or len(resume_text.strip()) < 10:
                logger.warning("Extraction failed or text too short (<10 chars) for: %s", resume_file.name)
                return Response(
                    {"error": "Could not extract sufficient text from the resume file. Ensure it is not empty."},
                    status=HTTP_400_BAD_REQUEST
                )

            # 3. Call Groq for Optimization and Recommendation
            logger.info("Starting ATS optimization and recommendation for: %s", resume_file.name)
            optimized_content = groq_optimizer.optimize(resume_text, job_description)
            recommendation = groq_optimizer.recommend(resume_text, job_description)

            if not optimized_content:
                return Response(
                    {"error": "Failed to generate optimized content from AI."},
                    status=HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                "original_filename": resume_file.name,
                "optimization_engine": f"Groq {groq_base.optimizer_model}",
                "recommendation": recommendation,
                "optimized_resume_markdown": optimized_content,
                "disclaimer": "This is an AI-generated optimization. Please review for factual accuracy."
            }, status=HTTP_200_OK)

        except Exception as e:
            logger.exception("Error during resume optimization")
            return Response(
                {"error": f"An unexpected error occurred: {e}"},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
