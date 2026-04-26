from pathlib import Path
from datetime import datetime
import re
import unicodedata

import pandas as pd

from src.render.docx_template import DocxTemplateRenderer


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

MASTER_PROFILE_PATH = ROOT_DIR / "data" / "reference" / "master_profile.xlsx"
BASE_CV_TEMPLATE_PATH = ROOT_DIR / "templates" / "base_cv.docx"
OUTPUT_DIR = ROOT_DIR / "data" / "output"

POSSIBLE_JOB_PATHS = [
    ROOT_DIR / "data" / "input" / "job_description.txt",
    ROOT_DIR / "data" / "input" / "job.txt",
    ROOT_DIR / "job_description.txt",
    ROOT_DIR / "job.txt",
]


# ============================================================
# UTILS
# ============================================================

def normalize_text(value):
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9€%+.#/\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_str(value):
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none", "nat"]:
        return ""

    return text


def get_value(row, possible_columns, default=""):
    if row is None:
        return default

    index_lower = {str(col).lower(): col for col in row.index}

    for col in possible_columns:
        actual = index_lower.get(col.lower())
        if actual is not None:
            value = safe_str(row[actual])
            if value:
                return value

    return default


def clean_filename_part(value, fallback, max_length=40):
    text = safe_str(value)

    if not text:
        text = fallback

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")

    if not text:
        text = fallback

    return text[:max_length].strip("_")


def format_year_or_date(value):
    value = safe_str(value)

    if not value:
        return ""

    # Plage d'années "2023-2026" → "2023 - 2026"
    range_match = re.match(r"^(20\d{2}|19\d{2})\s*[-–]\s*(20\d{2}|19\d{2})$", value.strip())
    if range_match:
        return f"{range_match.group(1)} - {range_match.group(2)}"

    # Datetime Excel: pd.Timestamp ou string longue
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if not pd.isna(parsed):
            return str(parsed.year)
    except Exception:
        pass

    # Cas "2026-04-07 00:00:00"
    match = re.search(r"(20\d{2}|19\d{2})", value)
    if match and len(value) > 10 and "-" in value:
        return match.group(1)

    return value


def clean_dash_join(*parts):
    """
    Joint proprement les éléments sans créer de tirets vides.
    """
    cleaned = [safe_str(p) for p in parts if safe_str(p)]

    if not cleaned:
        return ""

    return " - ".join(cleaned)


def split_multi_value(text):
    """
    Split tags / skills avec séparateurs fréquents.
    """
    text = safe_str(text)

    if not text:
        return []

    parts = re.split(r"[|;,/\n]+", text)
    return [p.strip() for p in parts if p.strip()]


def load_job_description():
    for path in POSSIBLE_JOB_PATHS:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")

    raise FileNotFoundError(
        "Aucune job description trouvée. Mets ton offre dans : "
        "data/input/job_description.txt"
    )


def get_sheet_case_insensitive(excel_file, wanted_name):
    """
    Récupère une feuille Excel même si elle est écrite Leadership au lieu de leadership.
    """
    sheet_map = {s.lower().strip(): s for s in excel_file.sheet_names}
    key = wanted_name.lower().strip()

    if key not in sheet_map:
        return pd.DataFrame()

    return pd.read_excel(excel_file, sheet_name=sheet_map[key])


def load_master_profile():
    if not MASTER_PROFILE_PATH.exists():
        raise FileNotFoundError(f"Master profile introuvable : {MASTER_PROFILE_PATH}")

    excel = pd.ExcelFile(MASTER_PROFILE_PATH)

    workbook = {
        "experiences": get_sheet_case_insensitive(excel, "experiences"),
        "leadership": get_sheet_case_insensitive(excel, "leadership"),
        "certifications": get_sheet_case_insensitive(excel, "certifications"),
        "skills": get_sheet_case_insensitive(excel, "skills"),
        "job_families": get_sheet_case_insensitive(excel, "job_families"),
        "settings": get_sheet_case_insensitive(excel, "settings"),
    }

    return workbook


# ============================================================
# JOB PARSER SIMPLE ET ROBUSTE
# ============================================================

