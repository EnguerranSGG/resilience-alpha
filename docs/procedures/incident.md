# Procédure de gestion d'incident (laboratoire)

Version opérateur, aussi indexée par le RAG (`ai/rag-assistant/documents/procedure-incident.md`).

1. **Constat** : Grafana (trafic, latence, 5xx) + UI métier.
2. **Ne pas** redémarrer les conteneurs pendant une démo Zero-Touch.
3. **Observer** le panneau d'incidents du frontend (`/api/remediation/status`).
4. Si mitigation appliquée : attendre la transaction de contrôle automatique.
5. Si `FAILED` : collecter logs (`make logs`), ne pas improviser un `docker restart` devant le jury sauf décision P5.
6. Restauration opérateur de dernier recours : `make gateway-restore`.

- [ ] TODO(P5) Chronométrer un dry-run mercredi.
