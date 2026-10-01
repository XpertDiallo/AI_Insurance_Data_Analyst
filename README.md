# AI Insurance Data Analyst V2

Copilote professionnel d'analyse des données d'assurance : **Connect → Profile → Clean → Validate → Analyze → Explain → Visualize → Report → Export**.

## Fonctionnalités principales

- Import CSV/TXT avec détection du séparateur/encodage/décimale, Excel multi-feuilles et JSON.
- Cycle de données **RAW / STAGING / CURATED** avec métadonnées et journal des transformations.
- Profiling : NA, doublons, types, cardinalités, score qualité, statistiques descriptives.
- Nettoyage guidé : noms de variables, types, doublons, imputations, standardisation, filtres.
- Connexions SQL en lecture seule : PostgreSQL, SQLite, MySQL, SQL Server ; Access selon le pilote ODBC de l'hôte.
- Analyse en langage naturel avec **Gemini** ; les calculs restent déterministes via Pandas/SQL.
- Fallback Gemini configurable : par défaut `gemini-3.5-flash-lite → gemini-3.1-flash-lite → gemini-3.8-flash`.
- KPI assurance : S/P, coût moyen, fréquence, encaissement, cession, rétention.
- Dashboards Plotly/Streamlit.
- Rapports cohérents : **HTML, PDF, DOCX, PPTX, XLSX**.
- Audit SQLite local, RBAC/authentification optionnelle, Docker et CI.

## Installation locale

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# renseigner GOOGLE_API_KEY dans l'environnement/secret manager
streamlit run app.py
```

> Le fichier `.env` n'est jamais versionné. Streamlit Community Cloud utilise `Secrets`; Docker/Cloud doit utiliser un secret manager ou variables d'environnement sécurisées.

## Authentification

Par défaut `AUTH_ENABLED=false` pour faciliter le développement. Pour activer le mode multi-utilisateur :

```bash
export AUTH_ENABLED=true
python scripts/create_user.py admin --role admin --password 'ChangeMeNow!'
```

Rôles prévus : `admin`, `analyst`, `business`, `manager`, `auditor`.

## Gemini et fallback

Le service `GeminiModelManager` centralise tous les appels. L'ordre des modèles est configuré via :

```bash
GEMINI_MODELS=gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash
```

Le gestionnaire effectue retries/backoff puis passe au modèle suivant. Si Gemini est absent, les fonctions déterministes (profiling, nettoyage, KPI, rapports) restent utilisables ; l'agent NL dispose d'un fallback heuristique limité.

Les identifiants de modèles Gemini évoluent : vérifier les modèles disponibles avant chaque déploiement :
- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/gemini-api/docs/pricing

## Sécurité importante

- Le LLM **ne calcule jamais** les KPI : il planifie et explique. Pandas/SQL exécute.
- Le moteur NL n'exécute pas `eval()`/`exec()` ; il sélectionne une opération dans une allow-list.
- SQL est limité à `SELECT`/`WITH`; les opérations DDL/DML sont bloquées.
- Les identifiants potentiels ne sont pas imputés automatiquement.
- Le RAW n'est jamais écrasé.
- Ne jamais utiliser un compte DB avec droits d'écriture pour la V2.

## Déploiement Docker

```bash
docker build -t ai-insurance-data-analyst-v2 .
docker run --rm -p 8501:8501 \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -v "$PWD/data:/app/data" \
  -v "$PWD/artifacts:/app/artifacts" \
  ai-insurance-data-analyst-v2
```

Ou avec PostgreSQL de démonstration :

```bash
docker compose up --build
```

## Déploiement Streamlit Community Cloud

1. Publier ce dépôt sur GitHub.
2. Dans Streamlit Community Cloud, choisir `app.py` comme fichier principal.
3. Ajouter les secrets nécessaires dans `Settings > Secrets`, par exemple :

```toml
GOOGLE_API_KEY = "..."
AUTH_ENABLED = "false"
```

Le stockage local `data/`, `artifacts/` et `logs/` convient à une démonstration. Pour une utilisation métier, utiliser un stockage persistant et un secret manager ; les fichiers uploadés ne doivent pas être considérés comme une sauvegarde durable.

## Tests

```bash
python -m compileall -q insurance_ai app.py
pytest
```

Les tests réseau Gemini, PostgreSQL/Access et le rendu Streamlit réel sont des tests d'intégration dépendants de l'environnement ; ils ne sont pas exécutés hors secrets/serveurs externes.

## Documentation

- `docs/CDC_AI_Insurance_Data_Analyst_V2.docx` : cahier des charges MOA.
- `docs/ARCHITECTURE.md`
- `docs/USER_GUIDE.md`
- `docs/DEPLOYMENT.md`
- `docs/SECURITY.md`
- `docs/TEST_PLAN.md`
- `docs/MOA_TRACEABILITY.md`

Les fichiers de démonstration dans `sample_data/` contiennent 71 enregistrements fictifs, dont 5 doublons exacts et plusieurs valeurs manquantes pour tester le profilage, la déduplication et l’imputation cellule par cellule. Le script reproductible est `scripts/generate_sample_data.py`.

Le notebook pédagogique [`docs/AI_Insurance_Data_Analyst_Pedagogical.ipynb`](docs/AI_Insurance_Data_Analyst_Pedagogical.ipynb) explique les blocs de code, le cycle RAW/STAGING/CURATED, les services déterministes et l’orchestration Agentic AI.