def extract_company(job_text):
    lines = [l.strip() for l in job_text.splitlines() if l.strip()]

    labeled_patterns = [
        r"company\s*[:\-]\s*(.+)",
        r"entreprise\s*[:\-]\s*(.+)",
        r"société\s*[:\-]\s*(.+)",
        r"employeur\s*[:\-]\s*(.+)",
        r"organization\s*[:\-]\s*(.+)",
    ]

    for line in lines[:25]:
        for pattern in labeled_patterns:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) <= 50:
                    return company

    # Cherche "Join <Company>", "at <Company>", "Why Join <Company>"
    context_patterns = [
        r"(?:why\s+)?join\s+([A-Z][A-Za-z0-9\-&]+)",
        r"join\s+the\s+([A-Z][A-Za-z0-9\-&]+)\s+team",
        r"([A-Z][A-Za-z0-9\-&]{2,})\s+is\s+(?:looking|seeking|hiring|searching|a\b)",
        r"([A-Z][A-Za-z0-9\-&]{2,})\s+recherche",
        r"(?:from\s+various|at)\s+([A-Z][A-Za-z0-9\-&]{2,})\b",
    ]

    _stop = {"the", "our", "this", "your", "a", "an", "we", "team", "role", "position",
             "company", "organization", "groupe", "group", "france", "paris"}

    for line in lines[:60]:
        for pattern in context_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                if candidate.lower() not in _stop and 2 <= len(candidate) <= 40:
                    return candidate

    return "Entreprise"


def looks_like_real_job_title(line):
    line_clean = safe_str(line)

    if not line_clean:
        return False

    lowered = line_clean.lower()

    bad_fragments = [
        "department oversees",
        "individual team members",
        "typically managing",
        "countries",
        "responsibilities",
        "activities",
        "both upstream",
        "downstream",
        "about the role",
        "job description",
        "description du poste",
        "your responsibilities",
        "what you will do",
        "profile required",
        "candidate profile",
    ]

    if any(fragment in lowered for fragment in bad_fragments):
        return False

    if len(line_clean) > 70:
        return False

    if len(line_clean.split()) > 9:
        return False

    title_keywords = [
        "analyst",
        "assistant",
        "associate",
        "manager",
        "coordinator",
        "specialist",
        "consultant",
        "chef de projet",
        "chargé",
        "responsable",
        "acheteur",
        "commercial",
        "supply",
        "operations",
        "logistics",
        "procurement",
        "data",
        "business",
    ]

    return any(keyword in lowered for keyword in title_keywords)


def extract_job_title(job_text):
    lines = [l.strip() for l in job_text.splitlines() if l.strip()]

    patterns = [
        r"job title\s*[:\-]\s*(.+)",
        r"titre\s*[:\-]\s*(.+)",
        r"poste\s*[:\-]\s*(.+)",
        r"intitulé\s*[:\-]\s*(.+)",
        r"position\s*[:\-]\s*(.+)",
    ]

    for line in lines[:40]:
        for pattern in patterns:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if looks_like_real_job_title(title):
                    return title

    # Essai avec nettoyage des parenthèses "(CDD / 1 an / ...)"
    for line in lines[:20]:
        cleaned = re.sub(r"\s*\([^)]*\)", "", line).strip()
        if cleaned and looks_like_real_job_title(cleaned):
            return cleaned

    for line in lines[:20]:
        if looks_like_real_job_title(line):
            return line

    return "Poste cible"


def extract_keywords(job_text):
    text = normalize_text(job_text)

    stopwords = {
        "the", "and", "for", "with", "you", "your", "are", "our", "this", "that",
        "will", "dans", "avec", "pour", "sur", "les", "des", "une", "est", "nous",
        "vous", "vos", "aux", "du", "de", "la", "le", "un", "en", "et", "au",
        "as", "to", "of", "in", "a", "an", "is", "be", "or", "by", "from",
    }

    words = re.findall(r"[a-z0-9+#.]+", text)
    words = [w for w in words if len(w) >= 3 and w not in stopwords]

    frequency = {}
    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    sorted_words = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:80]]


def parse_job(job_text):
    title = extract_job_title(job_text)
    company = extract_company(job_text)
    keywords = extract_keywords(job_text)

    return {
        "company": company,
        "job_title": title,
        "keywords": keywords,
        "raw_text": job_text,
        "normalized_text": normalize_text(job_text),
    }


# ============================================================
# SCORING
# ============================================================

