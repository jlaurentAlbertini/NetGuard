# Étape 1.4 — Isolation et permissions

Statut : **validée le 1er octobre 2026 pour le montage spécialisé du laboratoire**. Le laboratoire minimal est ensuite consolidé en [1.5](lab-compose.md).

## Périmètre et politique

Le générateur, la cible et le point de capture utilisent le montage de [1.3](lab-visibility.md). Les échanges entre le générateur et la cible restent autorisés. Les services du laboratoire ne doivent pas disposer d'une route de sortie, d'un accès aux autres réseaux Docker ou aux services de l'hôte, ni de permissions d'administration réseau.

Ces contrôles concernent une cible maîtrisée, sur un moteur Docker local. L'opérateur qui administre Docker reste une autorité de confiance : il peut modifier les réseaux, exécuter des processus ou lire les captures. Le lab ne prétend pas l'isoler du moteur ou d'un administrateur hôte.

## Mesures appliquées

| Frontière | Mesure dans `lab/visibility/compose.yaml` | Vérification |
| --- | --- | --- |
| Sorties du lab | Bridge `internal: true`, mode IPv4 `isolated`, un seul réseau par service | Inspection Docker, aucune route IPv4 hors sous-réseau, essais vers un service témoin séparé |
| Adresse du bridge | Pas d'adresse attribuée au bridge en mode `isolated` | Option inspectée et tentative vers l'adresse IPAM réservée bloquée |
| IPv6 | Réseau sans IPv6 et `disable_ipv6=1` dans les espaces réseau | Configuration et état noyau contrôlés |
| DNS | Résolveur amont limité à `127.0.0.1`, aucune recherche de suffixe hôte | Résolution du service interne fonctionnelle ; requêtes vers le DNS témoin bloquées ; nom externe synthétique non résolu |
| Exposition | Aucun port publié, aucun réseau hôte, aucun socket Docker monté | Inspection des conteneurs et tentative depuis le réseau témoin |
| Générateur et cible | UID/GID 65532, toutes les capabilities retirées, `no-new-privileges` | Identité et permissions réelles ; opérations interdites effectivement refusées |
| Capture | Seulement `NET_RAW`, `SETUID`, `SETGID` au démarrage, puis UID/GID 65534 sans capability effective | État réel de tcpdump et de son superviseur avant validation |
| Écriture | Racines en lecture seule ; seul le capteur dispose d'un tmpfs `/capture` de 8 Mio | Écriture dans `/tmp` refusée et taille du tmpfs mesurée |
| Ressources | Par service : mémoire 128 Mio, plafond CPU 0,5, 32 processus ; journaux Docker 1 Mio × 1 | Limites appliquées inspectées |

`internal: true` seul laisse normalement une adresse sur le bridge. Le mode `isolated` supprime cette adresse et ferme ainsi ce chemin vers les services de l'hôte. L'adresse `172.30.50.1` demeure réservée dans l'IPAM ; elle ne représente plus une passerelle joignable. [Modes de passerelle Docker](https://docs.docker.com/engine/network/port-publishing/#gateway-modes).

