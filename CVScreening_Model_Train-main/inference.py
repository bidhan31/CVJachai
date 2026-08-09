"""
Inference module for Resume Screening — Production ATS Engine

Real-world job screening pipeline:
  1. Parse resume → extract all features (skills, experience, education, seniority, etc.)
  2. Classify into job domain (category prediction)
  3. Score against specific job requirements (weighted multi-factor)
  4. Apply knockout criteria (hard filters → auto-reject)
  5. Detect red flags & employment gaps
  6. Make screening decision: SHORTLIST / REVIEW / REJECT with reasons
  7. Rank all candidates for a position
"""

import re
import numpy as np
import json
import joblib
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer

from config import (
    MODEL_SAVE_DIR, TOP_K_RESULTS,
    EDUCATION_LEVELS,
    SENIORITY_LEVELS, SCORING_WEIGHTS,
    SCREENING_THRESHOLDS, KNOCKOUT_CRITERIA,
)
from feature_extractor import ResumeFeatureExtractor, extract_text_from_file


class ResumeScreeningEngine:
    """
    Production ATS screening engine.

    Workflow (same as a real recruiter):
      1. engine = ResumeScreeningEngine()
      2. job = {...}  or  job = engine.parse_job_description("free text JD")
      3. result = engine.screen_resume(resume_text, job)
         → returns score, decision (SHORTLIST/REVIEW/REJECT), breakdown, red flags
      4. ranked = engine.rank_resume_files(file_list, job)
         → returns sorted candidates with decisions
    """

    def __init__(self, model_dir: str = None):
        model_dir = Path(model_dir) if model_dir else MODEL_SAVE_DIR

        # Load trained artifacts
        model_path = model_dir / "best_classifier.pkl"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Missing model artifact: {model_path}. Run train.py after create_dataset.py."
            )
        self.model = joblib.load(model_path)

        scaler_path = model_dir / "scaler.pkl"
        if not scaler_path.exists():
            raise FileNotFoundError(
                f"Missing scaler artifact: {scaler_path}. Run train.py after create_dataset.py."
            )
        self.scaler = joblib.load(scaler_path)

        meta_path = model_dir / "model_metadata.json"
        if not meta_path.exists():
            raise FileNotFoundError(
                f"Missing metadata artifact: {meta_path}. Run train.py after create_dataset.py."
            )
        with open(meta_path, 'r') as f:
            self.metadata = json.load(f)

        self.extractor = ResumeFeatureExtractor()
        self.categories = self.metadata["categories"]

        # Load skill list from metadata (ensures feature vector matches training exactly)
        if "skill_list" in self.metadata:
            self.all_skills = self.metadata["skill_list"]
        else:
            # Fallback for models trained before skill_list was saved
            from config import TECHNICAL_SKILLS, SOFT_SKILLS
            self.all_skills = TECHNICAL_SKILLS + SOFT_SKILLS

        # Load SBERT model for semantic embeddings
        print("Loading SBERT transformer model...")
        self.sbert = SentenceTransformer(self.metadata.get("semantic_model", "all-MiniLM-L6-v2"))

        print(f"ATS Engine loaded: {self.metadata['best_model']}")
        print(f"  CV Accuracy: {self.metadata['cv_accuracy']*100:.1f}%")
        print(f"  Categories:  {self.categories}")

    # ==================================================================
    # Core: build feature vector (must match training format exactly)
    # ==================================================================

    def _build_feature_vector(self, resume_text: str) -> tuple:
        features = self.extractor.extract_all(resume_text)

        skill_vector = []
        all_found_skills = features["technical_skills"] + features["soft_skills"]
        for skill in self.all_skills:
            skill_vector.append(1.0 if skill in all_found_skills else 0.0)

        # Numeric features — MUST match exact order in create_dataset.py skill_columns
        skill_vector.append(float(features["years_of_experience"]))
        skill_vector.append(float(features["education_score"]))
        skill_vector.append(float(features["num_certifications"]))
        skill_vector.append(float(features["num_sections"]))
        skill_vector.append(float(features.get("seniority_score", 0)))
        skill_vector.append(float(features.get("resume_quality_score", 0)))
        skill_vector.append(float(features.get("num_employment_gaps", 0)))
        skill_vector.append(float(features.get("total_gap_months", 0)))
        skill_vector.append(float(features.get("num_red_flags", 0)))

        skill_array = np.array([skill_vector], dtype=np.float32)
        
        # Get semantic embeddings from SBERT
        semantic_vector = self.sbert.encode([resume_text], convert_to_numpy=True)
        
        combined = np.hstack([skill_array, semantic_vector])
        combined_scaled = self.scaler.transform(combined)

        return combined_scaled, features

    # ==================================================================
    # Category prediction
    # ==================================================================

    def predict_category(self, resume_text: str) -> Dict:
        combined_scaled, _ = self._build_feature_vector(resume_text)
        predicted_idx = self.model.predict(combined_scaled)[0]

        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(combined_scaled)[0]
            confidence = float(probabilities[predicted_idx])
            all_probs = {
                cat: float(prob) for cat, prob in zip(self.categories, probabilities)
            }
        else:
            confidence = 1.0
            all_probs = {cat: (1.0 if i == predicted_idx else 0.0)
                         for i, cat in enumerate(self.categories)}

        return {
            "predicted_category": self.categories[predicted_idx],
            "confidence": confidence,
            "all_probabilities": all_probs,
        }

    # ==================================================================
    # Job description parser (free text → structured requirements)
    # ==================================================================

    def parse_job_description(self, jd_text: str) -> Dict:
        """Parse a free-text job description into structured requirements.

        This is what real ATS systems do — extract requirements from JD text
        so you can match resumes against them automatically.
        """
        jd_lower = jd_text.lower()

        # --- Extract required skills ---
        all_resume_skills_regex = re.compile(r'\b(' + '|'.join(map(re.escape, sorted(self.all_skills, key=len, reverse=True))) + r')\b')
        found_skills = list(set(all_resume_skills_regex.findall(jd_lower)))

        # Split into required (near "required"/"must") vs preferred
        required_context = ""
        preferred_context = ""
        for section_kw in ["required", "must have", "mandatory", "essential", "minimum"]:
            idx = jd_lower.find(section_kw)
            if idx >= 0:
                required_context += jd_lower[idx:idx+500] + " "
        for section_kw in ["preferred", "nice to have", "bonus", "desired", "plus"]:
            idx = jd_lower.find(section_kw)
            if idx >= 0:
                preferred_context += jd_lower[idx:idx+500] + " "

        required_skills = []
        preferred_skills = []
        for skill in found_skills:
            if skill in required_context:
                required_skills.append(skill)
            elif skill in preferred_context:
                preferred_skills.append(skill)
            else:
                required_skills.append(skill)  # default to required

        # --- Experience ---
        min_exp = 0
        max_exp = 99
        exp_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
            r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)',
            r'minimum\s*(\d+)\s*(?:years?|yrs?)',
            r'at\s*least\s*(\d+)\s*(?:years?|yrs?)',
        ]
        for pat in exp_patterns:
            m = re.search(pat, jd_lower)
            if m:
                groups = m.groups()
                min_exp = int(groups[0])
                if len(groups) > 1 and groups[1]:
                    max_exp = int(groups[1])
                else:
                    max_exp = min_exp + 10
                break

        # --- Education ---
        best_edu = "any"
        best_score = 0
        for keyword, score in EDUCATION_LEVELS.items():
            if keyword in jd_lower and score > best_score:
                best_score = score
                best_edu = {6: "phd", 5: "masters", 4: "bachelors",
                            3: "diploma", 2: "hsc", 1: "ssc"}.get(score, "any")

        # --- Seniority ---
        seniority = "any"
        for level, info in SENIORITY_LEVELS.items():
            for title_kw in info["titles"]:
                if title_kw in jd_lower:
                    seniority = level
                    break
            if seniority != "any":
                break

        # --- Category (predict from JD text using the trained model) ---
        try:
            prediction = self.predict_category(jd_text)
            category = prediction["predicted_category"]
        except Exception:
            category = ""

        return {
            "required_skills": list(set(required_skills)),
            "preferred_skills": list(set(preferred_skills)),
            "min_experience": min_exp,
            "max_experience": max_exp,
            "education_level": best_edu,
            "seniority": seniority,
            "category": category,
        }

    # ==================================================================
    # MAIN: Screen a single resume against job requirements
    # ==================================================================

    def screen_resume(self, resume_text: str, job_requirements: Dict) -> Dict:
        """Full ATS screening: score, match, decide + reasons.

        Args:
            resume_text: Raw resume text
            job_requirements: Structured dict with keys:
                - required_skills: List[str]
                - preferred_skills: List[str]
                - min_experience: int
                - max_experience: int
                - education_level: str
                - seniority: str (optional)
                - category: str (optional)

        Returns comprehensive screening result.
        """
        features = self.extractor.extract_all(resume_text)
        reasons = []      # human-readable screening notes
        knockouts = []    # instant-reject reasons

        # ==================== 1. Skill Matching ====================
        required_skills = [s.lower() for s in job_requirements.get("required_skills", [])]
        preferred_skills = [s.lower() for s in job_requirements.get("preferred_skills", [])]
        all_resume_skills = features["technical_skills"] + features["soft_skills"]

        if required_skills:
            req_matched = [s for s in required_skills if s in all_resume_skills]
            req_missing = [s for s in required_skills if s not in all_resume_skills]
            req_score = len(req_matched) / len(required_skills)
        else:
            req_matched, req_missing = [], []
            req_score = 1.0

        if preferred_skills:
            pref_matched = [s for s in preferred_skills if s in all_resume_skills]
            pref_score = len(pref_matched) / len(preferred_skills)
        else:
            pref_matched = []
            pref_score = 1.0

        # Knockout: required skill threshold
        ko_min = KNOCKOUT_CRITERIA["min_required_skills_pct"]
        if required_skills and req_score < ko_min:
            knockouts.append(
                "Missing too many required skills ({}/{} matched, need {}%)".format(
                    len(req_matched), len(required_skills), int(ko_min * 100)
                )
            )

        if req_missing:
            reasons.append("Missing required: {}".format(", ".join(req_missing)))
        if req_matched:
            reasons.append("Matched required: {}".format(", ".join(req_matched)))

        # ==================== 2. Experience Matching ====================
        min_exp = job_requirements.get("min_experience", 0)
        max_exp = job_requirements.get("max_experience", 99)
        resume_exp = features["years_of_experience"]

        if min_exp <= resume_exp <= max_exp:
            exp_score = 1.0
        elif resume_exp < min_exp:
            gap = min_exp - resume_exp
            exp_score = max(0.0, 1.0 - gap / max(min_exp, 1))
            reasons.append("Experience: {} yrs (need {}-{})".format(
                resume_exp, min_exp, max_exp))
            # Knockout: way under minimum
            if gap > KNOCKOUT_CRITERIA["max_experience_gap"]:
                knockouts.append("Experience too low: {} yrs vs {} minimum".format(
                    resume_exp, min_exp))
        else:
            over = resume_exp - max_exp
            exp_score = max(0.0, 1.0 - over / max(max_exp, 1))
            reasons.append("Possibly overqualified: {} yrs (max {})".format(
                resume_exp, max_exp))

        # ==================== 3. Education Matching ====================
        edu_scores = {
            "phd": 6, "masters": 5, "bachelors": 4,
            "diploma": 3, "hsc": 2, "ssc": 1, "any": 0,
        }
        required_edu = job_requirements.get("education_level", "any").lower()
        required_edu_num = edu_scores.get(required_edu, 0)
        resume_edu_num = features["education_score"]

        if resume_edu_num >= required_edu_num:
            edu_score = 1.0
        else:
            edu_score = resume_edu_num / max(required_edu_num, 1)
            reasons.append("Education: {} (need {})".format(
                features["education_level"], required_edu))
            # Knockout: education not met
            if KNOCKOUT_CRITERIA["min_education_met"] and required_edu_num > 0 and resume_edu_num < required_edu_num:
                knockouts.append("Education requirement not met: {} < {}".format(
                    features["education_level"], required_edu))

        # ==================== 4. Category Matching ====================
        job_category = job_requirements.get("category", "").lower()
        prediction = self.predict_category(resume_text)

        if job_category and job_category in prediction["all_probabilities"]:
            cat_score = prediction["all_probabilities"][job_category]
        else:
            cat_score = prediction["confidence"]

        if job_category and prediction["predicted_category"] != job_category:
            reasons.append("Category mismatch: predicted {} (wanted {})".format(
                prediction["predicted_category"], job_category))

        # ==================== 5. Seniority Matching ====================
        job_seniority = job_requirements.get("seniority", "any").lower()
        resume_seniority = features["seniority_level"]
        resume_sen_score = features["seniority_score"]

        if job_seniority == "any":
            sen_score = 1.0
        else:
            job_sen_num = SENIORITY_LEVELS.get(job_seniority, {}).get("score", 3)
            diff = abs(resume_sen_score - job_sen_num)
            if diff == 0:
                sen_score = 1.0
            elif diff == 1:
                sen_score = 0.7
            elif diff == 2:
                sen_score = 0.4
            else:
                sen_score = 0.1
                reasons.append("Seniority mismatch: {} (wanted {})".format(
                    resume_seniority, job_seniority))

        # ==================== 6. Resume Quality ====================
        quality_score = features["resume_quality_score"] / 100.0

        # ==================== 7. Certification Bonus ====================
        req_certs = [c.lower() for c in job_requirements.get("certifications", [])]
        if req_certs:
            cert_matched = [c for c in req_certs if c in features["certifications"]]
            cert_score = len(cert_matched) / len(req_certs)
        else:
            # Bonus for having any relevant certs
            cert_score = min(1.0, features["num_certifications"] / 3) if features["num_certifications"] > 0 else 0.0

        # ==================== OVERALL SCORE ====================
        w = SCORING_WEIGHTS
        overall = (
            req_score       * w["required_skills"]
            + exp_score     * w["experience"]
            + edu_score     * w["education"]
            + pref_score    * w["preferred_skills"]
            + cat_score     * w["category_match"]
            + sen_score     * w["seniority_match"]
            + quality_score * w["resume_quality"]
            + cert_score    * w["certifications"]
        )
        overall_pct = round(overall * 100, 2)

        # ==================== SCREENING DECISION ====================
        if knockouts:
            decision = "REJECT"
            decision_reason = "Knockout: " + knockouts[0]
        elif overall_pct >= SCREENING_THRESHOLDS["shortlist"]:
            decision = "SHORTLIST"
            decision_reason = "Strong match — recommend for interview"
        elif overall_pct >= SCREENING_THRESHOLDS["maybe"]:
            decision = "REVIEW"
            decision_reason = "Partial match — needs manual review"
        else:
            decision = "REJECT"
            decision_reason = "Score below threshold ({:.0f}%)".format(overall_pct)

        # ==================== RED FLAGS ====================
        red_flag_summary = []
        for rf in features.get("red_flags", []):
            red_flag_summary.append({
                "flag": rf["flag"],
                "description": rf["description"],
                "severity": rf["severity"],
            })

        return {
            "overall_score": overall_pct,
            "decision": decision,
            "decision_reason": decision_reason,
            "knockouts": knockouts,

            "breakdown": {
                "required_skills_score":  round(req_score * 100, 1),
                "preferred_skills_score": round(pref_score * 100, 1),
                "experience_score":       round(exp_score * 100, 1),
                "education_score":        round(edu_score * 100, 1),
                "category_score":         round(cat_score * 100, 1),
                "seniority_score":        round(sen_score * 100, 1),
                "quality_score":          round(quality_score * 100, 1),
                "certification_score":    round(cert_score * 100, 1),
            },

            "candidate": {
                "name":                features.get("candidate_name", ""),
                "email":               features.get("email", ""),
                "phone":               features.get("phone", ""),
                "years_of_experience": resume_exp,
                "education_level":     features["education_level"],
                "seniority_level":     resume_seniority,
                "predicted_category":  prediction["predicted_category"],
                "category_confidence": prediction["confidence"],
            },

            "skills": {
                "required_matched": req_matched,
                "required_missing": req_missing,
                "preferred_matched": pref_matched,
                "all_skills_found":  all_resume_skills,
                "certifications":    features["certifications"],
            },

            "red_flags": red_flag_summary,
            "employment_gaps": features.get("employment_gaps", []),
            "resume_quality": features["resume_quality_score"],
            "screening_notes": reasons,
        }

    # ==================================================================
    # Backward-compat wrappers
    # ==================================================================

    def score_resume(self, resume_text: str, job_requirements: Dict) -> Dict:
        """Backward-compatible scoring (calls screen_resume internally)."""
        result = self.screen_resume(resume_text, job_requirements)
        return {
            "overall_score": result["overall_score"],
            "decision": result["decision"],
            "breakdown": result["breakdown"],
            "details": {
                "required_skills_matched": result["skills"]["required_matched"],
                "required_skills_missing": result["skills"]["required_missing"],
                "preferred_skills_matched": result["skills"]["preferred_matched"],
                "years_of_experience": result["candidate"]["years_of_experience"],
                "education_level": result["candidate"]["education_level"],
                "predicted_category": result["candidate"]["predicted_category"],
                "category_confidence": result["candidate"]["category_confidence"],
                "all_skills_found": result["skills"]["all_skills_found"],
                "certifications": result["skills"]["certifications"],
                "candidate_name": result["candidate"]["name"],
                "seniority_level": result["candidate"]["seniority_level"],
                "red_flags": result["red_flags"],
                "screening_decision": result["decision"],
                "screening_reason": result["decision_reason"],
            },
        }

    def score_resume_file(self, file_path: str, job_requirements: Dict) -> Dict:
        text = extract_text_from_file(Path(file_path))
        if not text or len(text) < 50:
            return {
                "error": "Could not extract text from {}".format(file_path),
                "overall_score": 0,
                "decision": "REJECT",
                "decision_reason": "Unreadable file",
            }
        result = self.screen_resume(text, job_requirements)
        result["file_path"] = str(file_path)
        return result

    def screen_resume_file(self, file_path: str, job_requirements: Dict) -> Dict:
        """Screen a resume file (PDF/DOCX/etc.) — full ATS pipeline."""
        text = extract_text_from_file(Path(file_path))
        if not text or len(text) < 50:
            return {
                "error": "Could not extract text from {}".format(file_path),
                "overall_score": 0,
                "decision": "REJECT",
                "decision_reason": "Unreadable file",
            }
        result = self.screen_resume(text, job_requirements)
        result["file_path"] = str(file_path)
        result["candidate"]["file"] = Path(file_path).name
        return result

    # ==================================================================
    # Ranking
    # ==================================================================

    def rank_resumes(self, resume_texts: List[str], job_requirements: Dict,
                     top_k: int = TOP_K_RESULTS) -> List[Dict]:
        results = []
        for idx, text in enumerate(resume_texts):
            try:
                r = self.screen_resume(text, job_requirements)
                r["resume_index"] = idx
                r["resume_preview"] = text[:200] + "..."
                results.append(r)
            except Exception as e:
                print("Error scoring resume {}: {}".format(idx, e))

        results.sort(key=lambda x: x["overall_score"], reverse=True)
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return results[:top_k]

    def rank_resume_files(self, file_paths: List[str], job_requirements: Dict,
                          top_k: int = TOP_K_RESULTS) -> List[Dict]:
        results = []
        for fp in file_paths:
            try:
                r = self.screen_resume_file(fp, job_requirements)
                if "error" not in r:
                    results.append(r)
            except Exception as e:
                print("Error scoring {}: {}".format(fp, e))

        results.sort(key=lambda x: x["overall_score"], reverse=True)
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return results[:top_k]

    # ==================================================================
    # Pretty-print screening result (for CLI / debugging)
    # ==================================================================

    def print_screening_result(self, result: Dict):
        """Print a human-readable screening report."""
        d = result.get("decision", "?")
        decision_colors = {"SHORTLIST": ">>", "REVIEW": "~~", "REJECT": "XX"}
        marker = decision_colors.get(d, "??")

        name = result.get("candidate", {}).get("name", "Unknown")
        score = result.get("overall_score", 0)

        print("\n" + "=" * 60)
        print("  [{marker}] {decision}  |  {name}  |  Score: {score}%".format(
            marker=marker, decision=d, name=name or "Unknown", score=score))
        print("=" * 60)

        # Decision reason
        print("  Reason: {}".format(result.get("decision_reason", "")))

        # Knockouts
        for ko in result.get("knockouts", []):
            print("  !! KNOCKOUT: {}".format(ko))

        # Score breakdown
        print("\n  Score Breakdown:")
        for key, val in result.get("breakdown", {}).items():
            bar = "#" * int(val / 5)
            print("    {:<25} {:>5.1f}%  {}".format(key, val, bar))

        # Candidate info
        cand = result.get("candidate", {})
        print("\n  Candidate:")
        if cand.get("name"):
            print("    Name:       {}".format(cand["name"]))
        if cand.get("email"):
            print("    Email:      {}".format(cand["email"]))
        print("    Experience: {} years".format(cand.get("years_of_experience", 0)))
        print("    Education:  {}".format(cand.get("education_level", "unknown")))
        print("    Seniority:  {}".format(cand.get("seniority_level", "unknown")))
        print("    Category:   {} ({:.0f}%)".format(
            cand.get("predicted_category", "?"),
            cand.get("category_confidence", 0) * 100))

        # Skills
        skills = result.get("skills", {})
        if skills.get("required_matched"):
            print("\n  Matched Required:  {}".format(", ".join(skills["required_matched"])))
        if skills.get("required_missing"):
            print("  Missing Required:  {}".format(", ".join(skills["required_missing"])))
        if skills.get("preferred_matched"):
            print("  Matched Preferred: {}".format(", ".join(skills["preferred_matched"])))

        # Red flags
        flags = result.get("red_flags", [])
        if flags:
            print("\n  Red Flags:")
            for rf in flags:
                sev = rf["severity"].upper()
                print("    [{}] {}".format(sev, rf["description"]))

        # Gaps
        gaps = result.get("employment_gaps", [])
        if gaps:
            print("\n  Employment Gaps:")
            for g in gaps:
                print("    {} - {} ({} months)".format(
                    g["after_year"], g["before_year"], g["months"]))

        print("  Resume Quality: {}%".format(result.get("resume_quality", 0)))
        print("=" * 60)