def row_search_text(row):
    columns = [
        "company",
        "job_title",
        "industry_tags",
        "job_family_tags",
        "tools_verified",
        "skills_verified",
        "skills_transferable",
        "skills_exposed",
        "kpis_verified",
    ]

    values = []

    for col in columns:
        if col in row.index:
            values.append(safe_str(row[col]))

    for i in range(1, 6):
        col = f"truth_bullet_{i}"
        if col in row.index:
            values.append(safe_str(row[col]))

    return normalize_text(" ".join(values))


def score_row(row, parsed_job):
    job_text = parsed_job["normalized_text"]
    keywords = parsed_job["keywords"]

    searchable = row_search_text(row)

    if not searchable:
        return 0

    score = 0

    for keyword in keywords:
        if keyword in searchable:
            score += 3

    # Boosts métiers importants
    boosts = {
        "supply": 12,
        "chain": 8,
        "logistics": 10,
        "warehouse": 10,
        "transport": 8,
        "procurement": 10,
        "purchasing": 8,
        "achats": 10,
        "operations": 8,
        "sap": 10,
        "ewm": 10,
        "stock": 8,
        "inventory": 8,
        "export": 8,
        "import": 8,
        "incoterms": 8,
        "forecast": 7,
        "data": 7,
        "analytics": 7,
        "finance": 7,
        "risk": 7,
        "media": 6,
        "marketing": 6,
    }

    for word, weight in boosts.items():
        if word in job_text and word in searchable:
            score += weight

    # Récence
    date_end = get_value(row, ["date_end", "end_year", "year", "date", "dates"])
    year_match = re.search(r"(20\d{2}|19\d{2})", safe_str(date_end))

    if year_match:
        year = int(year_match.group(1))
        score += max(0, year - 2020)

    return score


def sort_by_recency(df):
    if df.empty:
        return df

    def extract_year(row):
        raw = get_value(row, ["date_end", "end_year", "year", "date", "dates"], "")
        years = re.findall(r"(20\d{2}|19\d{2})", safe_str(raw))

        if years:
            return max(int(y) for y in years)

        return 0

    df = df.copy()
    df["_sort_year"] = df.apply(extract_year, axis=1)
    return df.sort_values(by=["_score", "_sort_year"], ascending=[False, False])


def select_top_rows(df, parsed_job, max_rows):
    if df.empty:
        return []

    df = df.copy()
    df["_score"] = df.apply(lambda row: score_row(row, parsed_job), axis=1)
    df = sort_by_recency(df)

    selected = df.head(max_rows)

    return [row for _, row in selected.iterrows()]


# ============================================================
# BULLETS
# ============================================================

def split_bullets(raw_value, max_bullets=4):
    text = safe_str(raw_value)

    if not text:
        return []

    text = text.replace("\r", "\n")

    # Cas où Excel contient de vraies lignes
    if "\n" in text:
        parts = text.split("\n")
    elif "•" in text:
        parts = text.split("•")
    elif "|" in text:
        parts = text.split("|")
    elif ";" in text:
        parts = text.split(";")
    else:
        parts = [text]

    bullets = []

    for part in parts:
        bullet = safe_str(part)
        bullet = bullet.lstrip("•").lstrip("-").strip()

        if len(bullet) < 10:
            continue

        bullets.append(bullet)

    return bullets[:max_bullets]


def extract_truth_bullets(row, max_bullets=4):
    # Priorité aux colonnes numérotées truth_bullet_1, truth_bullet_2, ...
    bullets = []
    for i in range(1, 8):
        value = get_value(row, [f"truth_bullet_{i}", f"bullet_{i}"], "")
        if value and len(value) > 5:
            bullets.append(value)
        if len(bullets) >= max_bullets:
            break

    if bullets:
        return bullets

    # Fallback colonne texte unique
    raw = get_value(
        row,
        ["truth_bullets", "bullets", "description", "evidence", "allowed"],
        "",
    )
    return split_bullets(raw, max_bullets=max_bullets)


# ============================================================
# CERTIFICATIONS
# ============================================================

