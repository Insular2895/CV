from src.generate_cv import main as generate_cv
from src.tracker.google_sheets_tracker import append_report_to_tracker

print("=" * 50)
print("ÉTAPE 1 — Génération du CV")
print("=" * 50)
generate_cv()

print()
print("=" * 50)
print("ÉTAPE 2 — Envoi vers Google Sheets")
print("=" * 50)
append_report_to_tracker()
