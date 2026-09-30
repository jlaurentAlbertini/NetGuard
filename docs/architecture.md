# NetGuard — Architecture système

## 1. Objectif

Ce document définit l'architecture système de NetGuard.

Il décrit :

- les responsabilités des principaux composants ;
- les frontières entre domaine, orchestration, infrastructure et interfaces ;
- le sens des dépendances ;
- le pipeline de traitement ;
- les règles architecturales nécessaires à la testabilité, la reproductibilité, la robustesse et l'extensibilité du système.

Les modèles de domaine détaillés et leurs invariants sont définis dans [`data-models.md`](./data-models.md).

Les décisions architecturales importantes et leur justification sont documentées dans [`decisions/`](./decisions/).

---

## 2. Principe général

NetGuard est une application défensive de surveillance réseau.

Son rôle est de transformer des observations réseau en informations structurées, puis d'appliquer des règles analytiques capables de produire des résultats de détection explicables.

Le pipeline conceptuel principal est :

```text
Network traffic
      ↓
Capture / Ingestion
      ↓
Normalization
      ↓
NetworkObservation
      ↓
Network State / Aggregation
      ↓
Detection Engine
      ↓
DetectionResult
      ↓
Alerting
      ↓
Alert
     /   \
    ↓     ↓
Persistence
          Presentation
```

Ce pipeline représente des responsabilités conceptuelles.

Il ne signifie pas que chaque étape doit correspondre à un processus, un service réseau, un thread ou une file de messages distincte.

---

## 3. Style architectural

NetGuard adopte initialement une architecture de **monolithe modulaire**.

Le système est organisé en modules aux responsabilités explicites tout en restant déployable comme une seule application.

Cette approche permet :

- de conserver des frontières internes fortes ;
- de tester le domaine indépendamment de l'infrastructure ;
- de limiter la complexité opérationnelle ;
- de faire évoluer certains composants ultérieurement sans introduire prématurément une architecture distribuée.

NetGuard n'utilise pas de microservices pour le premier incrément.

Cette décision est détaillée dans :

[`ADR-001 — Modular Monolith`](./decisions/ADR-001-Modular-Monolith.md)

---

# 4. Couches conceptuelles

L'architecture distingue quatre couches principales :

```text
NetGuard
├── Core
├── Application
├── Infrastructure
└── Interfaces
```

Ces couches représentent des responsabilités et des règles de dépendance.

Elles ne nécessitent pas nécessairement une correspondance exacte avec quatre répertoires uniques.

---

# 5. Core

Le `Core` contient les concepts et règles métier de NetGuard.

Il définit notamment :

- les observations réseau normalisées ;
- les objets valeur réseau ;
- les règles d'identité et de contexte réseau ;
- les modèles temporels nécessaires au domaine ;
- les concepts de provenance nécessaires à l'analyse ;
- les agrégats réseau lorsqu'ils sont utiles ;
- les états analytiques ;
- les contrats des détecteurs ;
- les règles de détection ;
- les résultats de détection ;
- les preuves structurées ;
- la sémantique des alertes ;
- les politiques métier nécessaires à leur interprétation.

Le Core ne dépend pas directement :

- d'une bibliothèque de capture ;
- d'un format PCAP particulier ;
- d'un framework HTTP ;
- d'un ORM ;
- d'une base de données ;
- d'une interface graphique ;
- d'un système de notification ;
- d'un fichier de configuration brut ;
- de variables d'environnement.

Le Core reçoit des valeurs déjà normalisées et validées selon ses contrats.

Les modèles du Core sont décrits dans :

[`data-models.md`](./data-models.md)

---

# 6. Application

La couche `Application` orchestre les cas d'utilisation de NetGuard.

Elle coordonne notamment :

- le démarrage et l'arrêt des traitements ;
- le cycle de vie du Detection Engine ;
- la réception des observations normalisées ;
- leur transmission aux composants analytiques appropriés ;
- la coordination de la transformation des résultats de détection en alertes ;
- l'appel des contrats de persistance ;
- l'exposition des résultats aux interfaces ;
- les politiques opérationnelles définies au niveau applicatif.

L'Application ne contient pas les algorithmes propres aux détecteurs.

Elle ne décide pas arbitrairement de la signification métier d'une détection.

