import os
import time


def is_gemini_enabled() -> bool:
    return os.getenv("USE_GEMINI", "false").lower() in ["1", "true", "yes"]


def get_model_chain(model=None):
    """
    Retourne la liste des modèles à essayer dans l'ordre.
    Exemple :
    GEMINI_MODEL=gemini-3-flash-preview
    GEMINI_FALLBACK_MODELS=gemini-2.5-flash,gemini-2.5-flash-lite
    """

    primary_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    fallback_models_raw = os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-2.5-flash,gemini-2.5-flash-lite"
    )

    fallback_models = [
        item.strip()
        for item in fallback_models_raw.split(",")
        if item.strip()
    ]

    model_chain = [primary_model] + fallback_models

    # Supprime les doublons en gardant l'ordre
    seen = set()
    unique_models = []

    for item in model_chain:
        if item not in seen:
            unique_models.append(item)
            seen.add(item)

    return unique_models


def is_retryable_gemini_error(error: Exception) -> bool:
    """
    Erreurs temporaires : saturation, quota temporaire, service indisponible.
    """

    error_text = str(error).lower()

    retryable_patterns = [
        "503",
        "unavailable",
        "high demand",
        "temporarily",
        "timeout",
        "deadline",
        "429",
        "rate limit",
        "resource_exhausted",
    ]

    return any(pattern in error_text for pattern in retryable_patterns)


def ask_gemini(prompt, model=None):
    """
    Appelle Gemini avec :
    - plusieurs modèles fallback
    - retry court par modèle
    - erreur finale claire si tout échoue
    """

    if not is_gemini_enabled():
        raise RuntimeError("Gemini est désactivé. Mets USE_GEMINI=true dans .env.")

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY manquante dans .env.")

    try:
        from google import genai
    except ImportError:
        raise RuntimeError("Package google-genai manquant. Lance : pip install google-genai")

    client = genai.Client()

    model_chain = get_model_chain(model)
    wait_times = [0]

    errors = []

    for selected_model in model_chain:
        for wait_time in wait_times:
            if wait_time > 0:
                time.sleep(wait_time)

            try:
                print(f"[Gemini] Tentative modèle : {selected_model}")

                response = client.models.generate_content(
                    model=selected_model,
                    contents=prompt,
                )

                text = (response.text or "").strip()

                if text:
                    return text

                errors.append(f"{selected_model}: réponse vide")

            except Exception as error:
                errors.append(f"{selected_model}: {error}")

                if not is_retryable_gemini_error(error):
                    raise error

                print(f"[Gemini] Erreur temporaire sur {selected_model}, fallback/retry...")

    raise RuntimeError(
        "Gemini indisponible sur tous les modèles : "
        + " | ".join(errors[-5:])
    )
