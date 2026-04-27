# CV Tailor

Outil Python pour générer automatiquement un CV DOCX personnalisé à partir d'une offre d'emploi.

Le script :
1. Lit une job description (`data/input/job_description.txt`)
2. Score et sélectionne les expériences les plus pertinentes depuis un fichier Excel
3. Optimise les bullets avec Gemini si activé (1 seul appel par CV)
4. Génère un CV DOCX dans `data/output/`
5. Envoie un rapport de suivi dans Google Sheets

---

## Installation

```bash
git clone https://github.com/Insular2895/CV.git
cd CV
python3 -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration étape par étape

### Étape 1 — Créer le fichier `.env`

```bash
cp .env.example .env
```

Ouvrir `.env` et remplir les variables (voir détails ci-dessous).

---

### Étape 2 — Clé API Gemini (optionnel)

> Passer cette étape si Gemini n'est pas utilisé (mettre `USE_GEMINI=false` dans `.env`).

1. Aller sur [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Créer une clé API
3. Copier la clé dans `.env` :
   ```
   GEMINI_API_KEY=AIza...
   ```

---

### Étape 3 — Google Sheets + Service Account

> Passer cette étape si le suivi Google Sheets n'est pas utilisé.

#### 3a. Créer le Google Sheet

1. Aller sur [Google Sheets](https://sheets.google.com) et créer un nouveau fichier
2. Copier l'ID dans l'URL :
   ```
   https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/edit
   ```
   L'ID est la partie entre `/d/` et `/edit`
3. Coller l'ID dans `.env` :
   ```
   GOOGLE_SHEET_ID=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

#### 3b. Créer un Service Account Google

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet (ou en sélectionner un existant)
3. Dans le menu → **APIs & Services** → **Bibliothèque**
   - Activer **Google Sheets API**
   - Activer **Google Drive API**
4. Dans **APIs & Services** → **Identifiants** → **Créer des identifiants** → **Compte de service**
5. Donner un nom au compte de service (ex. `cv-tailor`) → Créer
6. Dans la liste des comptes de service, cliquer sur le compte créé → **Clés** → **Ajouter une clé** → **JSON**
7. Un fichier JSON est téléchargé automatiquement

#### 3c. Placer le fichier JSON

```bash
mkdir -p credentials
cp ~/Downloads/nom-du-fichier-telecharge.json credentials/service_account.json
```

#### 3d. Partager le Google Sheet avec le Service Account

1. Ouvrir le fichier `credentials/service_account.json`
2. Copier la valeur du champ `"client_email"` (format : `cv-tailor@xxx.iam.gserviceaccount.com`)
3. Dans le Google Sheet → **Partager** → coller cet email → **Éditeur** → **Envoyer**

---

### Étape 4 — Préparer le master profile Excel

```bash
cp data/reference/master_profile_example.xlsx data/reference/master_profile.xlsx
```

Ouvrir `master_profile.xlsx` dans Excel ou LibreOffice et remplir les feuilles :

#### Feuille `experiences`

| Colonne | Description |
|---|---|
| `experience_id` | Identifiant unique (ex. `EXP_001`) |
| `company` | Nom de l'entreprise |
| `location` | Ville / pays |
| `job_title` | Intitulé du poste |
| `date_start` | Date de début (ex. `2023-09`) |
| `date_end` | Date de fin (ex. `2025-06` ou `Présent`) |
| `industry_tags` | Tags secteur (ex. `Supply Chain, Import/Export`) |
| `job_family_tags` | Famille métier (ex. `ADV, Logistics`) |
| `context` | Contexte de l'expérience (optionnel) |
| `truth_bullet_1` à `truth_bullet_5` | Bullets factuels de l'expérience (max 5) |
| `tools_verified` | Outils maîtrisés (ex. `SAP EWM, Excel`) |
| `skills_verified` | Compétences prouvées |
| `skills_transferable` | Compétences transférables |
| `skills_exposed` | Compétences exposées (sans expertise confirmée) |
| `kpis_verified` | KPIs réels (ex. `réduction de 20% des délais`) |
| `evidence_strength` | Force de la preuve (`high`, `medium`, `low`) |
| `cv_priority` | Priorité d'affichage (`1` = prioritaire) |

