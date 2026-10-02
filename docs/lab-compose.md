# Étape 1.5 — Consolidation du laboratoire Docker Compose

Statut : **validée le 1er octobre 2026** pour le laboratoire minimal à trois services. La qualification ci-dessous concerne l'image Linux/ARM64 exécutée avec Docker Desktop ; les autres plateformes restent à qualifier.

## Lancement

Prérequis : moteur Docker Linux local prenant en charge le mode réseau `isolated`, Docker Compose et Python ≥ 3.11 sur l'hôte. Le contrôle des routes prend en charge macOS et Linux (`ip` requis sur Linux).

Depuis la racine du dépôt :

```sh
python3 -B scripts/lab.py verify
```

Cette commande construit l'image, lance les 35 contrôles d'isolation, puis les deux captures de visibilité avec recréation de la cible. Le second pilote réutilise l'image. Chaque pilote conserve ses précontrôles, limites, rapports et nettoyage. Si une preuve échoue, la commande s'arrête avec un code d'erreur. Les résultats restent dans `artifacts/lab/`, ignoré par Git ; une validation complète produit deux dossiers de preuve.

| Commande / option | Effet |
| --- | --- |
| `python3 -B scripts/lab.py isolation` | Isolation et permissions uniquement. |
| `python3 -B scripts/lab.py visibility` | Deux captures et recréation de la cible uniquement. |
| `python3 -B scripts/lab.py verify --rebuild` | Reconstruction sans cache de couches, vérification de la base auprès du registre, puis toutes les preuves. |
| `python3 -B scripts/lab.py verify --skip-build` | Réutilisation d'une image locale correspondant exactement aux sources de construction. |
| `--context <contexte-local>` | Choix explicite du moteur Docker local. |
| `--help` | Aide, sans démarrer de conteneur. |

`--rebuild` et `--skip-build` sont incompatibles. Une construction ordinaire peut utiliser le cache Docker. Les pilotes historiques restent utilisables et acceptent les mêmes options de construction. Aucun service permanent ne reste démarré après une preuve réussie.

## Image et dépendances

L'image du laboratoire est nommée **`netguard-lab:1.5`**. Elle partage les outils nécessaires aux trois services ; elle ne contient pas le futur sensor NetGuard.

- La base Alpine 3.23.6 est fixée par digest dans le Dockerfile.
- `packages.lock` fixe les **44 paquets installés**, y compris les dépendances transitives et les paquets de base, sous la forme `nom=version`.
- La construction compare la liste complète réellement installée au verrou. Une version indisponible, un paquet supplémentaire ou une différence de version fait échouer la construction.
- `.dockerignore` autorise uniquement le Dockerfile, ses règles d'exclusion, le verrou et les deux scripts destinés aux conteneurs. Les pilotes, captures et fichiers locaux ne sont pas envoyés comme entrées utiles de construction.

Python 3.12.15, tcpdump 4.99.5 et libpcap 1.10.7 restent les outils de capture qualifiés. Le verrou complet constitue la référence des versions, révisions Alpine comprises.

`image.py` calcule l'empreinte des cinq fichiers de construction et l'enregistre dans un label de l'image. Avant chaque preuve, cette empreinte est comparée aux sources locales, même avec `--skip-build`. Une image absente ou périmée est refusée avant le démarrage des services. Le pilote utilise ensuite l'identifiant immuable de l'image pour les services Compose et le témoin, avec construction et téléchargement implicites désactivés lors du démarrage.

Les rapports enregistrent cet identifiant, l'empreinte des sources de l'image, celle du verrou et la plateforme de l'image. Ce contrôle protège contre une réutilisation accidentelle d'une ancienne image ; l'opérateur Docker reste une autorité de confiance.

Références : [base par digest et cache Docker](https://docs.docker.com/build/building/best-practices/), [options de construction Compose](https://docs.docker.com/reference/cli/docker/compose/build/), [gestion des paquets Alpine](https://docs.alpinelinux.org/user-handbook/0.1a/Working/apk.html).

## Configuration réseau

Les paramètres restent externes au code métier et sont lus dans l'environnement du pilote :

| Variable | Valeur par défaut |
| --- | --- |
| `LAB_SUBNET` | `172.30.50.0/24` |
| `LAB_GATEWAY` | `172.30.50.1` — réservation IPAM, sans passerelle joignable |
| `LAB_SOURCE_IP` | `172.30.50.10` |
| `LAB_TARGET_IP` | `172.30.50.20` |

Pour changer l'adressage, exporter un ensemble cohérent de ces quatre variables avant le lancement. Le pilote refuse les chevauchements avec les routes et réseaux Docker détectés, puis transmet explicitement les valeurs contrôlées à Compose. Il ne lit pas de fichier `.env` pour ces réglages. `LAB_IMAGE_REF` et `LAB_SOURCE_SHA256` sont réservés au pilote et réécrits par celui-ci.

La configuration conserve le réseau interne en mode `isolated`, aucun port publié, les privilèges réduits et les bornes de [1.4](lab-isolation.md). Le fichier Compose reste dans `lab/visibility/compose.yaml` ; le point d'entrée supporté pour les preuves est `scripts/lab.py`.

## Qualification et limites de reproductibilité

Deux reconstructions sans cache ont réussi : mêmes 44 versions de paquets, 35 contrôles d’isolation par reconstruction et deux captures de 18 paquets chacune par passage. Chaque nettoyage est confirmé. Les identifiants des deux images diffèrent ; la conclusion porte sur les versions et les preuves, pas sur une identité bit à bit. Le refus d'une image périmée est aussi testé en modifiant temporairement une copie d'une source, puis en la restaurant : le pilote doit s'arrêter avant les services et ne pas lancer la seconde preuve.

La reproductibilité visée est celle des versions et du comportement du laboratoire. Elle ne garantit pas un identifiant d'image identique bit à bit : les métadonnées et horodatages de construction peuvent différer. Les versions verrouillées doivent toujours être disponibles dans les dépôts Alpine ; elles ne sont pas archivées dans ce dépôt. En cas de retrait, la construction échoue au lieu de choisir silencieusement d'autres versions. `--rebuild` n'efface pas les images ni les autres ressources Docker du poste.

La qualification Linux/ARM64 avec Docker Desktop ne vaut pas validation de Linux natif, AMD64 ou Windows. Les rapports décrivent l'image du projet ; aucun inventaire personnel du poste n'est publié.

## Mise à jour des dépendances

1. Examiner la nouvelle base et les versions souhaitées dans les sources officielles.
2. Construire une image candidate dans un contexte temporaire ; relever la liste complète des paquets installés et mettre à jour le digest et `packages.lock` ensemble selon le besoin.
3. Mettre à jour la version de l'image dans `image.py` et la valeur par défaut du Compose si elle change.
4. Exécuter `python3 -B scripts/lab.py verify --rebuild`, comparer les rapports, puis revoir le diff avant publication.

Les mises à jour, y compris de sécurité, sont volontaires et revues. Aucun contournement du verrou ou contrôle de fraîcheur ne fait partie du lancement normal.

Suite : **1.6 — Scénarios de trafic contrôlés**. Les scénarios actuels restent ceux des preuves ; les captures de référence élargies et la qualification finale suivent aux étapes 1.7 à 1.9.
