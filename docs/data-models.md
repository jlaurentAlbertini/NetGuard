# NetGuard — Modèles de domaine

## 1. Objectif

Ce document définit les modèles de domaine et les invariants sémantiques utilisés par NetGuard.

Il constitue la référence pour déterminer :

- ce qu'une observation réseau représente ;
- comment les identifiants réseau sont interprétés ;
- comment NetGuard représente les paquets et les flux ;
- comment le temps et la provenance sont modélisés ;
- comment les composants d'analyse maintiennent leur état ;
- quel contrat les détecteurs respectent ;
- comment les résultats de détection sont représentés ;
- comment les preuves structurées sont matérialisées ;
- comment les alertes sont représentées et suivies.

Ce document décrit des **contrats sémantiques**.

Il ne prescrit pas une classe Python pour chaque concept et ne signifie pas que tous les modèles décrits doivent être implémentés dès le premier incrément.

Le principe général est :

> NetGuard définit les distinctions nécessaires à un modèle réseau correct, mais n'implémente que les abstractions réellement nécessaires aux capacités présentes.

Les responsabilités architecturales générales sont définies dans [`architecture.md`](./architecture.md).

Le fonctionnement du moteur de détection est détaillé dans [`detection-engine.md`](./detection-engine.md).

---

# 2. Vue d'ensemble

Le chemin conceptuel principal est :

```text
Réalité réseau
      │
      │ observation imparfaite
      ▼
NetworkObservation
      │
      ├── PacketObservation
      └── FlowObservation
      │
      ├───────────────┐
      │               │
      ▼               ▼
État analytique      Flow éventuel
      │
      └───────┬───────┘
              ▼
           Detector
              │
              ▼
       DetectionResult
              │
              └── Evidence
              │
              ▼
            Alert
              │
              ▼
     Persistence / API / UI
```

Les distinctions suivantes sont fondamentales :

```text
PacketObservation ≠ paquet réel universel

FlowObservation ≠ Flow

Flow ≠ état mutable utilisé pour construire un Flow

Observation ≠ état analytique

État analytique ≠ Evidence

DetectionResult ≠ Alert

Evidence ≠ archive brute

Adresse réseau ≠ identité durable de machine

Network scope ≠ provenance

Source ≠ point d'observation

Observation time ≠ processing time

Severity ≠ confidence

Alert ≠ incident confirmé
```

La distinction générale à préserver est :

```text
réalité réseau
    ≠
ce que NetGuard observe
    ≠
ce que NetGuard calcule
    ≠
ce que la règle conclut
    ≠
la manière dont cette conclusion est suivie
```

---

# 3. NetworkObservation

## M1 — NetworkObservation est le concept racine des observations réseau analysables

`NetworkObservation` représente une observation réseau normalisée comprise par le Core.

Ce concept n'impose pas une hiérarchie d'héritage particulière.

L'implémentation pourra prendre la forme la plus adaptée aux besoins du code, par exemple une union de types, un protocole ou une autre représentation explicite.

## M2 — Les types d'observation restent sémantiquement distincts

Une observation paquet, un résumé de flux et une future catégorie d'observation possèdent des granularités, invariants et garanties différents.

NetGuard n'utilise pas un événement universel rempli de champs optionnels pour représenter indistinctement ces concepts.

Chaque détecteur indique explicitement les types qu'il accepte.

De petits objets valeur communs peuvent être partagés lorsque leur sémantique est réellement commune.

## M3 — PacketObservation représente l'observation individuelle d'un paquet à un point de capture donné

Une `PacketObservation` ne garantit pas l'identité unique d'un paquet dans le réseau.

Plusieurs sources peuvent observer le même paquet.

Une duplication de collecte et une retransmission réseau constituent des phénomènes distincts.

Aucun objet natif de bibliothèque de capture n'est exposé au Core.

## M4 — Flow et FlowObservation sont distincts

`Flow` représente un état ou agrégat construit par NetGuard.

`FlowObservation` représente une observation reçue dont la sémantique est déjà agrégée sous forme de flux.

Lorsqu'une `FlowObservation` est introduite, sa sémantique précise notamment si elle constitue :

- un résumé final ;
- un instantané cumulatif ;
- une mise à jour incrémentale ;
- une autre forme explicitement définie.

Aucun de ces modèles n'est créé uniquement pour satisfaire l'architecture.

Le premier détecteur peut utiliser directement des `PacketObservation` et son propre état borné.

## M5 — Les propriétés communes découlent de leur sémantique

Une propriété n'est pas déplacée vers un modèle commun uniquement parce qu'elle apparaît dans plusieurs structures.

Même le temps peut posséder une sémantique différente selon le type d'observation.

Par exemple, un paquet peut être associé à un instant tandis qu'une observation agrégée peut décrire un intervalle.

## M6 — Les absences pertinentes possèdent une sémantique explicite

Lorsque cela influence la validation ou l'analyse, NetGuard distingue notamment :

- non applicable ;
- inconnu ;
- non fourni ;
- non observable.

Cette distinction n'est introduite que lorsqu'elle possède une utilité analytique réelle.

NetGuard n'impose pas un système complexe d'état d'absence à chaque propriété.

## M7 — Le modèle domaine reste distinct des représentations techniques sans duplication systématique

Le Core définit les faits et invariants métier.

Les frontières techniques effectuent les traductions nécessaires.

Des modèles séparés pour API, stockage, sérialisation ou transport ne sont introduits que lorsque leurs contraintes le justifient.

NetGuard n'impose pas automatiquement plusieurs copies presque identiques d'un même concept.

---

# 4. Identité réseau et endpoints

## M8 — Les identifiants réseau sont typés selon leur sémantique

Adresse IP, adresse MAC, port et autres identifiants réseau ne sont pas interchangeables.

IPv4 et IPv6 appartiennent au concept d'adresse IP tout en conservant leur version.

Le Core ne représente pas indistinctement tous les identifiants réseau sous forme de chaînes libres.

## M9 — Les adresses possèdent une égalité sémantique et une représentation canonique

Les comparaisons utilisent des valeurs normalisées plutôt que des chaînes libres.

Deux représentations textuelles équivalentes d'une même adresse représentent la même valeur réseau dans un même contexte.

La normalisation ne fusionne pas implicitement différentes familles d'adresses.

## M10 — Une adresse ne constitue pas une identité durable de machine

Adresse IP, adresse MAC et `Host` constituent des concepts distincts.

NetGuard ne suppose ni qu'une adresse représente toujours une seule machine, ni qu'une machine possède toujours une seule adresse.

Les relations entre ces concepts représentent des observations, enrichissements ou déductions contextualisées.

DNS, hostname, MAC observée, inventaire ou futures corrélations ne remplacent pas implicitement l'identité analytique utilisée par les détecteurs.

Toute fusion future d'identités suit une politique explicite.

## M11 — Aucun Endpoint universel n'est imposé à toutes les observations

La définition d'un endpoint dépend de la couche et de la sémantique concernées.

`IP + port` convient à certains transports mais n'est pas imposé aux protocoles qui ne possèdent pas de ports.

Un identifiant ICMP, par exemple, n'est pas représenté artificiellement comme un port.

NetGuard n'impose pas prématurément une hiérarchie universelle telle que `IPEndpoint`, `TCPEndpoint` et `UDPEndpoint`.

## M12 — Un port est interprété dans le contexte de son protocole

Un numéro de port seul ne définit pas un endpoint de transport.

```text
TCP/53 ≠ UDP/53
```

Toute identité de communication utilisant des ports conserve donc le contexte du protocole de transport correspondant.

La présence d'un port ne prouve pas l'identité d'un protocole applicatif ou d'un service.

## M13 — Les protocoles conservent leur niveau sémantique

Les informations de couche liaison, réseau, transport et application restent distinguées.

Un champ ambigu `protocol` ne mélange pas, par exemple :

```text
IPv6
TCP
HTTP
```

Une information protocolaire inconnue n'est pas remplacée par une valeur supposée.

## M14 — Source et destination décrivent le sens de l'observation

Source et destination décrivent la direction de l'observation considérée.

Elles ne signifient pas automatiquement :

- client et serveur ;
- initiateur et répondeur ;
- attaquant et victime ;
- interne et externe.

Ces rôles nécessitent une interprétation explicite.

L'observation du trafic dans le sens inverse ne doit pas modifier accidentellement l'identité d'un comportement suivi par un détecteur.

## M15 — Toute direction relative possède un référentiel explicite

Les notions `inbound` et `outbound` n'ont de sens que relativement à un référentiel défini, par exemple :

- une interface ;
- une zone réseau ;
- un hôte ;
- un périmètre surveillé.

Elles ne sont pas déduites uniquement de l'ordre source → destination.

## M16 — Les clés directionnelles et bidirectionnelles sont distinctes

Une clé directionnelle conserve :

```text
A → B
```

Une clé bidirectionnelle peut canonicaliser :

```text
A → B
B → A
```

en :

```text
A ↔ B
```

selon une convention explicite.

Cette canonicalisation n'efface pas le sens des observations ni les rôles éventuellement établis.

Les deux concepts ne sont pas cachés derrière une clé ambiguë unique.

## M17 — L'identité réseau est contextualisée et limitée dans le temps

Une adresse peut être réutilisée dans différents périmètres réseau.

Les mêmes adresses, ports et protocoles peuvent également représenter des communications successives.

Toute observation analysable possède donc un contexte réseau défini.

Pour le laboratoire initial, ce contexte peut provenir d'une configuration statique unique.

Un `sensor_id` n'est pas automatiquement un `network_scope`.

Plusieurs sources peuvent observer le même périmètre réseau.

Lorsque certaines adresses nécessitent un contexte supplémentaire pour être interprétées sans ambiguïté, notamment certaines adresses IPv6 link-local, ce contexte est préservé.

NAT, transformations ou frontières de capture ne constituent pas à eux seuls une identité réseau globale ou permanente.

## M18 — Les informations absentes ne sont pas remplacées par des valeurs fictives

Une information indisponible n'est pas remplacée par une valeur artificielle.

Par exemple :

```text
port non observable ≠ port 0
```

Un fragment ou une capture tronquée peut masquer une information réellement présente sur le réseau.

Lorsque cela influence la validation, l'éligibilité ou la décision, NetGuard distingue les différentes causes d'absence.

Un détecteur traite une observation uniquement lorsque les informations nécessaires à sa règle sont disponibles avec les garanties requises.

## M19 — Chaque détecteur définit sa propre clé de regroupement

Une clé de communication n'est pas automatiquement une clé de détection.

