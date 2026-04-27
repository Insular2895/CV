# CV Tailor

Outil Python pour générer automatiquement un CV DOCX adapté à une offre d'emploi.

Le script :
1. Lit une job description (`data/input/job_description.txt`)
2. Sélectionne les expériences les plus pertinentes depuis un fichier Excel
3. Optimise les bullets avec Gemini si activé (1 appel par CV)
4. Génère un CV DOCX dans `data/output/`
5. Envoie un rapport de suivi dans Google Sheets

---

## Installation

```bash
git clone https://github.com/Insular2895/CV.git
cd CV
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

### 1. Créer le fichier `.env`

```bash
cp .env.example .env
```

Remplir les variables dans `.env` :

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Clé API Gemini (Google AI Studio) |
| `USE_GEMINI` | `true` pour activer, `false` pour désactiver |
| `GOOGLE_SHEET_ID` | ID du Google Sheet de suivi |
| `GOOGLE_SHEET_TAB` | Nom de l'onglet (défaut : `applications`) |

### 2. Créer le fichier `credentials/service_account.json`

Pour envoyer des données dans Google Sheets, il faut un Service Account Google :

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet (ou utiliser un existant)
3. Activer l'API **Google Sheets** et l'API **Google Drive**
4. Créer un **Service Account** → Clés → JSON
5. Télécharger le fichier JSON et le placer ici :
   ```
   credentials/service_account.json
   ```
6. Dans Google Sheets, partager le fichier avec l'adresse email du service account (format `xxx@xxx.iam.gserviceaccount.com`)

### 3. Préparer le master profile Excel

Partir du fichier exemple :

```bash
cp data/reference/master_profile_example.xlsx data/reference/master_profile.xlsx
```

Remplir chaque feuille :

| Feuille | Colonnes clés |
|---|---|
| `experiences` | `company`, `position_title`, `location`, `date_start`, `date_end`, `industry_tags`, `tools_verified`, `skills_verified`, `truth_bullet_1`…`truth_bullet_4` |
| `leadership` | `organisation`, `role`, `location`, `year`, `truth_bullet_1`, `truth_bullet_2` |
| `certifications` | `certification_name`, `issuer`, `year` |
| `skills` | `skill_name` |

### 4. Préparer le template CV

Partir du fichier exemple :

```bash
cp templates/base_cv_example.docx templates/base_cv.docx
```

Personnaliser la mise en page dans Word (nom, contact, couleurs, polices...).  
Les placeholders `[[EXP_1_BULLETS]]`, `[[EXP_1_COMPANY]]` etc. seront remplacés automatiquement.

**Placeholders disponibles :**

| Placeholder | Contenu |
|---|---|
| `[[EXP_1_COMPANY]]` | Entreprise expérience 1 |
| `[[EXP_1_POSITION_TITLE]]` | Poste expérience 1 |
| `[[EXP_1_LOCATION]]` | Lieu expérience 1 |
| `[[EXP_1_DATES]]` | Dates expérience 1 |
| `[[EXP_1_BULLETS]]` | Bullets expérience 1 |
| `[[EXP_2_COMPANY]]` | Entreprise expérience 2 |
| `[[EXP_2_POSITION_TITLE]]` | Poste expérience 2 |
| `[[EXP_2_LOCATION]]` | Lieu expérience 2 |
| `[[EXP_2_DATES]]` | Dates expérience 2 |
| `[[EXP_2_BULLETS]]` | Bullets expérience 2 |
| `[[LEAD_1_ORG]]` | Organisation leadership |
| `[[LEAD_1_ROLE]]` | Rôle leadership |
| `[[LEAD_1_LOCATION]]` | Lieu leadership |
| `[[LEAD_1_DATES]]` | Dates leadership |
| `[[LEAD_1_BULLETS]]` | Bullets leadership |
| `[[TECHNICAL_SKILLS]]` | Compétences techniques (liste) |
| `[[CERTIFICATION_ENTRIES]]` | Certifications (liste) |

### 5. Ajouter la job description

Coller l'offre d'emploi dans :

```
data/input/job_description.txt
```

---

## Lancer la génération

```bash
python3 run.py
```

Le script génère le CV dans `data/output/` et envoie une ligne dans Google Sheets.

Pour générer le CV uniquement (sans Google Sheets) :

```bash
python3 -m src.generate_cv
```

---

## Gemini (optionnel)

Quand Gemini est activé, le script fait **1 seul appel par CV** et tourne entre plusieurs modèles :

```
GEMINI_ROTATION_MODELS=gemini-2.5-flash-lite,gemini-2.5-flash,gemini-2.5-flash-preview-05-20
GEMINI_DAILY_LIMIT_PER_MODEL=20
```

3 modèles × 20 appels/jour = **60 CV/jour** avec optimisation Gemini.

Si Gemini échoue (quota, erreur réseau), le CV est quand même généré avec les bullets originaux.

---

## Fichiers non versionnés

Ces fichiers contiennent des données personnelles ou sensibles et ne doivent **jamais** être pushés sur GitHub :

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
git ls-files | grep -E "(\.env|credentials|service_account|master_profile\.xlsx|job_description|base_cv\.docx)"
```

Cette commande ne doit rien retourner.