Lorsqu'une transformation entre `DetectionResult` et `Alert` implique une décision métier, cette décision reste définie dans le domaine approprié même si son exécution est orchestrée par l'Application.

---

# 7. Infrastructure

La couche `Infrastructure` contient les implémentations dépendant de technologies externes.

Elle peut notamment contenir :

- les adaptateurs de capture live ;
- les lecteurs PCAP ;
- les adaptateurs de normalisation depuis les bibliothèques externes ;
- les repositories ;
- les mappings de persistance ;
- les implémentations de base de données ;
- les mécanismes de transport ;
- les intégrations d'observabilité ;
- les implémentations concrètes de contrats exprimés par les couches internes.

Les objets techniques externes sont traduits aux frontières.

Un objet fourni par une bibliothèque de capture ne traverse pas directement jusqu'aux détecteurs.

De même, un modèle ORM n'est pas le modèle canonique du domaine.

---

# 8. Interfaces

La couche `Interfaces` expose les interactions avec l'utilisateur ou d'autres consommateurs du système.

Elle peut notamment contenir :

- une API HTTP ;
- une CLI ;
- les contrats nécessaires au frontend ;
- les contrôleurs ou adaptateurs d'entrée.

Les interfaces traduisent les interactions externes vers les cas d'utilisation de l'Application.

Elles ne contiennent pas les algorithmes de détection.

Une interface ne décide pas arbitrairement qu'un comportement réseau est suspect et ne modifie pas la signification métier d'une alerte.

---

# 9. Direction des dépendances

Les dépendances de code doivent pointer vers les couches les plus internes.

La direction conceptuelle est :

```text
                Core
                 ▲
                 │
             Application
                 ▲
                 │
       ┌─────────┴─────────┐
       │                   │
Infrastructure         Interfaces
```

Le Core ne connaît pas l'Infrastructure ou les Interfaces.

L'Application dépend des contrats nécessaires à l'exécution de ses cas d'utilisation.

L'Infrastructure fournit des implémentations de contrats exprimés par les couches qui en ont besoin.

Les Interfaces utilisent l'Application pour déclencher ou consulter les cas d'utilisation.

Cette règle est détaillée dans :

[`ADR-003 — Inward Dependencies`](./decisions/ADR-003-inward-dependencies.md)

---

# 10. Propriété des contrats

Un contrat appartient conceptuellement à la couche qui exprime le besoin.

Par exemple, si l'Application a besoin de persister une `Alert`, elle dépend d'un contrat correspondant à ce besoin.

Une implémentation concrète de repository appartient à l'Infrastructure.

Conceptuellement :

```text
Application
    │
    │ depends on
    ▼
AlertRepository contract
    ▲
    │ implements
    │
DatabaseAlertRepository
Infrastructure
```

Cette organisation évite que les couches internes dépendent des technologies utilisées pour satisfaire leurs besoins.

---

# 11. Pipeline d'ingestion

NetGuard peut recevoir des informations réseau depuis plusieurs sources.

Le premier périmètre prévoit notamment :

```text
Live Capture
     │
     ├──────────────┐
     │              │
     ▼              │
Capture Adapter     │
                    │
PCAP                 │
  │                  │
  ▼                  │
PCAP Adapter         │
     │               │
     └───────┬───────┘
             ▼
        Normalization
             ▼
     NetworkObservation
```

Les sources externes ne définissent pas le modèle métier de NetGuard.

Elles sont adaptées vers les contrats du Core.

---

# 12. Normalisation

La normalisation constitue une frontière essentielle du système.

Elle transforme une représentation externe en observation comprise par NetGuard.

Conceptuellement :

```text
External representation
        ↓
   validation /
   interpretation
        ↓
   normalization
        ↓
NetworkObservation
```

La normalisation doit :

- préserver les distinctions sémantiques pertinentes ;
- représenter explicitement les informations indisponibles lorsque nécessaire ;
- préserver la provenance nécessaire ;
- conserver la signification temporelle des observations ;
- éviter d'inventer des informations absentes ;
- rejeter ou diagnostiquer explicitement les entrées incompatibles avec le contrat domaine.

Le Core ne dépend pas des objets propres à la technologie de capture.

Cette décision est détaillée dans :