#### Feuille `leadership`

| Colonne | Description |
|---|---|
| `Organisation` | Nom de l'association / projet |
| `Role` | Rôle occupé |
| `City` | Ville |
| `Year` | Année ou période |
| `truth_bullet_1` à `truth_bullet_5` | Bullets factuels (max 5) |

#### Feuille `certifications`

| Colonne | Description |
|---|---|
| `cert_name` | Nom de la certification |
| `issuer` | Organisme émetteur |
| `date_obtained` | Date d'obtention |
| `related_families` | Familles métier associées |
| `status` | Statut (`obtained`, `in progress`) |

#### Feuille `skills`

| Colonne | Description |
|---|---|
| `skill_name` | Nom de la compétence technique |
| `skill_family` | Famille (ex. `supply`, `data`, `marketing`) |
| `type` | Type (`tool`, `method`, `soft`) |

---

### Étape 5 — Préparer le template CV

```bash
cp templates/base_cv_example.docx templates/base_cv.docx
```

Ouvrir `base_cv.docx` dans Word et personnaliser la mise en page (nom, contact, couleurs, polices...).

Les placeholders suivants sont remplacés automatiquement par le script :

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
| `[[TECHNICAL_SKILLS]]` | Compétences techniques (liste) |
| `[[CERTIFICATION_ENTRIES]]` | Certifications (liste) |

> Les placeholders `[[EXP_1_COMPAGNY]]` (faute d'orthographe) sont aussi supportés pour compatibilité.

---

### Étape 6 — Ajouter la job description

Coller l'offre d'emploi dans :

```
data/input/job_description.txt
```

---

## Lancer la génération

Commande unique (génération + Google Sheets) :

```bash
python3 run.py
```

Génération uniquement (sans Google Sheets) :

```bash
python3 -m src.generate_cv
```

Le CV est généré dans `data/output/` avec un nom du type :
```
CV_Prenom_Nom_Entreprise_Poste_20260427_143022.docx
```

---

## Gemini — optimisation des bullets

Quand Gemini est activé, le script fait **1 seul appel par CV** (tout le CV en un JSON) et tourne entre plusieurs modèles automatiquement :

```
CV 1 → gemini-2.5-flash-lite
CV 2 → gemini-2.5-flash
CV 3 → gemini-2.5-flash-preview-05-20
CV 4 → gemini-2.5-flash-lite
...
```

Avec les paramètres par défaut :
- 3 modèles × 20 appels/jour = **60 CV optimisés par jour**
- Si Gemini échoue (quota, erreur réseau, JSON invalide) → le CV est quand même généré avec les bullets originaux

---

## Structure du projet

```
cv-tailor/
├── data/
│   ├── input/                      ← job_description.txt (non versionné)
│   ├── reference/
│   │   ├── master_profile_example.xlsx   ← modèle vide (versionné)
│   │   └── master_profile.xlsx           ← ton fichier réel (non versionné)
│   └── output/                     ← CV générés (non versionné)
├── templates/
│   ├── base_cv_example.docx        ← template exemple (versionné)
│   └── base_cv.docx                ← ton template réel (non versionné)
├── credentials/
│   └── service_account.json        ← clé Google (non versionné)
├── src/
│   ├── generate_cv.py              ← moteur principal
│   ├── llm/
│   │   ├── gemini_client.py        ← client Gemini + rotation
│   │   └── cv_enhancer.py          ← optimisation bullets
│   ├── render/
│   │   └── docx_template.py        ← injection placeholders DOCX
│   └── tracker/
│       └── google_sheets_tracker.py ← suivi Google Sheets
├── run.py                          ← commande unique
├── .env.example                    ← variables d'environnement (modèle)
└── requirements.txt
```

---

## Sécurité — fichiers à ne jamais pousser

Ces fichiers contiennent des données personnelles ou des clés sensibles :

```
.env
credentials/service_account.json
data/reference/master_profile.xlsx
data/input/job_description.txt
data/output/
templates/base_cv.docx
```

Vérifier avant chaque push :

```bash
git ls-files | grep -E "(\.env$|service_account|master_profile\.xlsx|job_description|base_cv\.docx)"
```

Cette commande ne doit rien retourner.
