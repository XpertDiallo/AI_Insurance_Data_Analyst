# Sécurité

## Menaces principales

- fuite de secrets ;
- injection SQL ;
- exécution de code arbitraire ;
- mélange de données entre utilisateurs ;
- uploads malveillants ;
- génération de chiffres non calculés par le LLM ;
- exposition de données sensibles à un fournisseur externe.

## Mesures V2

- secrets par variables d'environnement/secret manager ;
- requêtes SQL `SELECT/WITH` uniquement et blocage lexical DDL/DML ;
- absence d'`eval`/`exec` pour les requêtes NL ;
- RBAC optionnel et authentification bcrypt ;
- RAW non écrasé ;
- journal d'audit ;
- minimisation des données transmises à Gemini : schéma, plan et résultats compacts ;
- limites d'upload au niveau Streamlit + reverse proxy/cloud ;
- volumes SQL plafonnés ;
- validation des identifiants et confinement des chemins de datasets dans le répertoire du projet ;
- encodage des identifiants SQL dans les URLs générées ;
- logs sans mots de passe.

## À renforcer avant production sensible

- SSO/OIDC d'entreprise ;
- stockage chiffré au repos ;
- antivirus/scan des uploads ;
- secret manager cloud ;
- réseau privé pour bases internes ;
- DLP/anonymisation ;
- tests SAST/DAST ;
- isolation conteneur/worker pour traitements lourds ;
- politique de rétention et purge automatisée ;
- revue juridique de l'usage de données personnelles.
