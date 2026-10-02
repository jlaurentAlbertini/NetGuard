# Étape 1.1 — Cadrage et prérequis du laboratoire

Statut : cadrage terminé ; preuve de visibilité réalisée en [1.3](lab-visibility.md). Frontières d’isolation et permissions éprouvées en [1.4](lab-isolation.md) ; laboratoire minimal consolidé en [1.5](lab-compose.md).

## 1. Objectif et critère de validation

Construire un laboratoire local, isolé et reproductible avec Docker Compose, dans lequel un générateur produit du trafic réel vers une cible et un point de capture permet d'observer ce trafic. Ce laboratoire servira ensuite au développement de NetGuard et à son scénario d'acceptation réel.

L'étape 1.1 est validée lorsque la plateforme de référence, les composants minimaux, les contraintes, les prérequis techniques et les critères de qualification sont explicites. Elle ne certifie ni l'isolation ni la visibilité réseau : leurs preuves appartiennent aux sous-étapes suivantes.

## 2. Base de conception reprise

Les corrections de l'audit 0.7 sont annoncées comme intégrées dans le README et la roadmap ; la dernière validation de clôture y reste à effectuer. Cette fiche ne remplace pas cet audit et ne déclare pas l'étape 0 clôturée.

| Décision existante | Conséquence pour le laboratoire |
| --- | --- |
| FR-001 et FR-002 : capture passive dans le lab local | Les scénarios visent exclusivement les services de NetGuard ; la capture observe le trafic. |
| FR-008 : première règle NG-NET-001 | Préparer du trafic TCP normal et un scan vertical vers une même cible ; aucun détecteur n'est implémenté ici. |
| NFR-011 et modèle réseau | Docker Compose est retenu ; plateforme, visibilité, permissions et exposition doivent être vérifiées. |
| TA4 et TA5 : garanties de source et position d'observation | Documenter ce qui est visible, les limites connues et le point de capture ; être sur le même réseau Docker ne prouve pas la visibilité. |
| TB1 : réseau vers capture | Un paquet issu du laboratoire reste une entrée non fiable pour NetGuard. |
| NFR-013 et sécurité | Permissions minimales ; pas de `privileged: true` par commodité. |
| TA10 : exposition cohérente avec les contrôles | Aucun service sans protection n'est exposé arbitrairement au réseau local. |
| NFR-010, NFR-014 et NFR-017 | Scénarios bornés, captures minimisées, limites de stockage et nettoyage explicites. |
| Architecture et ADR-001 à ADR-003 | Le lab ne change pas le monolithe modulaire ni les dépendances vers le Core ; la capture technique reste dans l'Infrastructure. |
| Stratégie de tests et NFR-003 | La suite standard reste indépendante du lab ; le futur E2E réel fait l'objet d'une procédure spécialisée. |

Sources du dépôt : [modèle réseau](network-model.md), [exigences fonctionnelles](requirements/functional.md), [exigences non fonctionnelles](requirements/non-functional.md), [architecture](architecture.md), [threat model](threat-model.md), [sécurité](security.md), [tests](testing.md) et [ADR](decisions/README.md).

## 3. Environnement d'exécution cible

Le laboratoire repose sur des **conteneurs Linux orchestrés avec Docker Compose**. Docker Desktop constitue l'environnement initial de qualification ; sa validation dépend de la preuve de visibilité du point de capture. Un déploiement Linux natif pourra être qualifié ultérieurement.

Les images doivent être compatibles avec l'architecture de l'environnement d'exécution. Les versions sont verrouillées en [1.5](lab-compose.md), avec une qualification Linux/ARM64 sous Docker Desktop. Les autres plateformes restent à qualifier.

Docker Desktop exécute le moteur dans une VM Linux. Le point de capture doit avoir accès au réseau des conteneurs ; une capture sur une interface physique de l'hôte ne prouve pas la visibilité des échanges internes. La [topologie retenue en 1.2](lab-topology.md) est éprouvée par le montage spécialisé [1.3](lab-visibility.md). [Documentation réseau Docker Desktop](https://docs.docker.com/desktop/features/networking/).

Si le mécanisme de capture retenu ne peut pas être mis en œuvre avec des permissions maîtrisées, l'environnement d'exécution sera réévalué à l'issue de 1.3.

## 4. Prérequis techniques