Chaque détecteur choisit les dimensions nécessaires à son analyse et documente celles qu'il inclut ou exclut.

Pour `NG-NET-001`, la clé candidate à valider lors de la conception détaillée du détecteur est :

```text
(
    network_scope,
    source_ip,
    destination_ip,
    transport_protocol
)
```

avec :

```text
destination_port → valeur distincte comptée dans la fenêtre
source_port      → ne partitionne pas l'état du scan
```

Cette clé reste une candidate tant que le contrat détaillé de `NG-NET-001` n'est pas validé.

## M20 — Les valeurs utilisées comme identifiants ou clés sont immuables

Leur égalité et leur hash reposent uniquement sur des champs explicites, stables et déterministes.

Aucune résolution DNS, réseau, base de données ou autre opération cachée n'intervient dans leur construction, comparaison ou hash.

Un hash respecte l'égalité de l'objet et reste stable pendant son utilisation comme clé.

Il n'est ni un identifiant persistant ni une garantie de stabilité entre exécutions.

La reproductibilité de l'analyse ne dépend pas de la valeur numérique du hash.

L'implémentation initiale privilégie les types standard Python `IPv4Address` et `IPv6Address` lorsque cela convient.

Les objets valeur composites NetGuard sont de préférence petits et immuables.

## M21 — Le support des protocoles est explicite et progressif

NetGuard distingue :

```text
ce que le modèle peut représenter
≠
ce que l'adaptateur sait observer ou décoder
≠
ce que le détecteur sait analyser
```

Un protocole inconnu ou non pris en charge n'est pas remplacé par un protocole connu.

Lorsqu'un identifiant protocolaire est disponible, il peut être préservé sans prétendre que NetGuard possède une prise en charge sémantique complète.

Le support d'un type dans le Core ne prouve pas le support complet de bout en bout.

Le premier incrément privilégie :

- les types standard Python pour IPv4 et IPv6 ;
- de petits objets valeur immuables lorsque nécessaire ;
- un `network_scope` explicite ;
- éventuellement un unique scope configuré pour le laboratoire ;
- uniquement les représentations de transport nécessaires aux premiers détecteurs ;
- des clés propres aux détecteurs ;
- aucun registre global d'hôtes prématuré ;
- aucun gestionnaire générique de conversations bidirectionnelles prématuré ;
- aucun modèle MAC sans besoin concret.

---

# 5. PacketObservation

## M22 — PacketObservation représente une occurrence d'observation, pas l'identité globale d'un paquet

Une instance correspond à l'observation individuelle rapportée par une source.

Un même paquet peut être observé plusieurs fois, notamment depuis plusieurs points de capture.

Deux observations similaires ne sont pas automatiquement des doublons.

Une retransmission réseau ne doit pas être confondue avec une duplication de collecte.

Un identifiant éventuel d'observation identifie cette occurrence sans prétendre identifier universellement le paquet.

## M23 — Toute PacketObservation possède un network_scope_id

Ce champ identifie le périmètre dans lequel les adresses sont interprétées.

Pour le laboratoire initial, il peut provenir d'une configuration statique unique.

Il n'est pas déduit arbitrairement des adresses présentes dans le paquet.

Le contexte supplémentaire nécessaire à une identité non ambiguë reste préservé conformément à M17.

## M24 — Toute PacketObservation possède une provenance explicite

La provenance permet de rattacher l'observation à sa source et, lorsque nécessaire, à une session de capture, un point d'observation ou un enregistrement.

Le contrat distingue clairement :

- la source de collecte ;
- le point d'observation ;
- le périmètre réseau.

Plusieurs sources peuvent observer le même périmètre.

La forme concrète de cette provenance dépend des besoins présents du système.

Le modèle n'impose pas prématurément qu'un `sensor_id` soit directement porté par chaque `PacketObservation` si une autre représentation explicite fournit la même garantie.

La provenance n'impose pas de conserver un chemin local sensible, un objet technique de capture ou toute autre information propre à l'implémentation.

## M25 — observed_at constitue le temps métier principal de l'observation

Il désigne l'instant rapporté pour l'observation du paquet.

Lors d'une relecture PCAP, il conserve le temps enregistré pour le paquet et non l'heure de sa relecture.

Un éventuel temps d'ingestion ou de traitement reste distinct.

L'absence d'un temps exploitable n'est pas compensée silencieusement par l'heure courante.

## M26 — Les timestamps sont non ambigus et respectent la précision disponible

La représentation interne possède une référence temporelle explicite et commune.

La normalisation ne prétend pas améliorer la précision ou l'exactitude de la source.

Lorsqu'une conversion réduit la résolution disponible, cette politique est définie.

Un timestamp normalisé ne garantit pas que les horloges de différentes sources sont synchronisées.

Plusieurs observations peuvent légitimement partager le même timestamp à la précision disponible.

NetGuard n'invente pas une précision supplémentaire pour leur imposer artificiellement un ordre temporel.

## M27 — Le contrat initial de PacketObservation analysable possède une sémantique IP explicite

Pour le premier incrément, une observation admise identifie une couche IPv4 ou IPv6 et ses adresses source et destination.

Cette restriction définit le périmètre initial du modèle.

Elle ne signifie pas que tout paquet réseau est IP.

Les observations hors de ce périmètre suivent une politique explicite.

Les extensions futures ne leur attribuent pas artificiellement des adresses IP.

## M28 — Les informations dérivables ne sont pas stockées plusieurs fois sans besoin

Une information déductible sans ambiguïté d'une valeur canonique peut être exposée comme propriété calculée.

Si une information dérivée est matérialisée pour une raison concrète, sa cohérence est garantie par construction ou validation.

Deux champs ne deviennent pas des sources de vérité concurrentes.

## M29 — L'identité protocolaire préservée correspond exactement au niveau effectivement identifié

NetGuard conserve l'identifiant protocolaire connu et distingue cette connaissance de sa capacité à décoder le protocole.

La signification d'un champ protocolaire est précise.

Il ne mélange pas un indicateur de couche suivante avec un protocole de transport effectivement identifié.

Un identifiant connu ne garantit pas que l'en-tête correspondant est disponible ou exploitable.

Un protocole non pris en charge n'est pas remplacé par TCP.

## M30 — Les informations spécifiques restent attachées au protocole concerné

Les champs TCP, UDP ou propres à un autre protocole conservent leur sémantique et sont regroupés dans une représentation appropriée.

Le modèle n'impose pas un ensemble universel de champs de transport majoritairement optionnels.

Le protocole identifié et les informations décodées ne doivent pas se contredire.

## M31 — Les flags TCP possèdent une représentation domaine explicite

Ils sont représentés par des valeurs NetGuard indépendantes des constantes et objets de la bibliothèque de capture.

Leur présence suppose que les bits correspondants ont effectivement pu être observés.

Des flags indisponibles ne sont pas équivalents à un ensemble de flags vide.

Le modèle ne déduit pas automatiquement une connexion établie ou une attaque de leur seule présence.

## M32 — Toute longueur possède une unité et une signification explicites

Un champ de longueur indique ce qu'il mesure, par exemple :

- octets capturés ;
- longueur rapportée de la trame ;
- longueur IP déclarée ;
- autre quantité explicitement définie.

Ces mesures ne sont pas interchangeables.

Une longueur déclarée dans un en-tête ne prouve pas que tous les octets correspondants ont été capturés.

Seules les mesures nécessaires aux capacités présentes sont introduites.

## M33 — Les limites de capture pertinentes sont représentées explicitement

Lorsque la source permet de savoir qu'une capture est tronquée ou partielle, cette information n'est pas perdue si elle affecte l'interprétation.

L'absence de preuve de troncature ne vaut pas toujours preuve de complétude.

Le modèle distingue ces situations lorsqu'elles influencent l'analyse.

La disponibilité d'un en-tête de transport ne garantit pas la disponibilité du reste du paquet.

## M34 — La fragmentation ne produit aucune information de transport fictive

NetGuard ne renseigne les ports, flags et autres champs de transport que lorsque leur présence et leur interprétation sont effectivement établies.

La fragmentation n'implique ni disponibilité systématique ni absence systématique de ces informations.

Le premier incrément ne suppose aucun réassemblage implicite.

Un futur résultat de réassemblage conserve une sémantique distincte de l'observation d'un fragment individuel.

## M35 — Le payload brut ne fait pas partie du PacketObservation canonique initial

Le Core reçoit les métadonnées nécessaires à ses analyses sans conserver systématiquement le contenu brut du paquet.

Un éventuel mécanisme de conservation de preuves reste séparé, avec une politique explicite de sécurité, de rétention et de référencement.

L'absence de payload dans le modèle ne signifie pas que le paquet observé n'en contenait pas.

## M36 — PacketObservation est immuable après validation

Ses valeurs métier ne changent plus après son admission dans le Core.

Cette garantie s'applique également aux collections et objets imbriqués.

Une structure déclarée immuable ne contient pas de dictionnaire, liste ou autre objet encore modifiable permettant d'altérer silencieusement son contenu.

Les enrichissements ultérieurs restent séparés ou produisent une nouvelle représentation explicitement liée à l'observation.

## M37 — Une PacketObservation valide respecte les invariants définis par son contrat

La validation vérifie notamment :

- la présence des champs obligatoires ;
- les types et domaines de valeurs ;
- la cohérence des adresses avec la couche IP représentée ;
- la cohérence entre le protocole identifié et les informations spécifiques ;
- la représentation explicite des absences pertinentes.

Cette validation garantit la cohérence du modèle.

Elle ne garantit pas la conformité intégrale du paquet à tous les protocoles.

## M38 — Les conditions d'admission, de représentation partielle et de rejet sont explicites

Le contrat définit le minimum nécessaire pour construire une `PacketObservation`.

Une observation partielle peut être admise si elle respecte ce minimum et représente honnêtement ses limites.

Une entrée qui ne permet pas de respecter le contrat est rejetée ou orientée vers un mécanisme diagnostique distinct.

Les rejets et cas non pris en charge sont observables.

Ils ne sont pas corrigés silencieusement par des valeurs inventées.

## M39 — La validité d'une observation ne garantit pas son éligibilité pour chaque détecteur

Chaque détecteur définit les informations et types d'observation qu'il exige.

Une observation IP valide peut être inexploitable par une règle nécessitant des ports TCP et des flags observables.

Elle n'est pas pour autant invalide pour tout le Core.

La normalisation établit les faits disponibles.

Le détecteur détermine s'ils suffisent à son analyse.

