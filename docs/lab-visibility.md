# Étape 1.3 — Preuve de visibilité du capteur

Statut : **preuve validée le 1er octobre 2026** sur le montage défini ci-dessous. Frontières d’isolation et permissions vérifiées ensuite en [1.4](lab-isolation.md), avec non-régression de la capture.

## Objectif et périmètre

Démontrer que le point de capture défini en [1.2](lab-topology.md) observe réellement les échanges TCP entre le générateur et la cible. Le montage est un test spécialisé du laboratoire ; il ne contient ni sensor NetGuard, ni normalisation métier, ni détecteur, ni alerte.

Le montage exécutable se trouve dans [`lab/visibility/`](../lab/visibility/). Ses trois services utilisent une image commune d'outillage. Ce premier fichier Compose permet de prouver la capture ; la consolidation du laboratoire minimal est réalisée en [1.5](lab-compose.md) et les scénarios complets restent prévus en 1.6.

## Exécution

Prérequis : moteur Docker Linux local accessible, Docker Compose et Python ≥ 3.11 sur l'hôte pour le pilote de cette preuve. Python sur l'hôte est nécessaire à ce pilote, pas aux futurs services conteneurisés de NetGuard. Le précontrôle des routes prend en charge macOS et Linux (`ip` requis sur Linux).

Depuis la racine du dépôt :

```sh
python3 -B lab/visibility/run.py
```

Pour sélectionner explicitement un contexte Docker local :

```sh
python3 -B lab/visibility/run.py --context <contexte-local>
```

Le pilote refuse un contexte dont l'endpoint n'est pas un socket Unix local. Il vérifie l'absence de chevauchement du sous-réseau avec les routes et les réseaux Docker existants, puis construit l'image, lance deux essais et nettoie ses propres ressources. La construction télécharge l'image de base et les paquets ; les scénarios utilisent ensuite uniquement le réseau interne du lab.

Variables optionnelles : `LAB_SUBNET`, `LAB_GATEWAY`, `LAB_SOURCE_IP`, `LAB_TARGET_IP`. Leurs valeurs par défaut sont celles de 1.2. En cas de conflit, fournir un ensemble cohérent d'adresses privées ; les valeurs contrôlées sont transmises explicitement à Compose. Le pilote crée un nom de projet temporaire unique pour chaque exécution. Il n'arrête ni ne supprime les ressources des autres projets.

Depuis 1.5, `--skip-build` exige une image dont l’empreinte correspond aux sources de construction. Après modification de ces sources, reconstruire ; `--rebuild` force une construction sans cache. Voir le [verrou et le contrôle de fraîcheur](lab-compose.md).

## Protocole et conditions de réussite

Chaque essai suit ces étapes :

1. Attendre que la cible HTTP réponde, puis démarrer le capteur dans son espace réseau.
2. Vérifier que l'interface capturée porte l'adresse de la cible et que le partage réseau pointe vers le conteneur cible actuel.
3. Attendre le message `listening on eth0` de tcpdump et l'état explicite de disponibilité du superviseur.
4. Envoyer une requête HTTP vers TCP/8080 avec un marqueur propre à l'essai et vérifier sa réponse côté générateur.
5. Effectuer une tentative de connexion vers chacun des ports fermés 8000, 8001 et 8002 ; chaque tentative doit être refusée.
6. Arrêter proprement tcpdump, récupérer le PCAP et ses statistiques puis vérifier leur contenu.
7. Supprimer les conteneurs et le réseau du test, recréer l'ensemble et répéter avec un nouveau marqueur. Le pilote vérifie que l'identifiant du conteneur cible a changé.

Le vérificateur exige un handshake TCP cohérent, la requête HTTP attendue, sa réponse `200` et son marqueur sur la même connexion. Il exige aussi un SYN et un RST/ACK correspondant pour chacun des trois ports fermés. Les adresses, ports et séquences sont corrélés ; les timestamps doivent correspondre à la fenêtre du scénario avec une tolérance de deux secondes. Le nombre de paquets du PCAP doit correspondre aux statistiques de tcpdump, avec zéro perte rapportée par le noyau.

La vérification des captures est indépendante du succès des requêtes côté générateur. Un fichier vide, tronqué, un marqueur absent ou des pertes connues font échouer la preuve. Le nombre exact de paquets n'est pas fixé, car le découpage TCP peut varier.

## Permissions et bornes

Le générateur et la cible fonctionnent sous UID/GID 65532, sans capability Linux. Aucun port n'est publié, aucun socket Docker n'est monté, le réseau est interne et les systèmes de fichiers racines sont en lecture seule.

Le conteneur de capture démarre avec uniquement `NET_RAW`, `SETUID` et `SETGID`. `NET_RAW` permet d'ouvrir la socket de capture ; les deux autres permissions permettent la baisse de privilèges de l'outil fourni par l'image. tcpdump utilise `-Z nobody` ; le superviseur rejoint ensuite le même UID/GID 65534 pour pouvoir l'arrêter proprement sans `KILL`. Avant de générer du trafic, le pilote vérifie que **tcpdump et le superviseur sont tous deux non-root, avec zéro capability effective**. `no-new-privileges` reste activé.

