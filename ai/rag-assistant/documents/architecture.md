# Architecture de RESILIENCE-ALPHA

> Document de référence indexé par l'assistant RAG. Mettre à jour à chaque décision d'architecture.

## Objectif

RESILIENCE-ALPHA est une plateforme de paiement **fictive** qui démontre une reprise automatique
(Zero-Touch Recovery) après un déni de service applicatif par surcharge HTTP, provoqué depuis un
PC Attaquant sur un réseau de laboratoire isolé.

## Chaîne de bout en bout

1. Un client (navigateur, PC Attaquant) atteint uniquement la passerelle `gateway` sur le port 8080.
2. La passerelle applique le rate limiting NGINX (profil `normal` ou `mitigation`) et le WAF
   ModSecurity avec l'OWASP Core Rule Set, puis route vers le frontend, `payment-api` ou `auth-service`.
3. `payment-api` enregistre les transactions fictives dans PostgreSQL et expose ses métriques HTTP.
4. Prometheus collecte les métriques toutes les 5 secondes et calcule les features (recording rules).
5. Alloy collecte les journaux JSON (passerelle, services) et les envoie à Loki.
6. Le détecteur ML (Isolation Forest) interroge Prometheus, calcule un score d'anomalie et envoie un
   événement structuré (contrat `AnomalyEvent` v1) au moteur de remédiation.
7. Le moteur de remédiation valide l'événement, vérifie la persistance de l'anomalie et une
   corroboration indépendante (dégradation Prometheus ou événements de sécurité Loki), puis lance le
   playbook Ansible `mitigate.yml`.
8. Le playbook demande à la passerelle d'appliquer le profil prévalidé `mitigation` ; la passerelle
   exécute `nginx -t` puis recharge sa configuration.
9. Le moteur vérifie le rétablissement par une transaction de contrôle passant par la passerelle.
10. Grafana et le frontend affichent la chronologie de l'incident.

## Réseaux

- `edge` : passerelle, frontend, `payment-api`, `auth-service`, moteur (lecture des vues publiques et
  vérification). Seul réseau dont un port est publié (passerelle).
- `backend` (interne) : `payment-api`, PostgreSQL.
- `observability` (interne) : Prometheus, Loki, Alloy, détecteur ML, moteur de remédiation, services
  instrumentés, exporter NGINX.
- `admin` : Grafana, publié uniquement sur l'adresse de bouclage par défaut.
- `rag` : assistant RAG et Ollama, profil Compose séparé, sans lien avec la remédiation.

## Principes de sécurité

- Aucun composant n'accède au socket Docker.
- Le moteur de remédiation ne peut que choisir entre deux profils NGINX figés dans l'image de la
  passerelle ; il ne peut pas exécuter de commande arbitraire.
- L'assistant RAG ne dispose d'aucun droit d'administration.
- Les secrets sont des fichiers locaux générés par `scripts/generate-secrets.sh`, montés comme
  Docker secrets et jamais commités.