[`ADR-002 — Normalized Domain Observations`](./decisions/ADR-002-normalized-domain-observation.md)

---

# 13. Network State

`Network State` désigne une responsabilité architecturale.

Il ne désigne pas un objet global universel obligatoire.

Les informations nécessaires à une analyse peuvent être maintenues par différents composants spécialisés :

```text
Network State
├── Flow aggregation state
├── Detector-specific state
├── Temporal windows
└── Future specialized analytical state
```

Un détecteur peut posséder son propre état local lorsque cela correspond à sa sémantique.

NetGuard n'impose pas initialement :

- un registre global d'hôtes ;
- un registre universel de flux ;
- un cache mutable partagé entre tous les détecteurs ;
- un objet unique représentant supposément tout l'état du réseau.

Les états analytiques sont bornés et possèdent un propriétaire explicite.

---

# 14. Flow et agrégation

Un `Flow` est une construction analytique de NetGuard.

Il ne constitue pas une étape obligatoire entre une observation et un détecteur.

Le système peut donc suivre :

```text
PacketObservation
        ↓
     Detector
```

sans passer par :

```text
PacketObservation
        ↓
       Flow
        ↓
     Detector
```

lorsque le `Flow` n'apporte rien à la règle concernée.

De même, une `FlowObservation` reçue depuis une source externe reste distincte d'un `Flow` construit par NetGuard.

Le premier incrément peut donc implémenter un détecteur utilisant directement des `PacketObservation` tout en conservant une architecture permettant l'introduction ultérieure de véritables agrégations de flux.

---

# 15. Detection Engine

Le `Detection Engine` coordonne les interactions analytiques avec les détecteurs.

Il est responsable notamment :

- de transmettre les entrées aux détecteurs appropriés ;
- de respecter leurs types d'entrée acceptés ;
- de piloter les interactions analytiques nécessaires ;
- de transmettre les signaux explicites de progression ou de finalisation lorsque requis ;
- d'isoler et d'identifier les défaillances de détecteurs ;
- d'appliquer les politiques moteur définies pour ces défaillances ;
- de collecter les `DetectionResult`.

Le Detection Engine ne contient pas les algorithmes spécifiques à chaque règle.

Conceptuellement :

```text
                 NetworkObservation
                        │
                        ▼
                Detection Engine
                 /      |      \
                /       |       \
               ▼        ▼        ▼
         Detector A Detector B Detector C
               │        │        │
               └────┬───┴───┬────┘
                    ▼       ▼
               DetectionResult(s)
```

Les détecteurs sont isolés par défaut.

Ils ne lisent ou ne modifient pas directement l'état mutable interne d'autres détecteurs.

L'ordre d'exécution de détecteurs indépendants ne doit pas modifier leurs décisions lorsqu'ils reçoivent les mêmes entrées contrôlées.

---

# 16. Contrat des détecteurs

Un détecteur est un composant du domaine représentant une règle analytique.

Conceptuellement :

```text
                    DetectorConfig
                          │
                          ▼
                 ┌────────────────┐
Observation ────►│    Detector    │
                 │                │
ControlSignal ──►│ optional state │
                 └───────┬────────┘
                         │
                         ▼
                DetectionResult(s)
```

Un détecteur :

- définit les types d'entrée qu'il accepte ;
- définit ses conditions d'éligibilité ;
- reçoit une configuration domaine validée ;
- peut posséder un état analytique local et borné ;
- produit zéro, un ou plusieurs résultats bornés ;
- produit les informations nécessaires à l'explication de ses décisions.

Un détecteur ne :

- capture pas le trafic ;
- lit pas directement la base de données ;
- appelle pas une API externe pour prendre une décision cachée ;
- lit pas directement un fichier de configuration ;
- persiste pas lui-même les alertes ;
- envoie pas directement des notifications ;
- dépend pas d'un thread ou timer autonome pour sa sémantique métier.

Le contrat détaillé est défini dans [`data-models.md`](./data-models.md).

---

# 17. DetectionResult, Evidence et Alert

La chaîne de référence est :

```text
Detector
   │
   ▼
DetectionResult
   │
   ├── conclusion métier
   ├── identité/version de règle
   ├── contexte de décision
   └── Evidence stable
           │
           ▼
         Alert
           │
           ├── identité de suivi
           ├── contexte historique
           ├── Evidence nécessaire
           ├── sévérité éventuelle
           └── état de suivi
```

