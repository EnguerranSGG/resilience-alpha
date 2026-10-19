# Politique de remédiation automatique

## Ce que l'automatisation peut faire

| Action | Effet | Réversible |
|---|---|---|
| `ENABLE_RATE_LIMIT` | Bascule la passerelle sur le profil NGINX **mitigation** (figé dans l'image) | Oui |
| `RESTORE_NORMAL_PROFILE` | Revient au profil **normal** après stabilité | Oui |

`RESTART_SERVICE` existe dans le contrat mais **n'est pas autorisé** par la politique par défaut.

## Ce qu'elle ne peut pas faire

* Exécuter une commande fournie par un événement : `recommended_action` est une énumération **comparée à une liste blanche**, jamais interprétée ; l'action exécutée est dérivée du **type** d'événement.
* Choisir un playbook, un fichier ou un hôte : le moteur ne transmet que `request_id` (validé par expression régulière) à un playbook fixé dans le code.
* Modifier la configuration NGINX librement : la passerelle n'accepte que `normal` ou `mitigation`, copie un profil figé, exécute `nginx -t` et revient en arrière en cas d'échec.
* Accéder au socket Docker, redémarrer un conteneur, agir sur une machine distante.

## Conditions de déclenchement

Toutes requises : action en liste blanche, modèle non synthétique (sauf dérogation explicite `REMEDIATION_POLICY_ACCEPT_SYNTHETIC_MODEL=true`, à ne pas utiliser en recette), score ≤ seuil de politique, ≥ 3 fenêtres consécutives, **corroboration indépendante** (Prometheus : p95 ≥ 800 ms ou erreurs ≥ 5 % ; ou Loki : ≥ 20 réponses 429/403 en 1 minute).

## Garde-fous d'exécution

* Pas de répétition pendant `MITIGATING`, `RECOVERED` ou une opération en cours.
* En `FAILED` : nouvelle tentative après délai, au plus `max_attempts`, puis escalade opérateur (état affiché, alerte Prometheus `RemediationFailed`).
* Restauration seulement après `restore_after_seconds` sans dégradation.
* Le succès n'est déclaré qu'après une **transaction de contrôle réelle** réussie via la passerelle.
* Mode `simulated` : aucune modification ; signalé partout (`SIMULATION`).

## Intervention humaine

Action opérateur documentée : `make gateway-restore`. Toute intervention humaine pendant la démonstration rend l'axe 1 non démontré (ND) : elle doit rester une procédure de secours.
