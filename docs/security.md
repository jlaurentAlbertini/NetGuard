# Sécurité

Statut : premières mesures du laboratoire implémentées et éprouvées en [1.4 — Isolation et permissions](lab-isolation.md). Les mesures des futurs composants NetGuard restent à implémenter.

Les scénarios ciblent exclusivement les services contrôlés du laboratoire. Le montage spécialisé applique les mesures suivantes :

- réseau interne en mode `isolated`, aucune route externe, IPv6 désactivé et DNS amont limité au loopback ;
- aucun port publié, socket Docker ou montage du disque hôte dans les services ;
- générateur et cible non-root sans capability ; capteur avec trois permissions de démarrage justifiées puis abandon des privilèges ;
- `no-new-privileges`, racines en lecture seule et plafonds CPU, mémoire, processus et journaux ;
- capture et stockage des preuves bornés, conservation hors Git, nettoyage des ressources temporaires contrôlé.

Le protocole vérifie les communications autorisées, les accès bloqués, les permissions réellement appliquées et le maintien de la capture. Ses résultats et limites sont détaillés en [1.4](lab-isolation.md). L'opérateur Docker reste une autorité de confiance et le réseau partagé de la cible et du capteur constitue une limite explicite.

Les captures réseau peuvent contenir des données sensibles : PCAP, journaux, fichiers `.env`, secrets et résultats locaux restent ignorés par Git. La documentation publique décrit les paramètres du projet et les preuves ; elle ne contient pas d'inventaire personnel du poste.

Les dépendances du laboratoire sont verrouillées en [1.5](lab-compose.md), avec comparaison des paquets installés et refus des images périmées. Leur mise à jour reste volontaire et doit être revalidée.

À poursuivre : validation des entrées du futur sensor, gestion des secrets, protection des interfaces et séparation des nouveaux services. Le laboratoire ne valide pas encore ces fonctions de NetGuard. Voir le [threat model](threat-model.md) et la [roadmap](roadmap.md).