Le DNS embarqué de Docker conserve la résolution des noms de services. Le réglage `dns: [127.0.0.1]` désigne le loopback du conteneur comme unique amont, où aucun serveur DNS n'écoute. Cela évite de reprendre les résolveurs du poste. Le capteur partage l'espace réseau de la cible et hérite de ces choix. Le simple échec d'un nom externe ne prouverait pas à lui seul l'absence de transfert : le protocole vérifie aussi la configuration DNS appliquée et les routes. [Services DNS Docker](https://docs.docker.com/engine/network/#dns-services).

Les trois permissions initiales du capteur servent à ouvrir la socket de capture puis à abandonner les privilèges. Le superviseur rejoint le même utilisateur que tcpdump pour le terminer proprement. Aucun `NET_ADMIN`, `SYS_ADMIN` ou mode privilégié n'est nécessaire. Après la baisse de privilèges, les tentatives d'ouverture d'une nouvelle socket brute, de passage à root et d'ajout d'une route sont refusées. La socket de capture déjà ouverte reste utilisable. [Permissions Linux dans Docker](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities).

## Exécution et résultat attendu

Prérequis : moteur Docker Linux local prenant en charge le mode `isolated`, Docker Compose et Python ≥ 3.11 sur l'hôte. Le précontrôle des routes prend en charge macOS et Linux (`ip` requis sur Linux). Un moteur qui refuse le mode réseau fait échouer la preuve ; aucun repli vers un réseau moins restrictif n'est prévu.

Depuis la racine du dépôt :

```sh
python3 -B lab/visibility/check_isolation.py
python3 -B lab/visibility/run.py --skip-build
```

La première commande construit l'image, vérifie l'isolation, puis retire ses conteneurs et réseaux temporaires. La seconde réutilise l'image pour vérifier deux captures, avec recréation de la cible. `--context <contexte-local>` permet de choisir explicitement le moteur. Les variables `LAB_SUBNET`, `LAB_GATEWAY`, `LAB_SOURCE_IP` et `LAB_TARGET_IP` suivent les règles de [1.3](lab-visibility.md).

Le pilote d'isolation doit terminer par :

```text
PASS: 35 isolation/permission checks; temporary resources removed.
```

Le rapport local `artifacts/lab/netguard-isolation-<identifiant>/report.json` contient le verdict de chaque contrôle, l'identifiant de l'image, les empreintes des fichiers utilisés et `cleanup_verified: true`. Les captures de non-régression sont conservées dans un dossier `netguard-visibility-<identifiant>` distinct. Ces fichiers sont ignorés par Git.

## Protocole de preuve

1. Vérifier le contexte local, les conflits d'adressage, la configuration Compose et le budget de stockage.
2. Démarrer le générateur et la cible ; vérifier HTTP ainsi que la résolution interne de `target-web`.
3. Créer un réseau témoin distinct avec un service HTTP et un DNS synthétique. Confirmer d'abord que les deux services répondent depuis leur propre conteneur.
4. Depuis le générateur et la cible, tester les permissions, les routes, le TCP et le DNS vers ce témoin, la résolution externe synthétique, l'adresse hôte fournie par Docker et l'adresse IPAM réservée.
5. Depuis le témoin, vérifier que la cible du lab reste inaccessible. Confirmer à nouveau que les témoins répondent et que le trafic interne du lab fonctionne.
6. Démarrer le capteur, attendre sa disponibilité et vérifier son espace réseau, la baisse de privilèges, les opérations refusées et les limites de ressources. Fermer proprement la capture.
7. Retirer uniquement les ressources identifiées par le projet et les labels propres à l'essai. Vérifier leur disparition, y compris après un échec.

Les témoins évitent de confondre un service absent avec un accès bloqué. Le réseau témoin utilise le routage Docker ordinaire, mais aucun test ne contacte Internet ni un service existant du LAN. Aucun port du témoin n'est publié sur l'hôte. Un petit serveur HTTP supplémentaire écoute temporairement sur `127.0.0.1` avec un port attribué automatiquement ; sa réponse est contrôlée depuis l'hôte puis il est arrêté.

Pour la frontière hôte, le verdict exige explicitement « réseau inaccessible » depuis les services du lab vers l'adresse `host-gateway`. Le témoin loopback n'est pas supposé représenter cette même adresse, notamment avec une VM Docker Desktop. La preuve porte sur l'absence de route ; elle ne certifie pas toutes les formes d'accès à l'hôte sur toutes les plateformes.

## Stockage et rétention

La capture reste bornée à 30 secondes, 512 paquets et 8 Mio de stockage mémoire. Tout arrêt anticipé par une limite invalide la preuve de visibilité. Les journaux Docker sont limités à 1 Mio par service et disparaissent avec les conteneurs.

Les deux pilotes partagent une admission des résultats dans `artifacts/lab/` :

- maximum 20 entrées ;
- budget de 128 Mio, avec 20 Mio disponibles exigés avant un nouvel essai ;
- refus des liens symboliques dans cet espace de résultats ;
- une seule preuve à la fois, protégée par un verrou local relâché à la fin du processus.

La réserve couvre les deux extractions de 8 Mio et leurs rapports. Il s'agit d'un contrôle des pilotes, pas d'un quota du système de fichiers : un ajout manuel reste possible. Les résultats sont conservés jusqu'à archivage ou suppression explicite par l'opérateur ; aucune preuve existante n'est effacée automatiquement. À saturation, le prochain essai s'arrête avant de créer ses conteneurs. Retirer uniquement les dossiers de résultats devenus inutiles, puis relancer. L'image construite reste disponible dans Docker et n'entre pas dans ce budget.

## Résultats et limites

Qualification : **35 contrôles réussis**, nettoyage vérifié. Les vérifications de stockage ont confirmé le refus au-delà de 20 entrées, la limite de budget, l'exclusion des liens symboliques, l'exclusion des exécutions concurrentes et la préservation des preuves existantes.

La non-régression de visibilité a validé deux captures de 18 paquets chacune après durcissement, avec recréation de la cible : HTTP et marqueur, SYN/RST des ports 8000–8002, adresses et timestamps cohérents, aucune perte rapportée par le noyau. Les empreintes des nouvelles captures figurent dans leurs rapports locaux ; les captures historiques 1.3 restent conservées.

Ces résultats portent sur le montage et les contrôles décrits. Les membres du bridge peuvent communiquer entre eux ; aucune ACL entre le générateur et la cible n'est revendiquée. Le partage de réseau inclut le loopback commun à la cible et au capteur. Les plafonds mémoire, CPU et processus sont inspectés, sans essai de saturation. Le protocole n'est ni un audit du noyau ou du moteur Docker, ni une garantie contre un administrateur malveillant. Une autre plateforme ou une modification des réseaux, permissions, services ou images exige de relancer les preuves.

**1.4 validée pour ce périmètre.** La [consolidation 1.5](lab-compose.md) versionne l’image, verrouille ses dépendances et fournit le lancement unifié.
