"""
Configuration for Resume Screening System
"""

from pathlib import Path

# ==================== Paths ====================
PROJECT_ROOT = Path(__file__).parent
DATASET_DIR = PROJECT_ROOT / "dataset"               # Root of ALL data sources
PROCESSED_DATA_DIR = PROJECT_ROOT / "processed_data"
PROCESSED_DATA_DIR.mkdir(exist_ok=True)
MODEL_SAVE_DIR = PROJECT_ROOT / "models"
MODEL_SAVE_DIR.mkdir(exist_ok=True)

# ==================== Dynamic Categories ====================
# Categories are NOT hardcoded. They are discovered automatically:
#   - From folder names inside dataset/ (folder name = category)
#   - From CSV column values (category/position column = category)
# Just drop resumes into  dataset/<YourCategory>/  and run create_dataset.py.
# The training pipeline reads categories from the processed data.
# The inference engine reads categories from the saved model metadata.

# Supported resume file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}

# ==================== Seniority Detection ====================
# Keywords that indicate seniority level (checked in order, highest first)
SENIORITY_LEVELS = {
    "executive": {
        "score": 6,
        "titles": [
            "ceo", "cto", "cfo", "coo", "ciso", "cmo", "cio",
            "chief executive", "chief technology", "chief financial",
            "chief operating", "chief information", "chief marketing",
            "president", "vice president", "vp ", "svp", "evp",
            "managing director", "general manager", "partner",
            "founder", "co-founder", "owner", "chairman",
        ],
        "min_experience": 15,
    },
    "director": {
        "score": 5,
        "titles": [
            "director", "head of", "global head", "regional head",
            "associate director", "assistant director",
            "program director", "department head",
        ],
        "min_experience": 10,
    },
    "senior": {
        "score": 4,
        "titles": [
            "senior ", "sr.", "sr ", "lead ", "staff ",
            "principal", "senior manager", "team lead",
            "senior engineer", "senior developer", "senior analyst",
            "senior consultant", "senior architect",
            "senior specialist", "senior associate",
        ],
        "min_experience": 6,
    },
    "mid": {
        "score": 3,
        "titles": [
            "manager", "supervisor", "specialist",
            "coordinator", "consultant", "engineer",
            "developer", "analyst", "designer",
            "administrator", "associate",
        ],
        "min_experience": 3,
    },
    "junior": {
        "score": 2,
        "titles": [
            "junior ", "jr.", "jr ", "associate ",
            "assistant ", "entry level", "entry-level",
            "graduate ", "fresher",
        ],
        "min_experience": 1,
    },
    "entry": {
        "score": 1,
        "titles": [
            "intern", "trainee", "apprentice",
            "student", "probation", "volunteer",
        ],
        "min_experience": 0,
    },
}

# ==================== Resume Quality Scoring ====================
# What a COMPLETE, professional resume should have (weights sum to 100)
QUALITY_CRITERIA = {
    "has_name":            8,   # Candidate name identifiable
    "has_email":           8,   # Contact email present
    "has_phone":           6,   # Phone number present
    "has_education":       12,  # Education section present
    "has_experience":      15,  # Work experience present
    "has_skills":          12,  # Skills listed
    "has_objective":       5,   # Career objective / summary
    "has_certifications":  5,   # Professional certifications
    "word_count_ok":       8,   # Not too short (<100) or too long (>5000)
    "multiple_sections":   8,   # Has 3+ sections (structured resume)
    "recent_experience":   8,   # Has recent work dates (not outdated)
    "no_red_flags":        5,   # No major red flags detected
}

# ==================== Red Flag Detection ====================
RED_FLAG_RULES = {
    "job_hopping": {
        "description": "Too many short-tenure jobs (<1 year each)",
        "severity": "medium",
    },
    "long_gap": {
        "description": "Employment gap > 2 years",
        "severity": "medium",
    },
    "no_contact": {
        "description": "No email or phone number found",
        "severity": "high",
    },
    "very_short": {
        "description": "Resume is extremely short (<100 words)",
        "severity": "high",
    },
    "no_experience": {
        "description": "No work experience or dates found",
        "severity": "low",
    },
    "overqualified": {
        "description": "Candidate appears significantly overqualified",
        "severity": "low",
    },
}

# ==================== Screening Decision Thresholds ====================
SCREENING_THRESHOLDS = {
    "shortlist":       70,  # Score >= 70 → SHORTLIST (interview)
    "maybe":           50,  # Score 50-69 → REVIEW (manual check)
    "reject":           0,  # Score < 50  → REJECT (auto-decline)
}