def select_certifications(df, parsed_job, max_certs=2):
    if df.empty:
        return []

    df = df.copy()
    df["_score"] = df.apply(lambda row: score_row(row, parsed_job), axis=1)
    df = sort_by_recency(df)

    selected = []

    for _, row in df.iterrows():
        cert_name = get_value(
            row,
            [
                "certification_name",
                "certification",
                "cert_name",
                "name",
                "title",
                "skill_name",
            ],
            "",
        )

        issuer = get_value(
            row,
            [
                "issuer",
                "organization",
                "company",
                "provider",
                "school",
                "entreprise",
            ],
            "",
        )

        if not cert_name and issuer:
            cert_name = issuer
            issuer = ""

        if not cert_name:
            continue

        line = clean_dash_join(cert_name, issuer)

        if line and line not in selected:
            selected.append(line)

        if len(selected) >= max_certs:
            break

    return selected


# ============================================================
# TECHNICAL SKILLS
# ============================================================

SKILL_TRANSLATIONS = {
    "performance analysis": "Analyse de performance",
    "press release writing": "Rédaction de communiqués de presse",
    "project management": "Gestion de projet",
    "stakeholder management": "Gestion des parties prenantes",
    "operations management": "Gestion des opérations",
    "operational coordination": "Coordination opérationnelle",
    "reporting": "Reporting",
    "kpi monitoring": "Suivi des KPI",
    "export operations": "Gestion export",
    "import operations": "Gestion import",
    "procurement": "Achats / Procurement",
    "purchasing": "Achats",
    "inventory management": "Gestion des stocks",
    "stock management": "Gestion des stocks",
    "supply chain coordination": "Coordination supply chain",
    "warehouse management": "Gestion d’entrepôt",
    "transport coordination": "Coordination transport",
    "process optimization": "Optimisation des processus",
    "business intelligence": "Business Intelligence",
    "dashboarding": "Dashboarding",
    "data analysis": "Analyse de données",
    "forecasting": "Prévision de la demande",
    "risk management": "Gestion des risques",
    "financial modeling": "Modélisation financière",
    "crm marketing": "CRM marketing",
    "email marketing": "Email marketing",
    "paid media": "Paid media",
    "media buying": "Achat média",
    "seo": "SEO",
    "sea": "SEA",
}


def translate_skill(skill):
    raw = safe_str(skill)
    key = normalize_text(raw)

    if key in SKILL_TRANSLATIONS:
        return SKILL_TRANSLATIONS[key]

    return raw


def select_technical_skills(skills_df, selected_experiences, parsed_job, max_skills=8):
    job_text = parsed_job["normalized_text"]

    candidates = []

    # 1. Depuis la feuille skills
    if not skills_df.empty:
        for _, row in skills_df.iterrows():
            skill_name = get_value(
                row,
                ["skill_name", "name", "skill", "competence", "compétence"],
                "",
            )

            if not skill_name:
                continue

            searchable = row_search_text(row)
            score = 0

            for keyword in parsed_job["keywords"]:
                if keyword in searchable:
                    score += 3

            if normalize_text(skill_name) in job_text:
                score += 12

            # Boost supply / ops
            supply_words = [
                "sap", "ewm", "supply", "procurement", "achats", "stock",
                "inventory", "export", "import", "incoterms", "warehouse",
                "transport", "forecast", "operations"
            ]

            for word in supply_words:
                if word in job_text and word in searchable:
                    score += 8

            if score > 0:
                candidates.append((translate_skill(skill_name), score))

    # 2. Depuis expériences sélectionnées
    for row in selected_experiences:
        for col in [
            "tools_verified",
            "tools",
            "skills_verified",
            "skills",
            "skill_tags",
            "technical_skills",
        ]:
            raw = get_value(row, [col], "")
            for skill in split_multi_value(raw):
                skill_norm = normalize_text(skill)
                score = 2

                if skill_norm in job_text:
                    score += 10

                candidates.append((translate_skill(skill), score))

    # 3. Fallback contextualisé
    fallback_by_context = []

    if any(w in job_text for w in ["supply", "chain", "warehouse", "transport", "procurement", "stock", "inventory", "logistics"]):
        fallback_by_context += [
            "SAP",
            "SAP EWM",
            "Coordination supply chain",
            "Gestion des stocks",
            "Achats / Procurement",
            "Gestion export",
            "Gestion import",
            "Incoterms (FCA, CPT, DAP)",
            "Optimisation des processus",
        ]

    if any(w in job_text for w in ["data", "analyst", "analytics", "dashboard", "reporting", "kpi"]):
        fallback_by_context += [
            "Excel",
            "SQL",
            "Python",
            "Looker",
            "Power BI",
            "Reporting",
            "Suivi des KPI",
            "Analyse de données",
        ]

    if any(w in job_text for w in ["marketing", "media", "ads", "crm", "campaign", "acquisition"]):
        fallback_by_context += [
            "Achat média",
            "Meta Ads",
            "Google Ads",
            "CRM marketing",
            "Email marketing",
            "SEO",
            "SEA",
            "Analyse de performance",
        ]

    for skill in fallback_by_context:
        candidates.append((skill, 5))

    # Déduplication avec score max
    score_by_skill = {}

    for skill, score in candidates:
        skill = safe_str(skill)

        if not skill:
            continue

        key = normalize_text(skill)

        if not key:
            continue

        if key not in score_by_skill or score > score_by_skill[key][1]:
            score_by_skill[key] = (skill, score)

    ranked = sorted(score_by_skill.values(), key=lambda x: x[1], reverse=True)

    return [skill for skill, _ in ranked[:max_skills]]


