# Procédure de détection

1. Prometheus scrape payment-api, gateway, remédiation (intervalle 5 s).
2. Recording rules : `request_rate`, `latency_p95`, `error_rate`, `cpu_usage`, `active_requests`.
3. `ml-detector` construit une fenêtre, applique Isolation Forest **si un modèle est chargé**.
4. Un `AnomalyEvent` n'est émis que si le score dépasse le seuil du modèle.
5. Sans modèle, **aucun événement** : le détecteur tourne mais reste silencieux (comportement actuel tant que `models/` est vide).

Limite : une anomalie statistique n'est pas une preuve d'attaque.

- [ ] TODO(P3) Documenter le jeu d'entraînement réel (période, labels, `trained_on_synthetic=false`).