# Knockout criteria — any of these = immediate REJECT regardless of score
KNOCKOUT_CRITERIA = {
    "min_required_skills_pct": 0.40,  # Must match >= 40% of required skills
    "min_education_met":       True,  # Must meet minimum education if specified
    "max_experience_gap":      5,     # Can't be >5 years below minimum experience
}

# ==================== Scoring Weights ====================
# How much each factor contributes to overall score (must sum to 1.0)
SCORING_WEIGHTS = {
    "required_skills":    0.30,
    "experience":         0.20,
    "education":          0.12,
    "preferred_skills":   0.10,
    "category_match":     0.10,
    "seniority_match":    0.08,
    "resume_quality":     0.05,
    "certifications":     0.05,
}

# ==================== Feature Extraction ====================
# Comprehensive skills database for resume screening

TECHNICAL_SKILLS = [
    # ---- Programming Languages ----
    "python", "java", "javascript", "c++", "c#", "php", "ruby", "swift",
    "kotlin", "typescript", "golang", "rust", "scala", "perl", "r",
    "matlab", "fortran", "cobol", "lua", "dart", "elixir", "haskell",
    "objective-c", "visual basic", "assembly", "groovy", "clojure",
    "shell scripting", "bash", "powershell", "vba",

    # ---- Web Development ----
    "html", "css", "react", "angular", "vue", "node.js", "django", "flask",
    "spring", "express", "nextjs", "bootstrap", "tailwind", "jquery",
    "sass", "less", "webpack", "graphql", "rest api", "soap",
    "wordpress", "drupal", "joomla", "magento", "shopify",
    "asp.net", "laravel", "ruby on rails", "svelte", "nuxtjs",
    "gatsby", "remix", "fastapi", "strapi",

    # ---- Mobile Development ----
    "android", "ios", "react native", "flutter", "xamarin", "ionic",
    "swiftui", "jetpack compose", "cordova", "pwa",

    # ---- Data / ML / AI ----
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data analysis", "data science", "big data", "hadoop", "spark", "kafka",
    "power bi", "tableau", "matplotlib", "seaborn", "plotly",
    "data mining", "data warehousing", "etl", "data modeling",
    "neural networks", "reinforcement learning", "generative ai",
    "langchain", "llm", "chatgpt", "openai", "hugging face",
    "apache airflow", "dbt", "snowflake", "databricks", "looker",
    "sas", "spss", "stata", "jupyter", "r studio",

    # ---- Cloud / DevOps / Infrastructure ----
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform",
    "ansible", "ci/cd", "linux", "git", "github", "gitlab", "bitbucket",
    "nginx", "apache", "tomcat", "iis",
    "cloudformation", "pulumi", "vagrant", "chef", "puppet",
    "prometheus", "grafana", "datadog", "splunk", "elk stack",
    "microservices", "serverless", "lambda", "cloud computing",
    "load balancing", "cdn", "dns", "ssl", "vpn",

    # ---- Databases ----
    "oracle", "sql server", "mariadb", "cassandra", "dynamodb",
    "couchdb", "neo4j", "hbase", "memcached", "sqlite",
    "firebase", "supabase", "cockroachdb", "timescaledb",

    # ---- Cybersecurity ----
    "cybersecurity", "penetration testing", "ethical hacking",
    "network security", "information security", "siem",
    "firewall", "ids", "ips", "encryption", "ssl/tls",
    "owasp", "vulnerability assessment", "soc", "incident response",
    "malware analysis", "forensics", "compliance", "gdpr",

    # ---- Networking / IT ----
    "networking", "tcp/ip", "dhcp", "routing", "switching",
    "lan", "wan", "wifi", "voip", "active directory",
    "windows server", "vmware", "hyper-v", "citrix",
    "helpdesk", "troubleshooting", "system administration",
    "it support", "hardware", "software installation",

    # ---- Finance / Accounts ----
    "tally", "sap", "quickbooks", "erp", "gst", "tds", "ifrs",
    "accounting", "auditing", "payroll", "taxation", "bookkeeping",
    "financial analysis", "budgeting", "cost accounting", "accounts payable",
    "accounts receivable", "bank reconciliation", "balance sheet",
    "financial reporting", "gaap", "profit and loss", "cash flow",
    "invoice", "ledger", "journal entries", "trial balance",
    "fixed assets", "depreciation", "working capital", "variance analysis",
    "hedge accounting", "risk management", "credit analysis",
    "mutual funds", "stock market", "forex", "derivatives",
    "financial modeling", "valuation", "due diligence", "mergers",
    "insurance", "underwriting", "claims processing",
    "bloomberg", "reuters", "fintech", "blockchain", "cryptocurrency",

    # ---- Admin / Office ----
    "ms office", "microsoft office", "excel", "word", "powerpoint",
    "outlook", "google workspace", "sharepoint", "typing",
    "data entry", "filing", "scheduling", "calendar management",
    "office management", "front desk", "reception",
    "inventory management", "procurement", "vendor management",
    "travel management", "event management", "facility management",
    "record keeping", "correspondence", "minute taking",
    "proofreading", "document management", "archiving",
    "google docs", "google sheets", "notion", "trello", "asana",
    "jira", "slack", "microsoft teams", "zoom", "confluence",

    # ---- Research / Academic ----
    "research methodology", "statistical analysis",
    "latex", "publication", "peer review", "grant writing",
    "literature review", "experimental design",
    "qualitative research", "quantitative research", "mixed methods",
    "survey design", "sampling", "hypothesis testing",
    "regression analysis", "anova", "chi-square", "t-test",
    "meta-analysis", "systematic review", "case study",
    "clinical trials", "research ethics", "irb", "thesis",
    "dissertation", "academic writing", "citation", "bibliography",

    # ---- Healthcare / Medical ----
    "patient care", "nursing", "clinical", "diagnosis", "treatment",
    "medical records", "emr", "ehr", "epic", "cerner",
    "pharmacy", "pharmacology", "drug administration",
    "vital signs", "blood pressure", "ecg", "x-ray", "mri", "ct scan",
    "ultrasound", "pathology", "radiology", "anesthesia",
    "surgery", "icu", "emergency medicine", "first aid", "cpr", "bls",
    "acls", "infection control", "sterilization", "hipaa",
    "physiotherapy", "occupational therapy", "speech therapy",
    "mental health", "counseling", "psychology", "psychiatry",
    "public health", "epidemiology", "biostatistics",
    "nutrition", "dietetics", "lab testing", "microbiology",
    "anatomy", "physiology", "dental", "optometry", "veterinary",
    "medical coding", "medical billing", "icd-10", "cpt codes",
    "health insurance", "telemedicine", "ayurveda", "homeopathy",

    # ---- Legal / Law ----
    "legal research", "litigation", "contract law", "corporate law",
    "criminal law", "civil law", "constitutional law", "family law",
    "intellectual property", "patent", "trademark", "copyright",
    "labor law", "employment law", "immigration law", "tax law",
    "real estate law", "environmental law", "banking law",
    "legal drafting", "legal writing", "brief writing",
    "case management", "court filing", "deposition",
    "arbitration", "mediation", "dispute resolution",
    "compliance", "regulatory", "governance", "due diligence",
    "legal aid", "paralegal", "notary", "power of attorney",
    "nda", "sla", "mou",

    # ---- Marketing / Sales / HR ----
    "digital marketing", "seo", "sem", "ppc", "google ads",
    "facebook ads", "social media marketing", "content marketing",
    "email marketing", "affiliate marketing", "influencer marketing",
    "brand management", "market research", "competitive analysis",
    "google analytics", "hubspot", "salesforce", "mailchimp",
    "crm", "lead generation", "conversion optimization",
    "copywriting", "content writing", "blogging", "video marketing",
    "public relations", "advertising", "media planning",
    "sales management", "business development", "account management",
    "cold calling", "b2b", "b2c", "retail", "e-commerce",
    "merchandising", "visual merchandising", "store management",
    "recruitment", "talent acquisition", "onboarding",
    "performance management", "employee relations", "hr policies",
    "compensation", "benefits administration", "hris",
    "succession planning", "workforce planning", "training",
    "learning and development", "organizational development",

    # ---- Engineering / Manufacturing ----
    "mechanical engineering", "electrical engineering", "civil engineering",
    "chemical engineering", "industrial engineering",
    "cad", "autocad", "solidworks", "catia", "ansys", "revit",
    "3d modeling", "3d printing", "prototyping",
    "manufacturing", "production planning", "quality control",
    "quality assurance", "iso 9001", "six sigma", "lean manufacturing",
    "supply chain", "logistics", "warehouse management",
    "project planning", "gantt chart", "primavera", "ms project",
    "bom", "mrp", "erp", "plc", "scada", "automation",
    "robotics", "mechatronics", "embedded systems", "iot",
    "pcb design", "circuit design", "vlsi", "fpga",
    "hvac", "plumbing", "welding", "cnc", "machining",
    "structural analysis", "surveying", "gis", "construction",
    "safety", "osha", "environmental management",
    "renewable energy", "solar", "wind energy", "power systems",
    "petroleum engineering", "mining", "geology",

    # ---- Education / Teaching ----
    "curriculum development", "lesson planning", "classroom management",
    "student assessment", "grading", "tutoring",
    "special education", "inclusive education", "differentiated instruction",
    "educational technology", "e-learning", "lms", "moodle", "canvas",
    "pedagogy", "andragogy", "blended learning", "online teaching",
    "examination", "question paper", "syllabus design",
    "school administration", "principal", "counselor",
    "training and development", "corporate training", "workshop facilitation",
    "professional development", "accreditation",

    # ---- Design / Creative ----
    "graphic design", "ui/ux", "photoshop", "illustrator", "figma",
    "sketch", "indesign", "after effects", "premiere pro",
    "video editing", "animation", "motion graphics",
    "photography", "videography", "branding", "logo design",
    "typography", "color theory", "wireframing",
    "user research", "usability testing", "interaction design",
    "responsive design", "accessibility",
    "canva", "coreldraw", "blender", "maya", "cinema 4d",

    # ---- Miscellaneous ----
    "agile", "scrum", "kanban", "waterfall", "prince2",
    "business analysis", "requirements gathering",
    "process improvement", "risk assessment",
    "technical writing", "documentation", "api documentation",
    "testing", "manual testing", "automation testing", "selenium",
    "junit", "pytest", "cypress", "postman", "swagger",
    "performance testing", "load testing", "jmeter",
    "version control", "code review", "pair programming",
    "oracle erp", "microsoft dynamics", "odoo",
    "bi tools", "reporting", "dashboard",
]

