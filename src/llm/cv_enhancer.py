from src.llm.gemini_client import ask_gemini, is_gemini_enabled


def improve_cv_text_with_gemini(text: str, job_text: str) -> str:
    """
    Améliore un texte simple avec Gemini.
    Fallback : retourne le texte original.
    """

    if not is_gemini_enabled():
        return text

    if not text or not text.strip():
        return text

    prompt = f"""
Tu es un expert CV ATS.

Objectif :
Améliore ce texte de CV pour qu'il corresponde mieux à l'offre.

Contraintes strictes :
- ne mens pas
- n'invente aucun chiffre
- ne crée aucune expérience
- garde le sens original
- style professionnel
- phrase plus claire, plus directe, plus orientée impact
- français naturel
- réponse uniquement avec le texte amélioré, sans explication

Offre :
{job_text}

Texte CV original :
{text}
"""

    try:
        improved = ask_gemini(prompt)
        return improved if improved else text
    except Exception as error:
        print(f"[Gemini fallback] {error}")
        return text


def improve_bullets_with_gemini(bullets: list, job_text: str) -> list:
    """
    Améliore une liste de bullets en un seul appel Gemini.
    Fallback : retourne les bullets originales.
    """

    if not is_gemini_enabled():
        return bullets

    if not bullets:
        return bullets

    bullets_text = "\n".join([f"- {bullet}" for bullet in bullets])

    prompt = f"""
Tu es un expert CV ATS.

Objectif :
Réécris ces bullets de CV pour mieux correspondre à l'offre.

Contraintes strictes :
- conserve exactement le même nombre de bullets
- ne mens pas
- n'invente aucun chiffre
- n'ajoute aucune expérience
- garde le sens original
- améliore la clarté et l'impact
- style professionnel
- français naturel
- chaque bullet doit rester court
- réponse uniquement sous forme de liste avec un bullet par ligne
- aucun commentaire avant ou après

Offre :
{job_text}

Bullets CV originaux :
{bullets_text}
"""

    try:
        response = ask_gemini(prompt)

        improved_bullets = []
        for line in response.splitlines():
            cleaned = line.strip()
            cleaned = cleaned.lstrip("-").lstrip("•").lstrip("*").strip()

            if cleaned:
                improved_bullets.append(cleaned)

        if len(improved_bullets) != len(bullets):
            print("[Gemini fallback] Nombre de bullets différent, conservation des bullets originales.")
            return bullets

        return improved_bullets

    except Exception as error:
        print(f"[Gemini fallback] {error}")
        return bullets
