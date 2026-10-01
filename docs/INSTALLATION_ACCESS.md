# Microsoft Access

Le connecteur Access utilise `pyodbc` et nécessite un pilote ODBC Access installé sur la machine qui exécute l'application.

## Windows recommandé

1. Installer le **Microsoft Access Database Engine** compatible avec l'architecture Python (64 bits recommandé).
2. Vérifier le pilote : `Microsoft Access Driver (*.mdb, *.accdb)`.
3. Installer les dépendances Python (`pip install -r requirements.txt`).
4. Dans la page **Base SQL**, choisir **Microsoft Access**, téléverser `.mdb/.accdb`, puis connecter.

## Linux / Docker

Le pilote Microsoft Access officiel n'est généralement pas disponible. Pour un déploiement professionnel Linux, migrer Access vers PostgreSQL/SQL Server ou exposer une extraction sécurisée intermédiaire.
