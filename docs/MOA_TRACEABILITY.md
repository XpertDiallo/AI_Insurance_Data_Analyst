# Traçabilité CDC → code

| Domaine CDC | Implémentation principale |
|---|---|
| Ingestion | `services/ingestion.py`, page Importer |
| RAW/STAGING/CURATED | `core/project_store.py`, page Nettoyage |
| Profiling qualité | `services/profiling.py`, page Qualité |
| Nettoyage | `services/cleaning.py` |
| Bases SQL | `services/database.py`, page Base SQL |
| Questions NL | `agents/analysis_agent.py` |
| Gemini fallback | `services/gemini_manager.py` |
| KPI assurance | `services/insurance_kpi.py` |
| Dashboard | page Dashboard, Plotly |
| Reporting | `reports/generator.py` |
| Audit | `core/audit.py` |
| Auth/RBAC | `services/auth.py` + `scripts/create_user.py` |
| Docker/CI | `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` |

Le cahier des charges complet est inclus au format DOCX dans le même dossier `docs/`.