Ces concepts possèdent des responsabilités distinctes.

## DetectionResult

Un `DetectionResult` représente la conclusion métier produite par une règle.

Il contient ou référence les informations structurées nécessaires à l'explication de cette conclusion.

## Evidence

Une `Evidence` représente les éléments structurés justifiant la conclusion.

Elle peut contenir :

- des faits observés ;
- des agrégats calculés ;
- les paramètres pertinents de la règle ;
- des références de provenance ;
- les limitations nécessaires à l'interprétation.

Elle est stable et bornée.

Elle ne constitue pas nécessairement une archive des observations brutes.

## Alert

Une `Alert` représente une conclusion de sécurité destinée au suivi et à la consultation.

Elle ne constitue pas une nouvelle observation réseau.

Sa création ne signifie pas qu'un incident ou une compromission est confirmé.

L'Application peut coordonner la transformation :

```text
DetectionResult
       ↓
     Alert
```

mais toute décision possédant une signification métier reste définie dans le domaine approprié.

---

# 18. Persistance

La persistance est une responsabilité d'infrastructure.

Les modèles de stockage ne constituent pas automatiquement les modèles canoniques du domaine.

Conceptuellement :

```text
Domain model
     ↓
Persistence mapping
     ↓
Storage model
     ↓
Database
```

Cette séparation permet au domaine d'évoluer indépendamment :

- du schéma SQL ;
- de l'ORM ;
- de la technologie de stockage.

Les mappings nécessaires sont réalisés aux frontières de l'Infrastructure.

La persistance d'une `Alert` ne signifie pas que l'état analytique ayant permis de la produire doit également être persisté.

L'état analytique est non persistant par défaut.

---

# 19. Configuration

NetGuard distingue la configuration métier de la configuration technique.

Exemples de configuration métier :

```text
detection window
threshold
analytical capacity limit
detector-specific policy
```

Exemples de configuration technique :

```text
database connection
HTTP port
capture adapter options
worker settings
logging configuration
```

Les représentations techniques telles que variables d'environnement, fichiers YAML ou options CLI sont interprétées aux frontières appropriées.

Le Core reçoit des valeurs validées correspondant à ses besoins métier.

Le premier incrément peut considérer la configuration analytique comme fixe pendant une exécution.

Le rechargement à chaud n'est pas requis.

---

# 20. Temps

NetGuard distingue explicitement :

```text
observation time
≠
processing time
≠
maintenance time
```

Le temps métier d'une observation représente le moment associé au fait réseau observé.

Le temps de traitement représente le fonctionnement du système.

Le temps de maintenance peut être utilisé pour des délais ou opérations techniques.

Les règles temporelles réseau utilisent normalement le temps métier des observations.

Une relecture PCAP conserve les timestamps des observations d'origine.

La vitesse de replay ne doit pas modifier une décision fondée sur le temps métier lorsque les entrées contrôlées restent équivalentes.

Une action de maintenance susceptible de modifier l'état analytique et donc les résultats doit être pilotée par des entrées ou signaux contrôlables.

Le Core ne dépend pas implicitement de l'heure système pour ses décisions métier.

---

# 21. Provenance

Les observations conservent la provenance nécessaire à leur interprétation.

NetGuard distingue notamment :

```text
source
≠
point d'observation
≠
session
≠
network scope
```

La provenance permet de comprendre l'origine d'une information.

Elle ne constitue pas automatiquement une garantie :

- d'authenticité ;
- d'intégrité ;
- de précision ;
- de confiance.

Les informations de provenance sont minimisées et bornées.

Les détails techniques ou sensibles qui ne sont pas nécessaires au domaine ne sont pas propagés automatiquement.

---

# 22. Déterminisme et reproductibilité

Les composants analytiques doivent être déterministes relativement à leurs entrées contrôlées.

Selon le composant, ces entrées peuvent comprendre :

```text
observations
+
ordre pertinent
+
configuration analytique
+
état initial
+
signaux de progression
+
versions de politiques applicables
```

À entrées contrôlées sémantiquement équivalentes, le système doit produire des décisions analytiques sémantiquement équivalentes.

Cette garantie n'impose pas que soient identiques :

