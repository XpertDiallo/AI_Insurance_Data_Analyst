# Limites connues et décisions V2

- Streamlit conserve une partie de l'état en session : pour une forte concurrence, externaliser l'état et les jobs.
- Le fallback Gemini dépend des modèles réellement autorisés pour la clé/projet au moment du déploiement.
- Access dépend d'un pilote ODBC présent sur l'hôte ; le support est environnement-dépendant.
- Le SQL validator est un garde-fou applicatif, pas un substitut à un compte DB read-only.
- L'analyse NL V2 couvre une allow-list d'opérations plutôt qu'un Python REPL arbitraire, choix volontaire de sécurité.
- La détection CSV est heuristique : l'utilisateur peut corriger le délimiteur/encodage/décimale.
- Les KPI assurance doivent être validés avec le dictionnaire de données réel et les conventions brut/net/acquis/émis.