La capture utilise `eth0`, avec livraison immédiate des paquets (`--immediate-mode`) et écriture par paquet (`-U`), sans mode promiscuité, avec le filtre `tcp and host <source> and host <cible>`. Les contrôles HTTP locaux sur loopback sont donc exclus. Limites : 30 secondes de capture, 512 paquets et un espace temporaire de 8 Mio en mémoire. La capture conserve les paquets complets pour vérifier les marqueurs synthétiques ; elle ne vise aucun trafic personnel. Un dépassement des limites fait échouer l'essai.

`NET_ADMIN`, le mode privilégié et le réseau de l'hôte ne sont pas utilisés. Les permissions de démarrage restent distinctes des permissions effectives pendant la capture ; elles sont contrôlées par le protocole de durcissement [1.4](lab-isolation.md).

Références : [sockets Linux et NET_RAW](https://man7.org/linux/man-pages/man7/packet.7.html), [baisse de privilèges de tcpdump](https://github.com/the-tcpdump-group/tcpdump/blob/master/tcpdump.c), [capabilities et partage réseau Compose](https://docs.docker.com/reference/compose-file/services/).

## Artefacts et reproductibilité

Les résultats sont écrits sous `artifacts/lab/<identifiant-du-test>/`, ignoré par Git :

- `report.json` : verdict global, versions des outils/paquets, image utilisée, empreintes des fichiers de preuve et contrôle du nettoyage ;
- `round-1/` et `round-2/` : `capture.pcap`, `tcpdump.log`, `scenario.json`, `capture-status.json` et `verification.json`.

Le PCAP est extrait pendant que le stockage mémoire du conteneur est monté. Le pilote arrête ensuite les conteneurs et retire le réseau créé. L'image locale est conservée pour les essais suivants. Les artefacts hôte sont conservés pour consultation ; chaque nouvelle exécution crée un dossier distinct. Depuis 1.4, les pilotes refusent un nouvel essai au-delà de 20 entrées ou si la réserve de 20 Mio ne tient pas dans le budget de 128 Mio. Un verrou exclut les preuves concurrentes. L’archivage ou la suppression des anciens résultats reste explicite ; voir la [rétention](lab-isolation.md#stockage-et-rétention).

Depuis [1.5](lab-compose.md), la base Alpine est fixée par digest et les 44 paquets installés sont verrouillés à des versions exactes, puis contrôlés pendant la construction. La disponibilité future des paquets et l’identité bit à bit de l’image ne sont pas garanties ; les limites et la procédure de mise à jour sont documentées.

Le vérificateur peut être relancé hors ligne, sans moteur Docker :

```sh
python3 -B lab/visibility/verify_capture.py \
  artifacts/lab/<identifiant-du-test>/round-1/capture.pcap \
  artifacts/lab/<identifiant-du-test>/round-1/scenario.json \
  --capture-log artifacts/lab/<identifiant-du-test>/round-1/tcpdump.log
```

Il prend en charge uniquement les petits PCAP classiques Ethernet/IPv4/TCP du protocole de preuve. Il ne remplace pas le futur adaptateur PCAP de NetGuard et n'appartient pas au Core.

## Limites de la conclusion

La preuve concerne le trafic de la cible unique sur son interface réseau. Elle ne démontre pas la visibilité entre d'autres conteneurs, ni la capture sur loopback, ni une absence universelle de pertes. Zéro perte rapportée par tcpdump ne certifie pas l'absence de pertes en amont. Les sorties, le DNS, les permissions et la frontière hôte font l’objet des contrôles et limites de [1.4](lab-isolation.md).

La suite standard des tests backend reste indépendante de Docker et de ce laboratoire. La preuve réseau ne constitue pas le scénario E2E final `trafic → NetGuard → détection → persistance → API`.

## Résultats de qualification

Exécution de référence : deux cycles indépendants, avec suppression puis recréation de la cible et du capteur.

| Contrôle | Essai initial | Après recréation |
| --- | --- | --- |
| Paquets capturés et vérifiés | 18 | 18 |
| Handshake, requête HTTP et réponse 200 avec marqueur | Validés | Validés |
| Ports fermés avec SYN et RST/ACK | 8000, 8001, 8002 | 8000, 8001, 8002 |
| Adresses et timestamps | Conformes | Conformes |
| Pertes rapportées par le noyau | 0 | 0 |
| UID effectif tcpdump et superviseur | 65534 | 65534 |
| Capabilities effectives pendant la capture | Aucune | Aucune |
| Fermeture de capture | Code 0, sans dépassement | Code 0, sans dépassement |

La cible a été recréée et les deux captures utilisent des marqueurs distincts. Le contrôle final confirme l'absence de conteneurs et de réseaux appartenant au projet temporaire.

Empreintes SHA-256 des captures de référence :

- Essai initial : `29cc40a24fc0936b10f106365acb51b6ca94ca4994214de66814723f712004f3`.
- Après recréation : `3ea63f83ddbe2ab4f93f5aa0394f83d2bb0cb2527b78991c117475bab0c23c4c`.

Outillage de l'image vérifiée : Alpine 3.23.6, Python 3.12.15, tcpdump 4.99.5 et libpcap 1.10.7. Ces versions décrivent les outils du montage reproductible, pas l'inventaire du poste hôte.

**1.3 validée pour ce périmètre.** Le durcissement et sa non-régression de capture sont documentés en [1.4 — Isolation et permissions](lab-isolation.md).