- les UUID techniques ;
- les clés primaires de base de données ;
- les timestamps de traitement ;
- les identifiants de session purement techniques ;
- les chemins locaux ;
- les détails d'implémentation.

La reproductibilité concerne la sémantique de l'analyse.

---

# 23. Traitement séquentiel initial

Le premier incrément privilégie un chemin de traitement séquentiel et déterministe.

Cette décision simplifie :

- l'ordre des observations ;
- la propriété des états ;
- les tests ;
- la reproductibilité ;
- la gestion des erreurs ;
- le raisonnement sur les transitions analytiques.

Elle n'interdit pas une future exécution concurrente.

Toute introduction de concurrence devra préserver explicitement les garanties métier définies par le modèle.

---

# 24. Buffers et capacité

Les files et buffers du pipeline sont bornés.

Le système ne suppose pas une mémoire infinie lorsque le trafic arrive plus rapidement qu'il ne peut être traité.

Les structures susceptibles de croître sont également bornées à l'intérieur des composants.

Cela concerne notamment :

- les buffers d'ingestion ;
- les états d'agrégation ;
- les états des détecteurs ;
- les collections internes ;
- les résultats produits ;
- les Evidence ;
- les informations de provenance ;
- l'observabilité en situation de surcharge.

Une limite globale ne suffit pas lorsqu'une structure interne peut elle-même croître sans borne.

Cette décision est détaillée dans :

[`ADR-004 — Bounded Deterministic Processing`](./decisions/ADR-004-bounded-deterministic-processing.md)

---

# 25. Surcharge et dégradation

La surcharge constitue un état explicite du système.

Lorsqu'une capacité est dépassée, NetGuard applique une politique définie.

Selon le composant, cela peut notamment entraîner :

- rejet ;
- éviction ;
- dégradation ;
- ralentissement ;
- arrêt contrôlé.

Une perte connue susceptible d'affecter l'analyse est observable.

NetGuard ne présente pas une analyse dégradée comme si toutes les informations avaient été traitées normalement.

Les politiques de surcharge restent elles-mêmes bornées et ne provoquent pas une accumulation illimitée de diagnostics.

---

# 26. Gestion des erreurs

NetGuard distingue plusieurs situations qui ne doivent pas être assimilées :

```text
entrée non prise en charge
≠
observation rejetée
≠
observation non éligible
≠
évaluation sans déclenchement
≠
expiration normale
≠
éviction de ressources
≠
erreur de détecteur
≠
erreur d'infrastructure
```

Une erreur empêchant une analyse attendue n'est pas transformée silencieusement en absence de détection.

Une défaillance de détecteur est identifiable.

La politique du moteur détermine si l'analyse peut continuer selon les garanties d'intégrité disponibles.

Intercepter une exception ne signifie pas automatiquement que l'état du détecteur reste cohérent.

Selon le cas, la politique peut prévoir :

- la poursuite ;
- la réinitialisation ;
- la désactivation du détecteur ;
- un arrêt contrôlé.

Aucun mécanisme transactionnel générique n'est imposé à tous les détecteurs pour le premier incrément.

---

# 27. Cycle de vie

Le cycle de vie de l'application est explicite.

Il distingue notamment :

```text
initialization
      ↓
start
      ↓
readiness
      ↓
operation
      ↓
controlled shutdown
```

Les échecs peuvent intervenir à chaque étape et suivent une politique définie.

L'Application pilote le cycle de vie général du Detection Engine.

Le Detection Engine pilote les interactions analytiques avec les détecteurs.

Les détecteurs restent responsables de leurs transitions métier internes.

Lors d'un arrêt contrôlé, NetGuard cesse d'accepter de nouveaux travaux selon la politique définie puis traite les travaux déjà acceptés conformément aux garanties annoncées.

Le système ne prétend pas qu'une donnée est durablement persistée avant que cette garantie ne soit réellement obtenue.

---

# 28. Composition Root

La construction des composants et l'association entre contrats et implémentations sont centralisées aux frontières de l'application.

Conceptuellement :

```text
Composition Root
      │
      ├── build Core components
      ├── build detectors
      ├── build Detection Engine
      ├── build repositories
      ├── build capture adapters
      ├── build interfaces
      └── connect contracts to implementations
```

