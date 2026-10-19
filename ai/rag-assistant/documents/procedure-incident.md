# Procédure de gestion d'incident — surcharge HTTP

> Procédure opérateur indexée par l'assistant RAG. Statut : brouillon à valider par P5 et P4.

## 1. Détection

- Symptômes : hausse du trafic, latence p95 élevée, réponses 503 du service de paiement, 429 de la
  passerelle.
- Sources : dashboard Grafana « RESILIENCE-ALPHA — Vue incident », panneau Incident du frontend,
  journaux Loki (`{service="gateway"}`), état du moteur (`GET /api/remediation/status`).
- Le détecteur ML signale une anomalie statistique. Une anomalie n'est pas une preuve d'attaque :
  le moteur de remédiation exige une corroboration (dégradation mesurée ou événements de sécurité).

## 2. Qualification

- Vérifier que la charge provient d'une machine du laboratoire (adresse du réseau du hotspot).
- Vérifier l'état du moteur : `SUSPECT` (non confirmé), `MITIGATING` (action en cours),
  `RECOVERED` (service vérifié), `FAILED` (échec).

## 3. Réponse automatique

- Aucune action manuelle n'est attendue pendant la démonstration.
- Le moteur active le profil NGINX `mitigation` (limitation stricte par adresse IP) via Ansible.
- Le moteur ne répète pas l'action pendant une mitigation en cours.

## 4. Escalade

- Si l'état reste `FAILED` après le nombre maximal de tentatives, l'incident sort du périmètre de la
  reprise automatique : appliquer la procédure de reprise manuelle du PCA/PRA et le consigner.
- Ne jamais désactiver le WAF ou la limitation pour « faire passer » la démonstration.

## 5. Clôture

- Exporter la chronologie (`GET /api/remediation/incidents`) et les captures Grafana.
- Renseigner MTTD et MTTR dans le rapport d'essai.
