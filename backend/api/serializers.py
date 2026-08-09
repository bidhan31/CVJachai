"""
Serializers for Resume Classifier API.
"""

from rest_framework import serializers

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.zip', '.png', '.jpg', '.jpeg'}
MAX_FILES = 1000              # Max number of resume files per request
MAX_JOB_CIRCULAR_LENGTH = 10_000  # Characters
MAX_TOP_K = 100
MAX_MIN_EXPERIENCE = 50      # Years
MAX_SKILLS_COUNT = 50
MAX_SKILL_LENGTH = 100       # Characters per individual skill


class ResumeUploadSerializer(serializers.Serializer):
    """Serializer for resume file uploads with full input validation."""

    job_circular = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text=f"Job description text (max {MAX_JOB_CIRCULAR_LENGTH} characters)",
    )
    resume_files = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        help_text=f"Resume files (PDF, DOCX, TXT, or ZIP). Max {MAX_FILES} files, no size limit.",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=MAX_TOP_K,
        help_text=f"Number of top candidates to return (1–{MAX_TOP_K}, default 5)",
    )
    skills = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text=f"Comma-separated required skills (max {MAX_SKILLS_COUNT} skills)",
    )
    min_experience = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        max_value=MAX_MIN_EXPERIENCE,
        help_text=f"Minimum years of experience (0–{MAX_MIN_EXPERIENCE})",
    )
    min_score = serializers.FloatField(
        required=False,
        default=0.0,
        min_value=0.0,
        max_value=1.0,
        help_text=(
            "Minimum final_score threshold (0.0–1.0, default 0.0). "
            "Resumes scoring below this value are excluded. "
            "If no resume meets this threshold, a 'no_candidates_found' response is returned."
        ),
    )

    # ------------------------------------------------------------------ #
    # Field-level validators                                               #
    # ------------------------------------------------------------------ #

    def validate_job_circular(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("job_circular cannot be blank.")
        if len(value) > MAX_JOB_CIRCULAR_LENGTH:
            raise serializers.ValidationError(
                f"job_circular is too long ({len(value)} chars). "
                f"Maximum allowed is {MAX_JOB_CIRCULAR_LENGTH} characters."
            )
        return value

    def validate_resume_files(self, files: list) -> list:
        if not files:
            raise serializers.ValidationError("At least one resume file is required.")

        if len(files) > MAX_FILES:
            raise serializers.ValidationError(
                f"Too many files uploaded ({len(files)}). Maximum is {MAX_FILES}."
            )

        errors = []
        for f in files:
            # --- Extension check ---
            name = getattr(f, 'name', '') or ''
            ext = ('.' + name.rsplit('.', 1)[-1]).lower() if '.' in name else ''
            if ext not in ALLOWED_EXTENSIONS:
                errors.append(
                    f"'{name}': unsupported format '{ext}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
                )
                continue



        if errors:
            raise serializers.ValidationError(errors)

        return files

    def validate_skills(self, value: str) -> str:
        if not value:
            return value

        skills = [s.strip() for s in value.split(',') if s.strip()]

        if len(skills) > MAX_SKILLS_COUNT:
            raise serializers.ValidationError(
                f"Too many skills provided ({len(skills)}). Maximum is {MAX_SKILLS_COUNT}."
            )

        long_skills = [s for s in skills if len(s) > MAX_SKILL_LENGTH]
        if long_skills:
            raise serializers.ValidationError(
                f"The following skills exceed the {MAX_SKILL_LENGTH}-character limit: "
                + ', '.join(f"'{s}'" for s in long_skills)
            )

        return value

class JobSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        from .models import Job
        model = Job
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'is_active')

class ApplicationSerializer(serializers.ModelSerializer):
    resume_download_url = serializers.SerializerMethodField()

    class Meta:
        from .models import Application
        model = Application
        fields = ('id', 'job', 'candidate_name', 'candidate_email', 'resume_file', 'resume_download_url', 'applied_at', 'match_score', 'analysis_data')
        read_only_fields = ('applied_at', 'match_score', 'analysis_data')

    def get_resume_download_url(self, obj):
        if not obj.resume_file:
            return None
        
        request = self.context.get('request')
        file_url = obj.resume_file.url
        
        # If it's a Cloudinary URL, we can add 'fl_attachment' to force download
        if 'res.cloudinary.com' in file_url:
            # Cloudinary raw files use /raw/upload/. We insert fl_attachment after /upload/
            if '/upload/' in file_url:
                return file_url.replace('/upload/', '/upload/fl_attachment/')
            return file_url

        # If it's a local URL, we use our backend's media serve view which forces download
        if not file_url.startswith('http') and request:
            # Convert /media/path/to/file to /media/path/to/file
            # The urls.py already handles /media/<path> with as_attachment=True
            return request.build_absolute_uri(file_url)
        
        return file_url