| Prérequis | Usage | Critère de disponibilité |
| --- | --- | --- |
| Moteur Docker pour conteneurs Linux | Exécuter les composants du laboratoire. | Le client accède au moteur et obtient ses informations serveur. |
| Docker Compose | Décrire et piloter les services, réseaux et volumes. | La commande `docker compose version` fonctionne ; la configuration du laboratoire minimal est validée en [1.5](lab-compose.md). |
| Git | Récupérer et versionner les sources du projet. | Le dépôt est accessible dans un répertoire de travail. |
| Images compatibles avec l'architecture cible | Exécuter le générateur, la cible et le point de capture. | Versions et architectures vérifiées lors de la construction du lab. |
| Ressources CPU, mémoire et disque | Exécuter les scénarios et conserver des captures bornées. | Capacité disponible à comparer au budget indicatif de la section 6. |
| Permissions de capture | Observer le trafic au point prévu. | Permissions minimales définies et vérifiées avec la topologie retenue. |

Le backend déclare Python ≥ 3.11 dans `backend/pyproject.toml`. Cette contrainte concerne le développement Python ; une installation Python sur l'hôte n'est pas un prérequis général pour exécuter un laboratoire conteneurisé. La version utilisée par les futurs composants sera fixée avec leurs dépendances.

Les versions minimales des outils et la matrice de compatibilité seront documentées à partir des configurations effectivement testées. La présence d'un outil de capture sur l'hôte ne suffit pas à valider la capture dans le laboratoire.

## 5. Composants du laboratoire minimal

| Composant / responsabilité | Rôle initial | Emplacement prévu |
| --- | --- | --- |
| Générateur de trafic | Produire des connexions normales et un scan vertical contrôlé ; cible, ports, cadence et durée explicites. | `lab/traffic-generator/` |
| Cible web | Offrir un service TCP/HTTP connu et des ports fermés permettant des scénarios observables. | `lab/targets/target-web/` |
| Point de capture technique | Prouver l'accès aux paquets et produire une capture témoin ; préparer le futur sensor NetGuard. | Service `capture-probe` partageant l’espace réseau de la cible ; tcpdump et permissions de démarrage/baisse de privilèges documentés en [1.3](lab-visibility.md). |
| Réseau supervisé | Porter les échanges entre générateur et cible avec un périmètre observable documenté. | Déclaration Compose à venir. |
| Accès d'administration | Piloter le lab depuis l'hôte ; prévoir sa séparation du trafic supervisé. | Commandes Docker depuis l’hôte ; aucun réseau de management dédié dans la topologie initiale. |
| Captures et journaux temporaires | Conserver les preuves de validation avec des limites et une procédure de nettoyage. | Répertoire local ignoré par Git, par exemple `artifacts/`. |

La topologie 1.2 décline ces rôles en trois services : générateur, cible web et capteur technique. La preuve de visibilité utilise tcpdump ; la bibliothèque du futur sensor NetGuard n'est pas encore choisie.

Périmètre réseau initial retenu pour le lab : IPv4, TCP et HTTP local. Un générateur et une cible suffisent au premier scénario ; leur duplication éventuelle viendra avec les tests qui l'exigent. IPv6, UDP, DNS applicatif et HTTPS ne sont pas des critères d'acceptation initiaux. Ce choix de laboratoire ne restreint pas les modèles métier généraux.

## 6. Contraintes et dimensionnement de départ