## M40 — PacketObservation ne certifie ni l'identité de l'émetteur ni le résultat de la communication

L'observation d'un paquet ne démontre pas :

- l'authenticité de son adresse source ;
- sa réception par la destination ;
- l'acceptation d'une connexion ;
- la présence d'un service particulier ;
- l'absence d'autres paquets non capturés.

Ces conclusions nécessitent des observations supplémentaires et des règles d'interprétation explicites.

## M41 — La sélection des couches représentées suit une politique explicite

Lorsqu'une capture contient plusieurs couches candidates, notamment en présence d'encapsulation, la couche représentée par `PacketObservation` suit une politique explicitement définie.

La présence de plusieurs couches candidates ne constitue pas nécessairement une erreur ou une ambiguïté de décodage.

Plusieurs couches peuvent être correctement identifiées tout en représentant différents niveaux d'encapsulation.

NetGuard ne mélange pas les adresses d'une couche avec les ports ou informations spécifiques d'une autre couche.

Il ne sélectionne pas arbitrairement la première ou la dernière couche reconnue.

Le support complet des encapsulations peut rester différé dans le premier incrément.

Leur traitement initial reste néanmoins déterministe, documenté et observable lorsqu'une entrée ne peut pas être représentée conformément au contrat.

---

# 6. Flow et FlowObservation

## M42 — Flow n'est pas une étape obligatoire entre observation et détection

Un détecteur peut analyser directement des `PacketObservation` lorsque cela correspond à sa sémantique.

La présence d'un modèle `Flow` ne force pas toutes les observations à être préalablement agrégées.

Un `Flow` n'est introduit dans un chemin d'analyse que lorsqu'il apporte une information ou abstraction réellement utile.

## M43 — Flow est une construction analytique de NetGuard

Un `Flow` représente un état agrégé construit par NetGuard à partir d'observations regroupées selon une définition et une politique explicitement définies.

Son existence, ses frontières et son identité dépendent de cette politique d'agrégation.

NetGuard ne présente pas un `Flow` comme une entité réseau universelle indépendante de cette politique.

## M44 — Une clé de regroupement ne constitue pas à elle seule l'identité temporelle d'un Flow

Une même clé réseau peut correspondre à plusieurs `Flow` successifs.

La politique d'agrégation définit les critères permettant de séparer ces instances, par exemple :

- une expiration ;
- une fermeture explicite ;
- un autre critère défini.

L'identité d'une instance dépend donc de sa clé de regroupement et de la politique temporelle qui gouverne sa création, sa continuation et sa séparation des instances suivantes.

Cette distinction n'impose pas immédiatement un identifiant universel de session.

Un hash de clé réseau n'est pas utilisé comme identité persistante supposée unique d'un `Flow`.

## M45 — La directionnalité d'un Flow fait partie de sa définition

Un `Flow` directionnel et un `Flow` bidirectionnel sont des abstractions différentes.

Une politique d'agrégation précise explicitement laquelle elle construit.

Dans un `Flow` bidirectionnel, la canonicalisation de la clé ne supprime pas la direction propre de chaque observation ni les compteurs directionnels nécessaires.

## M46 — La canonicalisation d'un Flow ne crée aucun rôle sémantique

L'ordre utilisé pour construire une clé stable est distinct des rôles observés ou inférés.

Initiateur, répondeur, client, serveur ou autres rôles nécessitent une règle séparée et des observations suffisantes.

Une position dans une clé canonique ne constitue pas une preuve de rôle réseau.

## M47 — Un Flow contient uniquement les agrégats nécessaires aux capacités présentes

Les métriques ou états ne sont pas ajoutés simplement parce qu'ils sont traditionnellement associés aux outils d'analyse réseau ou aux formats de flow.

Chaque donnée agrégée possède une définition explicite et une raison d'être.

Le modèle initial reste limité aux informations réellement nécessaires aux capacités de NetGuard.

## M48 — Les bornes temporelles observées d'un Flow sont distinctes de ses temps techniques de gestion

`first_observed_at` et `last_observed_at`, lorsqu'ils existent, décrivent les observations admises dans le `Flow` selon leur temps métier.

Ils sont distincts des temps techniques pouvant correspondre notamment :

- à la création de l'état ;
- à son expiration ;
- à son éviction ;
- à sa finalisation.

Une observation tardive ou hors ordre ne modifie les bornes observées que conformément à la politique d'admission.

L'absence de nouvelles observations ne doit pas empêcher indéfiniment l'expiration ou le nettoyage de l'état.

## M49 — Chaque compteur d'un Flow possède une grandeur comptée explicitement définie

Un compteur d'observations représente le nombre d'observations effectivement admises dans l'agrégat selon sa politique.

Il ne garantit pas le nombre de paquets uniques ayant réellement existé ou circulé sur le réseau.

Lorsqu'une source agrégée est utilisée, le nombre de rapports reçus et le nombre de paquets rapportés par ces rapports constituent deux grandeurs distinctes.

Toute déduplication, fusion multi-source ou correction possède une politique explicite.

Aucun compteur ne masque la différence entre :

- observations reçues ;
- observations agrégées ;
- quantités rapportées par une source.

## M50 — Les agrégats de volume conservent la sémantique de la mesure agrégée

Un compteur d'octets précise ce qui est effectivement additionné.

Octets capturés, longueurs IP déclarées, longueurs de trame et autres mesures ne sont pas mélangés sous un `byte_count` ambigu.

Une métrique n'est introduite que si les observations sources fournissent une mesure compatible avec sa définition.

## M51 — Le début observé d'un Flow n'est pas nécessairement le début réel de la communication

Un `Flow` peut être créé à partir d'une observation intermédiaire lorsque la politique d'agrégation l'autorise.

L'absence d'observation du commencement d'une communication n'est pas transformée en preuve que la première observation admise correspond à son commencement réel.

Le modèle distingue donc le début observé de l'éventuel début réel, que NetGuard peut ne pas connaître.

## M52 — La fermeture d'un Flow possède une cause explicite

Un `Flow` peut notamment être clôturé à la suite :

- d'une expiration selon une politique temporelle ;
- d'une éviction liée aux ressources ;
- d'un arrêt du traitement ou de la source ;
- d'une condition protocolaire explicitement définie ;
- d'une autre condition prévue par la politique.

Ces causes ne sont pas sémantiquement équivalentes.

La clôture signifie que NetGuard cesse de maintenir cette instance selon sa politique.

Elle ne prouve pas nécessairement que la communication réelle s'est terminée au même instant.

## M53 — L'état d'agrégation actif est distinct d'une représentation finalisée

L'état mutable nécessaire à la construction d'un `Flow` n'est pas nécessairement le même contrat que la représentation stable exposée au reste du système.

La finalisation d'un agrégat NetGuard ne signifie pas nécessairement que la communication réseau est terminée.

La politique définit également le traitement d'une observation tardive correspondant à un `Flow` déjà finalisé.

Selon la politique, cette observation peut notamment conduire :

- à un rejet comptabilisé ;
- à une correction explicitement versionnée ;
- à la création d'un nouvel agrégat.

Un résultat déjà finalisé ou publié n'est pas modifié silencieusement.

## M54 — FlowObservation représente une observation agrégée fournie par une source

Une `FlowObservation` décrit un agrégat reçu d'une source externe ou d'un composant possédant déjà cette sémantique.

Elle ne doit pas être confondue avec un `Flow` construit par NetGuard à partir de ses propres observations.

Sa provenance permet de comprendre que les compteurs, bornes temporelles et autres propriétés rapportées proviennent de cette source.

## M55 — La sémantique de mise à jour d'une FlowObservation est explicite

Une `FlowObservation` indique si ses valeurs représentent notamment :

- un instantané cumulatif ;
- un incrément ou delta ;
- un rapport final ;
- une autre sémantique explicitement définie.

Ces catégories ne sont pas combinées comme si elles étaient équivalentes.

Le traitement définit lorsque nécessaire le comportement face :

- aux répétitions ;
- aux remises à zéro des compteurs ;
- aux arrivées désordonnées.

Un rapport dont la sémantique de mise à jour est inconnue ou insuffisamment établie n'est pas additionné arbitrairement à d'autres rapports.

## M56 — FlowObservation ne reconstruit pas artificiellement les observations élémentaires absentes

Un agrégat externe n'est pas transformé en un faux ensemble de `PacketObservation`.

Les informations absentes du rapport source ne sont pas recréées ou supposées.

Un détecteur nécessitant des propriétés disponibles uniquement au niveau paquet ne devient pas éligible simplement parce qu'une `FlowObservation` existe.

## M57 — La clé, la directionnalité et les garanties d'une FlowObservation reflètent le contrat de sa source

NetGuard préserve la signification de l'observation fournie sans exposer au Core les objets techniques de la source.

Les conventions purement techniques peuvent être normalisées lorsqu'elles ne modifient pas la sémantique.

NetGuard n'invente aucune garantie absente de la source concernant notamment :

- la directionnalité ;
- la granularité ;
- la complétude ;
- l'identité d'une communication.

Toute conversion vers une abstraction possédant une autre sémantique constitue une opération explicitement définie.

## M58 — L'agrégation de sources de granularités différentes nécessite une politique explicite

NetGuard ne fusionne pas automatiquement `PacketObservation` et `FlowObservation` dans un même état d'agrégation.

Une telle fusion définit notamment :

- leur compatibilité sémantique ;
- les risques de double comptage ;
- la provenance ;
- leur granularité ;
- leur politique temporelle.

Lorsque paquets et résumés peuvent couvrir tout ou partie du même trafic, ils ne sont pas additionnés naïvement.

Le premier incrément ne suppose aucune fusion générique de ces granularités.

## M59 — Une FlowObservation possède une identité d'occurrence distincte de l'identité de la communication décrite

Plusieurs observations agrégées similaires peuvent correspondre à différents rapports logiques provenant de sources, fenêtres ou mises à jour différentes.

L'identité d'un rapport logique est également distincte de ses éventuelles réceptions répétées.

Lorsqu'une source fournit un mécanisme fiable permettant d'identifier ces répétitions, NetGuard peut appliquer une politique de déduplication explicite.

Lorsque la source ne fournit pas suffisamment d'informations pour les reconnaître avec certitude, NetGuard ne prétend pas disposer d'une déduplication certaine.

La corrélation entre plusieurs `FlowObservation` ne découle donc pas uniquement de l'égalité de leurs endpoints ou de leur clé réseau.

## M60 — La construction des Flow est déterministe relativement à l'ensemble de ses entrées contrôlées

