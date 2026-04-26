from pathlib import Path


# =========================
# Chemins projet
# =========================

# Racine du projet : cv-tailor-v1/
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# Dossiers
# =========================

DATA_DIR = BASE_DIR / "data"
REFERENCE_DIR = DATA_DIR / "reference"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

TEMPLATES_DIR = BASE_DIR / "templates"


# =========================
# Fichiers principaux
# =========================

MASTER_PROFILE_PATH = REFERENCE_DIR / "master_profile.xlsx"
BASE_CV_TEMPLATE_PATH = TEMPLATES_DIR / "base_cv.docx"
JOB_DESCRIPTION_PATH = INPUT_DIR / "job_description.txt"


# =========================
# Fichiers optionnels / futurs
# =========================

APPLICATION_TRACKER_PATH = DATA_DIR / "application_tracker.xlsx"
RAW_JOB_URLS_PATH = INPUT_DIR / "job_urls.txt"


# =========================
# Paramètres génération CV
# =========================

DEFAULT_MAX_EXPERIENCES = 2
DEFAULT_MAX_LEADERSHIP = 1
DEFAULT_MAX_CERTIFICATIONS = 2
DEFAULT_MAX_TECHNICAL_SKILLS = 8

MAX_FILENAME_LENGTH = 115


# =========================
# Création automatique des dossiers
# =========================

def ensure_project_directories():
    directories = [
        DATA_DIR,
        REFERENCE_DIR,
        INPUT_DIR,
        OUTPUT_DIR,
        TEMPLATES_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


ensure_project_directories()