Les composants métier ne construisent pas directement leurs dépendances techniques.

Différents modes d'exécution peuvent posséder des Composition Roots distincts.

Par exemple :

```text
live monitoring
PCAP replay
tests
CLI utility
```

peuvent assembler les mêmes composants domaine avec différentes infrastructures.

---

# 29. Modes d'exécution

L'architecture doit permettre au minimum deux sources principales :

```text
Live capture
```

et :

```text
PCAP replay
```

Ces deux modes convergent vers les mêmes contrats domaine après normalisation.

Conceptuellement :

```text
Live Capture ─────┐
                  │
                  ▼
             Normalization
                  │
                  ▼
          NetworkObservation
                  │
                  ▼
             Analysis
                  ▲
                  │
             Normalization
                  ▲
                  │
PCAP Replay ──────┘
```

Un détecteur ne doit pas avoir besoin de savoir si une observation provient d'une capture live ou d'un PCAP sauf lorsque cette provenance possède une signification métier explicitement documentée.

---

# 30. Observabilité

L'observabilité permet de comprendre le fonctionnement du système sans modifier la sémantique de l'analyse.

Elle peut notamment couvrir :

- observations reçues ;
- observations rejetées ;
- observations non prises en charge ;
- états créés ;
- expirations ;
- évictions ;
- saturation ;
- erreurs de détecteurs ;
- erreurs d'infrastructure ;
- résultats produits ;
- alertes créées ;
- latences et capacités techniques lorsque pertinent.

Les logs, métriques et traces ne deviennent pas des entrées cachées de la logique de détection.

L'observabilité est elle-même bornée afin qu'une situation de surcharge ne génère pas une seconde surcharge par accumulation de diagnostics.

---

# 31. Sécurité architecturale

Les entrées réseau sont considérées comme non fiables.

La normalisation et les frontières techniques doivent donc traiter avec prudence :

- paquets malformés ;
- valeurs inattendues ;
- fichiers PCAP invalides ;
- volumes excessifs ;
- protocoles inconnus ;
- données tronquées ;
- entrées susceptibles de provoquer une consommation excessive de ressources.

Le principe du moindre privilège est appliqué.

Lorsque la capture réseau nécessite des privilèges particuliers, ces privilèges ne doivent pas être propagés à l'ensemble de l'application sans nécessité.

Le Core ne dépend pas de privilèges système particuliers.

Les données collectées sont minimisées conformément aux besoins analytiques.

Le payload brut n'est pas conservé par défaut dans le modèle canonique initial.

Les détails de sécurité sont développés dans :

[`security.md`](./security.md)

et :

[`threat-model.md`](./threat-model.md)

---

# 32. Compatibilité sémantique

L'évolution des contrats ne se limite pas à la compatibilité syntaxique.

Une modification peut conserver les mêmes champs tout en changeant leur signification.

NetGuard considère donc la compatibilité sémantique lors de l'évolution :

- des observations ;
- des politiques d'agrégation ;
- des détecteurs ;
- des Evidence ;
- des Alert ;
- des représentations persistées ;
- des contrats exposés.

Une modification qui change la signification d'une règle ou d'un résultat doit rester traçable.

Les données historiques ne sont pas silencieusement réinterprétées selon une nouvelle sémantique.

---

# 33. Invariants architecturaux

Les invariants suivants constituent la référence architecturale de NetGuard.

1. Le Core est indépendant de la présentation et de l'API.

2. Les détecteurs sont indépendants des technologies de collecte.

3. Les données externes sont normalisées avant leur utilisation par le Core, sans perdre les distinctions sémantiques nécessaires.

4. Les détecteurs ne persistent pas directement leurs résultats.

5. La logique métier est testable sans infrastructure réelle.

6. Les états de détection sont bornés en temps et/ou quantité selon leur sémantique.

7. Les erreurs aux frontières suivent une politique explicite.

8. Les dépendances externes sont maintenues aux frontières lorsque cela est pertinent.

9. L'analyse est reproductible relativement à ses entrées contrôlées.

10. Les buffers du pipeline sont bornés.

11. Les situations de surcharge sont observables.

12. Le pipeline initial privilégie ordre et déterminisme.

13. Temps d'observation et temps de traitement restent distincts.

