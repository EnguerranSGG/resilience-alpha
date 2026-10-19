# Documentation des composants

> Indexée par l'assistant RAG. Chaque responsable met à jour la section de son composant.

## gateway (P2/P4)

Passerelle unique exposée. NGINX avec ModSecurity v3 et OWASP CRS 4. Rôle du WAF : bloquer les
requêtes malveillantes connues (injections SQL, XSS, traversée de chemin…) par score d'anomalie ;
il ne protège pas, seul, contre une surcharge de requêtes légitimes, d'où le rate limiting.
Profils : `normal` (limite large) et `mitigation` (5 requêtes/s par IP, rafale 10).

## payment-api (P1)

FastAPI + SQLAlchemy + PostgreSQL. Transactions fictives avec montants décimaux, statuts `PENDING`,
`COMPLETED`, `FAILED`, idempotence par en-tête `Idempotency-Key`. Expose `/metrics`.

## auth-service (P1)

Émet des JWT RS256 pour des comptes fictifs (`demo`, `probe`, `loadtest`). Seul détenteur de la clé
privée.

## frontend (P1)

React, TypeScript, Tailwind. Connexion, formulaire de transaction, liste, statut du service et
panneau d'incident alimenté par les vues publiques du moteur.

## Observabilité (P2)

Prometheus (métriques et features), Loki (journaux), Alloy (collecte des fichiers de logs), Grafana
(dashboards provisionnés).

## ml-detector (P3)

Isolation Forest (scikit-learn), features `request_rate`, `latency_p95`, `error_rate`, `cpu_usage`,
`active_requests`. Sans modèle chargé, il n'émet aucun événement. Un modèle entraîné sur des données
synthétiques est refusé par le moteur de remédiation par défaut.

## remediation-engine (P2)

États `NORMAL`, `SUSPECT`, `MITIGATING`, `RECOVERED`, `FAILED`. Liste blanche d'actions :
`ENABLE_RATE_LIMIT` (mitigate.yml) et `RESTORE_NORMAL_PROFILE` (restore.yml). Aucune route ne permet
d'exécuter une commande.

## rag-assistant (P3)

Ollama + LangChain, modèle local de 3 milliards de paramètres par défaut, index vectoriel local.
Lecture seule, indépendant du moteur de remédiation.

## Risques résiduels connus (à compléter par P5)

- Sous Docker Desktop, l'adresse IP source vue par la passerelle peut être celle de la passerelle
  réseau Docker et non celle du PC Attaquant : la limitation par IP peut alors pénaliser tous les
  clients externes. À vérifier lors du premier essai réseau.
- Le modèle ML peut produire des faux positifs ou des faux négatifs ; ses performances réelles
  doivent être mesurées sur des données collectées.
- Le moteur conserve ses incidents en mémoire : un redémarrage perd l'historique non exporté.
- Une attaque distribuée (plusieurs adresses) n'est pas couverte par la limitation par IP.
