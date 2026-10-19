# models/

Emplacement du modèle chargé par `ml-detector` (monté en lecture seule dans le conteneur) :

* `isolation_forest.joblib` : pipeline `StandardScaler` + `IsolationForest` et métadonnées ;
* `isolation_forest.json` : métadonnées lisibles (version, date, sources, seuil, quantiles, métriques, `trained_on_synthetic`).

Ces fichiers ne sont **pas** commités. Un fichier `.joblib` ne doit être chargé que s'il a été produit par l'équipe (désérialisation pickle).

État au 2026-10-19 : **aucun modèle**. Le détecteur tourne sans émettre d'événement.