14. Les dépendances temporelles du Core sont contrôlables.

15. L'orchestration des cas d'utilisation appartient à l'Application.

16. Les infrastructures lentes peuvent être isolées lorsque cela est justifié sans déplacer la logique métier.

17. Le Core contient le domaine et ses invariants.

18. Les dépendances de code pointent vers l'intérieur.

19. Les contrats appartiennent à la couche qui exprime le besoin.

20. La configuration technique brute ne traverse pas le Core.

21. Les modèles de persistance restent distincts du modèle domaine lorsque leurs contraintes diffèrent.

22. La construction des dépendances est centralisée dans un Composition Root.

23. Le cycle de vie de l'application est explicite.

24. La provenance nécessaire à l'interprétation et à la reproductibilité est préservée.

25. L'évolution des contrats préserve ou explicite les changements de sémantique.

---

# 34. Conséquences pour le premier incrément

L'architecture définie dans ce document n'impose pas l'implémentation immédiate de toutes les abstractions prévues.

Le premier incrément peut rester volontairement simple.

Il peut notamment utiliser :

```text
PacketObservation
        ↓
Detection Engine
        ↓
NG-NET-001
        ↓
DetectionResult
        ↓
Alert
```

avec :

- une seule configuration de `network_scope` pour le laboratoire ;
- une provenance minimale ;
- un traitement séquentiel ;
- un état local et borné pour le détecteur ;
- aucune persistance générale des états analytiques ;
- aucune communication directe entre détecteurs ;
- aucun système de plugins dynamiques ;
- aucun registre global d'hôtes ;
- aucun mécanisme distribué ;
- aucun score générique de confiance ;
- aucun workflow complet de gestion d'incidents.

Cette simplicité initiale est compatible avec l'architecture.

Les frontières sont définies maintenant afin d'éviter qu'une implémentation rapide crée des dépendances difficiles à retirer ultérieurement.

---

# 35. Références

Les documents suivants complètent cette architecture :

- [`data-models.md`](./data-models.md) — modèles de domaine et invariants M1 à M140 ;
- [`detection-engine.md`](./detection-engine.md) — fonctionnement détaillé du moteur de détection ;
- [`network-model.md`](./network-model.md) — modèle réseau sémantique et préparation de la topologie du laboratoire ;
- [`security.md`](./security.md) — exigences et principes de sécurité ;
- [`threat-model.md`](./threat-model.md) — menaces prises en compte ;
- [`testing.md`](./testing.md) — stratégie de validation et de test ;
- [`development.md`](./development.md) — conventions de développement ;
- [`decisions/`](./decisions/) — décisions architecturales et leurs justifications.

Les ADR actuellement structurants sont notamment :

- [`ADR-001 — Modular Monolith`](./decisions/ADR-001-Modular-Monolith.md)
- [`ADR-002 — Normalized Domain Observations`](./decisions/ADR-002-normalized-domain-observation.md)
- [`ADR-003 — Inward Dependencies`](./decisions/ADR-003-inward-dependencies.md)
- [`ADR-004 — Bounded Deterministic Processing`](./decisions/ADR-004-bounded-deterministic-processing.md)
- [`ADR-005 — Separate Detection Results from Alerts`](./decisions/ADR-005-Separate-Detection-Results.md)
- [`ADR-006 — Separate Domain and Persistence Models`](./decisions/ADR-006-separate-domain-and-persistence-models.md)
- [`ADR-007 — No Universal Pre-Detection Aggregation`](./decisions/ADR-007-no-universal-pre-detection-aggregation.md)

---

# 36. Statut

L'architecture système définie lors de l'étape 0.2 reste valide après la conception détaillée des modèles de l'étape 0.3.

L'étape 0.3 précise notamment les frontières suivantes :

```text
NetworkObservation
        ↓
analytical state / aggregation
        ↓
Detector
        ↓
DetectionResult
        ↓
Evidence
        ↓
Alert
```

La formulation historique simplifiée :

```text
Detector → Alert
```

doit désormais être comprise comme un raccourci architectural.

La sémantique de référence est :

```text
Detector
    ↓
DetectionResult
    ↓
transformation métier / orchestration
    ↓
Alert
```

avec des `Evidence` stables et bornées permettant d'expliquer la conclusion analytique.

