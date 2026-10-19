# Synthèse du cahier des charges

Source : *SUJET DE WORKSHOP NATIONAL — PROJECT RESILIENCE-ALPHA*, EPSI, session octobre 2026, 12 pages. Document officiel non recopié ici.

## Contraintes opérationnelles

- 5 apprenants, 4 sprints (lundi–jeudi), jury vendredi (10 min : 5 + 5).
- Plateforme de paiement fictive, données 100 % fictives.
- Attaque depuis un **second PC**, réponse **sans intervention corrective humaine**.
- Un redémarrage de conteneur ne prouve pas la reprise : nouvelle transaction + intégrité.
- Cinq piliers obligatoires : dev, infra, IA/data, cyber, gouvernance.
- Stack prescrite : microservices, Compose, Ansible, Prometheus, Grafana, Loki, ML, Ollama+LangChain RAG, WAF, SIEM, SOPS/Vault, React/Tailwind.
- RAG : modèle local ≤ 8B, pas d'administration.
- PC Hôte Windows + Docker Desktop/WSL2, hotspot `192.168.137.0/24` typique.
- IA générative autorisée ; maîtrise exigée devant le jury.
- Aucune attaque hors labo.

## Évaluation locale

`(note individuelle + 2 × note jury) / 3`. Axe 1 (démo Zero-Touch) = 5 points ; ND = 0/5 si reprise manuelle en live.

## Livrables

Voir [LIVRABLES.md](LIVRABLES.md).