Le résultat dépend notamment :

- de la séquence d'observations admises ;
- de la configuration ;
- de l'état initial ;
- de la version de la politique d'agrégation ;
- des éventuels signaux temporels ou de cycle de vie nécessaires.

À entrées contrôlées et politique équivalentes, l'agrégation produit des résultats sémantiquement équivalents.

Cette exigence couvre également :

- les décisions d'expiration ;
- les décisions de finalisation ;
- les décisions d'éviction.

Les identifiants aléatoires, le temps système implicite ou autres détails non contrôlés ne modifient pas silencieusement les décisions métier.

## M61 — Tout état de Flow actif est borné, y compris dans ses structures internes

Le système définit des limites temporelles et/ou quantitatives pour les agrégats actifs.

Les structures maintenues à l'intérieur de chaque agrégat sont elles aussi bornées lorsque leur cardinalité peut croître avec le trafic.

Une collection illimitée de ports, adresses, identifiants ou observations ne doit pas contourner les limites globales de mémoire.

Les politiques d'expiration et d'éviction sont définies et observables.

Une éviction liée aux ressources reste distincte d'une terminaison réseau observée ou d'une finalisation normale.

## M62 — Flow conserve les limites d'identité établies par le modèle réseau

L'agrégation ne transforme pas automatiquement une adresse en identité durable de machine.

Un `Flow` ne permet pas à lui seul de conclure qu'une adresse représente durablement un `Host` unique.

Les enrichissements, résolutions et corrélations restent soumis aux règles d'identité et de contexte définies notamment par M10 et M17.

L'agrégation ne crée donc pas implicitement une identité plus forte que celle portée par les observations dont elle provient.

---

# 7. Temps et provenance

## M63 — Temps métier et temps techniques sont distincts

Le temps associé au fait observé est distingué des temps :

- de réception ;
- de traitement ;
- de persistance ;
- de publication.

Chaque timestamp possède une signification explicite.

Un temps technique ne remplace pas silencieusement un temps métier absent.

## M64 — Les détections temporelles réseau raisonnent sur le temps métier approprié aux observations

Les fenêtres décrivant l'activité réseau utilisent normalement le temps des observations.

Une observation agrégée peut décrire un intervalle.

Son temps métier ne se réduit pas arbitrairement à son heure de réception.

Chaque règle précise les instants ou intervalles qu'elle utilise.

Une règle portant sur le fonctionnement de NetGuard peut utiliser un temps technique explicitement défini.

## M65 — Normaliser les timestamps ne synchronise pas les horloges

Une référence temporelle commune ne garantit ni l'exactitude des horloges sources ni leur alignement.

Une analyse entre plusieurs sources ne suppose pas leur synchronisation sans justification.

Toute correction d'horloge possède une politique explicite et conserve la traçabilité nécessaire.

## M66 — Le temps canonique possède une référence non ambiguë

Les instants comparables utilisent une convention temporelle commune explicitement définie.

Une heure locale dépourvue de contexte suffisant n'est pas interprétée arbitrairement.

Le choix concret de représentation et ses limites sont documentés lors de l'implémentation.

## M67 — Résolution de représentation et précision de connaissance sont distinctes

Le nombre de décimales disponible dans un type ne démontre pas la précision de la source ni l'exactitude de son horloge.

NetGuard ne fabrique pas une précision supplémentaire.

Les conversions réduisant la résolution suivent une politique définie.

Les observations ayant le même timestamp restent légitimes.

## M68 — Ordre d'admission et ordre temporel sont distincts

L'ordre dans lequel NetGuard traite les observations ne garantit pas leur ordre chronologique.

Lorsque plusieurs observations partagent le même temps métier, une politique explicite détermine leur traitement sans modifier leurs timestamps.

Les garanties de reproductibilité précisent l'ordre d'entrée requis.

## M69 — Le caractère tardif d'une observation dépend d'une politique explicite

Une observation n'est pas qualifiée de tardive uniquement parce que son timestamp précède l'heure système.

La politique définit :

- la référence de progression ;
- le désordre éventuellement toléré ;
- le comportement appliqué.

Elle ne nécessite pas immédiatement un mécanisme complexe de réordonnancement.

## M70 — Une donnée tardive ne modifie pas silencieusement un résultat stabilisé

La politique définit quand un résultat est considéré comme stabilisé et comment sont traitées les observations ultérieures susceptibles de l'affecter.

Les comportements suivants sont distincts :

- rejet ;
- correction versionnée ;
- nouveau résultat.

Une publication ou persistance préalable n'est pas réécrite silencieusement.

## M71 — La maintenance utilise une notion de temps explicite et contrôlable

Les délais opérationnels sont distingués des fenêtres métier.

Une horloge adaptée à la mesure de durées peut servir aux délais techniques sans être confondue avec les timestamps des observations.

Si une action de maintenance supprime ou modifie un état susceptible d'influencer la détection, son déclenchement fait partie des entrées contrôlées de l'analyse.

Une expiration sur inactivité ne doit pas introduire indirectement une dépendance cachée à l'heure système.

## M72 — La vitesse de replay ne modifie pas les décisions fondées sur le temps métier

À observations admises, ordre, configuration, état initial et signaux de progression équivalents, accélérer ou ralentir une relecture produit des décisions sémantiquement équivalentes.

La maintenance respecte cette propriété.

Si la vitesse entraîne des pertes ou une dégradation liée aux ressources, les entrées ne sont plus équivalentes.

Cette limitation est signalée et n'est pas présentée comme une analyse identique.

## M73 — Toute observation analysable possède une provenance explicite et exploitable

La provenance permet de rattacher l'information à son origine et au contexte nécessaire à son interprétation.

Elle peut être portée directement ou référencée par un contrat explicite.

Une référence ne doit pas nécessiter une résolution technique cachée dans les détecteurs.

## M74 — Source, point d'observation, session et périmètre réseau restent distincts

Ces concepts répondent à différentes questions :

- **source** : quel producteur ou enregistrement fournit l'information ;
- **point d'observation** : depuis quel emplacement logique elle a été observée ;
- **session** : dans quelle exécution ou séquence de collecte elle s'inscrit ;
- **network scope** : dans quel périmètre ses identifiants réseau sont interprétés.

Ils peuvent être liés sans être assimilés.

## M75 — Les identifiants de provenance possèdent une portée et une durée de validité définies

Lorsqu'un identifiant de source ou de session est nécessaire, son unicité attendue, sa stabilité et ses conditions de renouvellement sont explicites.

Un identifiant local à une exécution n'est pas présenté comme global ou permanent.

L'identité d'un enregistrement et celle d'une exécution de replay peuvent être distinctes.

## M76 — La provenance minimise les informations techniques et sensibles

Seules les informations nécessaires :

- à l'interprétation ;
- au diagnostic ;
- à l'audit ;
- à la reproductibilité

sont conservées.

La provenance ne contient pas par défaut :

- de secrets ;
- de chemins locaux complets ;
- d'objets propres à une bibliothèque.

Une référence maîtrisée peut remplacer un détail technique sensible.

## M77 — La provenance ne constitue pas une garantie de confiance

Identifier une source ne prouve ni :

- son authenticité ;
- son intégrité ;
- l'exactitude de ses informations.

Validation structurelle, authentification éventuelle de la source et fiabilité de ses affirmations constituent des garanties distinctes.

NetGuard ne déduit pas une confiance globale de la seule présence d'une provenance.

## M78 — Les transformations préservent la traçabilité nécessaire à l'interprétation des résultats

Normalisation, agrégation, correction et enrichissement conservent les références et politiques nécessaires pour expliquer l'origine des informations produites.

Cette exigence n'impose pas de conserver indéfiniment chaque paquet ou une liste illimitée de contributeurs.

La traçabilité reste :

- proportionnée ;
- bornée ;
- soumise à une politique de rétention.

## M79 — Toute dépendance de détection à la provenance est explicite et justifiée par le domaine

Un contexte tel que le périmètre ou le point d'observation peut avoir une signification métier.

Un nom de fichier, chemin local ou identifiant technique arbitraire ne doit pas modifier une décision.

Les éléments de provenance réellement utilisés par une règle font partie de ses entrées documentées et testées.

## M80 — La reproductibilité dépend des éléments de provenance sémantiquement pertinents

Une relecture peut posséder une nouvelle session d'exécution tout en représentant les mêmes observations métier.

Les changements de provenance purement techniques ne modifient pas les décisions.

Les références de source, versions de transformation et configurations nécessaires à l'explication d'un résultat restent disponibles selon la politique de traçabilité.

### Portée du premier incrément

Pour le premier incrément, cela demande surtout de définir :

- les timestamps utilisés ;
- la provenance minimale ;
- le traitement du désordre ;
- le déclenchement des expirations.

Cela n'impose :

- ni synchronisation distribuée ;
- ni score générique de confiance ;
- ni moteur universel de traçabilité.

---

# 8. État d'analyse

## M81 — L'état d'analyse est une mémoire de travail dérivée des observations et des entrées de contrôle explicites

L'état d'analyse contient les informations nécessaires pour évaluer une règle sur plusieurs observations ou dans le temps.

Il est dérivé des observations admises, mais celles-ci ne constituent pas ses seules entrées.

Les éléments suivants peuvent également provoquer des transitions :

- expiration ;
- réinitialisation ;
- configuration ;
- événements explicites du cycle de vie.

L'état est une mémoire de travail analytique.

Il ne constitue ni une nouvelle observation réseau ni une nouvelle source de vérité indépendante des données et politiques dont il provient.

## M82 — La structure de l'état est définie par le besoin analytique qui l'utilise et possède un propriétaire explicite

Chaque détecteur ou composant d'analyse définit les informations, agrégats et structures nécessaires à sa logique.

Un état possède un composant propriétaire responsable de ses transitions et de son cycle de vie.

NetGuard n'impose pas un état universel contenant toutes les informations susceptibles d'être utiles à tous les détecteurs.

Les structures communes ne sont introduites que lorsqu'elles possèdent :

- une sémantique réellement partagée ;
- un besoin démontré.

## M83 — Chaque état d'analyse possède une clé de regroupement explicitement définie lorsque son besoin nécessite plusieurs groupes

La clé utilisée pour retrouver ou associer un état analytique est déterminée par la sémantique de la règle.

Elle n'est pas automatiquement :

- une clé de `Flow` ;
- une identité d'hôte ;
- une clé universelle NetGuard.

Les dimensions incluses et exclues font partie du contrat de l'analyse.

