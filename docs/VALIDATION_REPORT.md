# Rapport de validation technique

Date : 01/10/2026

## Contrôles exécutés

- `python -m compileall -q insurance_ai app.py scripts` : **OK**.
- `pytest -q` : **18 tests réussis**.
- Smoke test Streamlit : serveur démarré sur un port local et `/_stcore/health` retourne HTTP 200 (`ok`).
- Smoke test bout-en-bout : import CSV `;`, profiling, dédoublonnage, imputation, RAW/CURATED, KPI S/P, dashboard, graphique PNG, rapports HTML/PDF/DOCX/PPTX/XLSX, SQLite : **OK**.
- Recherche de `eval()` / `exec()` dans le code applicatif : **aucun**.
- Recherche de clé Google hardcodée de forme `AIza...` : **aucune**.
- Les mots-clés SQL destructifs sont bloqués par le validateur ; le seul `INSERT` applicatif est interne au journal SQLite d'audit.
- Les identifiants projet/dataset et les chemins de fichiers sont contrôlés pour empêcher une sortie du répertoire de données ; les chemins de datasets sont portables (relatifs au projet).
- Les identifiants et mots de passe de connexion SQL sont encodés avant construction des URLs SQLAlchemy.

## Couverture fonctionnelle automatisée

- ingestion CSV/Excel/JSON ;
- détection CSV ;
- profiling ;
- nettoyage, cast, imputation, catégories ;
- règles de qualité ;
- SQL read-only + SQLite ;
- KPI assurance ;
- analytics allow-list ;
- dashboard ;
- fallback Gemini simulé ;
- project store RAW/CURATED ;
- graphiques ;
- reporting multi-format.

## Tests dépendants de l'environnement

Ils nécessitent des ressources externes et doivent être exécutés en recette :

- vrai appel Gemini avec `GOOGLE_API_KEY` ;
- PostgreSQL/MySQL/SQL Server réels ;
- Microsoft Access avec pilote ODBC local ;
- démarrage navigateur Streamlit ;
- déploiement Docker/cloud ;
- tests de charge et multi-utilisateurs.

La validation fournie garantit la cohérence du code et des modules testables dans l'environnement disponible ; elle ne peut garantir l'absence absolue de défaut sur des services externes non accessibles pendant cette génération.
