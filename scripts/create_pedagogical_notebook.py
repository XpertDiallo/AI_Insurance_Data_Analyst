"""Generate a detailed pedagogical notebook for the application."""
from __future__ import annotations
import json
from pathlib import Path

def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)}

def py(text: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text.splitlines(True)}

def main() -> None:
    cells = [
        md("""## Guide de lecture — 18 blocs dans l’ordre

La progression suit le fonctionnement réel : comprendre l’architecture, préparer l’environnement et la mémoire, charger et fiabiliser les données, calculer les indicateurs, puis activer l’orchestration Agent IA et ses garde-fous LLM.

1. Architecture · 2. Structure de l’Agent IA · 3. Bibliothèques Python · 4. Configuration et secrets · 5. Mémoire Streamlit · 6. Ingestion · 7. Qualité · 8. Nettoyage · 9. Versions · 10. KPI · 11. Dashboard · 12. Analytics · 13. Agents · 14. Gemini · 15. Switches LLM · 16. Clé API · 17. Reporting et sécurité · 18. Rôle du LLM. Les flux complets et limites sont présentés en annexes.
"""),
        md("""# AI Insurance Data Analyst V2 — notebook pédagogique\n\nCe notebook explique bloc par bloc le code de l’application et son lien avec l’orchestration Agentic AI.\n\nPrincipe directeur : **l’IA comprend l’intention et explique ; les services déterministes calculent et modifient les données**.\n\nParcours : `CONNECT → PROFILE → CLEAN → VALIDATE → ANALYZE → EXPLAIN → VISUALIZE → REPORT → EXPORT`.\n"""),
        md("""## 1. Architecture globale\n\n```text\nUtilisateur → Streamlit/app.py → SupervisorAgent/AnalysisAgent\n                                      │\n        ┌─────────────────────────────┴─────────────────────────────┐\n        │ Ingestion │ Profiling │ Cleaning │ Analytics │ KPI │ Report │\n        └─────────────────────────────┬─────────────────────────────┘\n                                      ▼\n                           ProjectStore + AuditLogger\n\nGeminiModelManager : planification JSON et explication, jamais calcul financier.\n```\n\nUne boucle agentique observe l’état, planifie, choisit un outil autorisé, exécute, vérifie et journalise. Elle ne lance pas de Python arbitraire.\n"""),
        md("""## 1.1 Structure réelle de l’Agent IA créé dans l’application

L’application met en place un **agent hybride et gouverné**, et non un chatbot qui exécute librement du code :

```text
Question / action → Streamlit + session_state
                           ↓
                    SupervisorAgent
                    route(profile/clean/ask)
                           ↓
                    AnalysisAgent
                 schéma → plan → validation
                      ↙          ↘
        AnalyticsService        GeminiModelManager
        calcul Pandas            JSON / explication
                      ↓
             résultat + méthode + audit
```

**Rôle des composants :**

- `SupervisorAgent` route les intentions vers profilage, nettoyage ou analyse ; ce routage critique est déterministe.
- `AnalysisAgent` transforme une question en plan structuré (`operation`, `column`, `filters`, `group_by`, `chart_type`) puis le valide.
- `AnalyticsService` exécute uniquement les opérations autorisées avec Pandas. Aucun Python ou SQL généré n’est exécuté.
- `GeminiModelManager` peut proposer un plan JSON et rédiger une explication, mais ne calcule pas les KPI et ne modifie pas directement le DataFrame.
- `ProfilingService`, `CleaningService`, `InsuranceKPIService`, `DashboardService` et les services de reporting sont les outils métier déterministes.
- `ProjectStore` persiste les versions ; `AuditLogger` trace les transformations, analyses et exports.

Cette structure suit le pattern **planner → validator → tool executor → verifier/auditor**. La dimension agentique vient de l’orchestration contrôlée et de la gestion d’état.
"""),
        py("""from insurance_ai.agents.analysis_agent import AnalysisAgent
from insurance_ai.agents.supervisor import SupervisorAgent
from insurance_ai.services.analytics import AnalyticsService

supervisor = SupervisorAgent()
agent = AnalysisAgent(analytics=AnalyticsService())
print('Routage analyse :', supervisor.route('analyze'))
print('Opérations autorisées :', sorted(agent.analytics.OPS))
print('LLM activé :', agent.llm.enabled)
"""),
        py("""from pathlib import Path
import pandas as pd
PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / 'insurance_ai').exists(): PROJECT_ROOT = PROJECT_ROOT.parent
DATA_PATH = PROJECT_ROOT / 'sample_data' / 'insurance_sample.csv'
df = pd.read_csv(DATA_PATH)
print(len(df), 'lignes |', len(df.columns), 'colonnes')
print('doublons =', int(df.duplicated().sum()), '| NA =', int(df.isna().sum().sum()))
df.head()
"""),
        md("""## Grandes composantes Python et utilité Agent IA\n\nLes dépendances sont organisées par responsabilité :\n\n- **Interface et état** : `streamlit` affiche les pages, widgets, messages et téléchargements ; `st.session_state` conserve la mémoire de travail du workflow.\n- **Données et calcul** : `pandas` manipule les DataFrames, `numpy` fournit les opérations numériques, `pyarrow/openpyxl/xlrd` gèrent Parquet et Excel.\n- **Visualisation** : `plotly` produit les graphiques interactifs ; `matplotlib` génère les images utilisées dans les rapports.\n- **Bases** : `sqlalchemy` abstrait les moteurs, `psycopg`, `pymysql` et `pyodbc` fournissent les connecteurs PostgreSQL, MySQL et ODBC.\n- **IA et contrats** : `google-genai` appelle Gemini ; `pydantic` et les dataclasses structurent les résultats et plans ; l’agent reste limité à des opérations allow-listées.\n- **Rapports** : `jinja2`, `reportlab`, `python-docx` et `python-pptx` alimentent les formats HTML, PDF, DOCX et PPTX.\n- **Sécurité/configuration** : `python-dotenv` charge l’environnement, `bcrypt` protège les mots de passe, `chardet` aide à détecter les encodages.\n- **Qualité** : `pytest` vérifie les parcours critiques avant déploiement.\n\nCette séparation transforme un LLM généraliste en orchestrateur d’outils spécialisés : il choisit l’outil, mais ne remplace pas les bibliothèques déterministes.\n"""),
        md("""## 2. Configuration et initialisation de `app.py`\n\n`core/config.py` construit `Settings` à partir des variables d’environnement : répertoires, taille maximale d’upload, clé Gemini, modèles autorisés, retries et timeout. Les secrets ne sont jamais codés dans l’application.\n\n`app.py` instancie `ProjectStore`, `AuditLogger`, `IngestionService`, `ProfilingService`, `CleaningService`, `DashboardService`, `ReportGenerator`, etc. `st.session_state` conserve utilisateur, projet, dataset actif et résultats entre deux reruns.\n\nLe rechargement défensif des services traite les processus Streamlit qui gardent un ancien module Python en mémoire.\n"""),
        py("""import os\nprint('APP_ENV =', os.getenv('APP_ENV', 'development'))\nprint('Gemini configuré =', bool(os.getenv('GOOGLE_API_KEY')))\nprint('Limite upload =', os.getenv('MAX_UPLOAD_MB', '200'), 'MB')\n"""),
        md("""## Mémoire de l’agent et fonctionnement Streamlit\n\nStreamlit réexécute `app.py` après une interaction. La mémoire courte est donc explicitement placée dans `st.session_state` : utilisateur, `project_id`, `df`, stade RAW/STAGING/CURATED, résultats d’analyse, graphiques et aperçu RAW.\n\nLa mémoire durable est séparée : `ProjectStore` conserve les versions de datasets et `AuditLogger` conserve les événements SQLite. `analysis_results` garde les résultats utiles au rapport, mais ce projet ne prétend pas être une mémoire conversationnelle complète : l’historique NL est structuré par résultats, pas par une conversation libre illimitée.\n\n`st.rerun()` recharge l’interface après une mutation afin que les sélecteurs, les NA et les cartes reflètent immédiatement le nouvel état. `st.cache_data` n’est pas utilisé par défaut : l’état métier doit rester explicite et éviter de mélanger les sessions.\n"""),
        md("""## 3. Ingestion et prévisualisation RAW\n\n`IngestionService` détecte encodage, séparateur et décimale des CSV, liste les feuilles Excel et aplati les JSON tabulaires. La page Importer contrôle la taille, affiche le parsing puis appelle `save_version(..., stage='RAW')`.\n\nL’aperçu RAW est conservé dans la session pour rester visible après un rerun ou un nettoyage STAGING. RAW est la copie de la source et ne doit pas être écrasé.\n"""),
        py("""from insurance_ai.services.ingestion import IngestionService\ningestion = IngestionService()\ndetection = ingestion.detect_csv(DATA_PATH.read_bytes())\nloaded, info = ingestion.read_uploaded(DATA_PATH.name, DATA_PATH.read_bytes())\nprint(detection)\nprint(info)\nloaded.head(3)\n"""),
        md("""## 4. Profilage et qualité\n\n`ProfilingService.profile(df)` calcule dimensions, types, types sémantiques, NA, cardinalité, exemples, min/max/moyenne/médiane et score qualité. Il ne modifie pas le DataFrame.\n\nLes règles métier (`not_null`, `unique`, `non_negative`, `allowed_values`, `date_order`) évaluent les violations et peuvent alimenter un rapport.\n"""),
        py("""from insurance_ai.services.profiling import ProfilingService\nprofile = ProfilingService().profile(df)\nprint(profile.summary)\nprint('doublons =', profile.duplicate_rows)\nprofile.columns[['column', 'missing', 'missing_pct', 'semantic_type']]\n"""),
        md("""## 5. Nettoyage et imputation cellule par cellule\n\n`CleaningService` expose normalisation, déduplication, cast, catégories, filtres et imputation. L’UI liste dynamiquement les variables avec NA, sélectionne une ligne, choisit une stratégie puis appelle `impute_cell`. Après chaque action, Streamlit rerun, recalcule les NA et écrit un `TransformationRecord`.\n\nLes identifiants potentiels ne peuvent recevoir qu’une valeur manuelle vérifiée : une moyenne ne doit jamais inventer une clé de police ou de sinistre.\n"""),
        py("""from insurance_ai.services.cleaning import CleaningService\ncleaner = CleaningService()\npositions = [i for i, missing in enumerate(df['region'].isna()) if missing]\noutcome = cleaner.impute_cell(df, 'region', positions[0], 'manual', 'Abidjan')\nprint(outcome.details)\nprint('NA avant/après =', df.region.isna().sum(), outcome.dataframe.region.isna().sum())\n"""),
        md("""## 6. Versions RAW / STAGING / CURATED\n\n`ProjectStore` écrit les datasets dans un projet et conserve source, stade, parent, dimensions, empreinte et chemin relatif. RAW conserve la source ; STAGING porte les transformations ; CURATED est la version validée et autorisée pour les analyses.\n"""),
        py("""from tempfile import TemporaryDirectory\nfrom insurance_ai.core.project_store import ProjectStore\nwith TemporaryDirectory() as folder:\n    store = ProjectStore(folder)\n    project_id = store.create_project('Notebook', owner='demo')\n    raw_meta = store.save_dataframe(project_id, df, name='sample', stage='RAW', source_type='csv', source_name=DATA_PATH.name)\n    print(raw_meta.to_dict())\n"""),
        md("""## 7. KPI assurance déterministes\n\n`InsuranceKPIService` calcule S/P, coût moyen, fréquence, encaissement, cession et rétention. Les résultats contiennent valeur, formule et avertissements ; les dénominateurs nuls sont traités. Gemini ne produit jamais ces chiffres.\n"""),
        py("""from insurance_ai.services.insurance_kpi import InsuranceKPIService\nkpis = InsuranceKPIService()\nloss_ratio = kpis.loss_ratio(df, 'claim_amount', 'written_premium')\nprint(loss_ratio)\nprint(kpis.as_display(loss_ratio))\n"""),
        md("""## 8. Dashboard sur RAW et CURATED\n\n`DashboardService.metric_columns` filtre selon le sens métier : primes (`written_premium`, `collected_premium`, `ceded_premium`, `net_premium`) et sinistres (`claim_amount`, coûts ou montants). Les identifiants sont exclus.\n\nLe même service reçoit le DataFrame RAW ou CURATED actif et produit cartes KPI, segments, tendances et principaux sinistres.\n"""),
        py("""from insurance_ai.services.dashboard import DashboardService\ndashboard = DashboardService()\npremium_cols = dashboard.metric_columns(df, 'premium')\nclaim_cols = dashboard.metric_columns(df, 'claims')\nprint('primes =', premium_cols)\nprint('sinistres =', claim_cols)\nview = dashboard.portfolio_overview(df, premium_col=premium_cols[0], claims_col=claim_cols[0], group_col='branch', date_col='effective_date')\nview.cards\n"""),
        md("""## 9. Analytics allow-listées\n\n`AnalyticsService.OPS` autorise seulement description, comptage, agrégations, top valeurs et corrélations. Les filtres sont limités à `==`, `!=`, `>`, `>=`, `<`, `<=`, `contains`.\n\nMême si Gemini propose un plan invalide, `_validate_plan` le rejette avant exécution. Aucun `eval()`/`exec()` n’est utilisé.\n"""),
        py("""from insurance_ai.services.analytics import AnalyticsService\nanalytics = AnalyticsService()\nresult = analytics.execute(df, {'operation': 'mean', 'column': 'written_premium', 'filters': []})\nprint(result.answer)\nprint(result.calculation)\n"""),
        md("""## 10. SupervisorAgent et AnalysisAgent\n\n`SupervisorAgent.route()` choisit profilage, nettoyage ou analyse. `AnalysisAgent` résume le schéma, demande éventuellement à Gemini un plan JSON, valide opération/colonnes/filtres puis délègue à `AnalyticsService`.\n\nSans clé Gemini, une heuristique offline reconnaît moyenne, somme, corrélation, top valeurs et description. Avec Gemini, seul le plan est généré ; Pandas calcule.\n"""),
        py("""from insurance_ai.agents.supervisor import SupervisorAgent\nsupervisor = SupervisorAgent()\nprint(supervisor.route('analyze'))\nanswer, plan = supervisor.ask('Quelle est la moyenne de written_premium ?', df)\nprint('plan =', plan)\nprint('résultat =', answer.data)\nprint('calcul =', answer.calculation)\n"""),
        md("""## 11. GeminiModelManager : fallback et gouvernance\n\nLe gestionnaire centralise timeout, retries avec backoff, modèles de secours et latence. `generate_json` parse les plans. Si tous les modèles échouent, qualité, nettoyage, KPI, dashboard et reporting restent disponibles.\n\nLe prompt reçoit un résumé de schéma plutôt que le dataset complet ; l’explication reçoit un résultat compact et doit mentionner la méthode sans inventer de nombres.\n"""),
        md("""## 12. Reporting, audit et sécurité\n\n`ReportPayload` alimente les rendus HTML/PDF/DOCX/PPTX/XLSX. `AuditLogger` journalise transformations, analyses et exports dans SQLite avec requêtes paramétrées.\n\nGarde-fous : secrets hors Git, uploads limités, SQL lecture seule, chemins confinés, RAW préservé, identifiants protégés, opérations NL allow-listées et séparation logique des projets.\n"""),
        py("""from insurance_ai.core.models import TransformationRecord\nrecord = TransformationRecord(transformation_id='demo-001', dataset_id='raw-demo', operation='impute_cell', column='region', parameters={'row_position': 9, 'strategy': 'manual', 'value': 'Abidjan'}, rows_before=len(df), rows_after=len(df), user='demo')\nrecord.to_dict()\n"""),
        md("""## 13. Flux complet Agentic AI\n\n```text\nQuestion → observation du schéma/session → plan JSON\n        → validation allow-list → outil Pandas/KPI/dashboard\n        → résultat déterministe → explication Gemini\n        → audit + ajout éventuel au rapport\n```\n\nLa valeur agentique vient de la coordination des outils et de la gestion de l’état. La sécurité vient de la validation avant l’action. Une évolution possible est de séparer des agents Ingestion, Qualité, Assurance, Visualisation et Reporting en conservant les mêmes contrats déterministes.\n"""),
        md("""## Références du dépôt\n\n- `app.py` : UI Streamlit, session et parcours utilisateur\n- `insurance_ai/agents/analysis_agent.py` : planification/explanation NL\n- `insurance_ai/agents/supervisor.py` : routage\n- `insurance_ai/services/analytics.py` : opérations allow-listées\n- `insurance_ai/services/gemini_manager.py` : fallback Gemini\n- `insurance_ai/core/project_store.py` : versions RAW/STAGING/CURATED\n- `insurance_ai/core/audit.py` : audit SQLite\n- `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/MOA_TRACEABILITY.md` : documentation de référence\n"""),
        md("""## 14. Lecture pédagogique d’un cycle agentique complet

Pour « Quelle est la moyenne de `written_premium` ? », le cycle réel est :

1. **Observer** : l’agent reçoit la question et un résumé du schéma, pas le dataset complet envoyé au modèle.
2. **Planifier** : Gemini retourne un JSON si disponible ; sinon l’heuristique locale détecte la moyenne et la colonne.
3. **Valider** : opération, colonnes et opérateurs de filtre sont contrôlés côté serveur.
4. **Exécuter** : `AnalyticsService.execute()` calcule avec Pandas et conserve valeur, formule et avertissements.
5. **Expliquer** : Gemini peut reformuler le résultat compact sans inventer de nombre ; le fallback reste disponible.
6. **Tracer** : le résultat peut rejoindre le rapport et l’action être journalisée par `AuditLogger`.

Pour une imputation, l’utilisateur sélectionne explicitement la cellule dans Streamlit. `CleaningService.impute_cell` contrôle le type et les identifiants potentiels, puis la transformation passe en STAGING et est auditée. L’IA ne décide donc jamais seule de remplacer une clé de police ou de sinistre.
"""),
        md("""## 15. Limites et bonnes pratiques d’un Agent IA en production

- **Déterminisme métier** : primes, sinistres, S/P et rétentions restent calculés par du code testé.
- **Contrat de sortie** : le modèle produit un JSON limité ; aucun SQL arbitraire ou Python généré n’est exécuté.
- **Minimisation** : le modèle reçoit un schéma et des résultats compacts, pas nécessairement toutes les données sensibles.
- **Résilience** : retries, modèles de secours et mode offline permettent de continuer sans Gemini.
- **Réversibilité** : RAW est conservé, les transformations sont versionnées et les opérations critiques sont auditées.
- **Évaluation** : les tests couvrent plans invalides, colonnes inconnues, données vides et erreurs de modèle.

Ce compromis est adapté à l’assurance : l’agent accélère la compréhension et la navigation, tandis que les règles de calcul et de sécurité restent sous contrôle logiciel.
"""),
        md("""## 16. Modèles LLM utilisés, switches et stratégie de fallback

`GeminiModelManager` est la passerelle LLM unique de l’application. Le code ne dépend pas d’un modèle écrit en dur dans l’interface : `Settings` lit `GEMINI_MODELS`, une liste ordonnée séparée par des virgules.

Configuration par défaut du dépôt :

```text
1. gemini-3.5-flash-lite
2. gemini-3.1-flash-lite
3. gemini-3.8-flash
```

Le **switch de modèle** est automatique : pour chaque modèle, le gestionnaire tente l’appel jusqu’à `GEMINI_MAX_RETRIES` retries. Après les échecs du modèle courant, il passe au modèle suivant. La réponse indique le modèle réellement utilisé, le nombre de tentatives, la latence et si un fallback a été nécessaire.

Les switches de comportement sont :

- `GOOGLE_API_KEY` présente : planification JSON et explication LLM activées ;
- clé absente ou client indisponible : mode offline, heuristique NL limitée, calculs métier toujours disponibles ;
- `json_mode=True` : demande de réponse JSON pour les plans, avec température basse (`0.1`) ;
- timeout configurable via `GEMINI_TIMEOUT_SECONDS` ;
- retries avec backoff borné (`1.5 × 2^n`, plafonné à 8 secondes).

Le modèle reste donc interchangeable. Pour ajouter un modèle compatible, on modifie la variable de configuration, sans changer `AnalysisAgent` ni les services de calcul.
"""),
        py("""from insurance_ai.core.config import settings
from insurance_ai.services.gemini_manager import GeminiModelManager

manager = GeminiModelManager()
print('Modèles configurés :', manager.models)
print('Timeout :', manager.timeout_seconds, 'secondes')
print('Retries par modèle :', manager.max_retries)
print('LLM activé :', manager.enabled)
print('Clé exposée :', bool(manager.api_key), '(la valeur n’est jamais affichée)')
"""),
        md("""## 17. Stockage sécurisé de la clé API Gemini

La clé est lue par `core/config.py` : d’abord depuis la variable d’environnement `GOOGLE_API_KEY`, puis depuis `st.secrets` si l’application tourne avec une configuration Streamlit. Elle est ensuite transmise uniquement au client `google-genai`. Elle n’est jamais incluse dans le prompt, le rapport, l’audit, le notebook ou les logs applicatifs.

**En local :** copier `.env.example` vers `.env` et renseigner `GOOGLE_API_KEY`. Le `.gitignore` exclut `.env`; il ne faut jamais committer ce fichier.

**Streamlit Community Cloud :** placer la clé dans `Settings → Secrets`. Le helper `_secret_or_env()` la récupère via `st.secrets` :

```toml
GOOGLE_API_KEY = "votre-cle-secrete"
GEMINI_MODELS = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash"
```

**Docker, CI/CD ou cloud privé :** injecter `GOOGLE_API_KEY` comme variable d’environnement ou via un secret manager. Ne pas la passer en argument de commande, ne pas l’inscrire dans Git et ne pas l’afficher dans `st.write`, `print` ou une trace.

La valeur peut être remplacée au runtime par un fournisseur de secrets ; le code métier ne change pas. En cas de rotation, remplacer le secret côté plateforme et redémarrer l’application. Si une clé a été exposée, la révoquer immédiatement auprès de Google et en générer une nouvelle.
"""),
        md("""## 18. Ce que le LLM fait et ne fait pas

| Fonction | LLM Gemini | Code local testé |
|---|---:|---:|
| Comprendre une question NL | Oui | Fallback heuristique |
| Proposer un plan JSON | Oui | Oui, plan offline |
| Valider une colonne/opération | Non | Oui, `AnalysisAgent._validate_plan` |
| Calculer un KPI assurance | Non | Oui, `InsuranceKPIService` |
| Modifier une cellule | Non | Oui, action Streamlit + `CleaningService` |
| Rédiger une explication | Oui, optionnel | Résultat déterministe conservé |

Cette séparation limite les hallucinations : le modèle peut orienter et expliquer, mais les chiffres, les transformations et les autorisations restent sous contrôle de l’application.
"""),
    ]
    groups: list[list[dict]] = []
    current: list[dict] = []
    for cell in cells:
        if cell['cell_type'] == 'markdown' and current:
            groups.append(current)
            current = []
        current.append(cell)
    if current:
        groups.append(current)
    order = {
        '# AI Insurance': 0,
        '## Guide de lecture': 1,
        '## 1. Architecture globale': 2,
        '## 1.1 Structure réelle': 3,
        '## Grandes composantes': 4,
        '## 2. Configuration': 5,
        '## Mémoire de l’agent': 6,
        '## 3. Ingestion': 7,
        '## 4. Profilage': 8,
        '## 5. Nettoyage': 9,
        '## 6. Versions': 10,
        '## 7. KPI': 11,
        '## 8. Dashboard': 12,
        '## 9. Analytics': 13,
        '## 10. SupervisorAgent': 14,
        '## 11. GeminiModelManager': 15,
        '## 16. Modèles LLM': 16,
        '## 17. Stockage sécurisé': 17,
        '## 12. Reporting': 18,
        '## 18. Ce que le LLM': 19,
        '## 13. Flux complet': 20,
        '## 14. Lecture pédagogique': 21,
        '## 15. Limites': 22,
        '## Références': 23,
    }
    def group_rank(group: list[dict]) -> int:
        first = ''.join(group[0].get('source', [])).splitlines()[0]
        return next((rank for prefix, rank in order.items() if first.startswith(prefix)), 999)

    groups.sort(key=group_rank)
    display_titles = {
        '## 1. Architecture globale': '## Bloc 1 — Architecture globale',
        '## 1.1 Structure réelle': '## Bloc 2 — Structure réelle de l’Agent IA',
        '## Grandes composantes': '## Bloc 3 — Grandes composantes Python et utilité Agent IA',
        '## 2. Configuration': '## Bloc 4 — Configuration et initialisation de Streamlit',
        '## Mémoire de l’agent': '## Bloc 5 — Mémoire de l’agent et cycle Streamlit',
        '## 3. Ingestion': '## Bloc 6 — Ingestion et prévisualisation RAW',
        '## 4. Profilage': '## Bloc 7 — Profilage et qualité',
        '## 5. Nettoyage': '## Bloc 8 — Nettoyage et imputation cellule par cellule',
        '## 6. Versions': '## Bloc 9 — Versions RAW / STAGING / CURATED',
        '## 7. KPI': '## Bloc 10 — KPI assurance déterministes',
        '## 8. Dashboard': '## Bloc 11 — Dashboard sur RAW et CURATED',
        '## 9. Analytics': '## Bloc 12 — Analytics allow-listées',
        '## 10. SupervisorAgent': '## Bloc 13 — SupervisorAgent et AnalysisAgent',
        '## 11. GeminiModelManager': '## Bloc 14 — GeminiModelManager et gouvernance LLM',
        '## 16. Modèles LLM': '## Bloc 15 — Modèles LLM, switches et fallback',
        '## 17. Stockage sécurisé': '## Bloc 16 — Stockage sécurisé de la clé API Gemini',
        '## 12. Reporting': '## Bloc 17 — Reporting, audit et sécurité',
        '## 18. Ce que le LLM': '## Bloc 18 — Ce que le LLM fait et ne fait pas',
        '## 13. Flux complet': '## Annexe A — Flux complet Agentic AI',
        '## 14. Lecture pédagogique': '## Annexe B — Lecture d’un cycle agentique complet',
        '## 15. Limites': '## Annexe C — Limites et bonnes pratiques en production',
    }
    for group in groups:
        first = ''.join(group[0].get('source', [])).splitlines()[0]
        for prefix, title in display_titles.items():
            if first.startswith(prefix):
                group[0]['source'][0] = title + '\n'
                break
    cells = [cell for group in groups for cell in group]
    notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}
    destination = Path(__file__).resolve().parents[1] / 'docs' / 'AI_Insurance_Data_Analyst_Pedagogical.ipynb'
    destination.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding='utf-8')
    print(destination)

if __name__ == '__main__':
    main()
