from pathlib import Path
from datetime import datetime

from src.loaders.excel_loader import ExcelProfileLoader
from src.parsers.job_parser import parse_job_description
from src.selectors.profile_selector import (
    select_top_experiences,
    select_top_leadership,
    select_certifications,
    select_technical_skills,
    build_replacements_from_selection,
)
from src.render.docx_template import DocxTemplateRenderer


BASE_DIR = Path(__file__).resolve().parent.parent

MASTER_PROFILE_PATH = BASE_DIR / "data" / "reference" / "master_profile.xlsx"
BASE_CV_TEMPLATE_PATH = BASE_DIR / "templates" / "base_cv.docx"
OUTPUT_DIR = BASE_DIR / "data" / "output"


SAMPLE_JOB_DESCRIPTION = """
Operations & Supply Chain Analyst - Ipsen

Ipsen recherche un profil capable de piloter des opérations supply chain,
coordonner des flux import-export, suivre les stocks, améliorer les processus,
produire des reportings KPI, créer des dashboards, utiliser Excel, SQL, Python,
Power BI ou Looker, et travailler avec des équipes commerciales, logistiques
et opérationnelles.

Localisation : Boulogne-Billancourt, Île-de-France

Missions :
- Analyse de performance opérationnelle
- Suivi des stocks et des flux
- Forecast de la demande
- Coordination fournisseurs et partenaires
- Reporting hebdomadaire
- Optimisation des processus
- Gestion des risques opérationnels
"""


def clean_filename(value):
    """
    Nettoie une valeur pour créer un nom de fichier propre.
    Exemple :
    Operations & Supply Chain Analyst -> Operations_and_Supply_Chain_Analyst
    """
    value = str(value).strip()

    if not value:
        return "Non_renseigne"

    replacements = {
        "&": "and",
        "/": "-",
        "\\": "-",
        ":": "-",
        ";": "-",
        ",": "",
        ".": "",
        "’": "",
        "'": "",
        "(": "",
        ")": "",
        "[": "",
        "]": "",
        "{": "",
        "}": "",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "à": "a",
        "â": "a",
        "ä": "a",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "ö": "o",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
        "É": "E",
        "È": "E",
        "Ê": "E",
        "À": "A",
        "Ç": "C",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = value.replace(" ", "_")

    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    value = "".join(char for char in value if char in allowed)

    while "__" in value:
        value = value.replace("__", "_")

    while "--" in value:
        value = value.replace("--", "-")

    return value.strip("_-")


def build_output_filename(parsed_job):
    """
    Génère un nom de fichier propre avec :
    - nom candidat
    - entreprise
    - intitulé du poste
    - date
    """
    candidate_name = "Lucas_Pertusa"

    company = parsed_job.get("company", "")
    job_title = parsed_job.get("job_title", "")

    if not company:
        company = "Entreprise"

    if not job_title:
        job_title = "Poste"

    company_clean = clean_filename(company)
    job_title_clean = clean_filename(job_title)
    date_stamp = datetime.now().strftime("%Y%m%d")

    filename = f"CV_{candidate_name}_{company_clean}_{job_title_clean}_{date_stamp}.docx"

    return filename


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    loader = ExcelProfileLoader(MASTER_PROFILE_PATH)
    workbook = loader.load()

    experiences_df = workbook.get("experiences")
    leadership_df = workbook.get("leadership")
    certifications_df = workbook.get("certifications")
    skills_df = workbook.get("skills")

    parsed_job = parse_job_description(SAMPLE_JOB_DESCRIPTION)
    job_text = SAMPLE_JOB_DESCRIPTION

    selected_experiences = select_top_experiences(
        experiences_df=experiences_df,
        job_text=job_text,
        max_items=2,
    )

    selected_leadership = select_top_leadership(
        leadership_df=leadership_df,
        job_text=job_text,
        max_items=1,
    )

    selected_certs = select_certifications(
        certifications_df=certifications_df,
        job_text=job_text,
    )

    technical_skills = select_technical_skills(
        skills_df=skills_df,
        job_text=job_text,
        max_items=8,
    )

    replacements = build_replacements_from_selection(
        experiences=selected_experiences,
        leadership_items=selected_leadership,
        certs=selected_certs,
        technical_skills=technical_skills,
        job_text=job_text,
    )

    output_filename = build_output_filename(parsed_job)
    output_path = OUTPUT_DIR / output_filename

    renderer = DocxTemplateRenderer(BASE_CV_TEMPLATE_PATH)
    renderer.render(replacements, output_path)

    print(f"DOCX generated: {output_path}")

    print("\nParsed job:")
    print(f"- Company: {parsed_job.get('company', '')}")
    print(f"- Job title: {parsed_job.get('job_title', '')}")
    print(f"- Location: {parsed_job.get('location', '')}")
    print(f"- Keywords: {', '.join(parsed_job.get('keywords', [])[:10])}")

    print("\nSelected experiences:")
    for row in selected_experiences:
        company = row.get("company", row.get("organization", ""))
        title = row.get("job_title", row.get("position_title", ""))
        print(f"- {company} / {title}")

    print("\nSelected leadership:")
    for row in selected_leadership:
        org = row.get("organization", row.get("project_name", ""))
        role = row.get("role", row.get("title", ""))
        print(f"- {org} / {role}")

    print("\nSelected certifications:")
    for row in selected_certs:
        cert = row.get("certification_name", row.get("name", ""))
        print(f"- {cert}")

    print("\nTechnical skills:")
    print(", ".join(technical_skills))


if __name__ == "__main__":
    main()