# ============================================================
# FORMAT ROWS
# ============================================================

def format_experience(row):
    company = get_value(row, ["company", "organisation", "organization", "org", "entreprise"], "")
    position = get_value(row, ["position_title", "position", "title", "job_title", "role"], "")
    location = get_value(row, ["location", "city", "city_state", "lieu"], "")

    raw_dates = get_value(row, ["dates", "date", "year", "date_range"], "")
    dates = format_year_or_date(raw_dates) if raw_dates else ""

    if not dates:
        start = get_value(row, ["date_start", "start_year"], "")
        end = get_value(row, ["date_end", "end_year"], "")
        dates = clean_dash_join(format_year_or_date(start), format_year_or_date(end))

    return {
        "company": company,
        "position": position,
        "location": location,
        "dates": dates,
        "bullets": extract_truth_bullets(row, max_bullets=4),
    }


def format_leadership(row):
    org = get_value(row, ["organisation", "organization", "company", "org", "activity", "project"], "")
    role = get_value(row, ["role", "position_title", "position", "title"], "")
    location = get_value(row, ["city", "location", "city_state", "lieu"], "")

    raw_dates = get_value(row, ["year", "dates", "date", "date_range"], "")
    dates = format_year_or_date(raw_dates) if raw_dates else ""

    if not dates:
        start = get_value(row, ["date_start", "start_year"], "")
        end = get_value(row, ["date_end", "end_year"], "")
        dates = clean_dash_join(format_year_or_date(start), format_year_or_date(end))

    return {
        "org": org,
        "role": role,
        "location": location,
        "dates": dates,
        "bullets": extract_truth_bullets(row, max_bullets=2),
    }


# ============================================================
# OUTPUT FILENAME
# ============================================================

def build_output_filename(parsed_job):
    company = parsed_job.get("company") or "Entreprise"
    title = parsed_job.get("job_title") or "Poste cible"

    title_clean = normalize_text(title)

    bad_fragments = [
        "department oversees",
        "individual team members",
        "typically managing",
        "countries",
        "responsibilities",
        "activities",
        "both upstream",
        "downstream",
    ]

    if (
        len(title_clean) > 60
        or title_clean.count(" ") > 6
        or any(fragment in title_clean for fragment in bad_fragments)
    ):
        title = "Poste cible"

    company = clean_filename_part(company, "Entreprise", max_length=28)
    title = clean_filename_part(title, "Poste_cible", max_length=38)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"CV_Lucas_Pertusa_{company}_{title}_{timestamp}.docx"

    if len(filename) > 115:
        filename = f"CV_Lucas_Pertusa_{company}_{timestamp}.docx"

    if len(filename) > 115:
        filename = f"CV_Lucas_Pertusa_{timestamp}.docx"

    return filename


# ============================================================
# BUILD REPLACEMENTS
# ============================================================

