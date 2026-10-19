# Risques résiduels (à actualiser après essais)

Ces lignes sont des **pistes**, pas des conclusions.

| Risque | Pourquoi il reste | Traitement envisagé | Décision |
|---|---|---|---|
| Faux négatif ML | Isolation Forest ≠ preuve d'attaque ; modèle encore absent | Collecte réelle, seuil, persistance | TODO(P3) |
| Faux positif → mitigation injustifiée | Charge légitime de démo | Politique de corroboration, restore auto | TODO(P2) |
| NAT Docker : une seule IP vue | Rate limit punit tout le hotspot | Mesure `client_ip`, éventuellement limite plus fine | TODO(P4) |
| RAM insuffisante + RAG | Ollama hors socle mais tentation de tout lancer | Profil `rag` séparé, délestage | TODO(P2) |
| Secret partagé trop largement | Fichiers locaux `./secrets` | SOPS + age, pas de chat / IA cloud | TODO(P4) |
| Scénario unique | Une seule attaque retenue | Assumer l'arbitrage devant le jury | TODO(P5) |

Aucune ligne de ce tableau n'est chiffrée. Toute cote devra citer un essai daté.
