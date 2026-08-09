import logging
import os
import re
import base64
import tempfile
import zipfile
import concurrent.futures
from pathlib import Path

from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF {pdf_path}: {e}")


def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = Document(docx_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception as e:
        raise Exception(f"Error extracting text from DOCX {docx_path}: {e}")


def extract_text_from_txt(txt_path: str) -> str:
    """Extract text from a TXT file."""
    try:
        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
    except Exception as e:
        raise Exception(f"Error extracting text from TXT {txt_path}: {e}")


def extract_text_from_image(img_path: str) -> str:
    """Extract text from an image using Groq Vision (Ultra-fast Cloud AI)."""
    try:
        from engine.groq import groq_base
        
        # Read and encode image to base64
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Call Groq Vision
        prompt = "Transcript the text in this resume image exactly. Return ONLY the text."
        text = groq_base.call_vision(prompt, encoded_string)
        
        if not text:
            logger.error("Groq Vision returned empty text for %s. Check API key and model availability.", img_path)
            return ""

        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from IMG {img_path} via Groq: {e}")
        return ""


def extract_text_from_file(file_path: str) -> str:
    """Route to appropriate extraction function based on file extension."""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    elif ext in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """
    Extract text from raw bytes (e.g. downloaded from Cloudinary URL).
    Uses a temp file internally so existing extractors can be reused.
    """
    ext = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        return extract_text_from_file(tmp_path)
    finally:
        os.unlink(tmp_path)


def extract_resumes_from_zip(zip_path: str, temp_dir: str) -> dict[str, str]:
    """
    Extract all resumes from a ZIP file.
    Returns dict: {filename: file_path}
    """
    resumes = {}
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Walk through extracted files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in ['.pdf', '.docx', '.txt']:
                    file_path = os.path.join(root, file)
                    resumes[file] = file_path
        
        return resumes
    except Exception as e:
        raise Exception(f"Error extracting ZIP file: {e}")


def process_resume_files(files: list, temp_dir: str = None) -> dict[str, str]:
    """
    Process multiple resume files (can be mixed types: PDF, DOCX, TXT).
    Returns dict: {filename: file_path}
    """
    resumes = {}
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    for file in files:
        filename = os.path.basename(file.name)
        temp_path = os.path.join(temp_dir, filename)
        with open(temp_path, 'wb') as f:
            f.write(file.read())
        
        ext = Path(filename).suffix.lower()
        
        # If it's a ZIP, extract contents
        if ext == '.zip':
            extracted = extract_resumes_from_zip(temp_path, temp_dir)
            resumes.update(extracted)
        elif ext in ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']:
            resumes[filename] = temp_path
        else:
            raise ValueError(f"Unsupported file format: {filename}")
    
    return resumes


def extract_all_resume_texts(resumes: dict[str, str]) -> dict[str, str]:
    """
    Extract text from all resume files using multi-threading.
    Returns dict: {filename: extracted_text}
    """
    logger.info("Starting ultra-fast text extraction using Multi-Threading for %d files...", len(resumes))
    resume_texts = {}
    
    def _extract_single(filename, file_path):
        try:
            return filename, extract_text_from_file(file_path)
        except Exception as e:
            logger.warning("Could not extract text from %s: %s", filename, e)
            return filename, ""

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {executor.submit(_extract_single, fname, fpath): fname for fname, fpath in resumes.items()}
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            fname, text = future.result()
            if text:
                resume_texts[fname] = text
            if i % 50 == 0:
                logger.info("... extracted %d/%d files ...", i, len(resumes))
    
    logger.info("Completed text extraction. Valid decoded files: %d", len(resume_texts))
    return resume_texts


def calculate_skill_bonus(resume_text: str, skills: list, min_experience: int = 0) -> float:
    """
    Calculate bonus score based on skills and experience found in resume.
    Returns a score between 0.0 and 1.0.
    """
    bonus = 0.0
    resume_lower = resume_text.lower()

    if skills:
        found = sum(1 for s in skills if s.lower() in resume_lower)
        bonus += (found / len(skills)) * 0.5

    if min_experience > 0:
        for yrs in range(min_experience, min_experience + 20):
            if f"{yrs} years" in resume_lower or f"{yrs}+ years" in resume_lower:
                bonus += 0.3
                break

    return min(bonus, 1.0)


# Common short stopwords to ignore when comparing texts
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "that", "this", "these",
    "those", "it", "its", "into", "as", "up", "if", "then", "than",
    "so", "not", "no", "also", "any", "all", "more", "other",
}


def _meaningful_words(text: str) -> set[str]:
    """Lowercase word tokens, 3+ chars, stripped of stopwords."""
    return {
        w for w in text.lower().split()
        if len(w) >= 3 and w not in _STOPWORDS
    }



def calculate_job_relevance(resume_text: str, job_circular: str) -> float:
    """
    Calculate keyword-overlap relevance between a resume and a job circular.
    Returns a score between 0.0 and 1.0.
    """
    job_words = _meaningful_words(job_circular)
    resume_words = _meaningful_words(resume_text)
    if not job_words:
        return 0.0
    overlap = job_words & resume_words
    return len(overlap) / len(job_words)


def extract_contact_info(text: str) -> dict:
    """Extract basic contact info like name, email, and phone using regex."""
    # Email regex
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = emails[0] if emails else "N/A"
    
    # Phone regex (basic)
    phones = re.findall(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)
    phone = phones[0] if phones else "N/A"
    
    # Name extraction (Heuristic: First non-empty line usually contains the name)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    name = lines[0] if lines else "Unknown"
    
    return {
        "name": name,
        "email": email,
        "phone": phone
    }