SOFT_SKILLS = [
    # ---- Communication ----
    "communication", "verbal communication", "written communication",
    "public speaking", "presentation", "storytelling",
    "active listening", "persuasion", "influence",

    # ---- Leadership & Management ----
    "leadership", "team leadership", "people management",
    "delegation", "motivation", "coaching", "mentoring",
    "strategic planning", "vision", "change management",
    "decision making", "conflict resolution", "mediation",

    # ---- Teamwork & Collaboration ----
    "teamwork", "collaboration", "cross-functional",
    "stakeholder management", "relationship building",
    "interpersonal", "cultural awareness", "diversity",

    # ---- Problem Solving & Thinking ----
    "problem solving", "critical thinking", "analytical",
    "logical thinking", "creativity", "innovation",
    "design thinking", "systems thinking", "research minded",

    # ---- Organization & Productivity ----
    "time management", "project management", "prioritization",
    "multitasking", "attention to detail", "accuracy",
    "organizational", "planning", "goal setting",
    "deadline management", "self-motivated", "initiative",

    # ---- Adaptability ----
    "adaptability", "flexibility", "resilience",
    "stress management", "work under pressure",
    "continuous learning", "growth mindset", "open minded",

    # ---- Customer & Service ----
    "customer service", "client management", "empathy",
    "patience", "service oriented", "customer satisfaction",

    # ---- Ethics & Professionalism ----
    "integrity", "accountability", "professionalism",
    "work ethic", "reliability", "dependability",
    "confidentiality", "ethical", "trustworthy",

    # ---- Negotiation & Business ----
    "negotiation", "contract negotiation", "deal closing",
    "business acumen", "commercial awareness", "entrepreneurship",
    "networking", "rapport building",
]

