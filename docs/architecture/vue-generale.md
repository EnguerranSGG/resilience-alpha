# Vue générale de l'architecture

Statut : **SCAFFOLDED** (description alignée sur le code actuel, à valider en équipe lundi).

## Intention

Plateforme de paiement **fictive** qui encaisse un DoS applicatif HTTP contrôlé, le détecte par Isolation Forest sur des métriques Prometheus, applique un profil NGINX de mitigation via Ansible, puis vérifie qu'une nouvelle transaction légitime réussit. Objectif de démonstration : Zero-Touch Recovery.

## Découpage

| Zone | Composants | Réseau Compose |
|---|---|---|
| Point d'entrée | `gateway` (NGINX + ModSecurity/CRS + rate limit) | `edge` + `apps` + `control` |
| Métier | `frontend`, `auth-service`, `payment-api`, `postgres` | `apps` / `backend` |
| Observabilité | Prometheus, Loki, Alloy, Grafana, nginx-exporter | `observability` (+ `admin` pour Grafana) |
| Détection / reprise | `ml-detector`, `remediation` | `observability` / `control` |
| RAG (profil `rag`) | `ollama`, `rag-assistant` | `rag` |

## Décisions déjà prises

1. Un seul point d'entrée HTTP publié vers le hotspot : la passerelle.
2. Le WAF n'est pas un hop séparé : il est embarqué dans l'image de la passerelle.
3. Le moteur de remédiation n'a pas accès au socket Docker. Il écrit une demande de profil ; la passerelle applique un fichier figé après `nginx -t`.
4. `recommended_action` du ML n'est jamais exécuté tel quel.
5. Ollama et le RAG sont hors du chemin critique (`--profile rag`).
6. Exécuteur réel : playbooks Ansible. Mode `simulated` uniquement pour les tests et le développement, explicitement journalisé.

## Non-objectifs

- Paiement réel, PCI-DSS, haute disponibilité multi-nœuds.
- Détection d'attaques autres que le DoS applicatif retenu (injections, exfiltration) : le WAF les bloque, le scénario de reprise ne les couvre pas.
- Administration distante de Vault / Prometheus / PostgreSQL.

## TODO

- [ ] TODO(équipe) Valider ce schéma avec les coachs lundi.
- [ ] TODO(P5) Relier chaque composant aux valeurs métier EBIOS.