Lorsqu'un état ne nécessite aucun regroupement distinct, l'absence de clé constitue elle-même un choix explicite.

## M84 — Une clé de regroupement conserve les dimensions nécessaires sans fragmenter inutilement le comportement recherché

Deux observations ne partagent un état que si la politique de la règle autorise leur regroupement.

Les contextes réseau, protocoles, directions ou autres dimensions dont la distinction influence la règle restent représentés.

L'omission d'une dimension constitue une décision analytique explicite et non une simplification accidentelle.

Inversement, ajouter indistinctement tous les champs disponibles peut fragmenter artificiellement un comportement que la règle cherche précisément à corréler.

## M85 — Tout état d'analyse est borné dans toutes les dimensions susceptibles de croître sans limite

Le système définit des limites adaptées :

- au nombre d'entrées ;
- aux structures internes de chaque entrée.

Une limite globale ne suffit pas lorsqu'une seule entrée peut contenir une collection dont la cardinalité peut croître sans borne.

Le bornage temporel correspond à une politique de rétention des informations nécessaires à l'analyse.

Un état régulièrement alimenté peut rester actif longtemps sans conserver indéfiniment l'intégralité de son historique.

Les limites retenues font partie du contrat de l'état.

## M86 — Tout état temporel possède une politique explicite d'expiration ou de finalisation

Lorsqu'une information n'a plus vocation à influencer une décision future, une politique définit quand elle peut être :

- supprimée ;
- finalisée ;
- remplacée.

Cette politique précise la référence temporelle ou le signal de progression utilisé conformément au modèle temporel de NetGuard.

L'absence de nouvelles observations pour une clé ne doit pas empêcher indéfiniment son nettoyage.

Une expiration susceptible d'influencer l'analyse ne dépend pas d'une horloge implicite pouvant modifier silencieusement les résultats.

## M87 — Expiration analytique et éviction liée aux ressources sont distinctes

Une expiration retire un état ou une information devenue inutile selon la politique analytique normale.

Une éviction retire un état afin de respecter une contrainte de capacité ou de ressources, potentiellement avant qu'il ait perdu son utilité analytique.

Ces événements ne sont pas sémantiquement équivalents.

Le système conserve cette distinction dans son comportement et son observabilité.

## M88 — Toute perte connue d'état susceptible de dégrader une analyse est observable

Lorsqu'une éviction, saturation, perte d'état ou autre événement connu peut réduire les informations disponibles, NetGuard expose cette dégradation de manière appropriée.

Il peut notamment indiquer :

- le nombre d'états évincés ;
- les composants concernés ;
- qu'une analyse fonctionne avec des informations dégradées.

NetGuard ne prétend pas déterminer rétrospectivement combien d'alertes hypothétiques auraient été produites sans cette perte lorsque cette information n'est pas connaissable.

Cette observabilité est elle-même bornée.

## M89 — L'état conserve le minimum d'information nécessaire à la décision, à son cycle de vie et à son explicabilité

Un détecteur ne conserve pas les observations complètes lorsqu'une représentation résumée et bornée suffit.

Toute information conservée possède une utilité explicite, notamment :

- décision ;
- expiration ;
- déduplication nécessaire ;
- production de preuves ;
- autre exigence définie.

La minimisation ne doit pas empêcher la production des informations nécessaires à l'explication des résultats.

## M90 — L'état nécessaire à la détection et les preuves nécessaires à l'alerte possèdent des représentations et cycles de vie distincts

Au moment où un résultat nécessitant une explication stable est produit, les informations nécessaires sont matérialisées dans une représentation adaptée.

Une alerte ne dépend pas d'une référence vers un état analytique mutable susceptible de :

- changer ;
- expirer ;
- être évincé.

Les preuves peuvent être des résumés bornés.

Cette exigence n'impose pas de conserver toutes les observations ayant contribué à la détection.

## M91 — La mutabilité de l'état d'analyse est locale, contrôlée et appartient à son propriétaire

Un état analytique peut être mutable lorsqu'une mise à jour incrémentale le justifie.

Ses modifications passent par les opérations définies par son composant responsable.

Les autres composants ne reçoivent pas une référence mutable permettant de le modifier silencieusement.

Pour le premier incrément, un traitement séquentiel avec propriétaire unique suffit sans mécanisme complexe de concurrence.

## M92 — L'état analytique est séparé des observations qui l'alimentent

Les transitions d'analyse modifient l'état du composant concerné, jamais les observations admises.

Une observation n'est pas modifiée pour mémoriser :

- l'avancement d'une analyse ;
- un compteur ;
- une annotation temporaire ;
- un résultat intermédiaire propre à un détecteur.

Les observations restent immuables.

Toute information dérivée appartient à l'état analytique ou à une nouvelle représentation explicitement définie.

## M93 — Les états des détecteurs sont isolés par défaut

Un détecteur ne lit ou ne modifie pas directement l'état mutable interne d'un autre détecteur.

Lorsqu'un état analytique doit réellement être partagé, ce partage possède :

- un besoin démontré ;
- un propriétaire explicite ;
- un contrat défini ;
- des règles de mise à jour ;
- un cycle de vie connu.

Un cache mutable implicitement partagé n'est pas un contrat domaine.

## M94 — L'état d'analyse n'est pas persistant par défaut

Un état temporaire utilisé pour une analyse en cours peut rester exclusivement en mémoire.

La persistance des alertes, observations historiques ou autres résultats ne signifie pas que fenêtres, cooldowns ou autres états internes sont automatiquement persistés.

La persistance d'un état analytique n'est introduite que lorsqu'une exigence explicite le justifie.

Pour le premier incrément, l'absence de persistance de ces états constitue un choix documenté.

## M95 — La continuité d'un état d'analyse à travers un redémarrage n'est jamais supposée implicitement

Lorsqu'un état n'est pas restauré, une nouvelle exécution commence avec l'état initial défini par son contrat.

Cette réinitialisation peut :

- entraîner une période disposant de moins d'historique ;
- permettre qu'une activité déjà signalée produise ultérieurement un nouveau résultat.

Ces limites sont documentées.

Si une future capacité exige une restauration, les éléments suivants sont explicitement définis :

- format de l'état ;
- version ;
- compatibilité avec la configuration ;
- garanties de reprise.

## M96 — Les transitions et choix de suppression d'état sont déterministes relativement à leurs entrées contrôlées

L'évolution de l'état dépend :

- des observations admises ;
- de leur ordre lorsque pertinent ;
- de la configuration ;
- de l'état initial ;
- des signaux explicites nécessaires à la politique.

À entrées contrôlées équivalentes, transitions, expirations et décisions d'éviction produisent un état sémantiquement équivalent.

Lorsque plusieurs états peuvent être supprimés ou traités, les critères de sélection et de départage sont explicites lorsqu'ils peuvent influencer l'analyse.

Les décisions ne dépendent pas silencieusement :

- de l'heure système ;
- d'un ordre d'itération arbitraire ;
- d'un identifiant aléatoire ;
- d'un accès réseau ;
- d'un état global caché

lorsque ces éléments ne font pas partie du contrat.

## M97 — Un changement de configuration affectant la sémantique de l'état possède une politique explicite

Lorsqu'une modification change la manière dont un état est :

- regroupé ;
- construit ;
- interprété ;
- expiré ;
- évalué,

l'état existant n'est pas silencieusement réinterprété.

La politique peut notamment imposer :

- une réinitialisation ;
- une migration explicite ;
- le maintien temporaire de l'ancienne configuration jusqu'à finalisation.

Modifier une fenêtre temporelle, une clé de regroupement ou une propriété structurelle ne garantit pas la compatibilité de l'état existant.

Pour le premier incrément, la configuration peut rester fixe pendant une exécution.

Cette règle n'impose pas le rechargement à chaud.

## M98 — Network State désigne une responsabilité architecturale, pas un agrégat universel obligatoire

Les états nécessaires aux `Flow`, détecteurs, fenêtres temporelles ou futures corrélations peuvent être représentés par des composants spécialisés.

La première règle de détection peut posséder son propre état borné sans nécessiter un registre global :

- d'hôtes ;
- de `Flow` ;
- de sessions ;
- de comportements.

Un composant commun n'est introduit que lorsque plusieurs usages justifient réellement son existence et qu'une sémantique commune peut être définie.

NetGuard évite la création prématurée d'un objet global mutable représentant supposément « l'état du réseau ».

---

## 8.1 Fiche de conception d'un état analytique

Chaque état analytique concret documente :

- **Propriétaire** — composant autorisé à modifier l'état.
- **Regroupement** — clé éventuelle et dimensions incluses/exclues.
- **Contenu** — informations conservées et justification.
- **Temps** — référence temporelle, rétention, expiration.
- **Capacité** — limites globales et internes.
- **Saturation** — rejet, éviction ou autre politique et critères.
- **Transitions** — entrées pouvant modifier l'état et opérations autorisées.
- **Preuves** — informations matérialisées avant disparition ou modification de l'état.
- **Continuité** — arrêt, redémarrage et changement éventuel de configuration.
- **Observabilité** — compteurs, diagnostics et indications de dégradation.

Pour le premier incrément, chaque détecteur peut posséder un état local, borné, en mémoire et contrôlé par un propriétaire unique.

Aucun registre global d'hôtes, système universel de `Network State`, persistance générale des états, rechargement à chaud ou mécanisme distribué n'est requis.

---

# 9. Contrat des détecteurs

## M99 — Un détecteur est un composant d'analyse du domaine

Un détecteur évalue des observations selon une règle analytique explicitement définie.

Il peut utiliser une configuration et un état analytique lorsque sa logique l'exige.

Son rôle est de produire des résultats d'analyse.

Il ne :

- capture pas le trafic ;
- persiste pas directement les résultats ;
- publie pas d'API ;
- réalise pas d'action de réponse réseau.

## M100 — Chaque détecteur définit explicitement les types d'entrée qu'il accepte

Un détecteur déclare les catégories d'observations ou représentations analytiques qu'il sait interpréter.

L'existence d'un type dans le Core ne rend pas automatiquement tous les détecteurs compatibles avec ce type.

Un détecteur conçu pour `PacketObservation` ne reçoit pas artificiellement une `FlowObservation` transformée en pseudo-paquets, et inversement.

## M101 — Compatibilité de type et éligibilité analytique sont distinctes

Une observation appartenant à un type accepté peut ne pas contenir les informations nécessaires à une règle particulière.

Chaque détecteur définit ses conditions d'éligibilité à partir des faits effectivement disponibles.

Une observation valide mais non éligible n'est pas considérée comme invalide pour le Core.