# ======================================================================
# CLI test
# ======================================================================

if __name__ == "__main__":
    print("ATS Screening Engine — Test\n")
    engine = ResumeScreeningEngine()

    # --- Test 1: Structured job requirements ---
    job = {
        "required_skills": ["python", "machine learning", "sql"],
        "preferred_skills": ["tensorflow", "docker", "aws"],
        "min_experience": 3,
        "max_experience": 10,
        "education_level": "bachelors",
        "seniority": "mid",
        "category": "technical",
    }

    sample_resume = """
    John Doe
    Software Engineer | 5 years experience
    john.doe@email.com | +1 555-123-4567

    Career Objective:
    Experienced software engineer seeking challenging ML role.

    Skills: Python, Java, Machine Learning, SQL, TensorFlow, Docker, Git
    Education: B.Tech Computer Science, MIT University (2018)

    Experience:
    - Senior Developer at TechCorp (2020-2025)
      Led ML pipeline development, deployed models to production.
    - Junior Developer at StartupXYZ (2018-2020)
      Built REST APIs, data processing pipelines.

    Certifications: AWS Certified Developer, TensorFlow Developer Certificate
    """

    print("\n--- Test 1: Structured job requirements ---")
    result = engine.screen_resume(sample_resume, job)
    engine.print_screening_result(result)

    # --- Test 2: Parse free-text job description ---
    jd_text = """
    Senior Python Developer — FinTech Company

    We are looking for a Senior Python Developer with 5+ years of experience
    in building scalable backend systems.

    Required Skills:
    - Python, Django, PostgreSQL, REST API
    - Docker, AWS, CI/CD

    Preferred:
    - Machine Learning, Kafka, Redis

    Education: Bachelor's degree in Computer Science or related field.

    Experience: Minimum 5 years in software development.
    """

    print("\n--- Test 2: Parse JD + screen ---")
    parsed_job = engine.parse_job_description(jd_text)
    print("Parsed JD:", json.dumps(parsed_job, indent=2))
    result2 = engine.screen_resume(sample_resume, parsed_job)
    engine.print_screening_result(result2)
