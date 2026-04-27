import json
from copy import deepcopy

from src.llm.gemini_client import ask_gemini, is_gemini_enabled


def clean_json_response(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1).strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    return cleaned


def improve_full_cv_with_gemini(selected_experiences, selected_leadership, job_text):
    """
    Optimise tous les bullets du CV en un seul appel Gemini.
    Fallback : retourne les contenus originaux si Gemini échoue.
    """

    if not is_gemini_enabled():
        return selected_experiences, selected_leadership

    experiences_copy = deepcopy(selected_experiences)
    leadership_copy = deepcopy(selected_leadership)

    payload = {
        "experiences": [
            {
                "index": index,
                "company": exp.get("company", ""),
                "position": exp.get("position", ""),
                "bullets": exp.get("bullets", []),
            }
            for index, exp in enumerate(experiences_copy)
        ],
        "leadership": [
            {
                "index": index,
                "org": lead.get("org", ""),
                "role": lead.get("role", ""),
                "bullets": lead.get("bullets", []),
            }
            for index, lead in enumerate(leadership_copy)
        ],
    }

    prompt = f"""
Tu es un expert CV ATS.

Objectif :
Réécris les bullets du CV pour mieux correspondre à l'offre.

Contraintes strictes :
- ne mens pas
- n'invente aucun chiffre
- n'ajoute aucune expérience
- garde le sens original
- conserve exactement le même nombre de bullets pour chaque bloc
- améliore la clarté, l'impact et la correspondance avec l'offre
- style professionnel
- français naturel
- bullets courts
- ne modifie pas les noms d'entreprise, postes, lieux ou dates
- réponse uniquement en JSON valide
- aucun commentaire avant ou après

Format de réponse obligatoire :
{{
  "experiences": [
    {{
      "index": 0,
      "bullets": ["bullet 1", "bullet 2"]
    }}
  ],
  "leadership": [
    {{
      "index": 0,
      "bullets": ["bullet 1", "bullet 2"]
    }}
  ]
}}

Offre :
{job_text}

CV à optimiser :
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""

    try:
        response = ask_gemini(prompt)
        response_json = json.loads(clean_json_response(response))

        for item in response_json.get("experiences", []):
            index = item.get("index")
            new_bullets = item.get("bullets", [])

            if not isinstance(index, int) or index < 0 or index >= len(experiences_copy):
                continue

            old_bullets = experiences_copy[index].get("bullets", [])

            if len(new_bullets) == len(old_bullets):
                experiences_copy[index]["bullets"] = [
                    str(b).strip().lstrip("-").lstrip("•").lstrip("*").strip()
                    for b in new_bullets
                    if str(b).strip()
                ]

        for item in response_json.get("leadership", []):
            index = item.get("index")
            new_bullets = item.get("bullets", [])

            if not isinstance(index, int) or index < 0 or index >= len(leadership_copy):
                continue

            old_bullets = leadership_copy[index].get("bullets", [])

            if len(new_bullets) == len(old_bullets):
                leadership_copy[index]["bullets"] = [
                    str(b).strip().lstrip("-").lstrip("•").lstrip("*").strip()
                    for b in new_bullets
                    if str(b).strip()
                ]

        return experiences_copy, leadership_copy

    except Exception as error:
        print(f"[Gemini fallback full CV] {error}")
        return selected_experiences, selected_leadership