## M102 — Une observation non éligible constitue une situation normale du filtrage analytique

Le fait qu'une observation ne corresponde pas aux conditions d'éligibilité d'une règle ne constitue pas en soi une erreur.

Le détecteur peut l'ignorer sans produire de résultat analytique individuel.

Cette situation n'impose pas la création d'un objet résultat pour chaque observation ignorée.

L'observabilité peut fournir des compteurs agrégés lorsque cela est utile sans journaliser systématiquement chaque non-éligibilité.

## M103 — Les préconditions analytiques d'un détecteur sont explicites

Toute information nécessaire à l'application correcte d'une règle est documentée et vérifiée.

Le détecteur ne suppose pas silencieusement :

- qu'un champ absent est disponible ;
- qu'un protocole est connu ;
- qu'une capture est complète ;
- qu'une horloge est fiable ;
- qu'un rôle réseau a été établi.

Les hypothèses nécessaires à l'interprétation de la règle font partie de son contrat.

## M104 — Un détecteur ne fabrique pas les faits manquants nécessaires à sa règle

Lorsqu'une information requise n'est pas disponible avec les garanties nécessaires, le détecteur :

- considère l'observation non éligible ;
- ou applique une branche explicitement prévue par sa règle.

Il ne remplace pas une absence, incertitude ou information non observable par une valeur fictive permettant artificiellement l'analyse.

## M105 — Chaque détecteur possède une configuration explicitement définie et validée

Les paramètres influençant sa logique possèdent :

- une signification ;
- un type ;
- un domaine de valeurs ;
- des invariants définis.

Une configuration invalide est rejetée avant le début normal de l'analyse.

Le détecteur reçoit une configuration domaine validée.

Il ne lit pas directement :

- des variables d'environnement ;
- des fichiers de configuration bruts ;
- d'autres représentations techniques.

## M106 — Configuration analytique et configuration technique d'exécution sont distinctes

Les paramètres modifiant la signification ou le comportement métier d'une règle appartiennent à son contrat analytique.

Les paramètres concernant :

- threads ;
- transport ;
- stockage ;
- infrastructure ;
- autres mécanismes techniques

restent à leurs frontières respectives.

Un détecteur ne dépend pas d'une configuration infrastructure sans justification domaine explicite.

## M107 — Un détecteur ne possède un état analytique que lorsque sa règle l'exige

Un détecteur stateless ne reçoit pas artificiellement un mécanisme d'état générique.

Lorsqu'un détecteur est stateful, son état respecte M81 à M98 et possède notamment :

- un propriétaire ;
- une politique de regroupement éventuelle ;
- un bornage ;
- une politique temporelle ;
- une observabilité explicite.

## M108 — Le traitement d'une entrée peut produire zéro, un ou plusieurs résultats analytiques, dans des limites définies

Le contrat ne suppose pas qu'une observation produit exactement un résultat.

Une observation éligible peut simplement faire évoluer l'état sans produire immédiatement de résultat.

La cardinalité des résultats et leur taille respectent des limites définies.

Toute limitation susceptible de supprimer, tronquer ou empêcher la production de résultats qui auraient autrement été émis est explicite et observable.

La forme concrète de l'API peut être choisie lors de l'implémentation tant qu'elle préserve cette sémantique et ces garanties de bornage.

## M109 — Un résultat de détection est distinct d'une Alert

Un `DetectionResult` représente la conclusion métier d'une règle et les faits nécessaires à son interprétation.

Une `Alert` représente cette conclusion dans le cadre de son suivi et de sa consultation.

Elle peut notamment posséder :

- une identité ;
- un état de traitement ;
- d'autres informations propres à son cycle de vie.

La couche Application peut coordonner la transformation d'un résultat de détection en `Alert`.

Lorsque cette transformation implique des décisions métier, notamment :

- attribution de sévérité ;
- regroupement ;
- suppression ;
- autre politique influençant la signification du résultat,

ces décisions restent définies dans le domaine approprié et ne sont pas inventées par l'orchestration technique.

Cette séparation fixe les responsabilités.

Elle n'impose pas immédiatement deux modèles techniques presque identiques si l'implémentation initiale peut préserver clairement la frontière sémantique.

## M110 — Tout résultat de détection identifie sans ambiguïté la règle qui l'a produit

Une règle possède un identifiant logique stable, par exemple :

```text
NG-NET-001
```

Cet identifiant est distinct :

- d'un nom d'affichage ;
- du nom d'une classe ;
- d'un identifiant d'instance ;
- d'un texte localisé.

Le même identifiant n'est pas réattribué silencieusement à une règle dont la signification serait incompatible avec celle des résultats historiques.

## M111 — Une évolution sémantique d'une règle reste traçable

Lorsqu'une modification change suffisamment les critères, la signification ou l'interprétation d'une règle pour affecter la compréhension de ses résultats, NetGuard dispose d'un moyen d'identifier cette évolution.

Cette traçabilité peut être portée par :

- une version de règle ;
- une version de politique ;
- une version applicative ;
- un autre mécanisme explicitement défini.

Le résultat permet de retrouver la version sémantique pertinente à son interprétation.

Le premier incrément n'impose pas un système autonome complexe de versionnage des détecteurs.

## M112 — Tout résultat positif contient ou référence les faits et le contexte nécessaires pour expliquer pourquoi la règle a été satisfaite

Un résultat ne se limite pas à :

- un booléen ;
- un message libre.

Il expose sous forme structurée les éléments pertinents ayant conduit à la décision.

L'explication permet notamment d'identifier :

- la règle ;
- sa version sémantique pertinente ;
- les faits observés ;
- les paramètres nécessaires à la compréhension du déclenchement.

Un nombre de ports observés, par exemple, n'explique pas suffisamment un déclenchement si le seuil et la fenêtre appliqués ne peuvent pas être déterminés.

Il n'est pas nécessaire de recopier toute la configuration si une référence stable permet de retrouver le contexte pertinent.

Les éléments explicatifs sont :

- stables ;
- structurés ;
- bornés.

L'explication ne dépend pas de l'accès futur à l'état mutable du détecteur.

## M113 — Les résultats analytiques sont structurés indépendamment de leur présentation textuelle

Les informations nécessaires à l'interprétation sont représentées par des données structurées.

Un message destiné à l'utilisateur peut être généré à partir de ces données mais n'en constitue pas l'unique représentation.

La logique applicative, la persistance et les traitements ultérieurs ne dépendent pas du parsing d'un texte de présentation.

Les preuves et informations structurées nécessaires restent immuables et bornées selon leur contrat.

## M114 — Un détecteur est déterministe relativement à ses entrées contrôlées

À observations admises, ordre pertinent, configuration, état initial et signaux de progression équivalents, un détecteur produit des décisions et transitions d'état sémantiquement équivalentes.

Les différences accidentelles :

- d'heure système ;
- d'identifiant aléatoire ;
- de stockage ;
- de vitesse d'exécution ;
- d'autres éléments extérieurs

ne modifient pas sa décision lorsqu'elles ne font pas partie de son contrat.

Les identifiants techniques attribués ensuite aux `Alert` ne font pas partie de cette équivalence analytique.

## M115 — L'évaluation d'un détecteur ne réalise pas d'entrée/sortie technique cachée

Les informations nécessaires à une décision sont fournies par ses entrées et contrats explicites.

Le détecteur n'interroge pas directement pendant son évaluation métier :

- une base de données ;
- le réseau ;
- un fichier ;
- une API externe ;
- une bibliothèque de capture.

Si un futur détecteur nécessite un enrichissement externe, celui-ci est modélisé explicitement à une frontière appropriée.

## M116 — Un détecteur ne décide pas directement du stockage ou de la publication de ses résultats

Le détecteur remet ses résultats au mécanisme d'orchestration prévu.

Il ne :

- persiste pas directement une `Alert` ;
- l'envoie pas au frontend ;
- déclenche pas lui-même une notification externe.

La réussite ou l'échec d'une infrastructure de sortie ne modifie pas rétroactivement la décision analytique déjà produite.

Les décisions métier intervenant entre `DetectionResult` et `Alert` restent définies dans le domaine approprié même lorsque leur exécution est orchestrée par l'Application.

## M117 — Non-éligibilité, évaluation sans déclenchement et erreur de détecteur sont des situations distinctes

Une observation peut être non éligible parce qu'elle ne satisfait pas les préconditions de la règle.

Une observation éligible peut être traitée sans produire de résultat positif.

Elle peut notamment enrichir un état analytique en vue d'évaluations futures.

Cette absence de déclenchement ne signifie pas nécessairement que le comportement est :

- normal ;
- bénin ;
- définitivement non suspect.

Une erreur correspond à un échec empêchant tout ou partie d'une analyse normalement attendue.

Une exception, violation d'invariant ou état incohérent n'est pas silencieusement transformé en absence de détection.

L'observabilité permet d'identifier qu'une partie de l'analyse n'a pas été réalisée correctement.

## M118 — Une défaillance de détecteur est identifiable et traitée selon une politique explicite du moteur

Le moteur permet d'identifier :

- quel détecteur a échoué ;
- quelles analyses peuvent avoir été affectées.

La poursuite dépend des garanties d'intégrité encore disponibles.

Intercepter une exception ne garantit pas que l'état du détecteur reste exploitable.

Une transition peut avoir été partiellement effectuée avant l'échec.

Selon le contrat et la nature de la défaillance, la politique peut notamment prévoir :

- une réinitialisation ;
- la désactivation du détecteur ;
- la poursuite lorsque l'intégrité est suffisamment garantie ;
- un arrêt contrôlé.

Une défaillance n'est pas présentée comme une absence de détection de ce détecteur ou comme une décision des autres détecteurs.

Cette règle n'impose pas un mécanisme transactionnel générique à tous les détecteurs.

## M119 — L'Application pilote le cycle de vie du moteur ; le moteur pilote les interactions analytiques avec les détecteurs

L'Application orchestre :

- le démarrage ;
- l'arrêt ;
- le fonctionnement général du `Detection Engine`.

Le moteur transmet aux détecteurs :

- les observations ;
- les signaux explicites de progression ;
- les signaux de finalisation ;
- les réinitialisations ;
- les autres événements analytiques prévus par leur contrat.

Les détecteurs restent responsables de leurs transitions métier et de l'intégrité de leur état.

Un détecteur ne lance pas implicitement son propre :

- thread ;
- timer ;
- ordonnanceur ;
- boucle autonome ;
- mécanisme de capture

pour faire évoluer son état métier.

