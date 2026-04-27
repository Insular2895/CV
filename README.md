<div align="center">

# ⚡ CV Tailor

**Génère automatiquement un CV DOCX ciblé à partir d'une offre d'emploi**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-AI-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com)
[![Google Sheets](https://img.shields.io/badge/Google_Sheets-Tracker-34A853?style=flat-square&logo=googlesheets&logoColor=white)](https://sheets.google.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## Comment ça marche

```
job_description.txt  +  master_profile.xlsx  →  CV DOCX personnalisé  →  Google Sheets
```

1. Tu colles une offre d'emploi dans `data/input/job_description.txt`
2. Le script **score** et **sélectionne** les expériences les plus pertinentes depuis ton Excel
3. **Gemini optimise** les bullets pour coller à l'offre *(1 seul appel par CV)*
4. Un **CV DOCX** est généré dans `data/output/`
5. Une ligne de suivi est automatiquement envoyée dans **Google Sheets**

---

## Fonctionnalités

| | |
|---|---|
| 🎯 **Scoring intelligent** | Sélection automatique des expériences par pertinence |
| 🤖 **Gemini intégré** | Optimisation des bullets en 1 appel (rotation 3 modèles, 60 CV/jour) |
| 📄 **Template DOCX** | Mise en page Word personnalisable via placeholders |
| 📊 **Tracker Google Sheets** | Suivi automatique de chaque candidature |
| 🔒 **Zéro donnée en ligne** | Tout tourne en local, tes données restent chez toi |

---

## Installation

```bash
git clone https://github.com/Insular2895/CV.git
cd CV
python3 -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration

### 1 — Fichier `.env`

```bash
cp .env.example .env
```

Ouvre `.env` et remplis tes clés (voir les sections Gemini et Google Sheets ci-dessous).

---

### 2 — Clé API Gemini *(optionnel)*

> Passe cette étape et mets `USE_GEMINI=false` dans `.env` si tu ne veux pas utiliser Gemini.

1. Aller sur **[Google AI Studio](https://aistudio.google.com/app/apikey)** → Créer une clé API
2. Copier la clé dans `.env` :

```env
USE_GEMINI=true
GEMINI_API_KEY=AIzaSy...
```

Le système tourne automatiquement entre 3 modèles Gemini (60 CV optimisés/jour par défaut).

---

### 3 — Google Sheets + Service Account *(optionnel)*

> Passe cette étape si tu ne veux pas de suivi Google Sheets. Lance juste `python3 -m src.generate_cv` à la place de `run.py`.

<details>
<summary><b>Voir les étapes détaillées</b></summary>

#### 3a — Créer le Google Sheet

1. Aller sur [Google Sheets](https://sheets.google.com) et créer un nouveau fichier
2. Récupérer l'**ID du Sheet** dans l'URL :

```
https://docs.google.com/spreadsheets/d/ ➜ CECI_EST_TON_SHEET_ID ➜ /edit
```

3. Coller l'ID dans `.env` :

```env
GOOGLE_SHEET_ID=1ABC...XYZ
GOOGLE_SHEET_TAB=applications
```

#### 3b — Créer un Service Account Google

1. Aller sur **[Google Cloud Console](https://console.cloud.google.com/)**
2. Créer un projet (ou en sélectionner un existant)
3. **APIs & Services → Bibliothèque** → Activer :
   - ✅ `Google Sheets API`
   - ✅ `Google Drive API`
4. **APIs & Services → Identifiants → Créer des identifiants → Compte de service**
5. Donner un nom (ex. `cv-tailor`) → Créer
6. Cliquer sur le compte créé → **Clés → Ajouter une clé → JSON**
7. Un fichier JSON est téléchargé automatiquement

#### 3c — Placer le fichier JSON

```bash
mkdir -p credentials
mv ~/Downloads/ton-fichier.json credentials/service_account.json
```

#### 3d — Partager le Sheet avec le Service Account

1. Ouvrir `credentials/service_account.json`
2. Copier la valeur du champ `"client_email"` → ressemble à `cv-tailor@projet.iam.gserviceaccount.com`
3. Dans Google Sheets → **Partager** → coller cet email → **Éditeur** → **Envoyer**

</details>

---

### 4 — Master Profile Excel

```bash
cp data/reference/master_profile_example.xlsx data/reference/master_profile.xlsx
```

Ouvrir `master_profile.xlsx` et remplir les feuilles :

<details>
<summary><b>Voir la structure complète des feuilles</b></summary>

#### Feuille `experiences`

| Colonne | Description |
|---|---|
| `experience_id` | Identifiant unique (ex. `EXP_001`) |
| `company` | Nom de l'entreprise |
| `location` | Ville / pays |
| `job_title` | Intitulé du poste |
| `date_start` | Début (ex. `2023-09`) |
| `date_end` | Fin (ex. `2025-06` ou `Présent`) |
| `industry_tags` | Secteurs (ex. `Supply Chain, Import/Export`) |
| `job_family_tags` | Familles métier (ex. `ADV, Logistics`) |
| `truth_bullet_1` … `truth_bullet_5` | Bullets factuels de l'expérience |
| `tools_verified` | Outils maîtrisés (ex. `SAP EWM, Excel`) |
| `skills_verified` | Compétences prouvées |
| `skills_transferable` | Compétences transférables |
| `skills_exposed` | Compétences exposées (sans expertise confirmée) |
| `kpis_verified` | KPIs réels (ex. `réduction 20% des délais`) |
| `cv_priority` | Priorité d'affichage (`1` = prioritaire) |

#### Feuille `leadership`

| Colonne | Description |
|---|---|
| `Organisation` | Nom de l'association / projet |
| `Role` | Rôle occupé |
| `City` | Ville |
| `Year` | Année ou période |
| `truth_bullet_1` … `truth_bullet_5` | Bullets factuels |

#### Feuille `certifications`

| Colonne | Description |
|---|---|
| `cert_name` | Nom de la certification |
| `issuer` | Organisme émetteur |
| `date_obtained` | Date d'obtention |
| `related_families` | Familles métier associées |
| `status` | `obtained` ou `in progress` |

#### Feuille `skills`

| Colonne | Description |
|---|---|
| `skill_name` | Nom de la compétence |
| `skill_family` | Famille (`supply`, `data`, `marketing`) |
| `type` | `tool`, `method` ou `soft` |

</details>

---

### 5 — Template CV DOCX

```bash
cp templates/base_cv_example.docx templates/base_cv.docx
```

Ouvrir `base_cv.docx` dans Word et personnaliser (nom, contact, couleurs, polices...).  
Les placeholders sont remplacés automatiquement à la génération.

<details>
<summary><b>Liste complète des placeholders</b></summary>

| Placeholder | Contenu injecté |
|---|---|
| `[[EXP_1_COMPANY]]` | Entreprise — expérience 1 |
| `[[EXP_1_POSITION_TITLE]]` | Poste — expérience 1 |
| `[[EXP_1_LOCATION]]` | Lieu — expérience 1 |
| `[[EXP_1_DATES]]` | Dates — expérience 1 |
| `[[EXP_1_BULLETS]]` | Bullets — expérience 1 |
| `[[EXP_2_COMPANY]]` | Entreprise — expérience 2 |
| `[[EXP_2_POSITION_TITLE]]` | Poste — expérience 2 |
| `[[EXP_2_LOCATION]]` | Lieu — expérience 2 |
| `[[EXP_2_DATES]]` | Dates — expérience 2 |
| `[[EXP_2_BULLETS]]` | Bullets — expérience 2 |
| `[[LEAD_1_ORG]]` | Organisation — leadership |
| `[[LEAD_1_ROLE]]` | Rôle — leadership |
| `[[LEAD_1_LOCATION]]` | Lieu — leadership |
| `[[LEAD_1_DATES]]` | Dates — leadership |
| `[[LEAD_1_BULLETS]]` | Bullets — leadership |
| `[[TECHNICAL_SKILLS]]` | Compétences techniques |
| `[[CERTIFICATION_ENTRIES]]` | Certifications |

</details>

---

### 6 — Job Description

Coller l'offre d'emploi dans :

```
data/input/job_description.txt
```

---

## Lancer la génération

```bash
python3 run.py
```

> Génère le CV **et** envoie la ligne dans Google Sheets.

Pour générer uniquement le CV (sans Sheets) :

```bash
python3 -m src.generate_cv
```

Le CV est créé dans `data/output/` avec un nom horodaté :

```
CV_Prenom_Nom_Entreprise_Poste_20260427_143022.docx
```

---

## Structure du projet

```
cv-tailor/
├── data/
│   ├── input/
│   │   └── job_description.txt          ← ton offre (non versionné)
│   ├── reference/
│   │   ├── master_profile_example.xlsx  ← modèle vide (versionné)
│   │   └── master_profile.xlsx          ← ton fichier réel (non versionné)
│   └── output/                          ← CV générés (non versionné)
├── templates/
│   ├── base_cv_example.docx             ← template exemple (versionné)
│   └── base_cv.docx                     ← ton template réel (non versionné)
├── credentials/
│   └── service_account.json             ← clé Google (non versionné)
├── src/
│   ├── generate_cv.py                   ← moteur principal
│   ├── llm/
│   │   ├── gemini_client.py             ← client Gemini + rotation modèles
│   │   └── cv_enhancer.py              ← optimisation bullets
│   ├── render/
│   │   └── docx_template.py             ← injection placeholders DOCX
│   └── tracker/
│       └── google_sheets_tracker.py     ← suivi Google Sheets
├── run.py                               ← commande unique
├── .env.example                         ← variables d'environnement (modèle)
└── requirements.txt
```

---

## Sécurité

Ces fichiers ne doivent **jamais** être pushés sur GitHub :

```
.env
credentials/service_account.json
data/reference/master_profile.xlsx
data/input/job_description.txt
data/output/
templates/base_cv.docx
```

Vérifier avant un push :

```bash
git ls-files | grep -E "(\.env$|service_account|master_profile\.xlsx|job_description|base_cv\.docx)"
```

✅ Cette commande ne doit rien retourner.
