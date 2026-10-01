# Guide utilisateur

1. **Créer/nommer le projet** dans Importer.
2. **Importer** un CSV/Excel/JSON ou connecter une base SQL.
3. Vérifier le parsing CSV proposé ; corriger le délimiteur si nécessaire.
4. Aller dans **Qualité** pour examiner NA, doublons et types.
5. Effectuer les corrections dans **Nettoyage** ; chaque action est traçable.
6. Cliquer **Créer la version CURATED** après validation métier.
7. Utiliser **Analyse IA** pour poser des questions ; le plan JSON et le calcul sont visibles.
8. Utiliser **Assurance KPI** pour les ratios déterministes.
9. Ajouter graphiques/tableaux au rapport via **Dashboard**.
10. Générer les livrables dans **Rapports**.
11. Vérifier l'historique dans **Audit**.

## Bonnes pratiques

- analyser CURATED plutôt que RAW/STAGING ;
- ne pas imputer une variable sensible sans justification ;
- confirmer la définition métier de chaque KPI ;
- utiliser un compte SQL read-only ;
- vérifier les graphiques et messages clés avant diffusion au comité.