EDUCATION_LEVELS = {
    # Doctorate level (6)
    "phd": 6, "doctorate": 6, "ph.d": 6, "d.phil": 6,
    "doctor of philosophy": 6, "dba": 6, "d.sc": 6, "d.litt": 6,
    "m.d.": 6, "doctor of medicine": 6, "juris doctor": 6,
    "edd": 6, "doctor of education": 6, "j.d.": 6,

    # Masters level (5)
    "master": 5, "mba": 5, "msc": 5, "m.sc": 5, "m.tech": 5, "mca": 5,
    "m.a": 5, "m.com": 5, "m.ed": 5, "postgraduate": 5,
    "m.phil": 5, "m.arch": 5, "m.des": 5, "m.pharm": 5,
    "masters degree": 5, "post graduation": 5, "pg diploma": 5,
    "mba degree": 5, "ms degree": 5, "ma degree": 5,
    "llm": 5, "msw": 5, "mph": 5, "mfa": 5, "mem": 5,

    # Bachelors level (4)
    "bachelor": 4, "bsc": 4, "b.sc": 4, "b.tech": 4, "bca": 4,
    "b.a": 4, "b.com": 4, "b.ed": 4, "bba": 4, "undergraduate": 4,
    "b.arch": 4, "b.des": 4, "b.pharm": 4, "bds": 4, "mbbs": 4,
    "b.e.": 4, "b.e": 4, "llb": 4, "bsw": 4, "bpt": 4,
    "honours": 4, "honors": 4, "graduation": 4,
    "bachelors degree": 4, "bachelor degree": 4, "ug degree": 4,

    # Diploma level (3)
    "diploma": 3, "polytechnic": 3, "advanced diploma": 3,
    "post diploma": 3, "graduate diploma": 3,
    "professional diploma": 3, "technical diploma": 3,
    "iti": 3, "industrial training": 3, "vocational": 3,
    "associate degree": 3, "foundation degree": 3,
    "certificate course": 3, "certification program": 3,

    # Higher Secondary (2)
    "hsc": 2, "12th": 2, "higher secondary": 2, "intermediate": 2,
    "plus two": 2, "+2": 2, "pre-university": 2, "puc": 2,
    "a-level": 2, "a level": 2, "class 12": 2, "xii": 2,
    "senior secondary": 2, "high school diploma": 2,

    # Secondary (1)
    "ssc": 1, "10th": 1, "secondary": 1, "matriculation": 1,
    "class 10": 1, "class x": 1, "o-level": 1, "o level": 1,
    "board exam": 1, "high school": 1, "10th pass": 1,
}

