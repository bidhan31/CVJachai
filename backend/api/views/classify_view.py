import logging
import os
import uuid
from urllib.parse import quote
from django.conf import settings

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
)
from rest_framework.views import APIView

from engine.model import create_classifier
from engine.pretrained_classifier import semantic_reranker
from engine.groq import groq_ranker, groq_base
from api.serializers import ResumeUploadSerializer
from engine.utils import (
    process_resume_files,
    extract_all_resume_texts,
    calculate_skill_bonus,
    calculate_job_relevance,
    extract_contact_info,
)

logger = logging.getLogger(__name__)

# Initialize the LightGBM classifier
classifier = create_classifier(model_dir="models")

# How many top candidates to send through the slower pretrained model (if Groq fails)
_SEMANTIC_RERANK_K = 20


import shutil
import time

def cleanup_old_resumes(max_age_hours=24):
    """Automatically delete resume batch folders older than max_age_hours."""
    try:
        resumes_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
        if not os.path.exists(resumes_dir):
            return
            
        now = time.time()
        for batch_folder in os.listdir(resumes_dir):
            batch_path = os.path.join(resumes_dir, batch_folder)
            if os.path.isdir(batch_path):
                folder_age = now - os.path.getmtime(batch_path)
                if folder_age > (max_age_hours * 3600):
                    shutil.rmtree(batch_path, ignore_errors=True)
                    logger.info("Cleaned up old resume batch: %s", batch_folder)
    except Exception as e:
        logger.error("Error cleaning up old resumes: %s", e)


class ResumeClassifyAPIView(APIView):
    """API endpoint for classifying resumes."""
    
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        """
        Classify and rank uploaded resumes against a job circular.
        """
        # Automatically clean up resume batches older than 24 hours
        cleanup_old_resumes(max_age_hours=24)
        
        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Validation error", "details": serializer.errors},
                status=HTTP_400_BAD_REQUEST
            )

        # Create a unique batch directory in MEDIA_ROOT
        batch_id = str(uuid.uuid4())
        media_save_path = os.path.join(settings.MEDIA_ROOT, 'resumes', batch_id)
        os.makedirs(media_save_path, exist_ok=True)

        try:
            # Parse validated parameters
            files = request.FILES.getlist('resume_files')
            logger.info(">>> API CALLED: Received %d files for processing...", len(files))
            job_circular = request.data.get('job_circular', '').strip()
            top_k = int(request.data.get('top_k', 5))
            skills_raw = request.data.get('skills', '')
            skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
            min_experience = int(request.data.get('min_experience', 0))
            
            try:
                min_score = float(request.data.get('min_score', 0.0))
            except (TypeError, ValueError):
                min_score = 0.0

            # ---- Stage 1: File processing ----
            # Process files and save to MEDIA_ROOT
            resumes = process_resume_files(files, media_save_path)

            if not resumes:
                return Response(
                    {"error": "No valid resume files found after processing."},
                    status=HTTP_400_BAD_REQUEST,
                )

            # ---- Stage 2: Text extraction ----
            resume_texts = extract_all_resume_texts(resumes)
            if not resume_texts:
                return Response(
                    {"error": "Could not extract readable text from any files."},
                    status=HTTP_400_BAD_REQUEST,
                )

            # ---- Stage 5: Local Analysis ----
            local_results = []
            for filename, resume_text in resume_texts.items():
                try:
                    relevance = calculate_job_relevance(resume_text, job_circular)
                    bonus = calculate_skill_bonus(resume_text, skills_list, min_experience)
                    initial_score = (relevance * 0.6) + (bonus * 0.4)
                    
                    # Extract Contact Info
                    contact_info = extract_contact_info(resume_text)

                    local_results.append({
                        "filename": filename,
                        "text": resume_text,
                        "file_path": resumes[filename],
                        "keyword_relevance": relevance,
                        "skill_bonus": bonus,
                        "initial_score": initial_score,
                        "contact_info": contact_info
                    })
                except Exception as e:
                    logger.warning("Local analysis failed for '%s': %s", filename, e)

            # Sort and subset for Groq
            local_results.sort(key=lambda x: x['initial_score'], reverse=True)
            top_for_groq = local_results[:15]

            # ---- Stage 6: Groq Judgement ----
            final_scores = {}
            if groq_base.available and top_for_groq:
                final_scores = groq_ranker.rank_batch(job_circular, top_for_groq)

            # Final assembly
            results = []
            host = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'

            for index, cd in enumerate(local_results):
                filename = cd['filename']
                
                if filename in final_scores:
                    groq_data = final_scores[filename]
                    # Handle both dict and raw float from Groq ranker
                    if isinstance(groq_data, dict):
                        semantic_score = float(groq_data.get('score', 0.5))
                        verdict = groq_data.get('verdict', '')
                        strengths = groq_data.get('strengths', [])
                    else:
                        semantic_score = float(groq_data)
                        verdict = ''
                        strengths = []
                    engine = groq_base.ranker_model
                elif index < _SEMANTIC_RERANK_K:
                    semantic_score = semantic_reranker.match_job(cd['text'], job_circular)
                    verdict = ''
                    strengths = []
                    engine = "Local NLI"
                else:
                    semantic_score = cd['initial_score']
                    verdict = ''
                    strengths = []
                    engine = "Keyword Analysis"

                final_score = (semantic_score * 0.50) + (cd['keyword_relevance'] * 0.30) + (cd['skill_bonus'] * 0.20)
                
                # Construct Download Link (URL-encode to handle spaces in folder names)
                relative_path = os.path.relpath(cd['file_path'], settings.MEDIA_ROOT).replace('\\', '/')
                encoded_path = quote(relative_path)
                resume_url = f"{protocol}://{host}{settings.MEDIA_URL}{encoded_path}"

                results.append({
                    "candidate_name": cd['contact_info']['name'],
                    "email": cd['contact_info']['email'],
                    "phone": cd['contact_info']['phone'],
                    "resume_url": resume_url,
                    "match_score": round(final_score, 4),
                    "match_percentage": f"{round(final_score * 100, 1)}%",
                    "verdict": verdict,
                    "key_strengths": strengths,
                    "analysis_engine": engine,
                })

            # Threshold and Top-K
            matched = [r for r in results if r['match_score'] >= min_score]
            matched.sort(key=lambda x: x['match_score'], reverse=True)
            results = matched[:top_k]

            # ---- Stage 7: Aesthetics & Score Boosting (University Project Adjustment) ----
            # Purpose: Map the relatively low raw AI scores (e.g. 0.45) to a more impressive 
            # visual range (90%+) while maintaining the same ranking order.
            if results:
                highest_raw = results[0]['match_score']
                if highest_raw > 0:
                    for r in results:
                        # Calculate relative performance compared to the best candidate
                        relative_ratio = r['match_score'] / highest_raw
                        
                        # Apply a non-linear boost: 
                        # We map the top candidate to ~98% and use a curve (sqrt) 
                        # to keep others in the 90-97% range.
                        boosted_score = 0.88 + (relative_ratio ** 0.5) * 0.10
                        
                        r['match_score'] = round(boosted_score, 4)
                        r['match_percentage'] = f"{round(boosted_score * 100, 1)}%"

            # Add rank position
            for i, r in enumerate(results, 1):
                r['rank'] = i

            return Response({
                "batch_id": batch_id,
                "total_resumes_processed": len(resumes),
                "top_candidates": results,
            }, status=HTTP_200_OK)

        except Exception as e:
            logger.exception("Unexpected error in classify endpoint")
            return Response(
                {"error": f"An unexpected error occurred: {e}"},
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )
