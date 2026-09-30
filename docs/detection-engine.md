# NetGuard — Detection Engine

## 1. Objectif

Ce document définit le rôle, les responsabilités et le fonctionnement conceptuel du moteur de détection de NetGuard.

Le `Detection Engine` constitue le mécanisme d'orchestration analytique entre :

- les observations normalisées ;
- les détecteurs ;
- leurs états analytiques éventuels ;
- les signaux de progression nécessaires ;
- les résultats de détection.

Il ne définit pas à lui seul les règles métier propres à chaque détecteur.

Les invariants détaillés du modèle sont définis dans [`data-models.md`](./data-models.md), notamment :

- M81 à M98 pour l'état analytique ;
- M99 à M119 pour le contrat des détecteurs ;
- M120 à M140 pour `Alert` et `Evidence`.

L'architecture générale est définie dans [`architecture.md`](./architecture.md).

---

# 2. Position dans l'architecture

Le moteur intervient après la normalisation des données externes.

Le chemin conceptuel principal est :

```text
Capture / PCAP / Future Source
              │
              ▼
        Normalization
              │
              ▼
     NetworkObservation
              │
              ▼
       Detection Engine
         /     |     \
        /      |      \
       ▼       ▼       ▼
Detector A Detector B Detector C
       │       │       │
       └───────┼───────┘
               ▼
      DetectionResult(s)
               │
               ▼
     Alerting / Application
               │
               ▼
             Alert
```

Le moteur travaille avec les modèles normalisés du Core.

Il ne reçoit pas directement les objets natifs d'une bibliothèque de capture.

---

# 3. Responsabilité du Detection Engine

Le `Detection Engine` pilote les interactions analytiques avec les détecteurs.

Il est notamment responsable de :

- connaître les détecteurs actifs pour une exécution ;
- transmettre les entrées aux détecteurs appropriés ;
- respecter leurs types d'entrée acceptés ;
- piloter les signaux analytiques nécessaires ;
- collecter les `DetectionResult` ;
- identifier les défaillances de détecteurs ;
- appliquer une politique explicite en cas d'échec ;
- exposer l'observabilité nécessaire à son fonctionnement ;
- préserver les garanties d'ordre et de déterminisme prévues par le système.

Le moteur ne contient pas les algorithmes spécifiques de détection.

Il ne décide pas lui-même qu'un scan, une anomalie ou un autre comportement réseau est présent.

Cette décision appartient au détecteur correspondant.

---

# 4. Responsabilité des détecteurs

Un détecteur représente une règle analytique du domaine.

Conceptuellement :

```text
                 DetectorConfig
                       │
                       ▼
              ┌─────────────────┐
Observation ─►│                 │
              │    Detector     │──► DetectionResult(s)
Signal ──────►│                 │
              └────────┬────────┘
                       │
                       ▼
                Analytical State
                  if required
```

Un détecteur définit notamment :

- son identité de règle ;
- sa version sémantique pertinente ;
- les types d'entrée qu'il accepte ;
- ses conditions d'éligibilité ;
- sa configuration métier ;
- son éventuel état analytique ;
- ses conditions de détection ;
- sa politique d'émission ;
- les informations nécessaires à l'explication de ses résultats.

Un détecteur ne :

- capture pas le trafic ;
- lit pas directement un PCAP ;
- interroge pas directement une base de données ;
- dépend pas d'un ORM ;
- lit pas directement les variables d'environnement ;
- envoie pas de notification ;
- persiste pas directement une alerte ;
- lance pas implicitement son propre thread ou timer métier.

---

# 5. Un détecteur n'est pas un plugin d'infrastructure

Le terme `detector` désigne une responsabilité du domaine.

Il ne signifie pas automatiquement :

- plugin dynamique ;
- module chargé à chaud ;
- processus séparé ;
- worker ;
- service réseau ;
- extension installable.

Le premier incrément peut construire explicitement les détecteurs dans le Composition Root.

Conceptuellement :

```text
Composition Root
      │
      ├── create detector configuration
      ├── validate configuration
      ├── create detectors
      ├── create Detection Engine
      └── register detectors in engine
```

Aucun système générique de découverte ou de chargement dynamique n'est requis.

---

# 6. Identité d'une règle

Chaque règle possède un identifiant logique stable.

Exemple :

```text
NG-NET-001
```

Cet identifiant est distinct :

```text
rule_id
≠
class name
≠
display name
≠
instance id
≠
Alert id
```

Un changement de nom de classe ou de texte affiché ne doit pas modifier l'identité logique de la règle.

Une évolution modifiant suffisamment la signification de la règle pour affecter l'interprétation historique de ses résultats reste traçable par un mécanisme de version approprié.

Le premier incrément n'impose pas un framework complexe de versionnage.

---

# 7. Entrées analytiques

Les détecteurs n'acceptent pas automatiquement tous les modèles du Core.

Chaque détecteur définit les types d'entrée qu'il sait analyser.

Exemples possibles :

```text
PacketObservation
FlowObservation
Flow
Future analytical representation
```

Ces types ne sont pas considérés comme interchangeables.

Par exemple :

```text
PacketObservation
        │
        ▼
packet detector
```

ne doit pas devenir implicitement :

```text
FlowObservation
        │
        ▼
fake PacketObservation
        │
        ▼
packet detector
```

Une représentation n'est convertie vers une autre que lorsqu'une transformation sémantiquement correcte a été explicitement définie.

---

# 8. Routage des entrées

Le moteur détermine quels détecteurs sont concernés par une catégorie d'entrée.

Conceptuellement :

```text
PacketObservation
        │
        ▼
Detection Engine
        │
        ├──► Detector A accepts PacketObservation
        │
        ├──► Detector B accepts PacketObservation
        │
        └──X Detector C accepts only another input type
```

Le routage par type ne constitue qu'un premier niveau.

Le fait qu'un détecteur accepte un type d'entrée ne signifie pas que chaque instance de ce type est analytiquement éligible.

---

# 9. Validité, compatibilité et éligibilité

NetGuard distingue :

```text
valid observation
        ↓
accepted input type
        ↓
eligible for rule
        ↓
rule evaluation
        ↓
possible DetectionResult
```

Ces étapes ne sont pas équivalentes.

## 9.1 Observation valide

Une observation respecte les invariants de son modèle.

## 9.2 Type accepté

Le détecteur sait interpréter cette catégorie de représentation.

## 9.3 Observation éligible

L'observation contient les informations et garanties nécessaires à la règle.

## 9.4 Évaluation

Le détecteur applique sa logique et met éventuellement à jour son état.

## 9.5 Déclenchement

La condition définie par la règle est satisfaite selon sa politique d'émission.

Une observation peut donc être valide et appartenir au bon type tout en restant non éligible pour une règle particulière.

---

# 10. Non-éligibilité

La non-éligibilité constitue une situation normale.

Exemple :

```text
PacketObservation IPv4 valide
        │
        ├── TCP header observable
        │       ↓
        │   eligible for TCP-specific rule
        │
        └── transport information unavailable
                ↓
            not eligible
```

Le détecteur ne fabrique pas les informations manquantes.

Une observation non éligible :

- n'est pas automatiquement une erreur ;
- n'est pas automatiquement rejetée par tout le Core ;
- n'impose pas la création d'un résultat individuel ;
- peut contribuer à des métriques agrégées lorsque cela est utile.

Le système évite de produire un log par observation normalement non éligible lorsque cela risquerait de créer une surcharge inutile.

---

# 11. Évaluation sans déclenchement

Une observation éligible peut être correctement traitée sans produire de `DetectionResult`.

C'est particulièrement important pour les règles temporelles.

Exemple :

```text
observation 1 ─┐
observation 2 ─┼──► update detector state
observation 3 ─┤
observation 4 ─┘

threshold not reached
        ↓
no DetectionResult yet
```

Cette situation ne signifie pas :

```text
traffic proven normal
```

Elle signifie uniquement que la politique d'émission de la règle n'a pas produit de résultat à ce stade.

La distinction de référence est :

```text
non-eligible
≠
evaluated without detection
≠
positive detection
≠
detector error
```

---

# 12. Configuration des détecteurs

Chaque détecteur reçoit une configuration métier validée.

Exemple conceptuel :

```text
PortScanDetectorConfig
├── window
├── distinct_port_threshold
├── state_capacity
└── emission_policy
```

La configuration définit uniquement les paramètres nécessaires à la sémantique de la règle.

Elle ne contient pas arbitrairement :

```text
database_url
HTTP_port
log_file
capture_device
worker_count
```

sauf si une propriété possède réellement une signification domaine pour la règle concernée.

---

# 13. Validation de configuration

Une configuration invalide doit être détectée avant le fonctionnement normal du détecteur.

Exemples d'invariants possibles :

```text
window > 0

threshold > 0

capacity > 0
```

Les invariants concrets appartiennent au détecteur concerné.

Le détecteur ne doit pas fonctionner avec une configuration partiellement invalide puis tenter de corriger silencieusement les valeurs.

Le premier incrément peut considérer la configuration comme immuable pendant une exécution.

---

# 14. Activation et désactivation

L'activation opérationnelle d'un détecteur est orchestrée en dehors de sa logique analytique.

Conceptuellement :

```text
Application configuration
        │
        ▼
Composition / Engine
        │
        ├── enabled detector A
        ├── enabled detector B
        └── detector C not active
```

Un détecteur n'a pas besoin d'inspecter une variable globale `enabled` à chaque observation.

Pour le premier incrément, l'ensemble des détecteurs actifs peut rester fixe pendant toute l'exécution.

Le hot enable/disable n'est pas requis.

Si cette capacité est ajoutée ultérieurement, son effet sur l'état analytique devra être explicitement défini.

---

# 15. État analytique des détecteurs

Un détecteur peut être :

```text
stateless
```

ou :

```text
stateful
```

selon sa règle.

Un détecteur stateless ne reçoit pas artificiellement un état générique.

Un détecteur stateful possède un état conforme aux invariants M81 à M98.

L'état est une mémoire de travail analytique.

Il ne constitue pas une nouvelle observation réseau.

---

# 16. Propriété de l'état

L'état d'un détecteur possède un propriétaire explicite.

Pour le premier incrément :

```text
Detector
   │
   └── owns its analytical state
```

Les autres détecteurs ne reçoivent pas de référence mutable permettant de modifier cet état.

Conceptuellement :

```text
Detector A ───► State A

Detector B ───► State B

Detector A ─X─► mutable State B
Detector B ─X─► mutable State A
```

Cette isolation réduit les dépendances cachées et facilite la reproductibilité.

---

# 17. État local plutôt qu'état réseau universel

Le moteur n'impose pas un objet global du type :

```text
GlobalNetworkState
```

contenant toutes les informations utilisées par tous les détecteurs.

La première règle peut utiliser :

```text
NG-NET-001
    │
    ▼
PortScanState
```

sans nécessiter :

```text
GlobalHostRegistry
GlobalFlowRegistry
GlobalBehaviorRegistry
UniversalNetworkState
```

Un état commun n'est introduit que lorsqu'un besoin partagé réel et une sémantique commune ont été établis.

---

# 18. Fiche de conception d'un état analytique

Tout état analytique concret doit permettre de documenter les éléments suivants.

## Propriétaire

Quel composant peut modifier l'état ?

## Regroupement

Quelle clé est utilisée ?

Quelles dimensions sont incluses ou exclues ?

## Contenu

Quelles informations sont conservées et pourquoi ?

## Temps

Quelle référence temporelle est utilisée ?

Quelle est la politique de rétention ?

## Capacité

Quelles limites existent :

- nombre d'entrées ;
- cardinalité des collections internes ;
- taille éventuelle des éléments ?

## Saturation

Que se passe-t-il lorsqu'une limite est atteinte ?

## Transitions

Quelles entrées peuvent modifier l'état ?

## Evidence

Quelles informations doivent être matérialisées avant que l'état change ou disparaisse ?

## Continuité

Que se passe-t-il lors :

- d'un arrêt ;
- d'un redémarrage ;
- d'un changement de configuration éventuel ?

## Observabilité

Quelles métriques ou informations de diagnostic permettent de comprendre son fonctionnement ?

---

# 19. Bornage des états

Tout état susceptible de croître avec le trafic est borné.

Il faut considérer au minimum deux dimensions.

## 19.1 Nombre d'états

Exemple :

```text
state_by_key:
    key A → state
    key B → state
    key C → state
    ...
```

Le nombre de clés ne peut pas croître sans limite.

## 19.2 Taille interne d'un état

Une limite globale ne suffit pas.

Exemple incorrect :

```text
maximum 10,000 states

but each state contains:

set_of_ports = unlimited
```

Un seul état pourrait alors consommer une quantité arbitraire de mémoire.

Les collections internes susceptibles de croître sont donc elles aussi bornées ou représentées par une structure dont la consommation maximale est maîtrisée.

---

# 20. Expiration analytique

Les informations qui ne peuvent plus influencer une décision future doivent pouvoir être retirées de l'état selon une politique explicite.

Exemple conceptuel :

```text
t0                         t1
|--------------------------|
       analysis window

older information
        ↓
no longer relevant
        ↓
expiration
```

La politique précise :

- quelle référence temporelle elle utilise ;
- ce qui expire ;
- quand l'expiration devient applicable ;
- l'effet de l'expiration sur les futures décisions.

Une clé régulièrement active peut rester présente longtemps tout en retirant progressivement les informations devenues trop anciennes.

---

# 21. Expiration et éviction

Le moteur et les détecteurs distinguent :

```text
expiration
```

et :

```text
resource eviction
```

## Expiration

L'information n'est plus nécessaire selon la politique analytique normale.

## Éviction

L'information aurait encore pu être utile mais est supprimée afin de respecter une limite de ressources.

Ces événements n'ont pas la même signification.

Une éviction susceptible de réduire la qualité de l'analyse est observable.

---

# 22. Temps métier

Les règles portant sur l'activité réseau utilisent normalement le temps métier des observations.

Exemple :

```text
PacketObservation.observed_at
```

Une fenêtre de détection ne dépend pas par défaut de :

```text
datetime.now()
```

ou du temps écoulé depuis que le programme a reçu l'observation.

Cette règle est essentielle pour obtenir un comportement cohérent entre :

```text
live capture
```

et :

```text
PCAP replay
```

---

# 23. Signaux de progression

Certaines transitions analytiques peuvent nécessiter un signal indiquant que le traitement a suffisamment progressé pour effectuer une action.

Le moteur peut transmettre de tels signaux lorsqu'ils sont nécessaires au contrat d'un détecteur.

Conceptuellement :

```text
Observation
Observation
Observation
ProgressSignal
Observation
FinalizationSignal
```

Ces signaux constituent des entrées contrôlées de l'analyse lorsqu'ils peuvent influencer :

- l'expiration ;
- la finalisation ;
- la suppression d'état ;
- la production d'un résultat.

Ils ne doivent pas être remplacés par une lecture cachée de l'heure système dans le détecteur.

---

# 24. Pas de framework temporel complexe obligatoire

Le contrat précédent ne signifie pas que le premier incrément doit implémenter :

- un système distribué de watermarks ;
- un ordonnanceur complexe ;
- une synchronisation multi-capteurs ;
- un moteur universel de fenêtres ;
- un système complet de réordonnancement.

Le premier détecteur doit utiliser le mécanisme le plus simple qui respecte les invariants temporels nécessaires.

L'abstraction ne doit devenir plus complexe que lorsque les besoins concrets l'exigent.

---

# 25. Observations tardives et hors ordre

L'ordre d'arrivée et l'ordre temporel peuvent différer.

Le traitement d'une observation tardive dépend de la politique du détecteur.

Conceptuellement :

```text
observed_at:

10:00
10:02
10:01
```

peut être reçu dans cet ordre sans que NetGuard modifie artificiellement les timestamps.

La règle définit ce qu'elle accepte comme désordre et comment ce désordre influence son état.

Une observation tardive ne modifie pas silencieusement un résultat déjà stabilisé.

---

# 26. Replay

Le replay PCAP utilise les temps métier enregistrés dans les observations.

Le comportement analytique ne doit pas dépendre de la vitesse physique de lecture du fichier.

Conceptuellement, ces deux exécutions :

```text
PCAP replay at 1x
```

et :

```text
PCAP replay at 100x
```

doivent produire des décisions analytiques sémantiquement équivalentes lorsque :

- les mêmes observations sont admises ;
- leur ordre pertinent est identique ;
- la configuration est identique ;
- l'état initial est identique ;
- les signaux de progression pertinents sont équivalents ;
- aucune dégradation de ressources ne modifie les entrées réellement traitées.

Si un replay accéléré provoque une saturation et une perte d'informations, les exécutions ne sont plus considérées comme analytiquement équivalentes.

Cette dégradation doit être observable.

---

# 27. Déterminisme

Un détecteur est déterministe relativement à ses entrées contrôlées.

Conceptuellement :

```text
result =
    detector(
        observations,
        relevant_order,
        config,
        initial_state,
        progress_signals,
        applicable_policy_versions
    )
```

À entrées contrôlées sémantiquement équivalentes, les décisions et transitions doivent être sémantiquement équivalentes.

Les décisions ne doivent pas dépendre silencieusement :

- de l'heure système ;
- d'un UUID aléatoire ;
- d'un ordre arbitraire de dictionnaire lorsqu'il influence la logique ;
- d'une requête réseau ;
- d'un accès à la base de données ;
- d'un état global caché.

---

# 28. Traitement séquentiel initial

Le premier incrément privilégie un traitement séquentiel.

Conceptuellement :

```text
Observation 1
     ↓
all relevant detectors
     ↓
Observation 2
     ↓
all relevant detectors
     ↓
Observation 3
```

Le détail exact de la boucle d'exécution sera choisi lors de l'implémentation.

L'objectif architectural est de disposer initialement :

- d'un ordre compréhensible ;
- d'un propriétaire unique des états ;
- d'un comportement facilement testable ;
- d'une gestion simple des erreurs ;
- d'une reproductibilité forte.

Cette décision n'interdit pas une future parallélisation.

---

# 29. Indépendance entre détecteurs

Plusieurs détecteurs peuvent analyser la même observation.

Conceptuellement :

```text
                   ┌──► Detector A
                   │
Observation ───────┼──► Detector B
                   │
                   └──► Detector C
```

Ils utilisent la même observation immuable.

Un détecteur ne modifie pas l'observation pour transmettre une information au suivant.

Un détecteur ne lit pas directement l'état interne d'un autre.

Ainsi, pour des détecteurs indépendants :

```text
A then B
```

et :

```text
B then A
```

ne doivent pas modifier leurs décisions métier respectives lorsqu'ils reçoivent les mêmes entrées contrôlées.

---

# 30. Pas de chaînage implicite

Un `DetectionResult` produit par un détecteur ne devient pas automatiquement l'entrée d'un autre détecteur.

Le système n'introduit pas implicitement :

```text
Detector A
    ↓
Detector B
    ↓
Detector C
```

Si une future corrélation entre résultats devient nécessaire, elle constitue une capacité analytique explicitement définie.

Elle possède alors :

- ses entrées ;
- sa sémantique ;
- son état éventuel ;
- son propriétaire ;
- ses garanties temporelles ;
- son propre contrat.

---

# 31. Condition de détection

Chaque détecteur définit précisément la condition qui produit un résultat positif.

Cette condition doit être suffisamment précise pour être :

- implémentable ;
- testable ;
- reproductible ;
- explicable.

Une formulation vague telle que :

```text
many suspicious packets
```

n'est pas suffisante.

Le contrat concret doit définir les grandeurs utilisées.

Exemple conceptuel :

```text
distinct_destination_ports >= configured_threshold
within configured_window
for configured_grouping_key
```

Le détail exact appartient à la règle concernée.

---

# 32. Politique d'émission

Satisfaire une condition analytique et produire un nouveau résultat ne sont pas nécessairement la même opération.

Une règle temporelle doit définir sa politique d'émission.

Exemples possibles :

```text
emit on threshold crossing
```

```text
emit once per window
```

```text
emit then require rearm
```

```text
emit with explicit cooldown
```

```text
emit for every qualifying transition
```

NetGuard n'impose pas une politique universelle.

La politique retenue fait partie du contrat de la règle lorsqu'elle influence les résultats produits.

---

# 33. Cooldown et réarmement

Un éventuel cooldown utilisé pour empêcher la production répétée de `DetectionResult` appartient à la sémantique analytique du détecteur.

Il fait alors partie de son état et de son contrat.

Il est distinct d'une limitation de notifications située en aval.

Ainsi :

```text
detector cooldown
```

et :

```text
notification throttling
```

ne sont pas équivalents.

Le premier modifie les résultats analytiques produits.

Le second modifie uniquement leur diffusion.

---

# 34. DetectionResult

Un détecteur produit des `DetectionResult`.

Un résultat représente une conclusion métier de la règle.

Conceptuellement :

```text
DetectionResult
├── rule identity
├── rule semantic context
├── analytical subject/context
├── relevant observed time/window
└── Evidence
```

Les champs exacts sont définis par les modèles du Core.

Un `DetectionResult` n'est pas simplement :

```text
True
```

ou :

```text
"port scan detected"
```

Il doit contenir ou référencer les informations structurées nécessaires à l'interprétation de la conclusion.

---

# 35. Cardinalité des résultats

Le traitement d'une entrée peut produire :

```text
0 result
1 result
N results
```

selon la règle.

Cette cardinalité est bornée.

Un détecteur ne doit pas construire en mémoire une liste de taille arbitraire pour une seule transition.

Les limites peuvent porter sur :

- le nombre de résultats ;
- la taille d'un résultat ;
- le nombre d'éléments d'Evidence ;
- la taille des collections imbriquées.

Toute limitation susceptible de supprimer des résultats qui auraient autrement été produits est explicite et observable.

---

# 36. Evidence

Les `Evidence` matérialisent les éléments nécessaires à l'explication d'un résultat.

Elles sont produites avant que l'état mutable dont elles proviennent puisse changer ou disparaître.

Conceptuellement :

```text
Mutable Detector State
          │
          │ detection occurs
          ▼
   Evidence snapshot
          │
          ▼
   DetectionResult
```

Le `DetectionResult` ne conserve pas simplement :

```text
reference_to_mutable_detector_state
```

pour expliquer ultérieurement sa décision.

Les Evidence sont :

- structurées ;
- stables ;
- immuables après stabilisation ;
- bornées ;
- adaptées à la règle.

---

# 37. Faits observés et agrégats calculés

Une `Evidence` distingue ce qui a été observé de ce qui a été calculé.

Exemple :

```text
Observed fact:
destination port 22 observed

Calculated aggregate:
24 distinct destination ports in window

Rule parameter:
threshold = 20
```

Ces informations ne sont pas présentées comme équivalentes.

Le détecteur ne transforme pas un agrégat calculé en prétendu fait directement observé.

---

# 38. Résumé des Evidence

Il n'est pas nécessaire de conserver toutes les observations ayant contribué à une détection.

Exemple :

```text
distinct ports counted: 24
ports shown as evidence: 10
```

Cette représentation doit indiquer clairement que :

```text
10 displayed ports
≠
complete list of 24 ports
```

La sélection des éléments présentés suit une politique déterministe lorsque cela influence la reproductibilité ou l'interprétation.

---

# 39. DetectionResult et Alert

Le moteur produit ou collecte des `DetectionResult`.

Il ne doit pas confondre ce résultat avec une `Alert`.

La frontière conceptuelle est :

```text
Detector
    ↓
DetectionResult
    ↓
Application / domain policy
    ↓
Alert
```

`DetectionResult` représente la conclusion métier de la règle.

`Alert` représente cette conclusion dans le cadre de son suivi et de sa consultation.

La couche Application peut orchestrer leur conversion.

Toute décision métier intervenant dans cette conversion reste définie dans le domaine approprié.

---

# 40. Transformation en Alert

Pour le premier incrément, une politique simple peut être retenue :

```text
1 DetectionResult
        ↓
1 Alert
```

Cela évite d'introduire prématurément :

- corrélation complexe ;
- regroupement multi-détections ;
- suppression avancée ;
- incident management ;
- fusion universelle d'alertes.

Cette simplicité ne doit cependant pas fusionner conceptuellement les deux responsabilités.

Une future politique pourra évoluer sans modifier le contrat fondamental du détecteur.

---

# 41. Sévérité

La sévérité n'est pas automatiquement une propriété universelle calculée par tous les détecteurs de la même manière.

Lorsqu'elle existe, elle suit une politique métier documentée.

Pour une Alert du premier incrément, la sévérité est obligatoire conformément à [FR-010](requirements/functional.md). Cette exigence ne rend pas son calcul obligatoire dans chaque détecteur : la politique domaine peut intervenir lors de la transformation du résultat en Alert.

Selon la règle, cette politique peut être :

- directement définie par le détecteur ;
- dérivée d'un `DetectionResult` selon une politique domaine séparée ;
- fixée par configuration métier.

La couche Application peut orchestrer cette décision mais ne doit pas inventer arbitrairement sa signification.

La sévérité ne représente pas automatiquement une probabilité ou un niveau de confiance.

---

# 42. Absence de score de confiance obligatoire

Le premier incrément n'exige pas de score générique de confiance.

Une règle déterministe n'a pas besoin d'inventer une valeur telle que :

```text
confidence = 0.87
```

sans définition statistique ou sémantique solide.

Si une notion de confiance est introduite ultérieurement, elle devra définir précisément ce qu'elle mesure.

---

# 43. Erreurs de détecteur

Une erreur de détecteur est distincte d'une absence de détection.

Exemple :

```text
eligible observation
       ↓
detector invariant failure
       ↓
ERROR
```

ne doit pas être présenté comme :

```text
no suspicious behavior
```

Le moteur doit pouvoir identifier :

- quel détecteur a échoué ;
- à quel moment analytique ;
- quelles analyses peuvent être affectées ;
- quelle politique a ensuite été appliquée.

---

# 44. Intégrité de l'état après erreur

Intercepter une exception ne prouve pas que l'état interne du détecteur est encore valide.

Exemple :

```text
state mutation begins
        ↓
partial mutation
        ↓
exception
```

Le moteur ne peut pas supposer automatiquement :

```text
state is safe
```

La politique du détecteur ou du moteur définit ce qui est garanti.

Selon le cas, le système peut :

- continuer lorsque l'intégrité est garantie ;
- réinitialiser l'état concerné ;
- désactiver le détecteur ;
- arrêter le traitement de manière contrôlée.

Le premier incrément n'impose pas de transaction générique autour de chaque transition de détecteur.

---

# 45. Isolation des défaillances

L'échec d'un détecteur ne doit pas être confondu avec l'échec analytique de tous les autres détecteurs.

Conceptuellement :

```text
Observation
    │
    ├──► Detector A → success
    ├──► Detector B → failure
    └──► Detector C → success
```

Le moteur identifie l'échec de B.

La possibilité de poursuivre dépend de la politique d'exécution et des garanties d'intégrité disponibles.

Le moteur ne doit pas prétendre que B a analysé correctement l'observation.

---

# 46. Politique d'erreur

Une politique d'erreur peut conceptuellement aboutir à :

```text
CONTINUE
RESET_DETECTOR
DISABLE_DETECTOR
STOP_ENGINE
```

Ces noms sont illustratifs.

Ils ne constituent pas une API imposée.

La politique concrète doit préserver deux principes :

1. une erreur analytique connue est observable ;
2. le système ne poursuit pas avec un état potentiellement incohérent comme si aucune erreur n'avait eu lieu.

---

# 47. Cycle de vie

L'Application pilote le cycle de vie général du moteur.

Conceptuellement :

```text
Application
    │
    ├── initialize engine
    ├── start analysis
    ├── provide observations
    ├── finalize analysis
    └── shutdown engine
```

Le moteur pilote les interactions analytiques avec les détecteurs.

Conceptuellement :

```text
Detection Engine
    │
    ├── deliver observations
    ├── deliver progress signals
    ├── request finalization when required
    └── apply reset/error policies
```

Les détecteurs restent responsables de leurs transitions métier.

---

# 48. Initialisation

Avant l'analyse normale, le moteur doit disposer de détecteurs correctement construits.

L'initialisation comprend conceptuellement :

```text
raw external configuration
        ↓
boundary parsing
        ↓
domain configuration validation
        ↓
detector construction
        ↓
engine construction
```

Une configuration invalide doit empêcher le démarrage normal du détecteur concerné selon la politique choisie.

Le détecteur ne découvre pas lui-même sa configuration depuis l'environnement.

---

# 49. Finalisation

Certains détecteurs peuvent nécessiter un signal de finalisation.

Ce signal peut notamment servir à :

- stabiliser un état ;
- libérer des informations ;
- produire un résultat lorsque la règle le prévoit explicitement ;
- réaliser une transition métier terminale.

La finalisation ne produit pas automatiquement des résultats pour tous les détecteurs.

Chaque règle définit si un tel signal possède une signification analytique.

Un arrêt brutal ne doit pas être présenté comme équivalent à une finalisation normale.

---

# 50. Réinitialisation

Lorsqu'un détecteur stateful est réinitialisé, son état retourne à un état initial défini.

Cette opération ne doit pas être confondue avec une expiration analytique normale.

Une réinitialisation peut notamment être provoquée par :

- une politique de récupération après erreur ;
- un nouveau cycle d'exécution ;
- une future modification incompatible de configuration ;
- une action explicitement prévue.

Lorsque la perte d'historique influence l'analyse future, cette dégradation ou limite est connue et documentée.

---

# 51. Redémarrage

Les états analytiques ne sont pas persistants par défaut.

Après un redémarrage :

```text
previous detector state
        ↓
not restored
        ↓
new initial state
```

sauf si une future exigence définit explicitement un mécanisme de restauration.

Cela signifie qu'après un redémarrage :

- une fenêtre peut perdre son historique ;
- un cooldown peut être perdu ;
- une activité déjà détectée peut produire un nouveau résultat ultérieurement.

Ces limites ne sont pas cachées.

Le premier incrément accepte cette propriété.

---

# 52. Changement de configuration

Pour le premier incrément, la configuration analytique reste fixe pendant une exécution.

Cela évite d'avoir à définir immédiatement :

- migration d'état ;
- double configuration simultanée ;
- rechargement à chaud ;
- compatibilité entre anciennes et nouvelles fenêtres ;
- réinterprétation des états existants.

Une future capacité de changement dynamique devra respecter M97.

Un état construit avec une ancienne sémantique ne sera pas silencieusement réinterprété avec une nouvelle configuration.

---

# 53. Observabilité du moteur

Le moteur expose les informations nécessaires pour comprendre son fonctionnement.

Les métriques exactes seront choisies lors de l'implémentation, mais peuvent notamment couvrir :

```text
observations_received
observations_routed
observations_ineligible
detector_evaluations
detection_results_emitted
detector_errors
detector_resets
detector_disables
state_evictions
state_expirations
```

Cette liste n'est pas un schéma obligatoire.

L'observabilité doit permettre de distinguer :

```text
nothing detected
```

de :

```text
analysis degraded or failed
```

lorsque cette différence est connue.

---

# 54. Observabilité bornée

Les mécanismes de diagnostic sont eux-mêmes bornés.

Une attaque ou un trafic malformé ne doit pas pouvoir provoquer :

```text
1 invalid packet
    ↓
1 huge log
    ↓
millions of packets
    ↓
unbounded logs / memory / disk
```

Les erreurs répétitives peuvent être :

- comptées ;
- agrégées ;
- échantillonnées ;
- limitées selon une politique explicite.

Cette limitation ne doit pas masquer l'existence d'une dégradation importante.

---

# 55. Performance

Le moteur doit permettre une analyse continue sans croissance mémoire non bornée.

L'optimisation ne doit cependant pas dégrader les garanties fondamentales du domaine.

En particulier, une optimisation ne doit pas introduire silencieusement :

- un changement de sémantique temporelle ;
- une perte non observable ;
- une dépendance à l'ordre d'exécution ;
- un partage mutable caché ;
- une déduplication incorrecte ;
- une modification des Evidence.

Les optimisations sont introduites à partir de mesures concrètes lorsque nécessaire.

---

# 56. Concurrence

Le premier incrément ne nécessite pas l'exécution concurrente des détecteurs.

Le modèle doit néanmoins éviter de rendre impossible une future parallélisation.

Une évolution vers :

```text
parallel detector execution
```

devra préserver :

- l'immuabilité des observations ;
- l'isolation des états ;
- les garanties d'ordre nécessaires ;
- le déterminisme métier ;
- la gestion explicite des erreurs ;
- le bornage des files ;
- la stabilité des résultats.

La concurrence n'est pas introduite uniquement parce qu'elle est techniquement possible.

---

# 57. Backpressure et surcharge

Le Detection Engine s'inscrit dans un pipeline dont les buffers sont bornés.

Si les observations arrivent plus vite qu'elles ne peuvent être analysées, le système ne suppose pas une file infinie.

La politique de surcharge appartient à l'architecture d'exécution et doit être explicite.

Une perte d'observations provoquée par la surcharge signifie que les détecteurs ne disposent plus du même ensemble d'entrées.

Les résultats obtenus ne doivent donc pas être présentés comme analytiquement équivalents à une exécution sans perte.

---

# 58. Tests d'un détecteur

Chaque détecteur doit pouvoir être testé sans :

- capture réseau réelle ;
- base de données ;
- serveur HTTP ;
- frontend ;
- accès réseau externe ;
- horloge système incontrôlée.

Un test doit pouvoir construire explicitement :

```text
configuration
+
observations
+
initial state
+
control/progress signals
```

et vérifier :

```text
DetectionResult(s)
+
resulting analytical state
```

lorsque cet état fait partie du comportement testé.

---

# 59. Tests d'éligibilité

Les tests doivent couvrir séparément :

```text
valid + eligible
valid + non-eligible
invalid observation rejected before detector
```

afin d'éviter que les règles confondent validation du modèle et éligibilité analytique.

Les cas d'informations absentes doivent également vérifier qu'aucune valeur fictive n'est introduite.

---

# 60. Tests temporels

Une règle temporelle doit être testée avec des timestamps contrôlés.

Les tests doivent notamment permettre de couvrir lorsque pertinent :

- observations dans l'ordre ;
- observations partageant le même timestamp ;
- observations hors ordre ;
- expiration ;
- passage de fenêtre ;
- signal de progression ;
- finalisation ;
- replay à vitesse différente ;
- observation tardive.

Aucun `sleep()` réel ne doit être nécessaire pour vérifier la sémantique temporelle du détecteur.

---

# 61. Tests de capacité

Les limites de l'état doivent être testées.

Il faut notamment vérifier :

- la limite du nombre de clés ;
- les limites internes d'une entrée ;
- la politique d'éviction ;
- l'observabilité de la dégradation ;
- le caractère déterministe du choix d'éviction lorsque celui-ci influence l'analyse.

Les tests doivent éviter qu'un état apparemment borné globalement contienne une structure interne illimitée.

---

# 62. Tests de reproductibilité

Un même scénario analytique exécuté avec les mêmes entrées contrôlées doit produire des résultats sémantiquement équivalents.

Le test ne doit pas exiger l'égalité de détails techniques sans importance, par exemple :

```text
database primary key
random Alert UUID
processing timestamp
```

La comparaison porte sur la décision métier et les informations nécessaires à son interprétation.

---

# 63. Tests d'erreur

Les tests du moteur doivent couvrir les défaillances d'un détecteur.

Ils doivent notamment vérifier :

- que l'erreur est identifiable ;
- qu'elle n'est pas convertie en absence de détection ;
- que la politique prévue est appliquée ;
- que l'état n'est pas réutilisé lorsque son intégrité n'est pas garantie ;
- que les autres détecteurs sont traités conformément à la politique du moteur.

---

# 64. Fiche de conception d'un détecteur

Avant l'implémentation d'une règle concrète, sa conception doit documenter au minimum les éléments suivants.

## Identité

```text
Rule ID:
Semantic version/context:
Display name:
```

## Objectif

Quel comportement la règle cherche-t-elle à identifier ?

## Entrées acceptées

Quels types analytiques sont acceptés ?

## Éligibilité

Quelles informations doivent être présentes ?

Quelles garanties sont nécessaires ?

## Sujet analytique

Sur quelle entité ou quel regroupement porte la conclusion ?

## Regroupement

Quelle clé est utilisée ?

Quelles dimensions sont incluses ou exclues ?

## Configuration

Quels paramètres influencent la règle ?

Quels sont leurs invariants ?

## Temps

Quelle notion de temps est utilisée ?

Existe-t-il une fenêtre ?

Comment les observations tardives sont-elles traitées ?

## État

Le détecteur est-il stateless ou stateful ?

Si stateful, appliquer la fiche de conception d'état.

## Condition de détection

Quelle condition exacte produit une conclusion positive ?

## Politique d'émission

Quand un `DetectionResult` est-il produit ?

## Réarmement / cooldown

Existe-t-il une politique empêchant des émissions répétées ?

## DetectionResult

Quelle conclusion structurée est produite ?

## Evidence

Quels faits, agrégats et paramètres expliquent la décision ?

## Limites

Quelles limites de capture, provenance ou interprétation affectent la règle ?

## Capacité

Quelles limites protègent la mémoire et la cardinalité des résultats ?

## Dégradation

Que se passe-t-il en cas d'éviction ou saturation ?

## Cycle de vie

Que se passe-t-il lors d'une finalisation, réinitialisation ou erreur ?

## Replay

Quelles garanties existent lors d'une relecture PCAP ?

## Déterminisme

Quelles entrées contrôlées déterminent entièrement le comportement ?

## Observabilité

Quels compteurs ou diagnostics sont nécessaires ?

## Tests

Quels scénarios minimaux prouvent le contrat ?

---

# 65. Premier détecteur : NG-NET-001

Le premier détecteur prévu par NetGuard est `NG-NET-001`.

Son objectif général est de détecter un comportement compatible avec un scan de ports.

Sa conception détaillée sera réalisée séparément à partir de la fiche précédente.

À ce stade, la clé candidate issue du modèle réseau est :

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
destination_port
    ↓
distinct value counted inside the analytical window
```

et :

```text
source_port
    ↓
does not partition the analytical state
```

Cette proposition reste à valider lors de la conception complète de `NG-NET-001`.

Le document présent ne fixe donc pas encore :

- le seuil ;
- la durée de fenêtre ;
- la politique exacte d'émission ;
- le cooldown éventuel ;
- les Evidence exactes ;
- les règles concernant les flags TCP ;
- la politique détaillée face aux observations hors ordre ;
- les limites numériques de capacité.

Ces décisions appartiennent au contrat concret du détecteur.

---

# 66. Chemin minimal du premier incrément

Le premier incrément du Detection Engine peut rester volontairement simple :

```text
PacketObservation
        │
        ▼
Detection Engine
        │
        ▼
NG-NET-001
        │
        ├── validated config
        │
        └── local bounded state
                │
                ▼
         DetectionResult
                │
                └── bounded Evidence
                        │
                        ▼
                      Alert
```

Le traitement peut être :

- séquentiel ;
- mono-processus ;
- sans plugin dynamique ;
- sans état distribué ;
- sans persistance de l'état du détecteur ;
- sans bus d'événements interne ;
- sans communication directe entre détecteurs ;
- sans moteur universel de fenêtres ;
- sans score générique de confiance.

Cette simplicité respecte l'architecture définie pour NetGuard.

---

# 67. Ce que le moteur ne doit pas devenir prématurément

Le premier Detection Engine ne doit pas devenir un framework générique surdimensionné.

Il n'est pas nécessaire d'introduire immédiatement :

```text
DynamicPluginManager
DetectorDependencyGraph
DistributedStateStore
GenericWindowEngine
DetectorMessageBus
DetectorScheduler
RuleDSL
RuleCompiler
GenericCEPFramework
UniversalCorrelationEngine
```

Ces abstractions ne seront introduites que si une exigence concrète les justifie.

L'objectif initial est de construire un moteur simple dont les contrats sont suffisamment propres pour permettre une évolution future.

---

# 68. Invariants du Detection Engine

Le moteur respecte les invariants suivants.

1. Les détecteurs reçoivent des représentations domaine, pas des objets natifs de capture.

2. Chaque détecteur définit les types d'entrée qu'il accepte.

3. Type accepté et éligibilité analytique sont distincts.

4. Une observation non éligible n'est pas une erreur.

5. Une évaluation sans résultat positif n'est pas une preuve de normalité.

6. Une erreur de détecteur n'est pas une absence de détection.

7. Les détecteurs ne fabriquent pas les faits nécessaires à leurs règles.

8. Les configurations métier sont validées avant l'analyse normale.

9. Un détecteur n'a un état que si sa règle l'exige.

10. Les états sont locaux et isolés par défaut.

11. Les états susceptibles de croître sont bornés globalement et intérieurement.

12. Expiration analytique et éviction de ressources restent distinctes.

13. Toute perte connue d'état susceptible de dégrader l'analyse est observable.

14. Les décisions temporelles réseau utilisent le temps métier approprié.

15. Les transitions temporelles influençant l'analyse sont contrôlables.

16. La vitesse de replay ne modifie pas la sémantique de la règle à entrées équivalentes.

17. Les détecteurs sont déterministes relativement à leurs entrées contrôlées.

18. Les détecteurs indépendants ne partagent pas implicitement d'état mutable.

19. Un résultat d'un détecteur ne devient pas implicitement l'entrée d'un autre.

20. La condition de détection est explicitement définie.

21. La politique d'émission est explicitement définie lorsqu'elle influence les résultats.

22. Les `DetectionResult` sont structurés et bornés.

23. Les `Evidence` nécessaires sont matérialisées avant de dépendre d'un état mutable susceptible de changer.

24. `DetectionResult` et `Alert` restent des responsabilités distinctes.

25. Les détecteurs ne persistent ni ne publient directement leurs résultats.

26. Une défaillance de détecteur est identifiable.

27. La poursuite après erreur dépend des garanties d'intégrité disponibles.

28. L'Application pilote le cycle de vie du moteur.

29. Le moteur pilote les interactions analytiques avec les détecteurs.

30. Aucun détecteur ne dépend implicitement d'un thread, timer ou mécanisme de capture autonome pour sa sémantique.

---

# 69. Relation avec les autres documents

Ce document décrit le fonctionnement du Detection Engine.

Les responsabilités sont réparties ainsi :

```text
architecture.md
    ↓
architecture globale et frontières

data-models.md
    ↓
invariants des modèles et contrats domaine

detection-engine.md
    ↓
orchestration analytique et fonctionnement du moteur

future detector specification
    ↓
contrat concret de NG-NET-001, NG-NET-002, ...
```

Les règles de ce document ne remplacent pas les invariants M1 à M140.

Elles expliquent comment les appliquer au moteur de détection.

---

# 70. Statut

Le contrat architectural du Detection Engine est cohérent avec les modèles validés lors de l'étape 0.3.

Le moteur initial peut être construit autour de :

```text
normalized observations
        ↓
sequential Detection Engine
        ↓
independent detectors
        ↓
local bounded analytical states
        ↓
structured DetectionResult
        ↓
stable bounded Evidence
        ↓
Alert creation
```

Cette architecture permet de commencer avec `NG-NET-001` sans imposer prématurément :

- des microservices ;
- des plugins dynamiques ;
- un état réseau global ;
- une infrastructure distribuée ;
- un moteur universel de corrélation ;
- un système générique de fenêtres ;
- une persistance des états analytiques ;
- un bus interne entre détecteurs.

Les extensions futures devront préserver les invariants du domaine ou documenter explicitement les décisions qui les remplacent.