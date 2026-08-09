"""
Semantic re-ranker using a pretrained HuggingFace zero-shot NLI model.

No hardcoded categories or descriptions.
Category labels are derived dynamically from whatever the model's metadata
reports — so this file never needs to change when new categories are added.

Pipeline:
    LightGBM  → fast initial classification of all resumes
    Reranker  → zero-shot NLI re-score of top-K candidates only
"""

import logging
import re
import os

logger = logging.getLogger(__name__)


def _slug_to_label(slug: str) -> str:
    """
    Convert a category slug to a human-readable NLI candidate label.

    Examples:
        "technical-roles"        → "technical roles"
        "accounts-officers"      → "accounts officers"
        "research-assistants"    → "research assistants"
        "peion"                  → "peon"   (handles known typo gracefully)
        "administration-officers"→ "administration officers"
    """
    # Fix known training-time typos so the NLI model understands the label
    typo_fixes = {"peion": "peon"}
    fixed = typo_fixes.get(slug, slug)
    # Replace hyphens/underscores with spaces and title-case
    return re.sub(r"[-_]+", " ", fixed).strip()


class SemanticReranker:
    """
    Lazy-loaded zero-shot NLI classifier.

    - Loads the model on the first classify() call (server startup not blocked).
    - Categories are passed in at classify time — nothing hardcoded here.
    - Falls back silently if transformers / torch are not installed.
    """

    MODEL_NAME = "cross-encoder/nli-MiniLM2-L6-H768"

    # Truncate each resume to avoid exceeding transformer token limits (~512 tokens).
    MAX_TEXT_CHARS = 2000

    def __init__(self) -> None:
        self._pipeline = None
        self._available: bool | None = None   # None = not yet tested

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """True if the pretrained model is loaded and ready."""
        if os.getenv('RENDER') == 'true' and os.getenv('PLAN') == 'free':
            return False  # Skip local heavy model on Render Free Tier to avoid OOM
        
        if self._available is None:
            try:
                self._load()
                self._available = True
                logger.info("Semantic reranker ready (%s).", self.MODEL_NAME)
            except Exception as exc:
                logger.warning(
                    "Semantic reranker unavailable — using LightGBM only. Error: %s", exc
                )
                self._available = False
        return self._available

    def classify(self, resume_text: str, categories: list[str]) -> dict[str, float]:
        """
        Zero-shot classify a single resume into the given categories.

        Args:
            resume_text: Raw text from the resume.
            categories:  List of category slugs from model metadata
                         (e.g. ["technical-roles", "accounts-officers"]).

        Returns:
            {slug: probability} sorted by probability descending.
            Empty dict if unavailable or inference fails.
        """
        if not self.available or not categories:
            return {}

        # Build a slug ↔ label mapping dynamically — no hardcoding
        label_to_slug = {_slug_to_label(cat): cat for cat in categories}
        candidate_labels = list(label_to_slug.keys())

        try:
            result = self._pipeline(
                resume_text[: self.MAX_TEXT_CHARS],
                candidate_labels=candidate_labels,
                multi_label=False,
            )
            return {
                label_to_slug[label]: float(score)
                for label, score in zip(result["labels"], result["scores"])
            }
        except Exception as exc:
            logger.warning("Zero-shot inference failed: %s", exc)
            return {}

    def classify_batch(
        self,
        resume_texts: dict[str, str],
        categories: list[str],
    ) -> dict[str, dict[str, float]]:
        """
        Classify multiple resumes into fixed categories.
        """
        results: dict[str, dict[str, float]] = {}
        for filename, text in resume_texts.items():
            scores = self.classify(text, categories)
            if scores:
                results[filename] = scores
        return results

    def match_job(self, resume_text: str, job_description: str) -> float:
        """
        Dynamically cross-check if a resume matches a specific job description.
        This uses Zero-Shot NLI to score the "entailment" of the match
        without any pre-selected categories.
        """
        if not self.available:
            return 0.0

        # We use the job description as a context and ask if the resume is a fit.
        # Hypothesis: "This candidate has the skills and experience required for this job."
        candidate_labels = ["a perfect match for this job", "not a match"]
        
        try:
            # We truncate both to fit within model limits
            text_to_check = f"Resume: {resume_text[:1000]}\n\nJob: {job_description[:1000]}"
            result = self._pipeline(
                text_to_check,
                candidate_labels=candidate_labels,
                multi_label=False,
            )
            # Return the score for the "match" label
            for label, score in zip(result["labels"], result["scores"]):
                if "perfect match" in label:
                    return float(score)
            return 0.0
        except Exception as exc:
            logger.warning("Dynamic matching failed: %s", exc)
            return 0.0

    # ── Private ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Lazy-load the HuggingFace pipeline."""
        if self._pipeline is not None:
            return
        # Import inside method so a missing package won't crash Django startup
        from transformers import pipeline as hf_pipeline, logging as hf_logging
        # Suppress the "UNEXPECTED" keys warning report for position_ids
        hf_logging.set_verbosity_error()
        
        logger.info("Loading pretrained model: %s …", self.MODEL_NAME)
        self._pipeline = hf_pipeline(
            "zero-shot-classification",
            model=self.MODEL_NAME,
            device=-1,   # CPU
        )


# Module-level singleton shared across all requests
semantic_reranker = SemanticReranker()