Cette organisation permet au moteur de contrôler :

- l'ordre ;
- les interactions ;
- les erreurs ;
- les signaux temporels

sans déplacer la logique analytique propre aux détecteurs.

Elle n'interdit pas une future exécution concurrente.

Elle interdit que cette concurrence devienne une dépendance cachée de la sémantique d'une règle.

### Portée du premier incrément

Le contrat initial des détecteurs reste simple :

- configuration domaine validée ;
- types d'entrée clairement définis ;
- conditions d'éligibilité explicites ;
- traitement séquentiel ;
- état local et borné uniquement lorsque nécessaire ;
- résultats structurés, explicables et bornés ;
- interactions pilotées par le `Detection Engine`.

Aucun système de plugins dynamiques, bus de communication entre détecteurs, ordonnanceur propre à chaque détecteur, mécanisme transactionnel générique ou infrastructure distribuée n'est requis.

La distinction de référence est :

```text
Observation
    ↓
Detector
    ↓
DetectionResult
    ↓
conversion / orchestration
    ↓
Alert
```

`DetectionResult` représente la conclusion métier de la règle.

`Alert` représente cette conclusion dans le cadre de son suivi et de sa consultation.

---

# 10. Alert et Evidence

## M120 — Alert représente un résultat de sécurité destiné au suivi et à la consultation

Une `Alert` expose une conclusion issue de l'analyse et les informations nécessaires à son suivi.

Elle ne constitue pas une observation réseau supplémentaire.

Elle provient d'un `DetectionResult` ou d'une transformation métier explicitement définie.

Sa création ne signifie pas automatiquement qu'un incident est confirmé.

## M121 — Une Alert stabilisée est interprétable indépendamment de l'état analytique courant

Son interprétation repose sur des informations conservées avec elle ou sur des références stables et accessibles selon une politique définie.

Elle ne dépend pas d'une fenêtre, d'un compteur ou d'une configuration mutable qui pourrait évoluer après sa production.

## M122 — L'identité d'une Alert est distincte des identités de règle et de comportement

L'identifiant d'alerte désigne un objet de suivi.

L'identifiant de règle désigne la logique analytique.

Une clé de regroupement ne prouve pas que deux alertes concernent une même activité réelle.

Déduplication, regroupement et corrélation reposent sur des politiques distinctes.

## M123 — Chaque temps d'une Alert possède une signification explicite

Les temps :

- des faits observés ;
- de la décision ;
- de la création ;
- des modifications de suivi

restent distinguables lorsqu'ils sont représentés.

Des champs tels que `first_seen` et `last_seen` précisent quelles observations ou quels résultats ils couvrent.

Ils ne sont pas automatiquement les bornes réelles de la communication.

## M124 — Le temps de création ne remplace pas celui des faits justificatifs

Une détection tardive ou une analyse PCAP peut produire aujourd'hui une alerte portant sur des observations anciennes.

L'affichage et les traitements ultérieurs préservent cette différence.

## M125 — Evidence représente les éléments structurés soutenant une conclusion analytique

Une `Evidence` décrit :

- les faits observés ;
- les agrégats calculés ;
- les paramètres pertinents

permettant de comprendre le déclenchement.

Ces catégories restent distinguables.

Une valeur calculée n'est pas présentée comme directement observée.

Le terme `Evidence` ne signifie pas :

- preuve certaine d'une attaque ;
- authenticité absolue ;
- causalité certaine ;
- valeur probatoire externe au système.

## M126 — Evidence ne renforce pas les garanties des observations sources

Une agrégation ne :

- rend pas authentique une adresse source ;
- complète pas une capture partielle ;
- transforme pas un nombre d'observations en nombre de paquets uniques.

Les limites connues pertinentes pour la conclusion sont conservées.

Leur absence de représentation ne doit pas suggérer une garantie que NetGuard ne possède pas.

## M127 — Evidence est structurée indépendamment de son rendu humain

La logique de suivi, la persistance et les traitements ultérieurs ne dépendent pas du parsing d'une description textuelle.

Le texte présenté à l'utilisateur reste cohérent avec les données structurées et leurs limites.

## M128 — Evidence est adaptée à la règle

Chaque règle définit les éléments nécessaires pour justifier sa conclusion, leur signification et leurs invariants.

Un socle commun est possible.

Aucun modèle universel rempli de champs facultatifs n'est imposé à toutes les règles.

NetGuard n'impose pas que toute `Evidence` contienne les observations brutes ayant contribué à la détection.

## M129 — Les Evidence sont bornées en nombre et en taille

Les limites couvrent :

- les collections ;
- les chaînes ;
- les structures imbriquées ;
- les autres contenus susceptibles de croître.

Une limitation ne doit pas produire une justification trompeuse.

Si les éléments indispensables à l'explication ne peuvent pas être représentés, le contrat prévoit un comportement explicite plutôt qu'une troncature silencieuse.

## M130 — Les résumés distinguent les quantités calculées des éléments présentés

Par exemple :

```text
24 ports distincts comptés
10 ports présentés
```

ne signifie ni que les 10 ports constituent la liste complète ni que seulement 24 observations ont été reçues.

Les comptes précisent lorsque nécessaire :

- leur périmètre ;
- leur caractère exact ou estimé ;
- leur méthode.

La sélection d'un échantillon suit une politique définie.

## M131 — La provenance conservée est suffisante et bornée

Les références permettent de comprendre l'origine des éléments justificatifs et les transformations pertinentes.

Conserver la traçabilité n'impose pas une liste illimitée de chaque observation contributrice.

Les limites de traçabilité sont explicites.

La provenance des `Evidence` respecte les règles M73 à M80.

## M132 — Les Evidence stabilisées sont immuables

Leur contenu, y compris les objets imbriqués, ne change pas silencieusement après production.

Une correction ou un complément produit une évolution traçable conformément à M139.

## M133 — La sévérité possède une signification métier définie

Elle exprime une importance ou priorité selon une politique documentée.

Son attribution reste explicable par la règle et les éléments de contexte effectivement disponibles.

Une valeur telle que :

```text
high
```

ne prouve pas à elle seule :

- un impact élevé ;
- une compromission.

Les niveaux concrets ne sont introduits que lorsqu'un besoin fonctionnel les justifie.

## M134 — Sévérité et confiance sont distinctes

La sévérité ne mesure pas automatiquement la certitude de la conclusion.

Si NetGuard introduit une notion de confiance, il précise :

- ce qu'elle évalue ;
- comment elle est établie.

Un score numérique n'est pas présenté comme une probabilité sans justification.

Aucun score de confiance n'est obligatoire pour le premier incrément.

## M135 — Une Alert ne prétend pas davantage que sa règle et ses observations ne permettent d'établir

Elle distingue le comportement observé de l'interprétation proposée.

Elle n'attribue pas automatiquement :

- une intention malveillante ;
- une identité physique ;
- une compromission ;
- une attaque réussie.

Exemple de formulation appropriée :

> Comportement compatible avec un scan de ports : le seuil configuré de ports de destination distincts a été atteint dans la fenêtre analysée.

Cela n'autorise pas à affirmer :

> Cette machine a attaqué et compromis la destination.

## M136 — L'état de suivi est distinct des faits analytiques

Les statuts tels que :

- ouvert ;
- en cours ;
- clôturé

décrivent le traitement de l'alerte.

Clôturer une alerte ne modifie pas ses observations justificatives et ne signifie pas nécessairement que l'activité réseau a cessé.

Une qualification humaine telle que « faux positif » reste identifiable comme une évaluation distincte.

Le premier incrément n'a pas besoin d'introduire un workflow complexe de traitement.

## M137 — Regroupement, suppression et répétition suivent des politiques métier explicites

Les critères, fenêtres et effets sur compteurs, preuves et notifications sont définis.

NetGuard distingue :

```text
absence de nouvelle détection
≠
suppression de création d'une Alert
≠
suppression d'une notification
```

Un résultat supprimé par politique n'est pas présenté comme une absence d'activité.

Deux `DetectionResult` similaires ne sont pas automatiquement considérés comme une même alerte.

Pour le premier incrément, une politique simple telle que :

```text
1 DetectionResult → 1 Alert
```

peut être retenue et le regroupement différé.

## M138 — Une Alert historique conserve son contexte d'interprétation

Elle permet de retrouver :

- la règle ;
- sa version sémantique ;
- les paramètres pertinents ;
- les bornes d'observation ;
- les preuves ;
- les limitations nécessaires à sa compréhension.

L'interprétation historique ne dépend pas silencieusement de la configuration ou des libellés actuels.

## M139 — Les corrections sont explicites et traçables

Une correction précise :

- ce qui change ;
- pourquoi ;
- lorsque pertinent, par quel acteur ou traitement.

Une nouvelle version, une relation de remplacement ou un historique adapté peut assurer cette garantie.

Aucun mécanisme complexe d'event sourcing n'est requis.

Une modification de suivi n'est pas confondue avec une correction des faits analytiques.

Le premier incrément peut choisir de ne pas supporter la correction d'alertes stabilisées.

## M140 — Alert et Evidence suivent une politique de minimisation et de rétention

NetGuard conserve les informations nécessaires à l'explication et au suivi sans accumuler automatiquement :

- payloads ;
- observations complètes.

Les durées de conservation et dépendances entre alerte, preuves et références sont définies.

Une preuve externe supprimée ne reste pas présentée comme consultable.

Son indisponibilité et ses conséquences sont explicites.

---

# 11. Relation entre DetectionResult, Evidence et Alert

La sémantique de référence est :

```text
Detector
   │
   ▼
DetectionResult
   │
   ├── conclusion métier
   ├── contexte de règle
   └── Evidence stable
           │
           │ transférée / conservée
           ▼
         Alert
           │
           ├── identité de suivi
           ├── contexte historique
           └── Evidence stable
```

La preuve nécessaire à l'explication est matérialisée au moment de la conclusion analytique.

L'`Alert` conserve la représentation nécessaire à l'interprétation historique de cette conclusion.

Cette relation ne signifie pas nécessairement que `DetectionResult` et `Alert` utilisent exactement le même objet Python.

Elle interdit en revanche qu'une couche technique réinterprète silencieusement les observations pour produire une preuve différente.

---

# 12. Informations minimales d'une Alert du premier incrément

Une alerte du premier incrément doit permettre de répondre aux questions suivantes :

