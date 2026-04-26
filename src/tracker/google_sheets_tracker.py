from pathlib import Path
from datetime import datetime
import json
import os

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

ENV_PATH = ROOT_DIR / ".env"
REPORT_PATH = ROOT_DIR / "data" / "output" / "last_run_report.json"
SERVICE_ACCOUNT_PATH = ROOT_DIR / "credentials" / "service_account.json"


# ============================================================
# ENV
# ============================================================

load_dotenv(ENV_PATH)

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
GOOGLE_SHEET_TAB = os.getenv("GOOGLE_SHEET_TAB", "applications").strip()


# ============================================================
# CONFIG
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DEFAULT_STATUS = "CV generated"

HEADERS = [
    "created_at",
    "company",
    "job_title",
    "salary",
    "location",
    "job_url",
    "cv_path",
    "mode",
    "notes",
    "updated_at",
    "status",
    "priority",
    "cv_file",
    "selected_experiences",
    "selected_certifications",
    "selected_technical_skills",
    "score",
]


# ============================================================
# UTILS
# ============================================================

def safe_str(value):
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in ["none", "nan", "nat"]:
        return ""

    return text


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_report_value(report, key, default=""):
    value = report.get(key, default)

    if value is None:
        return default

    return value


def safe_join(value):
    """
    Convertit proprement une liste / dict / texte en valeur lisible pour Google Sheets.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        cleaned_items = []

        for item in value:
            if isinstance(item, dict):
                # Expériences
                company = safe_str(
                    item.get("company")
                    or item.get("organisation")
                    or item.get("organization")
                    or item.get("org")
                )

                position = safe_str(
                    item.get("position_title")
                    or item.get("position")
                    or item.get("role")
                    or item.get("title")
                )

                dates = safe_str(item.get("dates") or item.get("year"))

                parts = [p for p in [company, position, dates] if p]

                if parts:
                    cleaned_items.append(" - ".join(parts))
                else:
                    cleaned_items.append(json.dumps(item, ensure_ascii=False))

            else:
                item_text = safe_str(item)
                if item_text:
                    cleaned_items.append(item_text)

        return " | ".join(cleaned_items)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return safe_str(value)


def calculate_score(report):
    raw_score = 0

    selected_experiences = get_report_value(report, "selected_experiences", [])

    if isinstance(selected_experiences, list):
        for exp in selected_experiences:
            if isinstance(exp, dict):
                raw_score += float(exp.get("score", 0) or 0)

    selected_leadership = get_report_value(report, "selected_leadership", [])

    if isinstance(selected_leadership, list):
        for exp in selected_leadership:
            if isinstance(exp, dict):
                raw_score += float(exp.get("score", 0) or 0)

    selected_certifications = get_report_value(report, "selected_certifications", [])

    if isinstance(selected_certifications, list):
        raw_score += len(selected_certifications) * 25

    selected_technical_skills = get_report_value(report, "selected_technical_skills", [])

    if isinstance(selected_technical_skills, list):
        raw_score += len(selected_technical_skills) * 10

    normalized_score = min((raw_score / 700) * 100, 100)

    return round(normalized_score, 2)


def extract_filename(path_value):
    path_text = safe_str(path_value)

    if not path_text:
        return ""

    return Path(path_text).name


# ============================================================
# GOOGLE SHEETS CLIENT
# ============================================================

def get_client():
    if not SERVICE_ACCOUNT_PATH.exists():
        raise FileNotFoundError(
            f"Service account introuvable : {SERVICE_ACCOUNT_PATH}\n"
            "Place ton fichier JSON dans credentials/service_account.json"
        )

    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH,
        scopes=SCOPES,
    )

    return gspread.authorize(credentials)


def get_worksheet(client):
    if not GOOGLE_SHEET_ID:
        raise ValueError(
            "GOOGLE_SHEET_ID est vide. Ajoute-le dans ton fichier .env"
        )

    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    try:
        worksheet = spreadsheet.worksheet(GOOGLE_SHEET_TAB)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=GOOGLE_SHEET_TAB,
            rows=1000,
            cols=len(HEADERS),
        )

    return worksheet


# ============================================================
# SHEET STRUCTURE
# ============================================================

def ensure_headers(worksheet):
    """
    Garde les headers existants si la feuille est déjà créée,
    mais ajoute les colonnes manquantes à droite.
    """

    existing_headers = worksheet.row_values(1)

    # Feuille vide
    if not existing_headers:
        worksheet.update("A1", [HEADERS])
        return HEADERS

    final_headers = existing_headers.copy()

    for header in HEADERS:
        if header not in final_headers:
            final_headers.append(header)

    if final_headers != existing_headers:
        end_col = number_to_column_letter(len(final_headers))
        worksheet.update(f"A1:{end_col}1", [final_headers])

    return final_headers


def number_to_column_letter(number):
    """
    1 -> A
    2 -> B
    27 -> AA
    """

    result = ""

    while number > 0:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result

    return result


# ============================================================
# BUILD ROW
# ============================================================

def build_tracker_row(report):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_docx = safe_str(get_report_value(report, "output_docx", ""))

    selected_experiences = get_report_value(report, "selected_experiences", [])
    selected_certifications = get_report_value(report, "selected_certifications", [])
    selected_skills = get_report_value(report, "selected_technical_skills", [])

    return {
        "created_at": now,
        "company": safe_str(get_report_value(report, "company_detected", "")),
        "job_title": safe_str(get_report_value(report, "job_title_detected", "")),
        "salary": safe_str(get_report_value(report, "salary", "")),
        "location": safe_str(get_report_value(report, "location", "")),
        "job_url": safe_str(get_report_value(report, "job_url", "")),
        "cv_path": output_docx,
        "mode": safe_str(get_report_value(report, "mode", "local")),
        "notes": "",
        "updated_at": now,
        "status": DEFAULT_STATUS,
        "priority": "",
        "cv_file": extract_filename(output_docx),
        "selected_experiences": safe_join(selected_experiences),
        "selected_certifications": safe_join(selected_certifications),
        "selected_technical_skills": safe_join(selected_skills),
        "score": calculate_score(report),
    }


def row_dict_to_values(row_dict, headers):
    return [row_dict.get(header, "") for header in headers]


# ============================================================
# APPEND
# ============================================================

def append_report_to_tracker(report_path=REPORT_PATH):
    print("Lecture du rapport de génération...")

    report = load_json(report_path)

    print("Connexion à Google Sheets...")

    client = get_client()
    worksheet = get_worksheet(client)

    print("Vérification des colonnes...")

    headers = ensure_headers(worksheet)

    print("Construction de la ligne tracker...")

    row_dict = build_tracker_row(report)
    row_values = row_dict_to_values(row_dict, headers)

    print("Ajout dans Google Sheets...")

    worksheet.append_row(
        row_values,
        value_input_option="USER_ENTERED",
    )

    print("Ligne ajoutée dans Google Sheets.")
    print(f"Entreprise : {row_dict.get('company')}")
    print(f"Poste : {row_dict.get('job_title')}")
    print(f"CV : {row_dict.get('cv_file')}")


# ============================================================
# MAIN
# ============================================================

def main():
    append_report_to_tracker()


if __name__ == "__main__":
    main()