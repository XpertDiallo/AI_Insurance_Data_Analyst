# Changelog

## Correctif — Imputation interactive

- Affichage dynamique des variables contenant des NA avec leur volume de cellules manquantes.
- Imputation cellule par cellule avec choix de stratégie et journalisation du numéro de ligne.
- Réparation manuelle explicite autorisée pour une cellule d’identifiant ; les méthodes statistiques restent bloquées.
- Ajout d’un test de non-régression sur l’imputation ciblée.

## 2.0.0 — 2026-09-29

- Application Streamlit structurée par couches.
- Import CSV/Excel/JSON, détection CSV et contrôle de taille.
- Cycle RAW/STAGING/CURATED et lineage.
- Profiling, règles de qualité et nettoyage guidé.
- Connexions SQL read-only + support Access via ODBC hôte.
- Analyse NL sécurisée : plan JSON allow-list, aucun `eval/exec`.
- Gemini avec retries, timeout et fallback configurable.
- KPI assurance et dashboard portefeuille.
- Rapports HTML/PDF/DOCX/PPTX/XLSX.
- Auth optionnelle, rôles, audit, Docker, CI et tests.
