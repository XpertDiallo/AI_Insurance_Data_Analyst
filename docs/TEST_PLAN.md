# Plan de tests

## Automatisés

- détection/import CSV ;
- Excel/JSON ;
- profiling ;
- nettoyage et imputation ;
- sécurité des requêtes SQL ;
- KPI assurance ;
- analytics allow-list ;
- fallback Gemini via faux client ;
- génération HTML/PDF/DOCX/PPTX/XLSX ;
- persistance RAW/CURATED et audit.

## Intégration manuelle

- Streamlit dans navigateur ;
- Gemini avec vraie clé ;
- PostgreSQL réel ;
- SQL Server/Access selon infrastructure ;
- gros fichiers ;
- tests multi-utilisateurs/auth ;
- test Docker ;
- génération de rapports complexes avec charte entreprise.

## Go-live

Aucun défaut bloquant/critique, tests MUST réussis, KPI validés par le métier, secrets et RBAC validés, rollback testé.