CERTIFICATIONS = [
    # ---- Finance / Accounting ----
    "cpa", "cma", "cfa", "ca", "icwa", "acca", "cia", "cfp",
    "enrolled agent", "caia", "frm", "chartered accountant",

    # ---- Project Management ----
    "pmp", "prince2", "scrum master", "agile", "csm", "psm",
    "capm", "pgmp", "safe", "pmi-acp", "itil",
    "six sigma green belt", "six sigma black belt", "lean six sigma",

    # ---- Cloud & IT ----
    "aws certified", "azure certified", "google certified",
    "aws solutions architect", "aws developer", "aws sysops",
    "azure administrator", "azure developer", "azure architect",
    "gcp professional", "gcp associate",
    "cisco", "ccna", "ccnp", "ccie", "comptia",
    "comptia a+", "comptia network+", "comptia security+",
    "comptia cloud+", "comptia linux+",
    "red hat", "rhce", "rhcsa",
    "vmware", "vcp", "vcap",

    # ---- Cybersecurity ----
    "cissp", "cism", "cisa", "ceh", "oscp", "gsec",
    "security+", "cysa+", "pentest+", "sscp",

    # ---- Data & Analytics ----
    "google data analytics", "ibm data science",
    "microsoft data analyst", "tableau certified",
    "databricks certified", "snowflake certified",
    "cloudera certified", "sas certified",

    # ---- Development ----
    "oracle certified", "java certified", "microsoft certified",
    "salesforce certified", "sap certified",
    "istqb", "selenium certified",

    # ---- Healthcare / Medical ----
    "bls", "acls", "pals", "nrp", "cna", "rn", "lpn",
    "medical license", "nursing license", "pharmacy license",
    "first aid certified", "cpr certified",

    # ---- Education ----
    "tefl", "tesol", "celta", "delta", "b.ed", "d.el.ed",
    "teaching license", "ugc net", "set", "tet", "ctet",

    # ---- Legal ----
    "bar exam", "bar council", "advocate license",

    # ---- Quality & Standards ----
    "iso 9001", "iso 14001", "iso 27001", "iso 45001",
    "cmmi", "cobit", "togaf",

    # ---- HR ----
    "shrm", "phr", "sphr", "cipd",

    # ---- Marketing / Digital ----
    "google ads certified", "hubspot certified",
    "facebook blueprint", "hootsuite certified",

    # ---- General ----
    "ielts", "toefl", "gre", "gmat", "sat", "cat", "gate",
    "upsc", "civil services", "bank exam", "ssc exam",
]

# ==================== Inference ====================
TOP_K_RESULTS = 10
