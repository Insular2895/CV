# CV Tailor V1

Moteur local de personnalisation de CV basé sur un profil maître Excel et un template DOCX.

## Scope V1
- Lecture des feuilles Excel de référence
- Parsing simple d'une offre (URL et/ou texte collé)
- Détection initiale de mots-clés et famille métier
- Sélection de données pour un premier rendu
- Injection de placeholders dans un template DOCX
- Génération d'un DOCX de test

## Structure
- `src/loaders/excel_loader.py` : lecture et validation des feuilles Excel
- `src/parsers/job_parser.py` : parsing simple de job description
- `src/render/docx_template.py` : injection de placeholders dans le DOCX
- `src/render_test.py` : script de test de bout en bout

## Fichiers attendus
- `data/reference/master_profile.xlsx`
- `data/reference/job_families_refined.xlsx` (optionnel)
- `templates/base_cv.docx`

## Installation
```bash
pip install -r requirements.txt
```

## Lancement test
```bash
python -m src.render_test
```

## Remarques
- Les placeholders du DOCX doivent rester en texte simple et ne pas être coupés en plusieurs styles Word.
- Le script V1 ne branche pas encore Gemini. Il prépare le pipeline local et le rendu de test.
