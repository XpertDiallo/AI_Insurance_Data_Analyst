# Architecture fonctionnelle et technique

## Couches

```text
Streamlit UI
    ↓
Supervisor / Agents
    ↓
Services déterministes
    ├─ Ingestion
    ├─ Profiling
    ├─ Cleaning
    ├─ Analytics
    ├─ Insurance KPI
    ├─ SQL read-only
    └─ Reporting
    ↓
ProjectStore + Audit

GeminiModelManager est transversal : compréhension/explication uniquement.
```

## Séparation des responsabilités

- `app.py` : interface et session utilisateur.
- `insurance_ai/agents` : orchestration et planification.
- `insurance_ai/services` : calculs et accès externes.
- `insurance_ai/core` : configuration, modèles, stockage, audit.
- `insurance_ai/reports` : rendu multi-format.

## Cycle de données

1. **RAW** : copie de la source, immuable fonctionnellement.
2. **STAGING** : transformations successives en mémoire/session.
3. **CURATED** : version validée et persistée, recommandée pour l'analyse.

## Analyse en langage naturel

Gemini reçoit uniquement le schéma et la question et retourne un plan JSON limité à une allow-list. Le plan est validé côté serveur puis exécuté par `AnalyticsService`. Aucun code Python généré n'est exécuté.

## Évolution production

La logique métier peut être exposée plus tard via FastAPI et un frontend React sans réécriture majeure. Pour les gros volumes, remplacer le stockage local par objet cloud + PostgreSQL metadata et exécuter les traitements dans des workers.