1. Quelle règle a conclu ?
2. Quelle version sémantique de cette règle est pertinente ?
3. Sur quels sujets et dans quel périmètre réseau ?
4. Pendant quelle période observée ?
5. Quels faits ont été directement observés ?
6. Quels agrégats ont été calculés ?
7. Quels paramètres ont permis de satisfaire la règle ?
8. Quelles limitations connues affectent la conclusion ?
9. Quelle sévérité a été attribuée ?
10. Quel est l'état de suivi de l'alerte, lorsqu'un tel suivi existe ?

Conformément à [FR-010](requirements/functional.md), une Alert du premier incrément comporte une sévérité. Son attribution suit une politique métier selon M133 ; elle ne constitue ni une confiance implicite ni une preuve d'attaque confirmée, conformément à M134 et M135.

Cela suffit à produire des alertes explicables sans imposer :

- la conservation de tous les paquets ;
- la conservation du payload brut ;
- un score générique de confiance ;
- une attribution d'intention malveillante ;
- un workflow complet de gestion d'incidents ;
- un système d'event sourcing ;
- une corrélation universelle des alertes.

---

# 13. Invariants transversaux du modèle

L'ensemble des règles M1 à M140 repose sur les invariants transversaux suivants.

## 13.1 Fait et interprétation

```text
réalité réseau
≠
ce que NetGuard observe
≠
ce que NetGuard calcule
≠
ce que la règle conclut
≠
la manière dont l'alerte est suivie
```

NetGuard ne renforce jamais silencieusement une garantie lors du passage d'un niveau au suivant.

## 13.2 Granularité

Les différents niveaux de granularité restent distincts.

```text
PacketObservation
≠
FlowObservation
≠
Flow
≠
état analytique
```

Une représentation agrégée ne recrée pas artificiellement les observations élémentaires absentes.

## 13.3 Identité réseau

Une adresse ou une clé de communication ne devient pas automatiquement une identité durable :

- de machine ;
- de communication ;
- de comportement.

Les contextes nécessaires restent explicites.

## 13.4 Temps

```text
observation time
≠
processing time
≠
maintenance time
```

Les décisions temporelles utilisent la notion de temps appropriée à leur sémantique.

## 13.5 Provenance

La provenance permet de comprendre l'origine d'une information.

Elle ne constitue pas à elle seule une garantie :

- de confiance ;
- d'authenticité ;
- d'intégrité ;
- d'exactitude.

## 13.6 État

Les états analytiques sont :

- spécialisés ;
- possédés par un composant explicite ;
- bornés ;
- contrôlés ;
- observables en cas de dégradation ;
- non persistants par défaut.

## 13.7 Détection

Les détecteurs restent indépendants de l'infrastructure.

Ils ne :

- capturent pas ;
- persistent pas ;
- publient pas directement leurs résultats.

## 13.8 Résultat analytique

Une absence de déclenchement n'est pas une preuve de normalité.

Une erreur n'est pas une absence de détection.

Une observation non éligible n'est pas une observation invalide.

## 13.9 Reproductibilité

À entrées contrôlées sémantiquement équivalentes, l'analyse produit des décisions sémantiquement équivalentes.

Les entrées contrôlées peuvent notamment inclure :

```text
observations
+
ordre pertinent
+
configuration analytique
+
état initial
+
signaux de progression temporelle
+
versions des politiques applicables
```

Les identifiants techniques, timestamps de traitement ou détails d'infrastructure ne font pas partie de cette équivalence lorsqu'ils n'influencent pas la sémantique.

## 13.10 Bornage

Les structures susceptibles de croître sont bornées :

- buffers du pipeline ;
- états de `Flow` ;
- états des détecteurs ;
- collections internes ;
- résultats ;
- `Evidence` ;
- provenance ;
- observabilité.

Une limite globale ne suffit pas si une structure interne peut elle-même croître sans borne.

## 13.11 Explicabilité

Les décisions positives sont expliquées par des informations :

- structurées ;
- stables ;
- bornées.

Une alerte historique reste interprétable sans dépendre de l'état mutable courant.

## 13.12 Portée de la V1

Le modèle définit davantage de distinctions que la première implémentation n'en matérialisera.

Cette différence est volontaire.

Définir une frontière sémantique ne signifie pas devoir immédiatement créer une classe, un service ou une infrastructure correspondante.

---

# 14. Portée d'implémentation initiale

Le premier incrément peut rester volontairement limité.

Il peut notamment implémenter dans le Core :

```text
network/
    valeurs IP nécessaires
    contexte réseau minimal
    provenance minimale
    PacketObservation
    métadonnées TCP nécessaires

detection/
    contrat Detector
    DetectionResult
    Evidence
    NG-NET-001
    état borné propre à NG-NET-001

alerts/
    Alert
```

L'Application peut fournir :

```text
DetectionEngine
orchestration des cas d'utilisation
cycle de vie
transformation DetectionResult → Alert
```

L'Infrastructure peut fournir :

```text
capture live
lecture PCAP
adaptateurs de normalisation
persistance
observabilité technique
```

Les Interfaces peuvent fournir :

```text
API
CLI
frontend
```

Le premier incrément n'exige notamment pas :

- une implémentation concrète de `FlowObservation` sans source réelle qui la nécessite ;
- une synchronisation temporelle multi-capteurs ;
- un registre générique global de `Host` ;
- un gestionnaire universel de conversations ;
- un état distribué ;
- des plugins dynamiques de détecteurs ;
- un bus de communication entre détecteurs ;
- le hot reload de configuration ;
- la persistance générale des états analytiques ;
- la migration des états ;
- un score générique de confiance ;
- un regroupement complexe des alertes ;
- un système complet de gestion d'incidents ;
- de l'event sourcing ;
- une hiérarchie universelle complexe d'`Evidence` ;
- un moteur générique de provenance ;
- un framework complexe de watermarking temporel.

---

# 15. Validation du modèle avec NG-NET-001

Le premier détecteur doit pouvoir être construit selon le chemin suivant :

```text
PacketObservation
       │
       ▼
vérification d'éligibilité
       │
       ▼
NG-NET-001
       │
       ├── configuration validée
       │
       └── état local borné
                │
                ▼
       condition satisfaite
                │
                ▼
        DetectionResult
                │
                └── Evidence stable et bornée
                         │
                         ▼
                       Alert
```

Le contrat détaillé de `NG-NET-001` devra notamment définir :

- son identifiant de règle ;
- sa version sémantique ;
- les types d'entrée acceptés ;
- ses conditions d'éligibilité ;
- sa clé de regroupement ;
- son sujet analytique ;
- ses paramètres ;
- sa référence temporelle ;
- sa fenêtre ;
- son seuil ;
- son état ;
- ses limites de capacité ;
- sa politique d'expiration ;
- sa politique d'éviction ;
- sa condition exacte de détection ;
- sa politique d'émission ;
- son éventuel réarmement ou cooldown ;
- les `Evidence` produites ;
- les limitations connues ;
- son comportement lors d'un replay ;
- ses garanties de déterminisme ;
- son observabilité.

La conception détaillée de `NG-NET-001` constitue une étape ultérieure.

Elle ne doit pas nécessiter l'invention d'un nouveau concept architectural fondamental absent du présent modèle.

---

# 16. Validation transversale

La validation de l'ensemble du modèle confirme les propriétés suivantes.

## 16.1 Les faits sont séparés des interprétations

La normalisation établit ce que NetGuard peut représenter honnêtement à partir d'une entrée.

Les détecteurs interprètent ensuite ces faits selon leurs règles.

Les alertes représentent les conclusions produites sans devenir de nouvelles observations réseau.

## 16.2 Les niveaux de granularité restent distincts

`PacketObservation`, `FlowObservation`, `Flow` et état analytique ne sont pas assimilés.

Une abstraction n'est introduite dans un chemin de traitement que lorsqu'elle apporte une valeur réelle.

## 16.3 L'identité réseau n'est pas renforcée artificiellement

Une adresse n'est pas automatiquement un hôte.

Une clé réseau n'est pas automatiquement une session.

Une canonicalisation ne crée pas un rôle réseau.

Une agrégation ne crée pas une identité plus forte que ses observations sources.

## 16.4 Le temps possède une sémantique explicite

Temps métier, temps de traitement et temps de maintenance restent distincts.

Le replay conserve la sémantique temporelle des observations.

Les décisions temporelles susceptibles d'influencer l'analyse restent contrôlables.

## 16.5 La provenance reste distincte du contexte réseau et de la confiance

La provenance décrit l'origine d'une information.

Le `network_scope` décrit le contexte dans lequel les identifiants réseau sont interprétés.

Aucun des deux ne prouve automatiquement la confiance ou l'authenticité.

## 16.6 Les états analytiques restent spécialisés

Un détecteur peut posséder son propre état local.

Aucun registre universel n'est nécessaire pour permettre le fonctionnement du premier détecteur.

## 16.7 Les détecteurs restent indépendants de l'infrastructure

Un détecteur peut être testé avec :

```text
observations
+
configuration
+
état initial
+
signaux de progression
```

sans :

```text
capture réelle
base de données
serveur HTTP
frontend
réseau externe
```

## 16.8 Les erreurs restent distinguables des décisions analytiques

Le modèle distingue notamment :

```text
unsupported
≠
rejected
≠
non-eligible
≠
evaluated without trigger
≠
normal expiration
≠
resource eviction
≠
detector failure
≠
infrastructure failure
```

Ces situations ne sont pas toutes transformées en « rien de suspect détecté ».

## 16.9 Les décisions sont reproductibles relativement à leurs entrées contrôlées

La reproductibilité porte sur la sémantique analytique.

Elle ne nécessite pas l'égalité des identifiants ou métadonnées purement techniques.

## 16.10 Les résultats restent explicables

Un résultat positif possède suffisamment d'informations structurées pour comprendre :

- quelle règle a conclu ;
- sur quels faits ;
- avec quels paramètres ;
- pendant quelle période ;
- sous quelles limitations.

## 16.11 Une Alert ne prétend pas davantage que la règle ne permet d'établir

Une détection de comportement compatible avec un scan n'est pas automatiquement une preuve :

- d'intention malveillante ;
- d'identité de l'attaquant ;
- d'attaque réussie ;
- de compromission.

## 16.12 Les objets historiques restent interprétables

Une alerte stabilisée ne dépend pas d'un état analytique mutable ou de la configuration actuelle pour être comprise.

## 16.13 La V1 peut rester simple

Les contrats du modèle permettent une évolution future sans imposer prématurément :

- microservices ;
- plugins dynamiques ;
- état distribué ;
- corrélation universelle ;
- moteur générique de fenêtres ;
- persistance de tous les états ;
- système complexe d'incidents.

---

