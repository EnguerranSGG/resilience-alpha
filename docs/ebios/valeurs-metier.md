# Valeurs métier essentielles

Contexte : entreprise financière **fictive**, plateforme de paiement simulée.

| ID | Valeur | Description | Disponibilité | Intégrité | Confidentialité | À confirmer |
|---|---|---|---|---|---|---|
| VM1 | Capacité à exécuter une transaction fictive | Processus métier démontré au jury | haute | haute | moyenne | [ ] TODO(P5) |
| VM2 | Confiance dans l'état du compteur de paiements | Pas de doublon, pas de perte silencieuse | moyenne | haute | moyenne | [ ] TODO(P5) |
| VM3 | Traçabilité de l'incident et de la reprise | Preuve pour le jury et le dossier | moyenne | haute | moyenne | [ ] TODO(P5) |
| VM4 | Secrets de laboratoire | JWT, mots de passe demo, jeton d'ingestion | basse | haute | haute | [ ] TODO(P5) |

Hypothèse de départ (à challenger) : l'indisponibilité de quelques minutes est
moins grave qu'une corruption des transactions ou qu'une exposition des secrets.

- [ ] TODO(P1/P5) Estimer un impact d'arrêt (minutes) à partir des essais, pas d'un barème inventé.
