import json
import logging
from .client import groq_base

logger = logging.getLogger(__name__)

class GroqOptimizer:
    """Specialized engine for ATS resume optimization."""

    def optimize(self, text, job_desc=None):
        if not groq_base.available:
            return None

        prompt = (
            "Rewrite this resume to be 100% ATS-friendly and professional.\n"
            "Use clear sections and impact-driven action verbs.\n\n"
        )
        if job_desc:
            prompt += f"TARGET JOB:\n{job_desc[:800]}\n\n"
        
        prompt += f"RESUME:\n{text[:4000]}"

        return groq_base.call(
            system_prompt="You are an expert Resume Writer. Provide a beautifully formatted Markdown resume.",
            user_prompt=prompt,
            model=groq_base.optimizer_model,
            temperature=0.3
        )

    def recommend(self, text, job_desc=None):
        """Generate a single paragraph of actionable improvement recommendations for the resume."""
        if not groq_base.available:
            return ""

        prompt = (
            "Analyze this resume and provide an extremely brief, high-level recommendation (exactly 1 to 2 short sentences, under 30 words total) "
            "for future improvements. Focus on the single most critical skill gap, formatting issue, or impact improvement.\n"
        )
        if job_desc:
            prompt += f"Highlight how the candidate can bridge gaps to better match this target job:\n"
            prompt += f"TARGET JOB:\n{job_desc[:800]}\n\n"

        prompt += f"RESUME:\n{text[:4000]}\n\n"
        prompt += "Provide exactly 1 or 2 short sentences of high-level feedback (maximum 30 words total). Keep it extremely concise. Do not use lists or bullet points."

        raw = groq_base.call(
            system_prompt="You are an expert Resume Coach. Provide exactly 1-2 very short sentences (under 30 words total).",
            user_prompt=prompt,
            model=groq_base.optimizer_model,
            temperature=0.4,
            json_mode=False
        )

        if raw:
            return raw.strip()
                
        return "Improve layout readability, add quantifiable project metrics, and align keywords directly to the target role."

groq_optimizer = GroqOptimizer()