def build_replacements(experiences, leadership, certifications, technical_skills):
    exp1 = experiences[0] if len(experiences) > 0 else {}
    exp2 = experiences[1] if len(experiences) > 1 else {}

    lead1 = leadership[0] if len(leadership) > 0 else {}

    replacements = {
        # Certifications
        "[[CERTIFICATION_ENTRIES]]": "\n".join(certifications),

        # Expérience 1
        "[[EXP_1_COMPAGNY]]": exp1.get("company", ""),
        "[[EXP_1_COMPANY]]": exp1.get("company", ""),
        "[[EXP_1_POSITION_TITLE]]": exp1.get("position", ""),
        "[[EXP_1_LOCATION]]": exp1.get("location", ""),
        "[[EXP_1_DATES]]": exp1.get("dates", ""),
        "[[EXP_1_BULLETS]]": exp1.get("bullets", []),

        # Expérience 2
        "[[EXP_2_COMPAGNY]]": exp2.get("company", ""),
        "[[EXP_2_COMPANY]]": exp2.get("company", ""),
        "[[EXP_2_POSITION_TITLE]]": exp2.get("position", ""),
        "[[EXP_2_LOCATION]]": exp2.get("location", ""),
        "[[EXP_2_DATES]]": exp2.get("dates", ""),
        "[[EXP_2_BULLETS]]": exp2.get("bullets", []),

        # Leadership
        "[[LEAD_1_ORG]]": lead1.get("org", ""),
        "[[LEAD_1_ROLE]]": lead1.get("role", ""),
        "[[LEAD_1_LOCATION]]": lead1.get("location", ""),
        "[[LEAD_1_DATES]]": lead1.get("dates", ""),
        "[[LEAD_1_BULLETS]]": lead1.get("bullets", []),

        # Skills
        "[[TECHNICAL_SKILLS]]": ", ".join(technical_skills),
    }

    return replacements


# ============================================================
# MAIN
# ============================================================

def main():
    print("Lecture de la job description...")
    job_text = load_job_description()

    print("Chargement du master profile...")
    workbook = load_master_profile()

    experiences_df = workbook["experiences"]
    leadership_df = workbook["leadership"]
    certifications_df = workbook["certifications"]
    skills_df = workbook["skills"]

    print("Analyse de la job description...")
    parsed_job = parse_job(job_text)

    print("Sélection des expériences...")
    selected_exp_rows = select_top_rows(experiences_df, parsed_job, max_rows=2)
    selected_exp_rows = sorted(
        selected_exp_rows,
        key=lambda row: max(
            (int(y) for y in re.findall(r"(20\d{2}|19\d{2})", safe_str(get_value(row, ["date_end", "end_year", "year", "date", "dates"], "")))),
            default=0,
        ),
        reverse=True,
    )
    selected_experiences = [format_experience(row) for row in selected_exp_rows]

    print("Sélection du leadership...")
    selected_lead_rows = select_top_rows(leadership_df, parsed_job, max_rows=1)
    selected_leadership = [format_leadership(row) for row in selected_lead_rows]

    print("Sélection des certifications...")
    selected_certifications = select_certifications(certifications_df, parsed_job, max_certs=2)

    print("Sélection des compétences techniques...")
    selected_skills = select_technical_skills(
        skills_df,
        selected_exp_rows,
        parsed_job,
        max_skills=8,
    )

    replacements = build_replacements(
        selected_experiences,
        selected_leadership,
        selected_certifications,
        selected_skills,
    )

    print("\n--- Résumé génération ---")
    print(f"Entreprise détectée : {parsed_job.get('company')}")
    print(f"Poste détecté : {parsed_job.get('job_title')}")

    print("\nExpériences sélectionnées :")
    for exp in selected_experiences:
        print(f"- {exp.get('company')} | {exp.get('position')} | {exp.get('dates')}")
        print(f"  Bullets : {len(exp.get('bullets', []))}")

    print("\nLeadership sélectionné :")
    for lead in selected_leadership:
        print(f"- {lead.get('org')} | {lead.get('role')} | {lead.get('dates')}")
        print(f"  Bullets : {len(lead.get('bullets', []))}")

    print("\nCertifications sélectionnées :")
    for cert in selected_certifications:
        print(f"- {cert}")

    print("\nCompétences techniques sélectionnées :")
    print(", ".join(selected_skills))

    print("")

    print("Construction du CV...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_filename = build_output_filename(parsed_job)
    output_path = OUTPUT_DIR / output_filename

    renderer = DocxTemplateRenderer(BASE_CV_TEMPLATE_PATH)
    renderer.render(replacements, output_path)

    if output_path.exists():
        print(f"CV généré : {output_path}")
    else:
        raise RuntimeError(f"Le fichier n'a pas été généré : {output_path}")


if __name__ == "__main__":
    main()