- Les scénarios utilisent exclusivement des cibles du lab ; les réseaux externes au laboratoire sont exclus du périmètre.
- Préparer les images et dépendances peut nécessiter Internet. Une fois les images présentes, l'exécution des scénarios doit fonctionner sans sortie Internet nécessaire ; la configuration et les contrôles d’isolation du montage spécialisé sont documentés en [1.4](lab-isolation.md).
- Un bridge dédié ne garantit pas à lui seul l'absence d'accès externe : Docker fournit par défaut une sortie par masquerading. Les flux autorisés et interdits doivent être décrits puis testés. [Documentation du bridge Docker](https://docs.docker.com/engine/network/drivers/bridge/).
- Aucun port hôte n'est nécessaire au principe générateur → cible → capture. Si un accès de consultation est introduit, il devra être justifié et limité à l'hôte local pour ce lab.
- Les permissions de capture seront justifiées individuellement après le choix de topologie ; les composants sans besoin de capture n'en hériteront pas. Le montage du socket Docker dans un conteneur du lab n'est pas un prérequis retenu.
- Chaque scénario aura une durée et un débit bornés. Les bornes des captures et la rétention locale des preuves sont définies en [1.4](lab-isolation.md) : budget de stockage et nombre de dossiers limités, conservation jusqu’à retrait explicite par l’opérateur. Les PCAP sont déjà ignorés par défaut dans Git.
- Le capteur devra préserver suffisamment d'informations pour interpréter sources, destinations, ports, timestamps et sens des échanges ; les effets d'une éventuelle traduction d'adresses seront documentés.

Budget de départ proposé pour les premiers essais : **4 processeurs virtuels, 4 Gio de mémoire pour Docker et 20 Gio de marge disque pour le lab**. Cette enveloppe indicative reste à confirmer par mesure ; elle ne constitue pas un minimum matériel validé. Les ressources disponibles doivent être vérifiées avant l'exécution. Les limites par service sont définies et contrôlées en [1.4](lab-isolation.md). Docker permet de régler les ressources de sa VM dans ses paramètres. [Réglages Docker Desktop](https://docs.docker.com/desktop/settings-and-maintenance/settings/).

## 7. Qualification de l'environnement

| Contrôle | Critère attendu | Échéance |
| --- | --- | --- |
| Clôture de l'audit 0.7 | Validation finale de la conception, suivie séparément du cadrage du lab. | Clôture de l'étape 0. |
| Accès au moteur et à Compose | Réponse du serveur Linux et commande Compose opérationnelle. | Avant les essais. |
| Ressources allouées | CPU, mémoire et espace disponibles adaptés au budget d'essai. | Avant les essais. |
| Adressage | Plan de référence défini en 1.2 ; absence de conflit avec les réseaux Docker et les routes à contrôler avant démarrage. | Avant les essais de 1.3. |
| Visibilité et permissions de capture | Échange témoin observable, avec les adresses et directions attendues. | 1.3. |
| Isolation et exposition | Communications autorisées fonctionnelles ; communications interdites bloquées. | 1.4. |
| Images et versions | Images compatibles, versions figées, construction et démarrage réussis. | 1.5. |
| Reproductibilité | Configuration Compose validée et lancement depuis un état propre. | 1.5, puis 1.8. |

Vérifications préalables depuis l'hôte :

```sh
docker context show
docker version
docker info
docker compose version
```

Le contexte doit désigner le moteur prévu pour le laboratoire. La réponse serveur doit confirmer un environnement Linux et une architecture compatible avec les images sélectionnées. Les résultats de qualification seront documentés avec les essais ; ces commandes ne constituent pas à elles seules une preuve de visibilité ou d'isolation.

## 8. Limites du travail et articulation avec la roadmap

La [roadmap du dépôt](roadmap.md) conserve sa numérotation officielle. Les sous-étapes 1.1 à 1.9 détaillent la préparation et la validation du laboratoire. La preuve technique de capture du lab prépare l'étape 2 de la roadmap, qui reste responsable de l'implémentation du sensor NetGuard.

La production éventuelle de PCAP témoins en 1.7 est un moyen de vérification du laboratoire ; elle n'implémente pas la fonction d'analyse PCAP de NetGuard, prévue ultérieurement. Le moteur de détection, les alertes, PostgreSQL, FastAPI et le dashboard restent dans leurs étapes respectives. Aucun seuil de NG-NET-001 n'est décidé dans cette fiche.

## 9. Bilan de 1.1

- [x] Environnement d'exécution cible et prérequis techniques définis.
- [x] Décisions pertinentes de l'étape 0 reprises avec leurs références.
- [x] Composants minimaux, périmètre et budget de départ définis.
- [x] Contraintes de visibilité, d'isolation et de permissions explicites.
- [x] Critères de qualification et étapes de validation identifiés.

**1.1 — Cadrage terminé.** La [preuve 1.3](lab-visibility.md) qualifie la visibilité du montage initial ; les frontières d’isolation et permissions sont éprouvées en [1.4](lab-isolation.md). Le laboratoire minimal est consolidé en [1.5](lab-compose.md). Le cadrage est complété par la [topologie réseau concrète (1.2)](lab-topology.md).
