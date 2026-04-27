from dotenv import load_dotenv
from src.llm.gemini_client import ask_gemini


def main():
    load_dotenv()

    result = ask_gemini("Réponds uniquement par : Gemini connecté.")
    print(result)


if __name__ == "__main__":
    main()
