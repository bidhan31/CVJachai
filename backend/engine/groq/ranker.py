import json
import time
import logging
from .client import groq_base

logger = logging.getLogger(__name__)

CHUNK_SIZE = 10
DELAY = 0.5

class GroqRanker:
    """Specialized engine for ranking large batches of resumes."""

    def rank_batch(self, job_desc, candidates):
        if not groq_base.available or not candidates:
            return {}

        final_scores = {}
        for i in range(0, len(candidates), CHUNK_SIZE):
            chunk = candidates[i : i + CHUNK_SIZE]
            
            prompt = (
                f"JOB DESCRIPTION:\n{job_desc[:600]}\n\n"
                "CANDIDATES:\n"
            )
            for c in chunk:
                prompt += f"- {c['filename']}: LocalRank={c.get('initial_score', 0.0):.2f}. Snip={c['text'][:500]}\n"
            
            prompt += (
                "\nReturn a JSON object where each key is the filename and each value is an object with:\n"
                "  'score': float 0.0-1.0 (how well they match the job)\n"
                "  'verdict': string (one short sentence: why they are a good or poor match)\n"
                "  'strengths': list of 2-3 key skills/traits that stand out\n"
                "Example: {\"file.pdf\": {\"score\": 0.87, \"verdict\": \"Strong ML background.\", \"strengths\": [\"Python\", \"Deep Learning\"]}}"
            )

            raw = groq_base.call(
                system_prompt="You are an expert recruiting AI. Output strictly valid JSON.",
                user_prompt=prompt,
                model=groq_base.ranker_model,
                json_mode=True
            )
            
            if raw:
                try:
                    clean = raw[raw.find("{"):raw.rfind("}")+1]
                    parsed = json.loads(clean)
                    # Support both old format {file: score} and new {file: {score, verdict}}
                    for fname, val in parsed.items():
                        if isinstance(val, dict):
                            final_scores[fname] = val
                        else:
                            final_scores[fname] = {"score": float(val), "verdict": "", "strengths": []}
                except Exception as e:
                    logger.error(f"Ranker Parse Error: {e}")

            if i + CHUNK_SIZE < len(candidates):
                time.sleep(DELAY)
        
        return final_scores

groq_ranker = GroqRanker()
