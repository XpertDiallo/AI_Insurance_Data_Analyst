# Déploiement

## 1. Pilote Streamlit

Convient à une démo ou un pilote avec faible volumétrie. Configurer `GOOGLE_API_KEY` dans les secrets de la plateforme.

## 2. Docker professionnel

1. construire l'image ;
2. pousser dans un registry ;
3. déployer sur Cloud Run, Render, Azure Container Apps, ECS/EKS ou serveur Docker ;
4. monter un stockage persistant pour `data/` et `artifacts/` ;
5. injecter les secrets au runtime ;
6. mettre HTTPS/reverse proxy ;
7. activer logs et monitoring.

## 3. Microsoft Access

L'accès dépend du pilote ODBC du système. Sur Windows, installer le Microsoft Access Database Engine et `pyodbc`. Pour Linux/containers, privilégier une migration vers PostgreSQL/SQL Server ou un service d'extraction intermédiaire.

## 4. Health check

Le Dockerfile utilise `/_stcore/health`.

## 5. Rollback

Taguer les images (`v2.0.0`, `v2.0.1`) et conserver la version précédente déployable.
