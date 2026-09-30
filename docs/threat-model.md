## Actifs à protéger — 0.5.1

Le threat model de NetGuard considère comme actif tout élément dont la perte d’intégrité, de confidentialité ou de disponibilité pourrait réduire la fiabilité de l’analyse, exposer des informations sensibles ou empêcher le système d’assurer son rôle de surveillance.

Les actifs ne se limitent donc pas aux données persistées ou aux secrets techniques. Dans un système de détection réseau, l’intégrité des observations, de l’état analytique et des conclusions produites constitue également une propriété de sécurité essentielle.

La protection d’un actif ne signifie pas que NetGuard garantit la vérité absolue des informations provenant du réseau. Le système protège la cohérence de ce qu’il observe, calcule et conclut dans les limites des informations dont il dispose.

La distinction fondamentale reste :

```text
réalité réseau
    ≠
ce que NetGuard observe
    ≠
ce que NetGuard calcule
    ≠
ce qu'une règle conclut
    ≠
la manière dont le résultat est conservé ou présenté
```

### A1 — Intégrité des observations réseau normalisées

Les observations réseau admises dans le Core constituent la représentation structurée de faits observés par NetGuard à partir d’une source donnée.

Leur intégrité doit être préservée pendant :

```text
source externe
    ↓
capture / lecture
    ↓
normalisation
    ↓
validation
    ↓
NetworkObservation
```

Une adaptation ne doit pas modifier silencieusement la signification d’une information, combiner des données provenant de couches incompatibles ou fabriquer une valeur manquante afin de produire artificiellement une observation valide.

La protection de cet actif ne signifie pas que NetGuard certifie la véracité des informations contenues dans le trafic.

Par exemple :

```text
source_ip = 192.0.2.10
```

signifie que cette adresse a été observée comme adresse source selon le contexte et les garanties de la source concernée.

Cela ne garantit pas que cette adresse identifie avec certitude la machine ayant réellement généré le trafic.

Une adresse peut notamment être usurpée et une source de capture peut fournir une vision incomplète du réseau.

La propriété protégée est donc :

```text
intégrité de la représentation de ce qui a été observé
```

et non :

```text
certitude sur la réalité complète du réseau
```

### A2 — Intégrité et bornage de l’état analytique

Les détecteurs et autres composants analytiques peuvent maintenir un état dérivé des observations précédemment admises.

Conceptuellement :

```text
observations
+
signaux contrôlés
        ↓
état analytique
        ↓
décision
```

Un attaquant capable de générer du trafic peut légitimement influencer cet état puisque le trafic constitue précisément une entrée du système.

NetGuard ne cherche donc pas à empêcher toute influence externe sur l’état analytique.

La propriété recherchée est que cet état évolue uniquement selon les règles définies à partir :

- des observations admises ;
- de la configuration applicable ;
- des signaux temporels ou de cycle de vie explicitement contrôlés ;
- des politiques de capacité définies.

L’état doit notamment être protégé contre :

```text
corruption interne
contamination entre scopes
regroupement incorrect
croissance non bornée
réutilisation après compromission de sa cohérence
confusion entre expiration analytique et éviction de ressources
```

Une contrainte de ressources peut provoquer une perte ou une éviction selon une politique explicite, mais cette situation doit rester distincte d’une transition analytique normale.

### A3 — Intégrité des conclusions de détection

Les conclusions produites par les détecteurs constituent le cœur de la valeur analytique de NetGuard.

Le chemin conceptuel est :

```text
observations
+
configuration analytique
+
état pertinent
        ↓
Detector
        ↓
DetectionResult
```

Un `DetectionResult` doit représenter fidèlement la conclusion réellement obtenue selon la règle et les entrées contrôlées qui lui sont applicables.

Son intégrité concerne notamment les éléments nécessaires à l’interprétation de la décision, tels que :

```text
rule_id
version ou contexte sémantique de la règle
faits observés pertinents
agrégats calculés
seuil utilisé
fenêtre temporelle
période couverte
```

Une erreur interne ne doit pas permettre à un résultat d’affirmer silencieusement des faits ou agrégats différents de ceux ayant réellement conduit au déclenchement de la règle.

La protection de cet actif concerne la fidélité de la conclusion analytique au contrat du détecteur.

Elle ne transforme pas une détection en preuve absolue qu’une attaque réelle a eu lieu.

### A4 — Intégrité et explicabilité des Evidence et Alert

Les `Evidence` et `Alert` stabilisent les informations nécessaires à la compréhension et à la consultation d’une conclusion analytique.

Leur relation reste conceptuellement :

```text
Detector
    ↓
DetectionResult
    │
    └── Evidence
            ↓
          Alert
```

Une `Evidence` stabilisée doit conserver les faits observés, calculs et paramètres nécessaires à l’interprétation de la conclusion sans dépendre d’un état analytique mutable qui pourrait évoluer ou disparaître ultérieurement.

Une `Alert` historique doit rester cohérente avec la conclusion dont elle provient.

La protection de cet actif doit notamment empêcher qu’une transformation, une persistance ou une consultation ultérieure modifie silencieusement :

```text
la règle concernée
les faits justificatifs
les paramètres analytiques pertinents
la période observée
la signification de la conclusion
```

L’explicabilité fait partie de cette intégrité : NetGuard doit pouvoir présenter les éléments structurés qui justifient la conclusion dans les limites des informations effectivement disponibles.

Une `Alert` reste néanmoins une conclusion de sécurité produite par une règle et non la certification d’un incident réel.

### A5 — Intégrité de la configuration analytique

Les paramètres qui modifient directement la sémantique d’une analyse constituent un actif critique.

Cela peut notamment concerner :

```text
seuil de détection
fenêtre temporelle
nombre minimal d’éléments distincts
activation future d’une règle
paramètres influençant le regroupement ou le calcul
```

Une modification non autorisée de ces valeurs peut réduire ou modifier les capacités de détection sans nécessairement provoquer de défaillance visible.

Par exemple :

```text
threshold = 20
```

modifié en :

```text
threshold = 50000
```

peut laisser NetGuard techniquement fonctionnel tout en modifiant profondément le comportement du détecteur.

L’intégrité de la configuration analytique est donc une propriété de sécurité distincte de la simple disponibilité du processus.

La configuration réellement utilisée pour une décision doit également rester cohérente avec les paramètres nécessaires à l’interprétation de cette décision.

### A6 — Intégrité de la configuration technique

La configuration technique contrôle les mécanismes d’exécution sans constituer directement la définition métier d’une règle.

Elle peut notamment concerner :

```text
capacités de buffers
limites de ressources
paramètres de capture
configuration de persistance
adresse d’écoute d’une interface
timeouts techniques
```

Une modification non autorisée peut provoquer :

```text
indisponibilité
perte de données
saturation
exposition réseau inattendue
dégradation des garanties analytiques
```

La configuration technique reste distincte de la configuration analytique même lorsqu’elle peut indirectement affecter la qualité de l’analyse.

Par exemple, une réduction de capacité provoquant davantage d’évictions ne transforme pas cette capacité en seuil métier.

Les conséquences connues d’une telle limitation doivent néanmoins rester observables.

### A7 — Confidentialité des données réseau collectées

NetGuard traite des informations réseau pouvant révéler des éléments sensibles sur les systèmes observés.

Selon les capacités effectivement implémentées, ces données peuvent notamment inclure :

```text
adresses IP
ports
horodatages
relations entre machines
protocoles observés
identifiants de sources
adresses MAC futures
métadonnées protocolaires
```

La disponibilité d’une information dans le trafic ne justifie pas automatiquement sa conservation, sa persistance ou son exposition.

NetGuard applique donc un principe de minimisation :

```text
collecter et conserver
uniquement ce qui est nécessaire
aux capacités réellement fournies
```

Le payload réseau brut ne fait pas partie par défaut de la représentation canonique initiale des observations.

Cette limitation réduit directement la quantité de données sensibles que NetGuard doit protéger.

Toute extension future de la collecte devra réévaluer les conséquences de confidentialité correspondantes.

### A8 — Intégrité, confidentialité et disponibilité des données persistées

Les données persistées constituent l’historique durable produit ou conservé par NetGuard.

Elles peuvent notamment inclure des `Alert`, leurs informations d’interprétation et d’autres données nécessaires aux capacités de consultation futures.

Leur intégrité doit empêcher qu’une donnée historique soit modifiée silencieusement de manière à changer la signification de ce qui avait été produit.

Leur confidentialité est importante car un historique peut révéler :

```text
machines observées
services
relations réseau
activité temporelle
comportements suspects
structure partielle du réseau
```

Leur disponibilité est également importante pour les fonctionnalités qui dépendent de l’historique.

Une perte de persistance reste cependant distincte de la validité analytique d’une conclusion déjà produite.

Ainsi :

```text
DetectionResult valide
        ↓
Alert créée
        ↓
échec de persistance
```

signifie que la garantie de stockage n’a pas été satisfaite.

Cela ne signifie pas que la conclusion analytique n’a jamais existé.

### A9 — Confidentialité des secrets techniques

Les secrets techniques nécessaires à certaines intégrations futures constituent un actif distinct de la configuration métier.

Ils peuvent notamment inclure :

```text
credentials de stockage
tokens
clés API
secrets d’intégration
```

Ces informations ne doivent être accessibles qu’aux composants qui en ont réellement besoin.

Elles ne doivent pas être propagées inutilement dans les couches internes ni apparaître intentionnellement dans :

```text
DetectionResult
Evidence
Alert
logs
métriques
réponses publiques d’API
messages de diagnostic
dépôt Git
```

La protection de cet actif porte principalement sur sa confidentialité.

Le mécanisme concret utilisé pour fournir ou stocker les secrets dépendra du mode de déploiement et n’est pas imposé par le threat model à cette étape.

### A10 — Disponibilité et capacité de traitement du pipeline

La capacité de NetGuard à continuer d’ingérer et d’analyser des observations constitue un actif de sécurité.

Le pipeline concerné est conceptuellement :

```text
Capture / Ingestion
        ↓
Normalization
        ↓
Network State
        ↓
Detection
        ↓
Alerting
```

Un environnement hostile peut tenter de provoquer une pression importante sur ce pipeline par :

```text
volume élevé
forte cardinalité
grand nombre de clés analytiques
données malformées
pression CPU
pression mémoire
saturation des buffers
```

NetGuard V1 ne prétend pas pouvoir traiter sans perte une charge arbitrairement élevée.

La propriété recherchée est plutôt :

```text
ressources bornées
+
politique explicite sous saturation
+
dégradation identifiable
+
pertes connues observables
```

Une surcharge ne doit notamment pas provoquer une croissance mémoire non bornée simplement pour préserver artificiellement toutes les entrées reçues.

La disponibilité doit donc être protégée sans promettre une capacité infinie.

### A11 — Disponibilité des capacités opérationnelles critiques

La présence d’un processus NetGuard vivant ne garantit pas que toutes ses capacités nécessaires fonctionnent correctement.

Selon le mode d’exécution, des capacités telles que :

```text
source de capture
détecteurs
persistance
consultation
```

peuvent être nécessaires au fonctionnement attendu.

Il faut donc préserver la distinction :

```text
processus vivant
≠
système prêt
≠
système pleinement opérationnel
```

Par exemple :

```text
processus actif
+
détecteur critique désactivé après défaillance
```

ne doit pas être interprété comme un fonctionnement nominal complet.

La disponibilité effective des capacités requises par le mode d’exécution constitue donc un actif distinct de la simple disponibilité du processus.

Les politiques exactes déterminant quelles capacités sont obligatoires ou optionnelles seront définies avec les modes d’exécution correspondants.

### A12 — Intégrité et disponibilité des signaux d’observabilité significatifs

L’observabilité n’est pas la source de vérité métier de NetGuard.

Les logs et métriques ne remplacent ni les observations, ni les résultats analytiques, ni les `Alert`.

Ils constituent néanmoins une capacité importante pour identifier :

```text
rejets
pertes connues
saturations
évictions de ressources
défaillances de détecteurs
échecs de persistance
dégradations opérationnelles
```

Une défaillance confinée ne doit pas devenir silencieuse uniquement parce que le reste du système continue à fonctionner.

De même, une perte connue susceptible de réduire les garanties analytiques doit pouvoir produire un signal opérationnel identifiable.

La protection de cet actif ne signifie pas que chaque événement doit produire un log individuel ni que toute information d’observabilité doit être conservée durablement.

La propriété recherchée est que les dégradations significatives connues restent observables dans les limites des garanties fournies par le système d’observabilité.

### Actifs volontairement non garantis

NetGuard ne considère pas comme actif protégeable la « vérité absolue du réseau ».

Le système travaille à partir d’observations nécessairement limitées par :

```text
position du capteur
visibilité disponible
qualité de la source
trafic effectivement observé
informations présentes dans les protocoles
limites de ressources
```

NetGuard ne garantit donc pas :

```text
l’identité réelle certaine d’un émetteur
l’absence de spoofing
l’observation de tout le trafic existant
la détection de toute activité malveillante
la confirmation qu’une Alert correspond à une attaque réelle
```

Ces limites ne doivent pas être compensées par des affirmations plus fortes que les observations disponibles.

La propriété de sécurité recherchée reste :

```text
préserver fidèlement
ce qui a été observé,
ce qui a été calculé
et ce que la règle a réellement conclu
```

### Portée de 0.5.1

Cette étape identifie les actifs dont la protection conditionne la fiabilité et la sécurité de NetGuard : observations normalisées, état analytique, conclusions de détection, Evidence et Alert, configurations analytique et technique, données réseau collectées, historique persistant, secrets techniques, capacité du pipeline, capacités opérationnelles critiques et signaux d’observabilité significatifs. Ces actifs serviront de référence pour définir les frontières de confiance, les capacités de l’attaquant et les menaces concrètes dans les sous-étapes suivantes.


## Frontières de confiance — 0.5.2

Cette section définit les principales frontières de confiance de NetGuard.

Une frontière de confiance apparaît lorsqu’une information passe d’un contexte possédant certaines garanties vers un contexte qui va s’appuyer sur ces garanties, ou lorsqu’une information quitte une zone interne vers un système ou un utilisateur externe.

Une frontière architecturale n’est pas automatiquement une frontière de confiance :

```text
frontière architecturale
≠
frontière de confiance
```

Par exemple, `Core` et `Application` constituent deux couches architecturales distinctes, mais appartiennent au même logiciel et au même processus dans l’architecture initiale. Leur séparation organise les responsabilités et les dépendances ; elle ne signifie pas que l’une doit considérer l’autre comme un acteur hostile.

À l’inverse, une donnée locale ou déjà persistée n’est pas automatiquement fiable simplement parce qu’elle se trouve sur la machine exécutant NetGuard.

Le principe général est :

```text
origine connue ou locale
≠
donnée nécessairement fiable
```

Les frontières définies ci-dessous précisent où NetGuard doit valider, adapter, limiter ou contrôler les informations qu’il reçoit ou expose.

### TB1 — Réseau observé vers capture

Le trafic réseau observé constitue une entrée non fiable.

NetGuard doit supposer qu’un acteur externe peut influencer ou contrôler certaines caractéristiques du trafic reçu, notamment :

```text
adresses
ports
protocoles
flags
tailles
ordre des paquets
fréquence
volume
fragmentation
contenu
combinaisons inhabituelles de champs
```

Une donnée provenant du réseau ne doit donc pas être considérée comme valide ou honnête uniquement parce qu’elle a été capturée.

Le principe est :

```text
paquet capturé
≠
paquet valide
≠
information nécessairement vraie
```

Un paquet peut également être syntaxiquement valide tout en contenant une information trompeuse.

Par exemple, une adresse IP source peut être correctement représentée dans le paquet tout en ayant été usurpée.

NetGuard doit pouvoir conserver fidèlement le fait :

```text
cette adresse a été observée comme adresse source
```

sans transformer cette observation en :

```text
cette adresse identifie avec certitude
la machine ayant réellement généré le trafic
```

Cette frontière protège notamment l’intégrité des observations, l’état analytique et la disponibilité du pipeline face à des entrées potentiellement hostiles.

### TB2 — Fichier PCAP vers lecteur PCAP

Un fichier PCAP constitue une entrée externe et doit être traité comme non fiable, même lorsqu’il est présent localement sur la machine exécutant NetGuard.

La relation suivante est donc fausse :

```text
fichier local
=
fichier fiable
```

Un PCAP peut provenir :

```text
d’un laboratoire
d’une autre machine
d’un téléchargement
d’un utilisateur
d’un système externe
d’une source potentiellement hostile
```

Il peut contenir des structures ou valeurs inhabituelles telles que :

```text
paquets malformés
tailles pathologiques
protocoles inattendus
timestamps inhabituels
captures tronquées
volumes importants
combinaisons de champs inattendues
```

Le lecteur PCAP et les bibliothèques utilisées pour interpréter ces données font donc partie de la surface d’attaque technique.

Le flux attendu reste :

```text
PCAP
    ↓
adapter Infrastructure
    ↓
décodage
    ↓
normalisation
    ↓
validation
    ↓
observation domaine
```

Un objet brut issu du parser PCAP ne devient pas directement une entrée analytique du détecteur.

### TB3 — Représentation technique vers modèle Core

La transformation d’une représentation technique en objet domaine constitue une frontière de confiance majeure.

Avant cette frontière, NetGuard peut manipuler une représentation provenant :

```text
d’une bibliothèque de capture
d’un parser PCAP
d’un format externe
d’un mécanisme technique d’ingestion
```

Après cette frontière, le Core reçoit une représentation conforme à son contrat.

Conceptuellement :

```text
représentation externe
        ↓
adaptation
        ↓
validation du format
        ↓
construction
        ↓
validation des invariants
        ↓
NetworkObservation valide
```

Les responsabilités restent séparées.

L’adaptateur Infrastructure connaît la représentation technique de la source et effectue les transformations nécessaires.

Le Core définit la sémantique et les invariants de ses propres modèles.

Une information manquante ne doit pas être fabriquée pour permettre artificiellement la construction d’un objet domaine.

Une fois un objet domaine valide construit, les composants internes peuvent s’appuyer sur les invariants garantis par son contrat.

Cette validation ne certifie cependant pas la vérité du fait réseau représenté.

La distinction reste :

```text
objet domaine valide
=
objet cohérent avec le contrat NetGuard
```

et non :

```text
objet domaine valide
=
description certaine de la réalité réseau
```

### TB4 — Configuration externe vers configuration validée

Toute configuration provenant d’une représentation externe doit être considérée comme non fiable avant parsing et validation.

Les sources futures peuvent notamment inclure :

```text
fichier
variables d’environnement
arguments CLI
mécanisme de déploiement
secret manager
```

Le flux attendu est :

```text
source externe
        ↓
chargement
        ↓
parsing
        ↓
validation
        ↓
configuration structurée
        ↓
composant concerné
```

Une configuration peut être incorrecte à cause d’une erreur utilisateur aussi bien que d’une modification malveillante.

Par exemple :

```text
threshold = -5
```

ou :

```text
port_scan_thresold = 20
```

ne doivent pas être transformés silencieusement en fonctionnement nominal si ces valeurs violent le contrat contrôlé par NetGuard.

Cette frontière protège notamment :

```text
configuration analytique
configuration technique
secrets techniques
```

Une configuration validée garantit la cohérence avec son contrat, pas l’intention de la personne ayant fourni la valeur.

### TB5 — Client externe vers Interfaces et Application

Toute future interface permettant à un utilisateur ou à un système externe d’interagir avec NetGuard constitue une frontière de confiance.

Pour une API HTTP, le chemin pourra par exemple être :

```text
client externe
        ↓
requête HTTP
        ↓
Interfaces / API
        ↓
Application
        ↓
Core
```

Les données provenant du client doivent être considérées comme non fiables.

Cela peut notamment concerner :

```text
paramètres
identifiants
filtres
pagination
payload
headers
valeurs de configuration exposées
commandes autorisées par l’interface
```

La couche Interfaces valide et adapte les contraintes propres au protocole externe.

Les règles métier et invariants internes ne doivent toutefois pas exister uniquement dans l’API.

La distinction reste :

```text
validité de la représentation externe
→ Interfaces

validité du cas d’utilisation
→ Application / Core

invariant domaine
→ Core
```

Cette séparation garantit qu’une autre interface, telle qu’une CLI, ne puisse pas contourner un invariant simplement parce que celui-ci aurait été implémenté uniquement dans l’adaptateur HTTP.

### TB6 — Domaine vers persistance

La persistance constitue une frontière technique distincte du modèle domaine.

Conceptuellement :

```text
objet domaine
        ↓
adapter de persistance
        ↓
représentation de stockage
        ↓
stockage
```

Une `Alert`, une `Evidence` ou un autre objet métier ne devient pas automatiquement un modèle de base de données.

L’adaptateur de persistance doit préserver la sémantique nécessaire lors de la conversion.

La distinction reste :

```text
modèle domaine
≠
modèle de persistance
```

Une erreur de mapping ne doit pas transformer silencieusement :

```text
identifiants
timestamps
faits justificatifs
paramètres analytiques
statuts
```

ou toute autre information nécessaire à l’interprétation historique du résultat.

Cette frontière protège principalement l’intégrité des données persistées et des conclusions stabilisées.

### TB7 — Persistance vers domaine

Une donnée relue depuis un stockage contrôlé par NetGuard n’est pas automatiquement valide pour le modèle courant.

Le stockage peut contenir des données affectées par :

```text
ancienne version du schéma
migration incorrecte
corruption
modification externe
bug historique
écriture partielle selon les garanties du stockage
```

La relation suivante ne doit donc pas être supposée :

```text
donnée présente dans la base
=
objet domaine nécessairement valide
```

Lorsqu’un adaptateur reconstruit un objet domaine depuis une représentation persistée, il doit respecter le contrat applicable à cette reconstruction.

Une donnée incompatible avec les invariants nécessaires ne doit pas être transformée silencieusement en objet valide en inventant ou en modifiant des informations.

Cette frontière devient particulièrement importante lorsque le schéma de persistance et les modèles domaine évoluent indépendamment.

### TB8 — Application vers interface externe

Une frontière de confiance existe également lorsque des informations quittent NetGuard.

Conceptuellement :

```text
Core / Application
        ↓
Interfaces
        ↓
utilisateur ou système externe
```

Une interface ne doit pas exposer automatiquement toutes les informations accessibles au processus.

Des informations telles que :

```text
credentials
tokens
stack traces internes
exceptions de drivers
configuration sensible
payload réseau non nécessaire
chemins locaux inutiles
détails techniques internes
```

ne doivent pas devenir publiques simplement parce qu’elles existent dans une couche interne.

Les représentations externes doivent être construites selon le contrat de l’interface et appliquer les principes de minimisation appropriés.

Cette frontière protège notamment :

```text
données réseau collectées
historique persistant
secrets techniques
détails internes d’implémentation
```

Les futures règles d’authentification et d’autorisation devront être appliquées à cette frontière lorsqu’un mode d’exposition nécessitera de distinguer plusieurs niveaux d’accès.

### TB9 — Composants NetGuard vers observabilité

L’observabilité constitue une sortie technique pouvant transporter des informations hors du composant qui les produit et éventuellement hors du processus NetGuard.

Conceptuellement :

```text
Core / Application / Infrastructure / Interfaces
                    ↓
              instrumentation
                    ↓
             logs / métriques
                    ↓
          destination technique
```

Une information ne devient pas sûre à exposer simplement parce qu’elle est destinée au diagnostic.

Cette frontière doit préserver les principes de :

```text
minimisation
structuration
maîtrise du volume
maîtrise de la cardinalité
protection des secrets
limitation des données sensibles
```

Par exemple :

```text
secret disponible dans le processus
≠
secret acceptable dans un log
```

et :

```text
adresse IP disponible dans une observation
≠
adresse IP appropriée comme label de métrique
```

Les informations non fiables provenant du réseau ne doivent pas non plus être utilisées de manière incontrôlée comme structure, nom d’événement ou dimension d’observabilité.

Cette frontière protège la confidentialité des données ainsi que la disponibilité du système d’observabilité.

### TB10 — Dépendances techniques vers NetGuard

NetGuard repose nécessairement sur des composants qu’il ne contrôle pas entièrement.

Cela peut notamment inclure :

```text
système d’exploitation
bibliothèques Python
bibliothèque de capture
parser PCAP
driver de stockage
framework HTTP futur
mécanismes réseau du système
```

Ces composants fournissent des garanties techniques nécessaires au fonctionnement de NetGuard, mais leurs objets et résultats ne deviennent pas automatiquement des objets domaine fiables.

Lorsqu’une bibliothèque traite une donnée externe, sa sortie reste adaptée et validée selon les contrats NetGuard avant d’être utilisée comme représentation métier lorsque cette validation est nécessaire.

Cette frontière permet notamment de conserver :

```text
objet de bibliothèque externe
≠
modèle domaine NetGuard
```

Les erreurs provenant d’une dépendance technique sont également traduites aux frontières lorsque l’appelant a besoin d’une sémantique d’échec indépendante de cette technologie.

Le threat model applicatif ne suppose toutefois pas que NetGuard puisse conserver ses garanties normales face à une compromission complète de son environnement d’exécution.

Les hypothèses précises concernant le système d’exploitation, le processus, l’opérateur et les dépendances de confiance seront définies dans la section consacrée aux hypothèses de confiance.

### Validation et vérité

Le franchissement réussi d’une frontière de validation garantit uniquement les propriétés définies par le contrat concerné.

Le principe fondamental est :

```text
entrée non fiable
        ↓
validation
        ↓
objet conforme au contrat
```

et non :

```text
entrée non fiable
        ↓
validation
        ↓
information garantie vraie
```

Quelques exemples illustrent cette distinction :

```text
adresse IP valide
≠
identité authentifiée

timestamp valide
≠
horloge source fiable

port valide
≠
service réellement présent

TCP SYN observé
≠
connexion réellement établie

Alert produite
≠
attaque confirmée
```

La validation protège la cohérence des représentations et des invariants que NetGuard est effectivement capable de vérifier.

Elle ne doit pas renforcer artificiellement les garanties fournies par la source.

### Frontières architecturales internes

Les séparations entre :

```text
Core
Application
Infrastructure
Interfaces
```

restent essentielles pour l’architecture du logiciel.

Elles ne constituent toutefois pas toutes des frontières de confiance hostiles.

En particulier :

```text
Core ↔ Application
```

représente une séparation de responsabilités et de dépendances dans la base de code, pas une hypothèse selon laquelle Application exécuterait du code hostile contre le Core.

De même, les détecteurs officiels de NetGuard sont isolés par leurs responsabilités et leurs états, mais ne sont pas considérés comme des plugins adverses exécutant du code arbitraire.

L’introduction future de plugins tiers non fiables, d’exécution de code utilisateur ou de composants distribués appartenant à des domaines de confiance différents nécessiterait une réévaluation explicite de ce threat model.

### Portée de 0.5.2

Cette étape identifie les principales frontières de confiance entre le réseau, les fichiers PCAP, les représentations techniques, le Core, la configuration, les interfaces externes, la persistance, l’observabilité et les dépendances techniques. Elle établit que les entrées externes ou persistées ne deviennent fiables qu’au regard des invariants effectivement validés, que les sorties doivent appliquer une minimisation adaptée et qu’une validation garantit la cohérence d’un contrat sans certifier la vérité complète des informations observées.


## Capacités de l’attaquant — 0.5.3

Cette section définit les capacités accordées à un acteur hostile dans le threat model de NetGuard V1.

L’objectif n’est pas encore de décrire les attaques concrètes contre le système, mais de préciser ce qu’un attaquant peut raisonnablement contrôler ou influencer. Les menaces seront construites ultérieurement à partir de ces capacités.

La distinction fondamentale est :

```text
capacité de l’attaquant
≠
objectif de l’attaquant
≠
menace résultante
```

Par exemple :

```text
capacité
→ générer un volume important de trafic

objectif
→ perturber NetGuard

menace résultante
→ saturation ou épuisement de ressources
```

Le modèle ne suppose ni un attaquant passif ni un attaquant omnipotent.

Le principe retenu est :

```text
NetGuard suppose
que ses entrées externes peuvent être hostiles

mais ne suppose pas
que son environnement d’exécution
est déjà entièrement compromis
```

### AC1 — Générer du trafic réseau observable contrôlé

Un attaquant peut générer du trafic susceptible d’être observé par NetGuard et contrôler une partie importante des caractéristiques du trafic qu’il produit.

Cela peut notamment concerner :

```text
adresses
ports
protocoles
flags
tailles
séquences
destinations
fréquence
timing
volume
```

Cette capacité ne signifie pas que l’attaquant contrôle l’ensemble du trafic observé par NetGuard.

Le modèle suppose seulement qu’il peut contrôler certains paquets, flux ou comportements susceptibles d’entrer dans le pipeline d’analyse.

NetGuard ne doit donc pas dépendre de l’hypothèse selon laquelle le trafic reçu suit nécessairement un comportement normal, coopératif ou attendu.

### AC2 — Produire des informations réseau trompeuses

Un attaquant peut produire des informations syntaxiquement valides dont la signification apparente ne correspond pas nécessairement à la réalité sous-jacente.

Selon les protocoles et le contexte, il peut chercher à influencer des informations telles que :

```text
adresses
ports
identifiants
séquences
flags
métadonnées protocolaires
```

Par exemple :

```text
source_ip = X
```

ne permet pas automatiquement de conclure :

```text
l’attaquant réel possède l’identité X
```

Cette capacité prolonge le principe défini par les frontières de confiance :

```text
validation
≠
preuve de vérité
```

NetGuard doit préserver fidèlement les informations observées sans leur attribuer une garantie d’identité, d’authenticité ou d’origine qu’il ne possède pas.

### AC3 — Produire des entrées réseau malformées ou inhabituelles

Un attaquant peut volontairement produire des entrées situées aux limites ou en dehors des comportements réseau habituels.

Cela peut notamment inclure :

```text
paquets tronqués
champs incohérents
valeurs limites
fragmentation inhabituelle
combinaisons rares de champs
protocoles inattendus
structures malformées
séquences atypiques
```

Les adaptateurs, parsers et mécanismes de normalisation ne doivent donc pas supposer que les données reçues respectent systématiquement les cas nominaux prévus par les protocoles.

Une entrée invalide peut être rejetée selon le contrat applicable sans qu’il soit nécessaire de fabriquer des valeurs permettant artificiellement son admission dans le Core.

Cette capacité concerne également les entrées techniquement valides mais suffisamment inhabituelles pour exercer des chemins rarement utilisés dans les composants de capture, de parsing ou de normalisation.

### AC4 — Générer un volume ou une cardinalité élevés

Un attaquant peut chercher à exercer une pression importante sur les ressources de NetGuard.

Cette pression peut provenir du volume brut :

```text
grand nombre de paquets
grand nombre d’observations
fort débit
activité soutenue
```

mais également de la cardinalité :

```text
grand nombre d’adresses
grand nombre de ports
grand nombre de flows
grand nombre de scopes
grand nombre de clés analytiques distinctes
grand nombre de combinaisons uniques
```

Ces deux dimensions doivent rester distinctes.

Par exemple :

```text
1 000 000 observations
sur une seule clé analytique
```

et :

```text
1 000 000 observations
sur 1 000 000 clés analytiques
```

peuvent provoquer des contraintes très différentes sur la mémoire, les agrégations et les états des détecteurs.

Cette capacité justifie que les buffers et états analytiques restent explicitement bornés.

NetGuard V1 ne suppose pas disposer de ressources suffisantes pour absorber sans perte une charge arbitrairement élevée.

### AC5 — Contrôler partiellement la temporalité de son activité

Un attaquant peut choisir quand il génère les actions réseau qu’il contrôle.

Il peut donc produire des comportements temporels tels que :

```text
activité concentrée
bursts
activité lente
activité espacée
activité proche d’un seuil temporel
activité proche d’une expiration
alternance de périodes actives et silencieuses
```

Cette capacité est particulièrement pertinente pour les détecteurs utilisant des fenêtres temporelles.

Elle ne signifie cependant pas que l’attaquant contrôle le temps de NetGuard lui-même.

La distinction reste :

```text
contrôle du moment d’émission
de certaines actions hostiles
≠
contrôle de l’horloge NetGuard
```

Le désordre, le retard ou la différence entre temps d’observation et temps de traitement peuvent également provenir du fonctionnement normal de la capture, des buffers, du replay ou du pipeline.

Ces phénomènes ne doivent donc pas être automatiquement attribués à une action hostile.

### AC6 — Adapter son comportement aux règles de détection

NetGuard ne suppose pas que ses règles de détection restent inconnues d’un attaquant.

Un acteur hostile peut connaître, déduire ou tester :

```text
les comportements recherchés
les regroupements utilisés
les fenêtres temporelles
les seuils publics ou observables
les caractéristiques générales d’une règle
```

Il peut ensuite adapter les actions qu’il contrôle, par exemple en les répartissant :

```text
dans le temps
entre plusieurs destinations
entre plusieurs sources qu’il contrôle
entre plusieurs caractéristiques observables
```

lorsque son environnement lui permet de le faire.

La sécurité de NetGuard ne doit donc pas reposer sur :

```text
l’attaquant ignore
le fonctionnement des détecteurs
```

Une règle connue peut rester utile, mais ses limites et possibilités d’évasion doivent pouvoir être analysées explicitement.

### AC7 — Fournir un PCAP non fiable spécialement construit

Lorsqu’un mode d’analyse PCAP est utilisé, NetGuard peut être amené à traiter un fichier provenant d’une source non fiable.

Un acteur hostile peut contrôler ou influencer :

```text
contenu du fichier
nombre de paquets
ordre des observations
timestamps
structures réseau
tailles
métadonnées interprétées par le lecteur
```

Il peut notamment construire un fichier destiné à exercer les cas limites du parser, de la normalisation ou du pipeline analytique.

Cette capacité signifie :

```text
NetGuard peut recevoir
un PCAP hostile
```

et non :

```text
l’attaquant possède
un accès arbitraire au système de fichiers
```

La capacité à fournir une entrée PCAP et la capacité à modifier librement les fichiers de la machine sont donc distinctes.

### AC8 — Envoyer des entrées hostiles aux interfaces accessibles

Lorsqu’une interface NetGuard est accessible à un acteur non fiable, celui-ci peut contrôler les requêtes qu’il lui adresse.

Selon l’interface effectivement implémentée, cela peut notamment concerner :

```text
paramètres
identifiants
filtres
pagination
payloads
valeurs limites
types inattendus
requêtes répétées
entrées malformées
entrées volumineuses
```

Cette capacité ne signifie pas que toutes les interfaces NetGuard sont nécessairement accessibles depuis Internet.

La relation suivante ne doit pas être supposée :

```text
interface réseau existante
→
interface accessible à tout acteur distant
```

L’exposition dépendra du mode de déploiement.

Le threat model considère donc un acteur disposant effectivement d’un accès à l’interface concernée, sans lui attribuer automatiquement un accès aux autres composants internes.

Une CLI locale n’est notamment pas assimilée à une API distante simplement parce qu’elles peuvent déclencher certains cas d’utilisation similaires.

### AC9 — Connaître les mécanismes publics de NetGuard

NetGuard étant destiné à être développé publiquement, la sécurité du système ne doit pas dépendre de la confidentialité de son architecture ou de son code source.

Un attaquant peut donc connaître :

```text
architecture
code source
règles de détection
formats documentés
valeurs par défaut publiques
comportements documentés
modèles de données publics
limitations connues
```

Le modèle suppose également qu’un acteur peut étudier le comportement du système et utiliser ces informations pour préparer ses entrées.

Le principe est :

```text
algorithme connu
≠
système automatiquement compromis
```

Les informations réellement secrètes doivent être limitées aux éléments qui nécessitent effectivement une confidentialité, tels que certains credentials, tokens ou secrets techniques.

La sécurité de NetGuard ne doit pas reposer sur :

```text
personne ne sait
comment NetGuard fonctionne
```

### AC10 — Provoquer des erreurs et dégradations à partir des entrées accessibles

Un attaquant peut chercher à provoquer des comportements dégradés en utilisant uniquement les entrées auxquelles il a légitimement accès selon les capacités précédentes.

Il peut notamment chercher à déclencher :

```text
erreurs de parsing
rejets répétés
exceptions de dépendances
saturation de buffers
pression sur les états analytiques
timeouts
échecs localisés
chemins de traitement inhabituels
```

Cette capacité ne signifie pas que toute erreur provoquée permet automatiquement une compromission du système.

La distinction reste :

```text
provoquer une erreur
≠
obtenir une exécution de code
≠
compromettre NetGuard
```

Le threat model devra analyser comment une erreur provenant d’une entrée hostile est :

```text
rejetée
confinée
observée
propagée
ou transformée en dégradation contrôlée
```

selon la responsabilité du composant concerné.

### Capacités non accordées à l’attaquant principal

Le modèle adverse principal de NetGuard V1 ne suppose pas qu’un attaquant possède déjà un contrôle arbitraire de l’environnement d’exécution.

En particulier, les capacités suivantes ne lui sont pas accordées par défaut :

```text
accès administrateur ou root à l’hôte
contrôle du kernel
lecture ou modification arbitraire de la mémoire du processus
modification arbitraire du code NetGuard
remplacement arbitraire de modules
écriture arbitraire dans le dépôt
modification arbitraire de tous les fichiers de configuration
accès automatique à la base de données
possession automatique des secrets techniques
contrôle arbitraire de l’horloge système
rupture arbitraire de primitives cryptographiques correctement utilisées
```

Une compromission complète de l’hôte permettrait notamment à un attaquant de :

```text
modifier le programme
altérer les observations
changer la configuration
falsifier les résultats
lire les secrets
désactiver les détecteurs
tuer le processus
```

Dans une telle situation, les garanties applicatives de NetGuard seraient largement invalidées.

La résistance à une compromission complète de l’environnement d’exécution n’est donc pas une garantie de NetGuard V1.

Cela n’empêche pas certaines de ces situations d’être considérées ultérieurement comme hypothèses environnementales, risques résiduels ou scénarios nécessitant une compromission préalable.

### Accès aux ressources internes

Une capacité externe ne doit pas être transformée implicitement en accès à toutes les ressources internes.

En particulier :

```text
capacité à générer du trafic
≠
accès à la base de données

capacité à fournir un PCAP
≠
accès arbitraire au système de fichiers

accès à une API
≠
accès au processus NetGuard

connaissance du code source
≠
capacité à modifier le code exécuté
```

Chaque menace future devra donc être compatible avec les capacités réellement nécessaires à sa réalisation.

Cette règle évite de construire des scénarios reposant sur des privilèges que le modèle n’a jamais accordés à l’attaquant.

### Contrôle du temps

L’attaquant peut contrôler la temporalité de certaines actions qu’il produit, mais ne possède pas automatiquement le contrôle de l’horloge utilisée par NetGuard.

Le modèle distingue donc :

```text
timing du trafic hostile
≠
temps d’observation
≠
temps de traitement
≠
horloge du système
```

Une horloge incorrecte, une mauvaise synchronisation ou une anomalie environnementale peuvent affecter certaines garanties temporelles sans nécessairement résulter d’une attaque.

Les hypothèses faites sur les sources de temps seront précisées avec les hypothèses de confiance.

### Connaissance et secrets

Le code, l’architecture et les mécanismes analytiques publics de NetGuard ne sont pas considérés comme des secrets.

Le système doit rester cohérent avec son modèle de sécurité lorsque l’attaquant connaît son fonctionnement général.

La distinction est :

```text
information publique sur le fonctionnement
≠
secret technique

règle de détection
≠
credential

architecture
≠
clé secrète
```

Cette distinction est particulièrement importante pour un projet dont le code source est destiné à être publiquement consultable.

### Erreur opérateur et comportement hostile

Une erreur commise par un opérateur légitime n’est pas automatiquement considérée comme une attaque.

La distinction reste :

```text
erreur opérateur
≠
action hostile
```

Une valeur de configuration incorrecte, un fichier invalide ou une mauvaise utilisation peuvent néanmoins produire des conséquences similaires à certaines entrées malveillantes.

NetGuard doit donc rester robuste face aux entrées invalides indépendamment de l’intention de leur origine lorsque cela relève de ses contrats.

Le threat model distingue cependant la cause hostile de la robustesse opérationnelle afin de ne pas attribuer artificiellement une intention malveillante à toute défaillance.

### Modèle adverse principal

Le threat model initial ne définit pas plusieurs profils d’attaquants indépendants tels qu’un attaquant réseau, un administrateur malveillant, un attaquant local ou un acteur de supply chain.

Le modèle principal considère un acteur hostile capable d’influencer les entrées externes auxquelles il dispose effectivement d’un accès.

Les capacités précises nécessaires à chaque menace pourront ensuite être référencées explicitement.

Par exemple :

```text
menace réseau
→ AC1 + AC4

évasion temporelle
→ AC5 + AC6

PCAP hostile
→ AC7

entrée hostile via une interface
→ AC8
```

Cette approche évite de donner implicitement toutes les capacités possibles à un unique attaquant omnipotent.

Si une évolution future introduit de nouvelles frontières de confiance, des plugins tiers, plusieurs utilisateurs avec des privilèges distincts, des composants distribués ou une exposition plus large, de nouveaux profils adverses pourront être introduits explicitement.

### Portée de 0.5.3

Cette étape définit un attaquant capable de contrôler ou d’influencer les entrées externes accessibles à NetGuard, notamment le trafic réseau, sa temporalité, son volume et sa cardinalité, les PCAP fournis et les requêtes adressées aux interfaces exposées. Elle suppose également que l’attaquant peut connaître le fonctionnement public du système et adapter son comportement aux règles de détection, sans lui accorder par défaut une compromission complète de l’hôte, un accès arbitraire aux ressources internes ou le contrôle de l’environnement d’exécution.


## Hypothèses de confiance — 0.5.4

Cette section définit les hypothèses de confiance nécessaires pour que NetGuard puisse fournir les garanties prévues par son architecture et son threat model.

Une hypothèse de confiance n’affirme pas qu’un composant est parfaitement sécurisé ni que toutes les informations qu’il fournit sont vraies.

Elle signifie que certaines garanties de NetGuard dépendent d’une propriété que l’application ne peut pas établir entièrement par elle-même.

La distinction fondamentale est :

```text
hypothèse de confiance
≠
garantie fournie par NetGuard
```

Le principe général retenu est :

```text
confiance
=
confiance limitée
à une propriété précise

et non

confiance
=
tout ce qui provient
de ce composant est vrai et sûr
```

Une hypothèse de confiance ne doit donc jamais annuler les validations ou frontières de confiance définies précédemment.

### TA1 — Intégrité suffisante de l’hôte

NetGuard suppose que la machine sur laquelle il s’exécute n’est pas entièrement compromise.

Cette hypothèse concerne notamment l’intégrité suffisante de :

```text
système d’exploitation
kernel
mémoire du processus
environnement d’exécution
mécanismes nécessaires au lancement de NetGuard
```

Un attaquant disposant d’un contrôle complet de l’hôte pourrait notamment :

```text
modifier les observations
changer la configuration
altérer les règles
falsifier les résultats
lire les secrets
désactiver des composants
modifier les logs
arrêter le processus
```

Dans cette situation, les mécanismes de validation internes à NetGuard ne peuvent pas rétablir à eux seuls une frontière de sécurité fiable.

L’hypothèse porte sur une intégrité suffisante de l’environnement pour permettre l’exécution correcte de NetGuard.

Elle ne signifie pas :

```text
l’hôte est parfaitement sécurisé
```

La résistance à une compromission complète de l’hôte n’est pas une garantie de NetGuard V1.

### TA2 — Intégrité du code NetGuard exécuté

NetGuard suppose que le code réellement exécuté correspond à la version que l’opérateur légitime souhaitait utiliser.

Cette hypothèse concerne notamment :

```text
code NetGuard
modules chargés
package installé
artefacts nécessaires à l’exécution
```

Une modification malveillante préalable du programme pourrait directement changer :

```text
normalisation
invariants
détecteurs
gestion des erreurs
persistance
présentation des résultats
observabilité
```

Le threat model applicatif ne suppose donc pas que NetGuard puisse détecter ou neutraliser arbitrairement sa propre modification avant exécution.

Cette hypothèse reste distincte de l’intégrité complète de l’hôte.

Par exemple, un package ou un artefact logiciel compromis peut modifier le comportement de NetGuard sans impliquer nécessairement une compromission préalable du kernel.

NetGuard V1 ne définit pas à cette étape son propre mécanisme de signature ou de vérification cryptographique du code exécuté.

### TA3 — Dépendances tierces suffisamment fiables

NetGuard suppose que les dépendances techniques utilisées respectent suffisamment leurs contrats documentés pour permettre le fonctionnement attendu du système.

Cela peut notamment concerner :

```text
runtime Python
bibliothèques de capture
parsers
drivers
bibliothèques de persistance
frameworks futurs
```

Cette confiance concerne le comportement technique de la dépendance.

Elle ne transforme pas les données traitées par cette dépendance en informations métier automatiquement fiables.

La distinction reste :

```text
bibliothèque suffisamment fiable
≠
sortie de bibliothèque
automatiquement fiable
```

Par exemple, une bibliothèque de parsing peut fonctionner correctement tout en retournant une représentation issue d’un paquet hostile.

Le chemin reste donc :

```text
dépendance technique
        ↓
représentation technique
        ↓
adaptation / validation
        ↓
modèle NetGuard
```

Les frontières de validation définies précédemment restent applicables.

### TA4 — Source de capture fidèle aux garanties qu’elle annonce

NetGuard suppose que la source de capture représente correctement les données qu’elle affirme avoir capturées dans les limites de ses propres garanties.

Cette hypothèse permet à NetGuard de traiter une observation comme provenant effectivement de la source déclarée.

Elle ne signifie pas que la source de capture :

```text
voit tout le trafic
ne perd jamais de paquets
connaît la réalité complète du réseau
authentifie les émetteurs
garantit l’identité des machines
dispose d’une visibilité parfaite
```

La distinction est :

```text
source de capture techniquement fidèle
≠
source de capture omnisciente
```

Les pertes, limitations ou caractéristiques connues de la source doivent être prises en compte lorsque leur connaissance est nécessaire aux garanties fournies.

Cette hypothèse n’annule pas la frontière entre le trafic réseau non fiable et NetGuard.

Un paquet correctement transmis par la source de capture peut toujours contenir des informations hostiles, trompeuses ou malformées.

### TA5 — Position d’observation pertinente pour l’analyse recherchée

NetGuard suppose que la source de capture choisie possède une visibilité suffisamment pertinente pour l’objectif de surveillance recherché.

NetGuard ne peut analyser que les événements qu’il est effectivement en mesure d’observer.

Le principe est :

```text
activité réseau existante
≠
activité nécessairement visible
par NetGuard
```

La visibilité dépend notamment :

```text
de la position du capteur
de l’interface choisie
de la topologie réseau
du trafic effectivement accessible
des mécanismes de capture
du contexte de déploiement
```

NetGuard ne suppose pas une visibilité totale du réseau.

La relation attendue est plutôt :

```text
qualité et couverture de la détection
dépendent de la visibilité disponible
```

Une activité située hors du périmètre observable ne peut pas être détectée uniquement par l’analyse du trafic visible.

Le choix d’une position d’observation adaptée fait donc partie des hypothèses nécessaires à l’utilisation correcte du système.

### TA6 — Sources temporelles suffisamment correctes pour les garanties utilisées

NetGuard suppose que les sources temporelles dont dépend une analyse possèdent une qualité suffisante pour les garanties temporelles réellement utilisées.

Cette hypothèse ne signifie pas :

```text
synchronisation parfaite
absence totale de dérive
timestamps toujours exacts
```

Le modèle conserve les distinctions :

```text
temps d’observation
≠
temps de traitement
≠
horloge système
```

ainsi que :

```text
timestamp valide
≠
timestamp nécessairement vrai
```

Dans un mode live, certaines opérations techniques peuvent dépendre de l’horloge de l’hôte.

Dans un replay PCAP, les timestamps présents dans le fichier font partie des données d’entrée et peuvent être incorrects, inhabituels ou hostiles.

Les détecteurs doivent utiliser explicitement la notion de temps appropriée à leur contrat.

La validité syntaxique d’un timestamp ne suffit donc pas à établir la fiabilité de son origine.

### TA7 — Configuration approuvée fournie par une autorité légitime

NetGuard suppose que la configuration destinée à contrôler son fonctionnement provient d’une autorité légitime dans le contexte de déploiement.

NetGuard reste responsable de vérifier les propriétés qu’il est capable de valider, telles que :

```text
types
formats
plages autorisées
invariants
clés reconnues
cohérence structurelle
```

Mais la validation ne permet pas nécessairement de déterminer si une valeur techniquement valide correspond réellement à l’intention de l’opérateur.

Par exemple :

```text
threshold = 50000
```

peut être parfaitement valide selon le type et la plage autorisée tout en produisant un comportement analytique très différent de celui attendu.

La distinction est donc :

```text
configuration valide
≠
configuration voulue
```

Le processus de déploiement doit garantir que les personnes ou systèmes autorisés contrôlent les sources de configuration appropriées.

NetGuard ne doit toutefois pas utiliser cette hypothèse pour ignorer la validation des valeurs reçues.

### TA8 — Secrets initialement provisionnés de manière sûre

Lorsqu’un mode de déploiement nécessite des secrets techniques, NetGuard suppose que ceux-ci lui sont initialement fournis par un mécanisme approprié au contexte.

Cela peut notamment concerner :

```text
credentials
tokens
clés
secrets d’intégration
```

NetGuard ne peut pas restaurer la confidentialité d’un secret déjà compromis avant son utilisation.

La séparation des responsabilités est :

```text
provisionnement initial sûr
→ hypothèse environnementale

minimisation de l’exposition
pendant l’utilisation
→ responsabilité NetGuard
```

NetGuard doit notamment éviter de propager inutilement ces secrets dans :

```text
Core
DetectionResult
Evidence
Alert
logs
métriques
réponses d’interface
messages de diagnostic
```

Cette hypothèse ne dispense donc pas NetGuard de protéger les secrets une fois qu’ils lui ont été confiés.

### TA9 — Stockage respectant les garanties techniques utilisées

NetGuard suppose que le système de stockage utilisé respecte les garanties techniques sur lesquelles l’adaptateur de persistance s’appuie.

Selon la technologie future, cela peut notamment concerner :

```text
écriture
lecture
atomicité demandée
transactions utilisées
contraintes effectivement configurées
signalement des erreurs
durabilité attendue
```

NetGuard reste responsable de :

```text
la transformation domaine → stockage
la transformation stockage → domaine
la gestion des erreurs de persistance
la validation nécessaire lors de la reconstruction
```

Faire confiance au moteur de stockage ne signifie pas faire confiance aveuglément à chaque donnée présente dans celui-ci.

La distinction reste :

```text
stockage techniquement fiable
≠
chaque donnée stockée
automatiquement valide
pour le modèle courant
```

Une ancienne donnée, une migration incorrecte ou une corruption peuvent toujours produire une représentation incompatible avec les invariants actuels.

La frontière de confiance entre persistance et domaine reste donc applicable.

### TA10 — Exposition des interfaces cohérente avec leurs contrôles d’accès

NetGuard suppose que l’exposition d’une interface est cohérente avec les mécanismes de contrôle d’accès effectivement fournis par cette interface et par son environnement de déploiement.

Une interface ne doit pas être considérée comme sûre uniquement parce qu’elle se trouve sur un réseau qualifié d’interne.

La relation suivante n’est pas admise :

```text
réseau interne
=
réseau automatiquement fiable
```

Lorsqu’une capacité NetGuard ne possède pas elle-même un mécanisme suffisant d’authentification ou d’autorisation, son déploiement doit limiter son accessibilité conformément au modèle prévu.

Cela peut notamment concerner :

```text
adresse d’écoute
interfaces réseau exposées
filtrage environnemental
isolation du service
permissions locales
```

Cette hypothèse permet de ne pas imposer prématurément une technologie particulière telle que :

```text
OAuth
JWT
reverse proxy spécifique
mécanisme IAM particulier
```

tout en interdisant de supposer qu’une interface non protégée peut être exposée arbitrairement sans conséquence sur le threat model.

Si le mode d’exposition évolue, les hypothèses et contrôles d’accès devront être réévalués.

### TA11 — Opérateur légitime non hostile

Le modèle adverse principal de NetGuard V1 suppose que l’opérateur disposant légitimement des privilèges nécessaires à l’administration du système n’utilise pas volontairement ces privilèges pour compromettre NetGuard.

Cette hypothèse ne signifie pas que l’opérateur ne peut pas commettre d’erreur.

Il peut notamment :

```text
choisir une mauvaise interface
fournir un fichier incorrect
configurer une valeur inadéquate
déployer NetGuard dans un contexte inadapté
mal interpréter une Alert
```

NetGuard doit rester robuste face aux erreurs qu’il est raisonnablement capable de détecter ou de contenir.

La distinction reste :

```text
erreur opérateur
≠
opérateur malveillant
```

Un administrateur hostile disposant d’un contrôle complet de l’hôte, du code, de la configuration et des secrets posséderait des capacités largement supérieures à celles de l’attaquant principal défini pour NetGuard V1.

Un tel scénario relève d’une extension du threat model ou d’une compromission préalable de l’environnement.

### Confiances explicitement non accordées

Certaines propriétés ne doivent pas devenir implicitement des hypothèses de confiance.

NetGuard ne suppose notamment pas :

```text
que le réseau est fiable
que le trafic interne est honnête
qu’un PCAP local est fiable
qu’une adresse réseau représente une identité authentifiée
que la capture possède une visibilité totale
qu’aucun paquet n’est jamais perdu
que chaque timestamp reçu est exact
que chaque donnée persistée est valide
que toute configuration valide correspond à l’intention de l’opérateur
que toute interface interne est inaccessible à un attaquant
que toute dépendance tierce transforme ses entrées en données métier fiables
```

En particulier :

```text
réseau interne
≠
réseau de confiance

PCAP local
≠
PCAP de confiance

donnée persistée
≠
vérité métier

donnée validée
≠
information authentifiée
```

Ces exclusions empêchent les hypothèses environnementales d’annuler les frontières de confiance établies précédemment.

### Limitation de la confiance

Une même composante peut être considérée comme fiable pour une propriété et non fiable pour une autre.

Par exemple :

```text
source de capture
→ suffisamment fiable
   pour transmettre ce qu’elle a capturé

mais

trafic transmis
→ toujours non fiable
   quant à son contenu
```

De même :

```text
stockage
→ suffisamment fiable
   pour fournir les garanties techniques demandées

mais

donnée relue
→ toujours soumise
   au contrat de reconstruction applicable
```

Et :

```text
opérateur légitime
→ autorisé à fournir la configuration

mais

configuration fournie
→ toujours validée
   avant utilisation
```

Le principe transversal est donc :

```text
faire confiance à un composant
pour une propriété précise

ne signifie jamais

faire confiance à toutes les données,
actions ou affirmations
provenant de ce composant
```

### Relation avec le modèle adverse

Les hypothèses de confiance complètent les capacités de l’attaquant sans les annuler.

Le modèle résultant est :

```text
entrées externes
potentiellement hostiles
        ↓
frontières de validation
        ↓
NetGuard
        ↓
exécution dans un environnement
suffisamment intègre
```

Ainsi :

```text
TA3
dépendance suffisamment fiable

n’annule pas

TB10
représentation technique
adaptée et validée
```

De même :

```text
TA4
source de capture fidèle
à ses garanties

n’annule pas

TB1
trafic réseau non fiable
```

Et :

```text
TA9
stockage respectant
ses garanties techniques

n’annule pas

TB7
donnée persistée
non automatiquement valide
```

Enfin :

```text
TA11
opérateur légitime

n’annule pas

TB4
configuration externe
validée avant utilisation
```

Cette séparation permet à NetGuard de dépendre raisonnablement de son environnement sans transformer cette dépendance en confiance universelle.

### Portée de 0.5.4

Cette étape définit les hypothèses environnementales nécessaires aux garanties de NetGuard V1 : intégrité suffisante de l’hôte et du code exécuté, fiabilité limitée des dépendances et de la capture, visibilité adaptée au contexte de surveillance, qualité suffisante des sources temporelles, provenance légitime de la configuration, provisionnement sûr des secrets, garanties techniques du stockage, exposition maîtrisée des interfaces et opérateur légitime non hostile. Chaque confiance reste limitée à une propriété précise et ne supprime ni les validations, ni les frontières de confiance, ni le caractère potentiellement hostile des entrées externes.


## Menaces principales — 0.5.5

Cette section identifie les principales menaces applicables à NetGuard V1 à partir des actifs à protéger, des frontières de confiance, des capacités de l’attaquant et des hypothèses de confiance définis précédemment.

Le modèle utilisé est :

```text
Actifs A1–A12
      +
Frontières TB1–TB10
      +
Capacités AC1–AC10
      +
Hypothèses TA1–TA11
      ↓
Menaces T01–T20
```

Une menace décrit un scénario susceptible d’affecter une propriété que NetGuard cherche à préserver.

La distinction reste :

```text
capacité de l’attaquant
≠
menace

menace
≠
vulnérabilité démontrée

menace
≠
incident confirmé
```

Certaines menaces correspondent à des actions directement hostiles contre le système. D’autres représentent des possibilités d’évasion, des dégradations analytiques ou des erreurs d’interprétation qu’un attaquant peut exploiter.

Les identifiants `T01` à `T20` constituent des références stables destinées à relier ultérieurement chaque menace aux composants concernés, aux mesures de réduction du risque, aux tests pertinents et aux risques résiduels.

Aucun score numérique de risque n’est attribué à cette étape. La probabilité et l’impact précis d’une menace dépendent notamment du contexte de déploiement, de l’exposition réelle des interfaces, des ressources disponibles et de la topologie réseau.

### T01 — Falsification ou tromperie sur l’identité réseau

Un attaquant capable de générer du trafic contrôlé et de produire des informations réseau trompeuses peut chercher à faire apparaître une observation comme provenant d’une entité qui n’est pas nécessairement son origine réelle.

Cette menace s’appuie principalement sur :

```text
AC1
AC2
```

Par exemple :

```text
adresse source observée = X
```

ne permet pas de conclure :

```text
identité réelle de l’attaquant = X
```

La menace ne réside donc pas uniquement dans la possibilité de falsifier certaines informations réseau.

Elle existe également si NetGuard transforme une propriété observée en affirmation d’identité plus forte que ce que l’observation permet réellement d’établir.

Les actifs principalement concernés sont :

```text
A1 — intégrité des observations normalisées
A3 — intégrité des conclusions de détection
A4 — intégrité et explicabilité des Evidence et Alert
```

Le principe applicable reste :

```text
identifiant réseau observé
≠
identité authentifiée
```

### T02 — Entrée malformée exploitant la capture, le parsing ou la normalisation

Un attaquant peut produire une entrée réseau malformée, inhabituelle ou spécialement construite afin d’exercer les limites des composants situés avant ou pendant la normalisation.

Cette menace s’appuie principalement sur :

```text
AC3
AC10
```

et peut également être rencontrée dans le contexte d’un PCAP hostile via `AC7`.

Les conséquences recherchées peuvent notamment être :

```text
exception non maîtrisée
crash
état incohérent
consommation excessive de ressources
mauvaise interprétation
normalisation incorrecte
```

Le chemin concerné peut être représenté par :

```text
entrée hostile
      ↓
capture / lecture
      ↓
parser
      ↓
adaptation
      ↓
normalisation
```

Deux conséquences doivent être distinguées.

La première est une défaillance visible :

```text
entrée malformée
→
échec ou indisponibilité
```

La seconde peut être plus dangereuse :

```text
entrée malformée
→
observation incorrecte
→
acceptation silencieuse
```

Les actifs principalement concernés sont :

```text
A1
A10
A11
A12
```

Une entrée invalide ne doit pas être transformée artificiellement en observation valide par fabrication de valeurs manquantes ou correction silencieuse de sa sémantique.

### T03 — Déni de service par volume

Un attaquant peut générer une quantité de trafic ou d’entrées supérieure à la capacité de traitement disponible.

Cette menace s’appuie principalement sur :

```text
AC4
AC10
```

Le threat model ne suppose pas que NetGuard puisse absorber une charge arbitrairement élevée sans perte ni dégradation.

La menace apparaît lorsque la surcharge conduit à une consommation non bornée ou à une dégradation non maîtrisée.

Par exemple :

```text
trafic massif
      ↓
accumulation dans les buffers
      ↓
croissance mémoire
      ↓
épuisement des ressources
      ↓
crash
```

Une autre forme importante est :

```text
trafic massif
      ↓
pertes
      ↓
absence de signal opérationnel
      ↓
illusion d’une analyse complète
```

Les actifs principalement concernés sont :

```text
A10 — disponibilité et capacité du pipeline
A11 — disponibilité des capacités opérationnelles critiques
A12 — observabilité des dégradations significatives
```

Les conséquences peuvent également affecter indirectement `A3` et `A4` si les pertes modifient les informations disponibles pour les détecteurs.

### T04 — Déni de service par explosion de cardinalité

Un attaquant peut exercer une pression importante sur NetGuard sans nécessairement produire un volume brut extrêmement élevé.

Il peut chercher à provoquer la création d’un grand nombre de clés analytiques distinctes.

Cette menace s’appuie principalement sur :

```text
AC4
AC10
```

Elle peut notamment concerner :

```text
adresses différentes
ports différents
flows différents
scopes différents
clés de regroupement différentes
combinaisons uniques de propriétés
```

La distinction avec `T03` est importante :

```text
fort volume
≠
forte cardinalité
```

Par exemple :

```text
1 000 000 observations
sur une seule clé
```

et :

```text
1 000 000 observations
sur 1 000 000 clés
```

peuvent avoir des conséquences très différentes sur les structures d’état.

Une cardinalité non bornée pourrait conduire à :

```text
création massive d’états
      ↓
croissance mémoire
      ↓
épuisement des ressources
```

Les actifs principalement concernés sont :

```text
A2 — intégrité et bornage de l’état analytique
A10
A11
```

### T05 — Empoisonnement de l’état analytique

Un attaquant peut produire des observations destinées à influencer volontairement l’état maintenu par un détecteur.

Cette menace s’appuie notamment sur :

```text
AC1
AC2
AC4
AC5
AC6
```

Le simple fait qu’un trafic influence un état analytique n’est pas une anomalie : cette influence fait partie du fonctionnement normal d’un détecteur stateful.

La menace apparaît lorsque l’attaquant exploite cette propriété afin de :

```text
polluer des agrégats
consommer les capacités d’état
provoquer des regroupements trompeurs
influencer le contexte d’observations ultérieures
forcer des évictions
contaminer un état qui ne devrait pas être partagé
```

Une mauvaise définition des clés de regroupement pourrait notamment permettre à des observations appartenant à des contextes différents d’influencer le même état.

Les actifs principalement concernés sont :

```text
A2
A3
A4
```

Cette menace justifie notamment l’importance de l’isolation des états, de leurs propriétaires explicites et de leurs règles de regroupement déterministes.

### T06 — Évasion par manipulation temporelle

Un attaquant capable de contrôler partiellement le timing de son activité et de connaître ou déduire les règles de détection peut chercher à organiser ses actions afin de rester hors des conditions temporelles d’une règle.

Cette menace s’appuie principalement sur :

```text
AC5
AC6
```

Par exemple, pour une règle conceptuelle :

```text
20 événements
dans une fenêtre de 60 secondes
```

un attaquant pourrait chercher à répartir son activité autour des limites de la fenêtre.

La menace peut notamment exploiter :

```text
seuils temporels
expiration d’état
frontières de fenêtres
rythme d’émission
périodes de silence
```

Une telle évasion n’implique pas nécessairement une erreur d’implémentation.

Une règle déterministe possède nécessairement un domaine dans lequel elle produit ou non un résultat.

La menace correspond donc à la possibilité d’adapter une activité hostile pour rester en dehors des conditions analytiques observées.

Les actifs principalement concernés sont :

```text
A3
A4
```

### T07 — Évasion par répartition de l’activité

Un attaquant peut chercher à répartir son activité entre plusieurs clés analytiques afin qu’aucun état individuel n’atteigne les conditions nécessaires au déclenchement d’une règle.

Cette menace s’appuie principalement sur :

```text
AC1
AC2
AC6
```

Selon les capacités réelles de l’attaquant, la répartition peut concerner :

```text
plusieurs sources
plusieurs destinations
plusieurs ports
plusieurs scopes
plusieurs caractéristiques observables
```

Le scénario général est :

```text
activité hostile globale
        ↓
répartition entre plusieurs états
        ↓
aucun état individuel
ne franchit le seuil
```

Cette menace reste distincte de `T06`.

```text
T06
→ répartition dans le temps

T07
→ répartition entre les dimensions
   de regroupement analytique
```

Les actifs principalement concernés sont :

```text
A2
A3
A4
```

### T08 — Exploitation des limites de visibilité

Un attaquant peut réaliser une activité située totalement ou partiellement en dehors du trafic observable par NetGuard.

Cette menace est liée à l’hypothèse `TA5`.

NetGuard ne possède pas nécessairement une visibilité complète sur le réseau surveillé.

Une activité peut notamment être :

```text
hors du segment observé
sur une interface non surveillée
sur un chemin réseau non visible
absente des données réellement capturées
```

Le principe reste :

```text
activité existante
≠
activité nécessairement observable
```

L’absence d’observation ne constitue donc pas une preuve d’absence d’activité hostile.

La menace devient particulièrement importante si une limitation de visibilité est transformée en affirmation excessive sur l’état de sécurité du réseau.

Les actifs principalement concernés sont :

```text
A3
A4
```

Cette menace représente également une limite fondamentale qui devra être explicitée dans les risques résiduels et les non-garanties.

### T09 — Exploitation des pertes et saturations pour réduire la détection

Un attaquant peut chercher à provoquer ou exploiter une dégradation technique afin de réduire la quantité d’informations effectivement disponible pour l’analyse.

Cette menace est liée notamment à :

```text
AC4
AC6
AC10
```

Elle se distingue de `T03`.

`T03` concerne principalement la disponibilité du système.

`T09` concerne les conséquences analytiques d’une dégradation technique.

Par exemple :

```text
activité réelle
= 25 observations pertinentes

5 observations perdues
pendant une saturation

activité analysée
= 20 observations
```

La conséquence générale est :

```text
dégradation technique
        ↓
perte ou éviction d’informations
        ↓
dégradation analytique
```

NetGuard ne doit pas prétendre reconstruire des observations qu’il n’a jamais reçues.

En revanche, une perte connue ou une saturation significative ne doit pas être silencieusement assimilée à une analyse complète.

Les actifs principalement concernés sont :

```text
A2
A3
A10
A12
```

### T10 — PCAP hostile

Un fichier PCAP fourni à NetGuard peut être spécialement construit afin d’exercer les limites de la chaîne de lecture et d’analyse.

Cette menace s’appuie principalement sur :

```text
AC7
AC10
```

L’attaquant peut notamment contrôler :

```text
taille du fichier
nombre de paquets
contenu des paquets
timestamps
ordre
structures réseau
protocoles
valeurs inhabituelles
```

Les conséquences recherchées peuvent inclure :

```text
crash
consommation excessive
erreur de parsing
normalisation incorrecte
résultat incohérent
comportement non déterministe
```

Cette menace possède des recouvrements avec `T02`, mais le PCAP constitue une surface d’entrée suffisamment importante pour être considéré séparément.

La distinction est :

```text
T02
→ entrée malformée ou inhabituelle
   traversant la chaîne d’ingestion

T10
→ fichier PCAP hostile considéré
   comme artefact d’entrée complet
```

Le caractère local d’un fichier ne constitue pas une garantie de confiance.

```text
PCAP local
≠
PCAP fiable
```

Les actifs principalement concernés sont :

```text
A1
A2
A3
A10
A11
```

### T11 — Altération de la configuration analytique

Un acteur disposant d’un accès suffisant à une source de configuration analytique peut chercher à modifier le comportement des détecteurs.

Cette menace affecte directement `A5`.

Elle peut notamment prendre la forme de :

```text
modification d’un seuil
modification d’une fenêtre
désactivation d’un détecteur
modification d’un paramètre analytique
modification d’un regroupement configurable
```

Par exemple :

```text
threshold = 20
```

pourrait être remplacé par :

```text
threshold = 50000
```

Le système pourrait alors continuer à fonctionner techniquement tout en produisant un comportement analytique profondément différent.

La menace peut donc être silencieuse du point de vue de la disponibilité.

Les actifs principalement concernés sont :

```text
A5
A3
A4
```

Cette menace nécessite un accès à la source de configuration ou une compromission préalable appropriée.

Elle n’est pas attribuée automatiquement à un attaquant disposant uniquement de capacités réseau telles que `AC1`.

### T12 — Altération de la configuration technique

Un acteur disposant d’un accès suffisant à la configuration technique peut chercher à modifier les conditions d’exécution de NetGuard.

Cette menace affecte directement `A6`.

Elle peut notamment concerner :

```text
taille des buffers
limites de ressources
interface de capture
paramètres de persistance
adresse d’écoute
activation de composants techniques
```

Les conséquences peuvent être :

```text
pertes supplémentaires
indisponibilité
mauvaise source de capture
exposition involontaire d’une interface
dégradation analytique indirecte
```

Les actifs principalement concernés sont :

```text
A6
A10
A11
```

et indirectement :

```text
A2
A3
A12
```

`T11` et `T12` restent distinctes afin de préserver la séparation entre configuration analytique et configuration technique.

### T13 — Altération, corruption ou mauvaise reconstruction de l’historique

Les données persistées peuvent être altérées, corrompues, mal migrées ou reconstruites avec une sémantique incompatible avec leur signification d’origine.

Cette menace concerne principalement :

```text
A4
A8
```

Elle peut résulter d’une action hostile lorsque l’attaquant possède un accès approprié au stockage, mais également d’une défaillance technique ou d’une migration incorrecte.

Les conséquences peuvent notamment être :

```text
Alert historique modifiée
Evidence incohérente
perte de données
mauvaise interprétation d’un ancien résultat
reconstruction incompatible avec les invariants courants
```

Une Alert historique ne doit notamment pas acquérir silencieusement une signification différente de celle qu’elle possédait lors de sa création.

La distinction reste :

```text
donnée persistée
≠
vérité métier automatiquement valide
```

### T14 — Exposition d’informations réseau sensibles

NetGuard collecte, calcule et conserve des informations susceptibles de révéler des caractéristiques importantes du réseau surveillé.

Cela peut notamment inclure :

```text
adresses
machines observées
ports
protocoles
relations entre systèmes
activité temporelle
résultats de détection
Alert
Evidence
```

Un accès non autorisé à ces informations pourrait permettre à un acteur hostile d’utiliser NetGuard comme source indirecte de reconnaissance.

Les actifs principalement concernés sont :

```text
A7 — confidentialité des données réseau collectées
A8 — confidentialité des données persistées
```

Les frontières particulièrement concernées sont notamment :

```text
TB8 — domaine vers interface externe
TB9 — composants vers observabilité
```

La minimisation des données collectées et exposées constitue donc une propriété de sécurité et pas uniquement une optimisation de stockage.

### T15 — Exposition de secrets techniques

Un secret technique utilisé par NetGuard peut être exposé involontairement par un composant du système.

Cette menace concerne principalement :

```text
A9
```

Les chemins possibles peuvent notamment inclure :

```text
logs
messages d’erreur
stack traces
réponses d’API
diagnostics
affichage de configuration
métriques
```

Une fuite peut ensuite permettre un accès à une ressource externe ou interne protégée par ce secret.

Le principe reste :

```text
secret accessible au processus
≠
secret acceptable dans
les sorties du processus
```

Les secrets ne doivent notamment pas devenir des données ordinaires de :

```text
DetectionResult
Evidence
Alert
observabilité
```

### T16 — Abus d’une interface exposée

Un acteur disposant d’un accès à une interface NetGuard peut chercher à l’utiliser d’une manière hostile ou pathologique.

Cette menace s’appuie principalement sur :

```text
AC8
AC10
```

Les entrées peuvent notamment inclure :

```text
requêtes répétées
payloads volumineux
filtres pathologiques
valeurs limites
identifiants inexistants
types inattendus
entrées malformées
opérations non autorisées
```

Deux propriétés doivent rester distinctes :

```text
validation de l’entrée
≠
autorisation de l’opération
```

Une requête techniquement valide n’est pas nécessairement une opération que son émetteur doit être autorisé à effectuer.

Les actifs potentiellement concernés sont :

```text
A7
A8
A10
A11
```

et, si de futures interfaces permettent de modifier des paramètres :

```text
A5
A6
```

L’exposition réelle d’une interface dépend du mode de déploiement et doit rester cohérente avec `TA10`.

### T17 — Défaillance confinée devenue silencieuse

NetGuard peut chercher à isoler une défaillance afin d’éviter qu’un composant défectueux provoque l’arrêt complet du système.

Ce confinement est souhaitable lorsqu’il est compatible avec le contrat du composant.

Cependant :

```text
confinement
≠
silence
```

Par exemple :

```text
Detector A
→ fonctionne

Detector B
→ échoue

pipeline
→ continue
```

peut être acceptable.

Mais si la défaillance de `Detector B` n’est pas rendue suffisamment observable :

```text
détecteur indisponible
      ↓
pipeline toujours actif
      ↓
apparence de fonctionnement complet
```

le système peut donner une représentation trompeuse de ses capacités opérationnelles.

Les actifs principalement concernés sont :

```text
A11
A12
```

et indirectement :

```text
A3
```

La disponibilité partielle doit donc pouvoir être distinguée d’un fonctionnement nominal complet.

### T18 — Manipulation ou saturation de l’observabilité par des données hostiles

Des données provenant d’une source non fiable peuvent influencer les informations envoyées vers les mécanismes d’observabilité.

Cette menace peut s’appuyer sur :

```text
AC1
AC2
AC3
AC4
AC10
```

Une utilisation non maîtrisée de valeurs externes dans les logs, métriques ou diagnostics peut notamment provoquer :

```text
log injection
volume excessif de logs
cardinalité excessive de métriques
ambiguïté des diagnostics
exposition de données réseau
consommation excessive de ressources
```

Par exemple :

```text
valeur réseau contrôlée
        ↓
label dynamique de métrique
        ↓
cardinalité non bornée
```

pourrait transformer l’observabilité elle-même en source de pression sur les ressources.

Les actifs principalement concernés sont :

```text
A12
A10
A7
```

Cette menace justifie que `TB9` soit considérée comme une véritable frontière de confiance.

### T19 — Confusion entre absence de détection et absence de menace

L’absence d’Alert ne constitue pas une preuve que le réseau est exempt d’activité hostile.

NetGuard peut produire :

```text
aucune Alert
```

pour plusieurs raisons différentes :

```text
aucune activité correspondant aux règles
activité hors visibilité
activité sous un seuil
activité répartie entre plusieurs états
activité organisée autour des fenêtres temporelles
observations perdues
état évincé
règle non applicable
règle désactivée
capacité opérationnelle dégradée
```

La menace apparaît si le système ou son interface transforme cette absence de résultat en affirmation plus forte :

```text
aucune Alert
→
réseau sûr
```

Cette conclusion n’est pas justifiée.

Les actifs principalement concernés sont :

```text
A3
A4
```

Le principe reste :

```text
absence de détection
≠
preuve d’absence de menace
```

### T20 — Confusion entre Alert et incident confirmé

Une Alert représente un résultat de suivi de sécurité produit à partir d’observations et d’une règle.

Elle ne constitue pas automatiquement une preuve qu’une attaque réelle a eu lieu.

La menace apparaît si une conclusion analytique est présentée avec une certitude supérieure à celle que les observations permettent réellement d’établir.

La relation incorrecte serait :

```text
Alert
=
incident confirmé
```

La relation correcte reste :

```text
Alert
→
résultat de sécurité
à examiner dans son contexte
```

Un comportement détecté peut notamment avoir une explication légitime ou ambiguë.

Les actifs principalement concernés sont :

```text
A3
A4
```

Cette menace prolonge l’invariant fondamental :

```text
réalité réseau
≠
ce que NetGuard observe
≠
ce que NetGuard calcule
≠
ce qu’une règle conclut
≠
la manière dont le résultat est suivi
```

### Relations entre les principales familles de menaces

Les menaces identifiées peuvent être regroupées conceptuellement afin de faciliter leur analyse ultérieure.

```text
T01–T02
→ intégrité et traitement des entrées

T03–T04
→ disponibilité et ressources

T05–T09
→ état, détection et limites analytiques

T10
→ entrée PCAP

T11–T13
→ configuration et persistance

T14–T16
→ confidentialité et interfaces

T17–T18
→ fonctionnement et observabilité

T19–T20
→ interprétation des résultats
```

Ces familles ne constituent pas des frontières étanches.

Une même menace peut affecter plusieurs propriétés du système.

Par exemple :

```text
saturation
→ disponibilité

mais aussi

saturation
→ pertes

puis

pertes
→ dégradation analytique
```

De même :

```text
exposition d’une interface
→ disponibilité

mais aussi

exposition d’une interface
→ confidentialité
```

Les relations entre menaces devront donc être conservées lors de l’analyse par composant.

### Menaces, limites analytiques et ruptures d’hypothèses

Toutes les menaces identifiées ne correspondent pas au même type de problème.

Certaines représentent des attaques contre une surface technique :

```text
T02
T03
T04
T10
T16
T18
```

D’autres représentent des possibilités d’évasion ou des limites inhérentes à une détection fondée sur des observations et des règles :

```text
T06
T07
T08
T09
```

D’autres encore concernent la manière dont les résultats sont interprétés :

```text
T19
T20
```

Enfin, certaines menaces telles que `T11`, `T12` ou `T13` peuvent nécessiter des capacités qui ne sont pas accordées par défaut à l’attaquant réseau principal.

Leur réalisation peut dépendre :

```text
d’un accès supplémentaire
d’une mauvaise exposition
d’une compromission préalable
d’une rupture d’hypothèse de confiance
```

Le fait qu’une menace soit documentée ne signifie donc pas que tous les attaquants du modèle possèdent automatiquement les capacités nécessaires pour la réaliser.

### Absence de score de risque arbitraire

Aucun score numérique de criticité, de probabilité ou de risque n’est fixé à cette étape.

Une notation telle que :

```text
T03 = 8.4 / 10
```

donnerait une précision artificielle sans disposer encore d’informations suffisantes sur :

```text
contexte de déploiement
ressources matérielles
topologie réseau
exposition réelle
volume normal attendu
données manipulées
contrôles environnementaux
```

Les identifiants `T01` à `T20` servent donc à assurer la traçabilité des menaces sans prétendre quantifier prématurément leur risque réel.

### Utilisation des catégories de menace génériques

Le threat model de NetGuard n’impose pas à cette étape qu’une menace appartienne artificiellement à une catégorie générique unique.

Des modèles tels que STRIDE peuvent être utilisés ultérieurement comme grille de contrôle afin de rechercher d’éventuels angles morts.

Ils ne remplacent cependant pas les menaces spécifiques au fonctionnement analytique de NetGuard.

Des scénarios tels que :

```text
empoisonnement d’état
évasion temporelle
évasion par répartition
confusion entre absence de détection
et absence de menace
```

doivent rester exprimés directement, même lorsqu’ils ne correspondent pas parfaitement à une catégorie générique unique.

### Traçabilité des menaces

Les identifiants de menace doivent permettre de construire progressivement une chaîne de traçabilité.

La forme recherchée est :

```text
menace
   ↓
composants concernés
   ↓
mesures de réduction
   ↓
tests pertinents
   ↓
risques résiduels
```

Par exemple :

```text
T04
↓
Network State / Detection Engine
↓
bornage des états
↓
tests de cardinalité et d’éviction
↓
risque résiduel sous surcharge extrême
```

Cette chaîne sera complétée dans les étapes suivantes du threat model sans modifier rétroactivement la signification des identifiants `T01` à `T20`.

### Portée de 0.5.5

Cette étape définit vingt menaces principales couvrant l’intégrité des entrées, la consommation de ressources, l’état analytique, les possibilités d’évasion, les limites de visibilité, les PCAP hostiles, la configuration, la persistance, la confidentialité, les interfaces, l’observabilité et l’interprétation des résultats. Ces menaces constituent désormais les scénarios de référence du threat model et pourront être reliées aux composants concernés, aux mesures de réduction du risque, aux tests de sécurité et aux risques résiduels.


## Analyse des menaces par composant — 0.5.6

Cette section projette les menaces `T01` à `T20` sur les principales responsabilités du pipeline NetGuard afin d’identifier où elles peuvent apparaître, se propager ou devenir observables.

L’objectif n’est pas encore de définir toutes les mesures de réduction du risque. Il s’agit d’établir la relation entre les menaces identifiées et l’architecture réelle du système.

La logique retenue est :

```text
T01–T20
   ↓
composants exposés
   ↓
responsabilités de sécurité
   ↓
propagation éventuelle
   ↓
conséquences sur le système
```

L’analyse suit les principales responsabilités fonctionnelles du pipeline :

```text
Capture / Ingestion
Normalization
Network State
Detection Engine
Alerting
Persistence
Interfaces
Observability
```

La couche Application conserve un rôle transversal d’orchestration et de gestion du lifecycle. La configuration et l’assemblage possèdent également une responsabilité transversale. Ces responsabilités sont analysées séparément des zones fonctionnelles du pipeline.

Une menace n’est pas nécessairement confinée au composant dans lequel elle apparaît initialement.

Par exemple :

```text
saturation de Capture
        ↓
perte d’observations
        ↓
Network State incomplet
        ↓
Detection Engine sous-informé
        ↓
résultat analytique différent
```

L’analyse par composant doit donc considérer à la fois l’exposition locale et les conséquences susceptibles de se propager aux étapes suivantes.

### Capture / Ingestion

La zone Capture / Ingestion constitue le premier point de contact avec les données réseau externes.

Elle comprend conceptuellement les mécanismes permettant de recevoir :

```text
trafic live
PCAP
autres sources d’observations futures
```

Les menaces particulièrement pertinentes sont :

```text
T02 — entrée malformée
T03 — déni de service par volume
T04 — explosion de cardinalité
T08 — limites de visibilité
T09 — pertes et saturations
T10 — PCAP hostile
```

La responsabilité de cette zone n’est pas de déterminer si le contenu observé représente la vérité du réseau.

Elle doit plutôt :

```text
recevoir une entrée potentiellement hostile
        ↓
préserver les informations nécessaires
        ↓
limiter les effets techniques d’une entrée invalide
        ↓
transmettre une représentation adaptée
à l’étape suivante
```

La capture ne doit donc pas transformer :

```text
paquet capturé
```

en :

```text
information réseau authentifiée
```

Le principe reste :

```text
capturé
≠
valide
≠
authentifié
≠
vrai
```

Les mécanismes de capture peuvent également connaître des pertes.

Une perte connue doit pouvoir être distinguée d’une observation normale.

La règle est :

```text
perte connue
→ rendre la dégradation observable lorsque possible

perte connue
≠
inventer les observations manquantes
```

NetGuard ne doit pas reconstruire arbitrairement ce qu’il n’a jamais observé.

Pour les PCAP, le caractère local du fichier ne change pas son statut de confiance.

```text
PCAP local
≠
PCAP fiable
```

La lecture d’un fichier doit donc rester une opération effectuée sur une entrée potentiellement hostile.

### Normalization

La normalisation constitue une frontière sémantique majeure du système.

Elle transforme une représentation provenant d’une technologie externe en représentation appartenant au modèle NetGuard.

Le passage conceptuel est :

```text
représentation technique externe
        ↓
adaptation
        ↓
validation des invariants applicables
        ↓
modèle domaine NetGuard
```

Les menaces particulièrement pertinentes sont :

```text
T01 — falsification ou tromperie sur l’identité réseau
T02 — entrée malformée
T10 — PCAP hostile
```

La responsabilité principale de la normalisation est de représenter fidèlement ce que NetGuard a effectivement observé sans lui attribuer une signification plus forte que celle que les données permettent d’établir.

Par exemple :

```text
source_ip = 192.0.2.10
```

peut devenir une adresse IP valide dans le modèle domaine.

Cette information ne doit cependant pas devenir implicitement :

```text
identité certaine de la machine responsable
```

La distinction reste :

```text
valeur syntaxiquement valide
≠
information authentifiée
```

La normalisation doit également éviter de fabriquer artificiellement des informations permettant de transformer une entrée invalide en observation apparemment valide.

Par exemple :

```text
information absente
≠
valeur fictive par défaut
```

lorsque l’absence possède une signification métier.

Cette zone protège donc le Core contre deux catégories de problèmes :

```text
données techniquement invalides

et

données techniquement valides
auxquelles une signification excessive
pourrait être attribuée
```

Une fois admise dans le Core, une observation doit respecter les invariants du modèle NetGuard, sans pour autant être considérée comme une preuve de vérité sur le réseau réel.

### Network State

Le Network State représente les états analytiques dérivés nécessaires aux traitements stateful.

Il constitue une zone particulièrement exposée aux menaces liées aux ressources, au regroupement et à l’influence volontaire des observations.

Les menaces particulièrement pertinentes sont :

```text
T03 — déni de service par volume
T04 — explosion de cardinalité
T05 — empoisonnement de l’état analytique
T06 — évasion temporelle
T07 — évasion par répartition
T09 — pertes et saturations
```

Un attaquant est naturellement capable d’influencer certains états analytiques par le trafic qu’il produit.

Cette influence n’est pas en elle-même une violation de sécurité.

Le fonctionnement attendu est :

```text
observation
→
transition d’état
```

La menace apparaît lorsque cette influence peut :

```text
dépasser le scope prévu
provoquer une croissance non bornée
contaminer un autre état
contaminer un autre détecteur
violer un invariant
forcer des évictions excessives
produire une évolution non déterministe
```

Chaque état analytique doit donc conserver des propriétés explicites concernant notamment :

```text
propriétaire
regroupement
contenu
temps
capacité
saturation
expiration
éviction
transitions
```

Le bornage est une propriété essentielle.

```text
état analytique
→
borné dans les dimensions pertinentes
```

La limite peut concerner :

```text
nombre d’entrées
durée de conservation
cardinalité
mémoire
autres ressources pertinentes
```

Une éviction liée aux ressources doit également rester distincte d’une expiration métier normale.

```text
expiration
≠
éviction sous pression
```

Lorsque cette distinction influence la qualité de l’analyse ou l’état opérationnel, elle doit pouvoir rester observable.

L’isolation des états est également essentielle.

```text
état Detector A
≠
état Detector B
```

sauf contrat explicite définissant un état partagé.

Une défaillance ou saturation locale ne doit pas contaminer implicitement des états sans relation métier.

### Detection Engine

Le Detection Engine orchestre l’application des détecteurs aux observations et états pertinents.

Les détecteurs portent les règles métier de détection, tandis que le moteur coordonne leur exécution selon les contrats définis.

Les menaces particulièrement pertinentes sont :

```text
T05 — empoisonnement de l’état
T06 — évasion temporelle
T07 — évasion par répartition
T09 — pertes et saturations
T11 — altération de configuration analytique
T17 — défaillance confinée devenue silencieuse
T19 — absence de détection interprétée comme absence de menace
T20 — Alert interprétée comme incident confirmé
```

Le moteur peut être affecté par `T11` via la configuration analytique qui lui est fournie, sans être propriétaire de sa source ni constituer son point d’entrée. La responsabilité Configuration / assemblage assure la traçabilité principale de cette menace.

Le moteur doit préserver la distinction entre :

```text
entrée non éligible
absence de déclenchement
résultat positif
erreur du détecteur
```

Ces situations ne doivent pas être fusionnées en un état ambigu.

En particulier :

```text
aucun DetectionResult
```

peut signifier plusieurs choses différentes et ne constitue pas automatiquement une affirmation sur l’état réel du réseau.

Une règle peut également être contournée sans être incorrectement implémentée.

```text
activité non détectée
≠
bug du détecteur
```

Un détecteur déterministe possède un domaine de détection défini par :

```text
ses entrées
son état
sa configuration
ses regroupements
ses fenêtres
ses seuils
```

Une activité située hors de ce domaine peut ne pas produire de résultat.

Le moteur doit également gérer les défaillances des détecteurs selon une politique explicite.

Un scénario tel que :

```text
Detector A
→ fonctionne

Detector B
→ échoue

pipeline
→ continue
```

peut être acceptable si le contrat autorise le confinement.

Mais :

```text
confinement
≠
silence
```

Une défaillance confinée qui réduit les capacités de détection doit pouvoir être distinguée d’un fonctionnement nominal complet.

Enfin, l’échec d’un détecteur ne doit pas automatiquement invalider les résultats métier déjà produits correctement par d’autres détecteurs.

### Alerting

La zone Alerting transforme les conclusions analytiques pertinentes en objets de suivi de sécurité exploitables.

Les menaces particulièrement pertinentes sont :

```text
T01 — tromperie sur l’identité
T09 — dégradation analytique liée aux pertes
T11 — altération de configuration analytique
T19 — absence de détection surinterprétée
T20 — Alert assimilée à un incident confirmé
```

Cette zone doit préserver les distinctions fondamentales :

```text
NetworkObservation
≠
DetectionResult
≠
Evidence
≠
Alert
≠
incident confirmé
```

Une Alert doit rester suffisamment stable et autonome pour pouvoir être interprétée après la disparition de l’état mutable ayant participé à sa création.

Elle doit conserver les faits nécessaires à sa compréhension sans inventer de garanties supplémentaires.

Une formulation telle que :

```text
comportement correspondant
à la règle NG-NET-001 observé
```

peut être compatible avec le modèle.

Une formulation équivalente à :

```text
cette machine est certainement
un attaquant
```

nécessiterait une garantie beaucoup plus forte que celle fournie par une simple observation réseau et une règle déterministe.

L’Alert doit donc préserver la provenance et les faits utiles tout en limitant ses affirmations aux conclusions réellement justifiées.

Le principe reste :

```text
explicabilité
≠
certitude absolue
```

### Persistence

La persistance conserve certaines informations produites par NetGuard afin de permettre leur consultation ultérieure.

Les menaces particulièrement pertinentes sont :

```text
T13 — altération ou corruption de l’historique
T14 — exposition d’informations réseau sensibles
T15 — exposition de secrets techniques
```

La persistance n’est pas supposée stocker la configuration et n’est pas propriétaire de ses sources. Elle peut subir les effets d’une configuration technique altérée, mais le point principal de traçabilité de `T11` et `T12` reste Configuration / assemblage.

`T03` peut également devenir pertinente si la persistance constitue un goulot d’étranglement capable de provoquer une pression sur le pipeline.

Les deux directions de transformation doivent être analysées séparément.

À l’écriture :

```text
objet domaine
      ↓
mapping
      ↓
représentation persistée
```

Le mapping ne doit pas perdre silencieusement une information nécessaire à l’interprétation future de l’objet.

À la lecture :

```text
représentation persistée
      ↓
reconstruction
      ↓
objet domaine
```

La présence d’une donnée dans le stockage ne suffit pas à garantir qu’elle respecte les invariants du modèle courant.

```text
donnée présente en base
≠
objet domaine automatiquement valide
```

La reconstruction doit prendre en compte les contrats applicables, notamment lorsque les données proviennent :

```text
d’une ancienne version
d’une migration
d’un stockage partiellement corrompu
d’une modification externe
```

L’historique doit également préserver la signification originale des résultats.

Une évolution de schéma ne doit pas transformer silencieusement :

```text
ancienne Alert avec signification X
```

en :

```text
Alert interprétée avec
une nouvelle signification Y
```

sans mécanisme explicite permettant de préserver ou retracer cette évolution.

La persistance constitue également une surface de confidentialité.

Les données conservées doivent rester limitées à ce qui est nécessaire au fonctionnement et aux usages prévus de NetGuard.

### Interfaces

Les Interfaces représentent les points d’interaction entre NetGuard et des acteurs externes tels que :

```text
client API
CLI
frontend
autres consommateurs futurs
```

Les menaces particulièrement pertinentes sont :

```text
T03 — pression volumétrique
T14 — exposition d’informations réseau sensibles
T15 — exposition de secrets
T16 — abus d’une interface exposée
T19 — mauvaise interprétation de l’absence de détection
T20 — mauvaise interprétation d’une Alert
```

Une interface possède deux directions de sécurité distinctes.

En entrée :

```text
extérieur
   ↓
Interface
   ↓
Application / Core
```

En sortie :

```text
Core / Application
   ↓
Interface
   ↓
extérieur
```

En entrée, une interface doit notamment considérer :

```text
validation protocolaire
types
formats
tailles
valeurs limites
opérations demandées
autorisation lorsque nécessaire
```

La distinction fondamentale est :

```text
requête valide
≠
opération autorisée
```

Une requête correctement formée ne doit pas être considérée comme autorisée uniquement parce qu’elle respecte son format.

En sortie, l’interface doit contrôler ce qu’elle expose.

Le principe est :

```text
donnée disponible en interne
≠
donnée devant être exposée
```

Une réponse externe ne doit notamment pas divulguer inutilement :

```text
secrets
credentials
stack traces
exceptions techniques brutes
chemins locaux
configuration interne sensible
données réseau non nécessaires
```

L’interface doit également préserver la sémantique des résultats.

Elle ne doit pas transformer une absence d’Alert en garantie de sécurité ni une Alert en incident confirmé.

### Observability

L’observabilité permet de comprendre l’état opérationnel de NetGuard et certaines dégradations connues du pipeline.

Les menaces particulièrement pertinentes sont :

```text
T03 — saturation
T09 — pertes et dégradations analytiques
T14 — exposition d’informations réseau
T15 — exposition de secrets
T17 — défaillance confinée devenue silencieuse
T18 — manipulation ou saturation de l’observabilité
```

L’observabilité possède un double rôle.

Elle constitue :

```text
un mécanisme permettant
de détecter certaines dégradations
```

mais également :

```text
une surface susceptible
de recevoir des données hostiles
```

Elle doit pouvoir rendre visibles, lorsque cela est pertinent :

```text
drops connus
saturation
évictions significatives
défaillances confinées
dégradation du pipeline
échecs de composants
états opérationnels importants
```

Cependant :

```text
observable
≠
tout journaliser
```

Une donnée réseau non fiable ne doit pas pouvoir provoquer sans contrôle :

```text
explosion du volume de logs
cardinalité non bornée de métriques
injection de contenu ambigu
exposition de données sensibles
exposition de secrets
```

Les valeurs contrôlées par le réseau ne doivent notamment pas devenir par défaut des labels de métriques à cardinalité non bornée.

L’observabilité doit rester elle-même bornée et proportionnée aux besoins opérationnels.

Une défaillance de l’observabilité ne doit pas non plus modifier rétroactivement la validité d’un résultat métier correctement produit.

```text
échec de logging
≠
DetectionResult invalide
```

### Configuration / assemblage / Composition Root

La configuration et l’assemblage constituent une responsabilité transversale déjà définie par l’architecture.

Les sources externes de configuration franchissent `TB4`. Elles ne sont pas considérées comme valides avant parsing et validation.

Le chemin attendu est :

```text
sources externes de configuration
        ↓
parsing
        ↓
validation
        ↓
configuration structurée
        ↓
Composition Root
        ↓
injection dans les composants concernés
```

Cette responsabilité concerne principalement :

```text
T11 — altération de la configuration analytique
T12 — altération de la configuration technique
```

Elle protège notamment l’intégrité de `A5` et `A6` à la frontière `TB4`.

La distinction reste :

```text
configuration analytique
≠
configuration technique
```

Le Composition Root assemble les composants et leur injecte les configurations validées correspondant à leurs besoins. Le Core ne lit pas directement les fichiers, variables d’environnement, arguments CLI ou autres mécanismes techniques de configuration.

La validation établit la conformité au contrat, pas la vérité des données ni la légitimité de toute modification. Les accès nécessaires à une altération restent ceux définis par `T11`, `T12` et les hypothèses de confiance existantes ; aucune capacité supplémentaire n’est accordée à l’attaquant principal.

Une configuration altérée peut affecter plusieurs composants sans que ceux-ci soient propriétaires de sa source. Par exemple, une modification analytique peut affecter le Detection Engine ou Alerting ; une modification technique peut affecter la capture, la persistance ou le lifecycle.

Cette responsabilité ne suppose pas que la configuration soit stockée dans Persistence.

Selon le chemin considéré, elle peut également être concernée par :

```text
T15 — exposition de secrets techniques
T17 — défaillance confinée devenue silencieuse
```

Les secrets éventuellement présents dans certaines configurations techniques restent confinés aux composants techniques qui en ont besoin. Leur présence ne doit pas conduire à leur propagation vers le Core, les DetectionResult, Evidence, Alert, logs, métriques ou interfaces.

Une défaillance de parsing, de validation ou d’assemblage ne doit pas être masquée par un fonctionnement présenté comme nominal alors que les capacités attendues ne sont pas disponibles. Cette situation relève de `T17` lorsqu’un échec connu est confiné puis rendu silencieux.

Cette analyse ne choisit aucune technologie de configuration, de gestion des secrets ou d’authentification.

### Orchestration Application et lifecycle

La couche Application possède une responsabilité transversale dans l’orchestration des composants et la gestion du lifecycle.

Elle doit permettre de distinguer des états tels que :

```text
initialisation
démarrage
readiness
fonctionnement
dégradation
arrêt
échec
```

Cette distinction est particulièrement importante pour `T17`. L’Application et le lifecycle peuvent également être affectés par `T12` à travers une configuration technique altérée, sans devenir propriétaires de sa source. La traçabilité principale de cette entrée reste Configuration / assemblage.

Un processus vivant ne signifie pas nécessairement que toutes les capacités de NetGuard sont disponibles.

```text
liveness
≠
readiness
≠
état opérationnel nominal
```

Par exemple :

```text
process
→ vivant

capture
→ active

détecteur important
→ en échec
```

ne doit pas nécessairement être présenté comme :

```text
NetGuard
→ pleinement opérationnel
```

L’orchestration doit également définir les responsabilités concernant :

```text
démarrage des composants
arrêt contrôlé
propagation des échecs
confinement lorsque prévu
gestion des ressources
publication de l’état opérationnel
```

Le confinement d’une défaillance doit être une décision explicite et non la conséquence accidentelle d’une exception ignorée.

Inversement, toute défaillance locale ne doit pas nécessairement provoquer l’arrêt global du système.

La politique dépend du rôle du composant et des garanties qu’il est encore possible de fournir.

### Propagation inter-composants

Une menace peut changer de nature en traversant le pipeline.

Par exemple :

```text
T03
trafic massif
      ↓
Capture
      ↓
buffer saturé
      ↓
observations perdues
      ↓
Network State incomplet
      ↓
Detection Engine sous-informé
      ↓
absence éventuelle de DetectionResult
```

Une menace initialement liée à la disponibilité devient alors une menace affectant l’analyse.

Autre exemple :

```text
T01
information réseau trompeuse
      ↓
Normalization
      ↓
observation correctement représentée
      ↓
Detection Engine
      ↓
DetectionResult
      ↓
Alert
```

Dans ce second scénario, la présence d’une information trompeuse dans le trafic ne signifie pas nécessairement que NetGuard a échoué.

Si chaque composant conserve correctement la distinction entre :

```text
information observée
```

et :

```text
identité réellement prouvée
```

le système peut produire un résultat fidèle à ce qu’il sait réellement.

La menace devient effective lorsqu’une couche ajoute une affirmation qui n’est pas justifiée par les données disponibles.

Une troisième propagation importante est :

```text
T17
défaillance locale
      ↓
confinement
      ↓
pipeline toujours actif
      ↓
capacité réduite
      ↓
état opérationnel incorrectement présenté
```

La sécurité du pipeline dépend donc non seulement du confinement des défaillances, mais également de leur effet sur les garanties encore réellement disponibles.

### Dégradation technique et dégradation analytique

Une dégradation technique peut modifier la qualité de l’analyse sans rendre immédiatement le système indisponible.

La relation est :

```text
dégradation technique
        ↓
modification des données disponibles
        ↓
modification possible
du résultat analytique
```

Cela peut notamment résulter de :

```text
drops
évictions
saturation
défaillance d’un détecteur
perte d’un état
lecture partielle
```

NetGuard ne doit pas prétendre connaître exactement les conséquences d’informations qu’il n’a pas reçues.

Il doit cependant distinguer, lorsque cela est techniquement connu :

```text
analyse effectuée
dans des conditions nominales
```

de :

```text
analyse effectuée
pendant une dégradation connue
```

Cette distinction ne nécessite pas nécessairement d’attacher toutes les métriques opérationnelles à chaque Alert.

Elle impose seulement de ne pas masquer une dégradation connue lorsqu’elle affecte significativement les garanties opérationnelles du système.

### Matrice de traçabilité par zone

La matrice suivante synthétise les menaces particulièrement pertinentes pour les zones du pipeline et les responsabilités transversales. Les mentions d’effets propagés ne désignent pas le propriétaire de la source de configuration.

| Zone | Menaces particulièrement pertinentes |
| --- | --- |
| Capture / Ingestion | T02, T03, T04, T08, T09, T10 |
| Normalization | T01, T02, T10 |
| Network State | T03, T04, T05, T06, T07, T09 |
| Detection Engine | T05, T06, T07, T09, T11 (effets de la configuration analytique reçue), T17, T19, T20 |
| Alerting | T01, T09, T11 (effets de la configuration analytique reçue), T19, T20 |
| Persistence | T13, T14, T15 ; T03 si goulot d’étranglement |
| Interfaces | T03, T14, T15, T16, T19, T20 |
| Observability | T03, T09, T14, T15, T17, T18 |
| Configuration / assemblage / Composition Root | T11, T12 (point principal de traçabilité) ; T15, T17 selon le chemin considéré |
| Orchestration Application et lifecycle | T12 (effets de la configuration technique reçue), T17 |

Les rôles suivants restent distincts :

```text
point d’entrée d’une menace
≠
composant affecté
≠
composant qui la propage
≠
emplacement futur d’une mitigation
```

Associer une menace à une responsabilité ne signifie pas que celle-ci est seule responsable de sa réduction.

Cette matrice représente :

```text
les relations principales
à considérer
```

et non :

```text
une preuve exhaustive
que toute interaction possible
a été couverte
```

Une menace peut affecter indirectement une zone même lorsqu’elle n’apparaît pas dans la ligne correspondante.

La propagation inter-composants doit donc rester prise en compte lors de l’analyse des mesures de réduction du risque.

### Responsabilités de sécurité et architecture

L’analyse confirme plusieurs décisions architecturales déjà établies.

La séparation :

```text
Capture
→
Normalization
→
Core
```

permet de maintenir les représentations techniques non fiables à la frontière et de préserver les invariants du modèle domaine.

Le bornage du Network State répond directement aux menaces liées :

```text
au volume
à la cardinalité
à l’empoisonnement d’état
```

La séparation :

```text
DetectionResult
≠
Alert
```

permet de distinguer une conclusion analytique d’un objet de suivi de sécurité.

La séparation :

```text
modèle domaine
≠
modèle de persistance
```

permet de contrôler la reconstruction des données et leur évolution historique.

La séparation :

```text
résultat métier
≠
observabilité
```

permet de rendre une dégradation opérationnelle visible sans transformer les logs ou métriques en source de vérité métier.

Enfin, le monolithe modulaire permet de confiner certaines défaillances lorsque cela est pertinent sans introduire prématurément des frontières distribuées supplémentaires.

### Portée de 0.5.6

Cette étape projette les menaces `T01` à `T20` sur Capture / Ingestion, Normalization, Network State, Detection Engine, Alerting, Persistence, Interfaces et Observability, tout en intégrant les responsabilités transversales de Configuration / assemblage / Composition Root et de l’Application et du lifecycle. Elle établit les principales responsabilités de sécurité de chaque zone, les chemins de propagation inter-composants et la distinction entre dégradation technique et dégradation analytique, afin de fournir une base traçable pour la définition des mesures de réduction du risque.


## Mesures de réduction du risque — 0.5.7

Cette section définit les principales mesures destinées à réduire les risques associés aux menaces `T01` à `T20`.

L’objectif n’est pas de prétendre supprimer entièrement ces menaces ni de fixer prématurément toutes les technologies qui seront utilisées.

La logique retenue est :

```text
menace
   ↓
mesures de réduction
   ↓
risque réduit
   ↓
risque résiduel
```

Les risques résiduels et les non-garanties seront explicités séparément.

Les mesures sont organisées par propriétés de sécurité transversales plutôt que par menace individuelle, car plusieurs menaces reposent sur les mêmes mécanismes de protection.

Une mesure peut donc réduire plusieurs menaces et une menace peut nécessiter plusieurs mesures complémentaires.

Le principe général est :

```text
défense unique
≠
sécurité suffisante

plusieurs propriétés cohérentes
→
réduction progressive du risque
```

### Validation et adaptation aux frontières

Toute donnée provenant d’une source externe doit franchir une frontière explicite avant d’être utilisée comme représentation domaine.

Le chemin attendu est :

```text
entrée externe
      ↓
parsing / adaptation
      ↓
validation applicable
      ↓
représentation interne
```

Cette mesure concerne notamment :

```text
trafic réseau
PCAP
configuration
requêtes d’interface
données persistées reconstruites
```

Un objet provenant directement d’une bibliothèque, d’un parser, d’un framework ou d’un format externe ne doit pas devenir implicitement un objet domaine.

Les invariants applicables doivent être vérifiés avant admission dans le modèle concerné.

Lorsqu’une représentation fiable ne peut pas être construite, l’entrée doit pouvoir être rejetée selon le contrat applicable.

NetGuard ne doit pas fabriquer silencieusement des valeurs uniquement pour permettre l’admission d’une entrée invalide.

Le principe reste :

```text
information absente
≠
valeur fictive
```

lorsque l’absence possède une signification.

Cette validation ne doit cependant pas être surinterprétée.

```text
validation
≠
authentification
≠
preuve de vérité
```

Une adresse IP syntaxiquement valide reste une adresse observée et non une identité certaine.

Cette mesure réduit principalement :

```text
T01
T02
T10
T16
```

### Bornage des ressources influençables par des entrées externes

Une entrée externe potentiellement non bornée ne doit pas provoquer automatiquement une croissance interne non bornée.

Le principe est :

```text
entrée externe potentiellement non bornée
≠
allocation interne potentiellement non bornée
```

Les structures dont la consommation peut dépendre d’entrées externes doivent disposer de limites adaptées à leur rôle lorsque leur croissance arbitraire pourrait affecter le système.

Cela peut notamment concerner :

```text
buffers
queues
états analytiques
nombre de clés analytiques
historique conservé en mémoire
taille des requêtes
pagination
résultats retournés
logs
cardinalité des métriques
```

Les limites concrètes ne sont pas nécessairement identiques entre composants.

Le threat model n’impose donc pas une valeur numérique universelle.

La propriété recherchée est :

```text
ressource exposée
→
dimension de croissance identifiée
→
limite explicite lorsque nécessaire
```

Cette mesure réduit principalement :

```text
T03
T04
T05
T09
T16
T18
```

### Politiques explicites de saturation

Le bornage d’une ressource doit être accompagné d’une politique définissant le comportement lorsque la limite est atteinte.

Par exemple, une structure possédant une capacité de `N` éléments doit définir ce qui se produit lorsque l’élément `N + 1` arrive.

Selon le composant et son contrat, les stratégies possibles peuvent notamment inclure :

```text
rejet
drop
éviction
ralentissement
confinement
échec contrôlé
```

Aucune politique universelle n’est imposée à toutes les ressources.

Un buffer de capture, un état analytique, une file de persistance et une requête d’interface ne possèdent pas nécessairement les mêmes contraintes.

Le principe transversal est :

```text
saturation
→
comportement défini
→
conséquence maîtrisée
→
dégradation observable lorsque pertinente
```

et non :

```text
saturation
→
comportement accidentel
```

Une saturation connue ne doit pas conduire NetGuard à prétendre disposer d’informations qu’il n’a plus.

Cette mesure réduit principalement :

```text
T03
T04
T09
T16
T18
```

### Isolation et propriété explicite des états analytiques

Chaque état analytique doit posséder un propriétaire et une sémantique explicites.

Par défaut :

```text
état Detector A
≠
état Detector B
```

Un état partagé ne doit exister que lorsqu’un contrat métier explicite le justifie.

Chaque état stateful doit définir les dimensions nécessaires à son fonctionnement, notamment :

```text
owner
grouping
content
time
capacity
saturation
expiration
eviction
transitions
```

Les clés de regroupement doivent être déterministes et documentées.

Une observation ne doit pas influencer un état situé hors du scope prévu uniquement à cause d’un regroupement implicite ou ambigu.

L’expiration métier doit également rester distincte d’une éviction provoquée par une contrainte de ressources.

```text
expiration
≠
éviction sous pression
```

Lorsque cette distinction influence la qualité de l’analyse, la perte d’état connue doit pouvoir être rendue observable.

Cette mesure réduit principalement :

```text
T04
T05
T06
T07
T09
```

### Déterminisme des traitements analytiques

À entrées métier, état initial et configuration équivalents, NetGuard doit chercher à produire un comportement analytique reproductible.

Le résultat ne doit pas dépendre implicitement :

```text
du hasard non contrôlé
du temps mur courant caché
d’un état global caché
de l’ordre accidentel de threads
d’une dépendance technique non déclarée
```

Lorsque l’ordre fait partie de la sémantique, celui-ci doit être explicitement défini.

Cette propriété permet notamment :

```text
tests reproductibles
replay déterministe
analyse des incidents
compréhension des Evidence
comparaison entre exécutions
```

Le déterminisme ne garantit pas que toutes les activités hostiles seront détectées.

Il garantit que les règles possèdent un comportement analysable et testable dans les conditions prévues.

Cette mesure réduit principalement les risques liés à :

```text
T05
T06
T07
T13
```

### Gestion explicite du temps

Les règles utilisant le temps doivent définir la notion temporelle sur laquelle elles reposent.

Le modèle conserve notamment :

```text
temps d’observation
≠
temps de traitement
```

Lorsqu’une règle dépend d’une fenêtre ou d’une expiration, son contrat doit préciser les propriétés pertinentes concernant :

```text
source temporelle
fenêtre
expiration
ordre
retard
observations tardives
```

Le Core ne doit pas dépendre implicitement du temps mur lorsqu’une source de temps contrôlable est nécessaire à la logique métier.

Cette mesure ne supprime pas les possibilités d’évasion temporelle.

Elle permet cependant de rendre les limites temporelles :

```text
explicites
déterministes
testables
documentables
```

Cette mesure réduit principalement :

```text
T05
T06
T09
```

### Préservation proportionnée de la provenance

NetGuard doit conserver suffisamment de provenance pour permettre de distinguer :

```text
ce qui a été observé
ce qui a été calculé
ce que la règle a conclu
```

Lorsque nécessaire à l’interprétation d’un résultat, la provenance peut notamment inclure :

```text
source
scope
point d’observation
session
temps pertinent
identifiant de règle
version ou paramètres analytiques pertinents
```

La provenance doit rester proportionnée au besoin.

Le principe n’est pas :

```text
tout conserver
au cas où
```

mais :

```text
conserver les informations
nécessaires à l’interprétation
et à la traçabilité
```

Le raw payload réseau ne devient donc pas une exigence générale.

Cette mesure doit rester compatible avec la minimisation des données.

Cette mesure réduit principalement :

```text
T01
T13
T19
T20
```

### Conclusions limitées aux faits disponibles

Les conclusions produites par NetGuard ne doivent pas dépasser les garanties réellement fournies par les observations et les règles.

Le système ne doit notamment pas transformer :

```text
adresse source observée
```

en :

```text
identité certaine de l’attaquant
```

Il ne doit pas transformer :

```text
aucune Alert
```

en :

```text
réseau sûr
```

Et il ne doit pas transformer :

```text
Alert
```

en :

```text
incident confirmé
```

sans élément supplémentaire permettant réellement cette conclusion.

Les représentations internes, l’API, la CLI et les futures interfaces graphiques doivent préserver cette sémantique.

Le vocabulaire utilisé pour présenter un résultat fait donc partie des propriétés de sécurité du système.

Le principe reste :

```text
réalité réseau
≠
observation
≠
calcul
≠
conclusion
≠
suivi de l’Alert
```

Cette mesure réduit principalement :

```text
T01
T08
T09
T19
T20
```

### Validation et contrôle de la configuration

Toute configuration externe doit être parsée et validée avant d’être utilisée.

Le chemin attendu est :

```text
source externe
      ↓
parsing
      ↓
validation
      ↓
configuration structurée
      ↓
injection dans le composant concerné
```

La séparation reste :

```text
configuration analytique
≠
configuration technique
```

Une configuration invalide ne doit pas provoquer silencieusement un retour vers une valeur par défaut qui masquerait l’erreur.

Le principe est :

```text
défaut documenté
≠
fallback silencieux après valeur invalide
```

Les sources capables de modifier une configuration doivent être contrôlées par le contexte de déploiement conformément aux hypothèses de confiance.

Les paramètres analytiques nécessaires à l’interprétation historique d’un résultat doivent rester retraçables lorsque cela est pertinent.

NetGuard V1 n’impose pas à cette étape une signature cryptographique de tous les fichiers de configuration.

Cette mesure réduit principalement :

```text
T11
T12
```

### Confinement explicite des défaillances

Une défaillance locale doit déclencher une politique explicite adaptée au contrat du composant.

Selon le contexte, une défaillance peut notamment conduire à :

```text
rejet de l’entrée
confinement du composant
dégradation du service
arrêt contrôlé
échec global
```

Le système ne doit pas appliquer implicitement la même stratégie à toutes les défaillances.

Le principe est :

```text
défaillance locale
≠
défaillance globale automatique
```

mais également :

```text
confinement
≠
silence
```

Une défaillance confinée qui réduit les capacités opérationnelles doit pouvoir être distinguée d’un fonctionnement nominal.

Une exception ne doit pas être ignorée uniquement afin de maintenir artificiellement le processus vivant.

Cette mesure réduit principalement :

```text
T02
T10
T17
```

et contribue également à limiter les conséquences de certaines saturations.

### Observabilité des dégradations connues

Les dégradations connues susceptibles d’affecter les garanties opérationnelles doivent pouvoir être rendues observables lorsque cela est pertinent.

Cela peut notamment concerner :

```text
drops connus
saturation
évictions de ressources
pertes d’état connues
détecteur indisponible
échecs importants
dégradation du pipeline
```

Le système doit permettre de distinguer autant que raisonnablement possible :

```text
fonctionnement nominal
```

de :

```text
fonctionnement dégradé connu
```

Cette propriété ne signifie pas qu’un log doit être produit pour chaque événement.

```text
observable
≠
un log par occurrence
```

Des mécanismes tels que l’agrégation, le comptage ou la limitation de fréquence peuvent être nécessaires afin que l’observabilité ne devienne pas elle-même une source de saturation.

Une dégradation inconnue ne peut évidemment pas être signalée comme connue.

NetGuard ne doit donc pas prétendre détecter toutes ses propres pertes possibles.

Cette mesure réduit principalement :

```text
T03
T04
T09
T17
T18
T19
```

### Observabilité elle-même bornée

Les mécanismes d’observabilité doivent respecter les mêmes principes de maîtrise des ressources que le reste du système.

Les données contrôlées ou influencées par une entrée externe ne doivent pas provoquer directement :

```text
volume non borné de logs
cardinalité non bornée de métriques
création arbitraire de noms de métriques
création arbitraire de labels
```

Les identifiants à forte cardinalité tels que :

```text
adresse IP
flow ID
Alert ID
valeur réseau arbitraire
```

ne doivent pas devenir par défaut des dimensions de métriques non bornées.

Les logs doivent également éviter la duplication systématique d’une même erreur à travers plusieurs couches.

Le principe est :

```text
observabilité utile
+
coût maîtrisé
```

Cette mesure réduit principalement :

```text
T03
T18
```

### Minimisation des données

NetGuard doit limiter les données collectées, conservées et exposées à ce qui est nécessaire aux fonctionnalités et garanties prévues.

Le principe est :

```text
collecter
ce qui est nécessaire

conserver
ce qui est nécessaire

exposer
ce qui est nécessaire
```

Cette règle s’applique notamment à :

```text
modèle domaine
Evidence
Alert
persistance
API
CLI
logs
métriques
```

Le payload réseau brut n’appartient pas au modèle canonique par défaut.

Une donnée disponible techniquement ne doit pas être conservée uniquement parce qu’elle pourrait éventuellement être utile.

La minimisation réduit à la fois :

```text
surface de confidentialité
volume de données sensibles
coût de stockage
risque d’exposition
```

Cette mesure réduit principalement :

```text
T14
T15
T18
```

### Protection et confinement des secrets

Les secrets techniques doivent rester limités aux composants qui en ont réellement besoin.

Ils ne doivent pas être propagés comme des données métier ordinaires.

En particulier, un secret ne doit pas apparaître volontairement dans :

```text
DetectionResult
Evidence
Alert
logs
métriques
réponses publiques
messages d’erreur externes
```

Les objets de configuration génériques contenant de nombreux secrets ne doivent pas être distribués inutilement à travers les couches.

Le mécanisme précis de provisionnement des secrets dépendra du mode de déploiement.

Le threat model n’impose donc pas à cette étape une technologie particulière telle que :

```text
Vault
Docker Secrets
service de secrets cloud
```

Cette mesure réduit principalement :

```text
T15
```

et limite certaines conséquences possibles de `T14` et `T16`.

### Contrôle des interfaces exposées

Toute interface exposée doit contrôler les entrées qu’elle accepte et les opérations qu’elle permet.

Cela peut notamment inclure :

```text
validation
taille des requêtes
pagination
filtres
coût des opérations
autorisation lorsque nécessaire
minimisation des réponses
```

Le principe reste :

```text
requête valide
≠
opération autorisée
```

Une entrée syntaxiquement valide peut également être pathologique du point de vue des ressources.

Par exemple :

```text
filtre valide
→
opération extrêmement coûteuse
```

Les limites doivent donc considérer le coût réel des opérations et pas uniquement la validité syntaxique des paramètres.

Les réponses doivent également éviter l’exposition inutile de données internes.

Le rate limiting peut constituer une mesure pertinente selon l’exposition réelle d’une interface, mais il n’est pas imposé universellement à tous les modes d’interaction.

Une CLI locale et une API accessible sur un réseau ne possèdent pas nécessairement les mêmes contraintes.

Cette mesure réduit principalement :

```text
T03
T14
T15
T16
```

### Reconstruction prudente depuis la persistance

Une représentation persistée ne doit pas être assimilée directement à un objet domaine valide.

Le chemin attendu est :

```text
donnée persistée
      ↓
mapping
      ↓
validation / reconstruction
      ↓
objet domaine
```

Cette reconstruction doit préserver les invariants et la sémantique applicables.

Les migrations et évolutions de schéma doivent éviter de modifier silencieusement la signification historique des résultats.

En particulier :

```text
ancienne Alert
```

ne doit pas être réinterprétée comme :

```text
nouvelle Alert avec une sémantique différente
```

sans mécanisme explicite permettant de préserver ou retracer cette évolution.

La persistance doit également rester distincte du modèle domaine afin d’éviter qu’une contrainte de stockage devienne implicitement une contrainte métier.

Cette mesure réduit principalement :

```text
T13
```

et contribue également à réduire certaines conséquences de `T14`.

### Principe de moindre privilège

NetGuard doit utiliser uniquement les privilèges nécessaires au mode d’exécution concerné.

Le principe est :

```text
fonction nécessitant un privilège
≠
tout le système doit disposer
de ce privilège
```

Par exemple, si une capacité particulière est nécessaire pour effectuer une capture live, cela ne signifie pas automatiquement que tous les composants NetGuard doivent fonctionner avec des privilèges équivalents.

La stratégie exacte dépendra :

```text
du système d’exploitation
du mécanisme de capture
du mode de déploiement
```

Cette mesure limite les conséquences potentielles d’une défaillance ou d’une vulnérabilité dans une zone exposée à des entrées hostiles.

Elle réduit notamment l’impact potentiel de :

```text
T02
T10
T16
```

### Maîtrise des dépendances techniques

Toute dépendance externe augmente la surface technique que NetGuard doit comprendre, maintenir et mettre à jour.

Une dépendance doit donc correspondre à un besoin explicite.

Le principe est :

```text
dépendance
→
besoin identifié
```

et non :

```text
dépendance
→
ajoutée sans nécessité claire
```

Les dépendances utilisées devront pouvoir être versionnées, mises à jour et remplacées lorsque nécessaire.

Les sorties de dépendances restent soumises aux frontières d’adaptation appropriées.

```text
dépendance de confiance
≠
donnée métier automatiquement fiable
```

Le choix d’un outil particulier d’analyse de dépendances ou de sécurité de supply chain n’est pas imposé à cette étape.

Cette mesure contribue principalement à limiter l’impact des menaces touchant :

```text
T02
T10
T13
T16
```

sans remettre en cause les hypothèses `TA2` et `TA3`.

### Tests des propriétés de sécurité

Les propriétés définies par le threat model doivent être testables lorsque cela est raisonnablement possible.

Les tests peuvent notamment couvrir :

```text
entrées malformées
valeurs limites
forte cardinalité
saturation
éviction
expiration
ordre temporel
observations tardives
détecteur défaillant
configuration invalide
clés inconnues
reconstruction depuis la persistance
non-divulgation de secrets
```

Les tests doivent vérifier les propriétés observables du système plutôt que les détails accidentels de l’implémentation.

Par exemple, un test de saturation doit pouvoir vérifier :

```text
limite respectée
+
politique appliquée
+
dégradation observable si nécessaire
```

et pas seulement :

```text
une fonction interne précise
a été appelée
```

Des PCAP synthétiques et déterministes peuvent être utilisés pour tester les chemins de lecture et d’analyse sans dépendre de captures sensibles réelles.

Le fuzzing pourra devenir pertinent pour certaines surfaces telles que les parsers, mais aucun framework particulier n’est imposé à cette étape.

Les tests réduisent le risque de régression des garanties définies par l’architecture.

Ils ne constituent pas une preuve d’absence de vulnérabilité.

### Préservation de l’état opérationnel réel

NetGuard doit distinguer son existence en tant que processus de la disponibilité réelle de ses capacités.

Le modèle doit préserver :

```text
liveness
≠
readiness
≠
état opérationnel
```

Une défaillance partielle peut permettre au processus de continuer tout en réduisant les capacités disponibles.

Lorsque cette réduction est significative, l’état présenté doit éviter de donner l’impression d’un fonctionnement nominal complet.

Par exemple :

```text
process vivant
+
capture active
+
détecteur important indisponible
```

ne doit pas automatiquement devenir :

```text
NetGuard pleinement opérationnel
```

Cette mesure réduit principalement :

```text
T09
T17
T19
```

### Absence de technologie de sécurité imposée prématurément

Le threat model définit les propriétés que l’implémentation devra respecter sans choisir prématurément une technologie lorsque plusieurs solutions restent possibles.

Cette étape ne fixe donc pas encore :

```text
technologie d’authentification précise
mécanisme de secrets précis
framework de fuzzing précis
outil de scanning de dépendances précis
valeurs universelles de rate limiting
valeurs universelles de buffers
valeurs universelles de capacité d’état
```

Ces choix devront être effectués lorsque :

```text
le besoin concret
+
le contexte de déploiement
+
les contraintes techniques
```

seront suffisamment connus.

Cette absence de choix technologique ne supprime pas les propriétés de sécurité définies dans cette section.

Par exemple :

```text
technologie de secrets non choisie
```

n’annule pas :

```text
les secrets ne doivent pas
être exposés dans les logs
```

De même :

```text
valeur de buffer non fixée
```

n’annule pas :

```text
le buffer doit être borné
```

### Matrice de traçabilité des mesures

La matrice suivante relie chaque menace aux principales familles de mesures destinées à en réduire le risque.

| Menace | Mesures principales |
| --- | --- |
| T01 | validation sémantique, provenance, conclusions limitées aux faits disponibles |
| T02 | validation aux frontières, confinement des défaillances, moindre privilège, tests |
| T03 | bornage des ressources, saturation explicite, observabilité, contrôle des interfaces |
| T04 | bornage de cardinalité, isolation des états, éviction explicite, tests |
| T05 | isolation et bornage des états, grouping explicite, déterminisme |
| T06 | temps explicite, déterminisme, tests des frontières temporelles |
| T07 | grouping explicite, isolation des états, limites analytiques documentées |
| T08 | visibilité explicitée, provenance, conclusions limitées |
| T09 | saturation explicite, pertes observables, état opérationnel réel, temps et état maîtrisés |
| T10 | PCAP traité comme entrée non fiable, validation, bornage, confinement, moindre privilège, tests |
| T11 | validation de la configuration analytique, contrôle des sources, traçabilité des paramètres pertinents |
| T12 | validation de la configuration technique, contrôle des sources, séparation des responsabilités |
| T13 | mapping explicite, reconstruction validée, déterminisme, préservation de la sémantique historique |
| T14 | minimisation, contrôle des interfaces, exposition limitée, contrôle d’accès selon le contexte |
| T15 | confinement des secrets, minimisation, contrôle des sorties et de l’observabilité |
| T16 | validation, bornage, contrôle du coût, autorisation lorsque nécessaire, moindre privilège |
| T17 | confinement explicite, observabilité des dégradations, état opérationnel fidèle |
| T18 | observabilité bornée, cardinalité maîtrisée, minimisation, contrôle des données externes |
| T19 | sémantique explicite, visibilité des dégradations, état opérationnel fidèle, conclusions limitées |
| T20 | Evidence structurée, provenance suffisante, vocabulaire précis, absence de suraffirmation |

Cette matrice représente les relations principales.

Elle ne signifie pas qu’une seule mesure suffit à neutraliser complètement une menace.

La relation correcte reste :

```text
menace
      ↓
plusieurs mesures complémentaires
      ↓
réduction du risque
```

### Défense en profondeur

Les mesures définies dans cette section doivent fonctionner comme des protections complémentaires.

Par exemple, face à une entrée malformée :

```text
parser robuste
      +
adaptation explicite
      +
validation domaine
      +
confinement des erreurs
      +
moindre privilège
      +
tests
```

réduit davantage le risque qu’une unique validation placée à un seul endroit.

De même, face à une saturation :

```text
ressource bornée
      +
politique de saturation
      +
observabilité
      +
état opérationnel fidèle
```

permet à NetGuard de rester cohérent même lorsque toutes les données ne peuvent plus être traitées.

Enfin, face à une conclusion analytique :

```text
observation fidèle
      +
état déterministe
      +
Evidence structurée
      +
provenance suffisante
      +
vocabulaire limité aux faits disponibles
```

réduit le risque de produire une affirmation plus forte que ce que les données permettent réellement d’établir.

La sécurité de NetGuard repose donc sur la composition de plusieurs propriétés cohérentes plutôt que sur un mécanisme unique supposé suffisant.

### Portée de 0.5.7

Cette étape définit les principales mesures de réduction applicables aux menaces `T01` à `T20` : validation aux frontières, bornage et saturation explicite des ressources, isolation des états, déterminisme, gestion explicite du temps, provenance, limitation des conclusions, contrôle de la configuration, confinement des défaillances, observabilité maîtrisée, minimisation des données, protection des secrets, contrôle des interfaces, reconstruction prudente depuis la persistance, moindre privilège, maîtrise des dépendances et tests des propriétés de sécurité. Ces mesures réduisent les risques identifiés sans prétendre les supprimer entièrement ni imposer prématurément des technologies ou valeurs de déploiement qui ne sont pas encore justifiées.

## Risques résiduels et non-garanties — 0.5.8

Cette section explicite les risques qui subsistent après l’application correcte des mesures de réduction définies précédemment ainsi que les garanties que NetGuard V1 ne prétend pas fournir.

L’existence de mesures de sécurité ne signifie pas qu’une menace est supprimée.

La relation retenue est :

```text
menace
   ↓
mesures de réduction
   ↓
probabilité et/ou impact réduits
   ↓
risque résiduel
```

Trois notions doivent rester distinctes :

```text
risque résiduel
≠
rupture d’hypothèse
≠
fonctionnalité hors périmètre
```

Un risque résiduel correspond à un risque qui reste possible malgré l’application correcte des mesures prévues.

Il ne doit pas être confondu avec les situations suivantes :

```text
risque résiduel
≠
mesure de réduction absente ou non appliquée
≠
violation d’un invariant
≠
défaut d’implémentation
```

Un état correctement borné dont la capacité est atteinte peut subir une éviction conforme à sa politique et perdre une information analytiquement utile : cette limite peut constituer un risque résiduel. Une croissance mémoire illimitée causée par un bug alors que l’état doit être borné constitue un défaut d’implémentation.

De même, une perte contrôlée et documentée ne doit pas être assimilée à une perte silencieuse non prévue. L’absence ou la mauvaise application d’une mesure prévue ne devient pas un risque résiduel par simple qualification.

Une rupture d’hypothèse correspond à une situation dans laquelle une hypothèse de confiance `TA1` à `TA11` n’est plus satisfaite.

Une fonctionnalité hors périmètre correspond à une capacité que NetGuard V1 ne cherche volontairement pas à fournir.

Cette distinction évite de présenter une limite connue, une hypothèse violée ou une fonctionnalité volontairement absente comme une vulnérabilité équivalente.

### Visibilité nécessairement partielle

NetGuard ne peut analyser que les informations qui atteignent effectivement ses sources d’observation.

Le chemin réel peut être représenté par :

```text
activité réseau réelle
        ↓
partie visible depuis
le point d’observation
        ↓
partie effectivement capturée
        ↓
partie correctement normalisable
        ↓
partie analytiquement exploitable
        ↓
détection éventuelle
```

Chaque étape peut réduire les informations disponibles pour les étapes suivantes.

Une activité située hors du point d’observation, empruntant un chemin non visible ou absente des données capturées peut donc ne jamais atteindre les détecteurs.

Le principe reste :

```text
absence d’observation
≠
absence d’activité
```

et :

```text
absence d’Alert
≠
absence de menace
```

Les mesures de réduction peuvent rendre certaines limitations de visibilité ou pertes connues observables, mais elles ne peuvent pas fournir une visibilité sur des données que NetGuard n’a jamais reçues.

Ce risque résiduel concerne particulièrement :

```text
T08
T09
T19
```

### Pertes possibles sous contrainte de ressources

Le bornage des ressources protège NetGuard contre une croissance mémoire ou une accumulation arbitraire.

Cette propriété implique cependant qu’une charge suffisamment importante peut dépasser les capacités disponibles.

La relation est :

```text
ressources bornées
+
charge supérieure aux capacités
→
rejet, drop, éviction,
ralentissement ou dégradation
selon la politique applicable
```

NetGuard cherche à rendre les saturations connues explicites et leurs conséquences maîtrisées.

Il ne garantit pas un traitement sans perte sous une charge arbitrairement élevée.

Lorsqu’une perte est connue, NetGuard peut chercher à rendre observable :

```text
qu’une perte a eu lieu
```

mais ne peut pas nécessairement connaître :

```text
le contenu exact perdu
toutes les observations manquantes
tous les états qui auraient évolué
tous les DetectionResult
qui auraient éventuellement été produits
```

Une perte qui n’est pas elle-même observable par NetGuard ne peut pas être signalée comme une perte connue.

```text
perte inconnue
≠
perte que NetGuard peut
automatiquement reconstruire
```

Ce risque résiduel concerne particulièrement :

```text
T03
T04
T09
```

### Résistance à une charge arbitraire non garantie

NetGuard cherche à maintenir :

```text
ressources bornées
comportement de saturation explicite
dégradation contrôlée
état opérationnel fidèle
```

Il ne garantit pas :

```text
traitement intégral
sans perte
sans ralentissement
sans rejet
d’une charge arbitrairement élevée
```

Aucune limite de buffer, de queue ou d’état ne peut supprimer le fait qu’un système dispose de ressources finies.

Les limites configurées déterminent donc un compromis entre :

```text
capacité
consommation de ressources
latence
risque de perte
```

Ce compromis appartient au comportement normal d’un système borné et ne constitue pas en lui-même une défaillance de sécurité.

### Évasion analytique toujours possible

Une règle déterministe possède nécessairement des conditions dans lesquelles elle produit ou ne produit pas un résultat.

Une règle conceptuelle telle que :

```text
N événements
dans une fenêtre W
```

définit automatiquement des frontières que l’activité observée peut ne pas franchir.

Un attaquant connaissant ou déduisant les règles peut chercher à adapter :

```text
son rythme
ses intervalles
ses sources
ses destinations
ses regroupements observables
la répartition de son activité
```

afin de rester en dehors des conditions de déclenchement.

Les mesures de déterminisme, de gestion explicite du temps et de définition précise des regroupements rendent le comportement compréhensible et testable.

Elles ne rendent pas la détection universelle.

Le principe est :

```text
détection déterministe
≠
détection exhaustive
```

Ce risque résiduel concerne particulièrement :

```text
T06
T07
```

### Influence résiduelle sur l’état analytique

Un attaquant contrôlant le trafic qu’il génère peut influencer l’état analytique construit à partir de ce trafic, dans les limites des capacités déjà définies.

Même avec un état borné, un propriétaire explicite, une isolation, des regroupements explicites et des transitions déterministes, NetGuard ne distingue pas toujours une activité légitime influençant l’état d’une activité volontairement conçue pour l’influencer.

Cette influence résiduelle concerne `T05`. Elle ne signifie pas que les invariants de l’état peuvent être violés : une fusion contraire à la politique de regroupement, une mutation non autorisée ou un défaut de bornage restent des défauts à corriger.

### Faux positifs possibles

Un détecteur peut identifier correctement un comportement correspondant à sa règle alors que ce comportement possède une explication légitime.

Par exemple, une activité ressemblant à un scan peut provenir :

```text
d’un administrateur
d’un outil d’inventaire
d’un scanner de sécurité légitime
d’une opération de maintenance
```

Dans ce cas :

```text
comportement correspondant
à la règle
```

peut être vrai alors que :

```text
attaque réelle
```

est faux.

Le principe reste :

```text
Alert
≠
attaque certaine
```

Une Alert doit donc représenter ce que NetGuard a effectivement détecté sans être transformée automatiquement en incident confirmé.

La possibilité de faux positifs est un risque résiduel inhérent à une détection fondée sur des observations et des règles.

Elle concerne particulièrement :

```text
T20
```

### Faux négatifs possibles

Une activité hostile peut ne produire aucune Alert.

Les causes peuvent notamment inclure :

```text
activité hors visibilité
perte d’observations
activité sous un seuil
évasion temporelle
répartition entre plusieurs états
protocole non analysé
détecteur absent
détecteur non applicable
configuration différente
dégradation opérationnelle
```

Le principe reste :

```text
absence d’Alert
≠
preuve de sécurité
```

NetGuard ne garantit donc pas la détection de toute activité hostile présente sur le réseau.

Cette non-garantie concerne particulièrement :

```text
T06
T07
T08
T09
T19
```

### Attribution non garantie

NetGuard peut conserver fidèlement une propriété réseau observée sans être capable d’établir l’identité réelle de l’acteur qui l’a produite.

Par exemple :

```text
source_ip observée = X
```

ne permet généralement pas de conclure :

```text
identité physique certaine = X
```

ni nécessairement :

```text
machine réellement responsable = X
```

ou :

```text
attaquant certain = X
```

NetGuard V1 n’est pas un système général d’authentification réseau ni un système d’attribution forensique.

La validation sémantique protège l’intégrité de la représentation interne.

Elle ne transforme pas une information observable en identité authentifiée.

Cette non-garantie concerne particulièrement :

```text
T01
T20
```

### Authenticité du trafic non garantie

Une donnée réseau peut être syntaxiquement et sémantiquement représentable sans être authentique.

Le principe est :

```text
paquet valide
≠
paquet authentique
```

De même :

```text
adresse valide
≠
identité authentifiée

timestamp valide
≠
preuve temporelle absolue

port valide
≠
preuve qu’un service réel
correspond à l’interprétation supposée
```

La normalisation garantit que NetGuard représente correctement les informations qu’il accepte dans son modèle.

Elle ne garantit pas que toutes les informations présentes dans le trafic décrivent fidèlement la réalité externe.

Cette non-garantie concerne particulièrement :

```text
T01
T02
```

### Exactitude temporelle absolue non garantie

NetGuard distingue les différentes notions temporelles pertinentes et cherche à rendre ses règles temporelles déterministes.

Il peut notamment préserver :

```text
temps d’observation
temps de traitement
timestamps disponibles
```

selon le type d’entrée.

Il ne garantit cependant pas que toutes les horloges ou sources temporelles externes sont parfaitement exactes ou synchronisées.

Cette limite est particulièrement importante pour les PCAP.

```text
timestamp contenu dans un PCAP
≠
preuve du moment réel
où l’événement réseau a eu lieu
```

Un PCAP hostile peut notamment contenir des timestamps volontairement trompeurs.

NetGuard peut appliquer une politique déterministe à ces valeurs sans être capable d’en prouver l’authenticité.

Cette non-garantie concerne particulièrement :

```text
T06
T10
```

### Disponibilité absolue non garantie

Les mécanismes de confinement, de bornage et de lifecycle réduisent le risque qu’une défaillance locale provoque inutilement une indisponibilité globale.

Ils ne garantissent pas une disponibilité permanente.

Des situations telles que :

```text
ressources insuffisantes
capture impossible
dépendance indisponible
erreur critique
stockage indisponible
configuration empêchant le démarrage
```

peuvent rendre une partie ou la totalité de NetGuard indisponible.

L’objectif est :

```text
état réel
→
comportement maîtrisé
→
état opérationnel compréhensible
```

et non :

```text
disponibilité absolue
```

Cette limite concerne particulièrement :

```text
T03
T10
T12
T17
```

### Persistance parfaite non garantie

NetGuard peut valider ses mappings, contrôler les erreurs de persistance et préserver la sémantique historique de ses objets.

Il ne peut cependant pas garantir la conservation des données face à toute défaillance possible du stockage ou de son environnement.

Le stockage peut notamment devenir :

```text
indisponible
corrompu
supprimé
mal configuré
```

selon les conditions de déploiement.

Une distinction fondamentale doit être conservée :

```text
résultat analytique correctement produit
+
échec de persistance
```

ne signifie pas :

```text
résultat analytique incorrect
```

Le résultat peut avoir existé correctement sans avoir pu être conservé.

Inversement :

```text
donnée présente en stockage
≠
vérité métier automatiquement valide
```

Cette limite concerne particulièrement :

```text
T13
```

et certaines conséquences de :

```text
T12
T14
```

### Confidentialité absolue non garantie

NetGuard est par nature un système qui observe et traite certaines informations réseau.

Une personne disposant d’un accès légitime à certaines fonctions peut donc avoir accès à des informations nécessaires à ces fonctions.

La propriété recherchée est :

```text
pas d’exposition inutile
```

et non :

```text
aucune information réseau
n’est jamais visible
```

La minimisation réduit la quantité d’informations sensibles manipulées et exposées.

Elle ne permet pas de garantir la confidentialité si l’environnement d’exécution, le stockage ou une infrastructure externe de confiance sont compromis au-delà des hypothèses prévues.

Cette limite concerne particulièrement :

```text
T14
T15
```

### Observabilité parfaite non garantie

NetGuard cherche à rendre observables les dégradations qu’il connaît et qui affectent significativement son fonctionnement.

Cela peut inclure :

```text
drops connus
saturation connue
évictions connues
détecteur en échec
état opérationnel dégradé
```

Cette propriété ne signifie pas que NetGuard peut détecter toutes ses propres défaillances possibles.

Le principe est :

```text
dégradation connue
→
observable lorsque pertinente
```

mais pas :

```text
toute dégradation possible
→
nécessairement détectée
```

De même :

```text
absence de signal de dégradation
≠
preuve mathématique
de fonctionnement parfait
```

Les mécanismes de health, readiness et état opérationnel restent utiles mais ne constituent pas des mécanismes omniscients.

Cette limite concerne particulièrement :

```text
T09
T17
T18
T19
```

### Reproductibilité conditionnelle

NetGuard cherche à fournir une analyse reproductible lorsque les conditions sémantiquement pertinentes sont équivalentes.

La propriété recherchée est :

```text
mêmes entrées
sémantiquement pertinentes
+
même configuration pertinente
+
même état initial pertinent
+
mêmes règles et versions pertinentes
+
mêmes politiques applicables
→
résultat reproductible attendu
```

Cette propriété ne signifie pas :

```text
deux exécutions quelconques
→
résultat nécessairement identique
```

Une modification de :

```text
configuration
version de règle
ordre sémantiquement pertinent
politique temporelle
état initial
entrée
```

peut légitimement modifier le résultat.

La reproductibilité dépend donc de la conservation des éléments nécessaires à la comparaison.

### Limites de la validation de configuration analytique

La validation réduit `T11`, mais ne prouve à elle seule ni la légitimité de l’autorité ayant modifié une configuration ni la pertinence de ses valeurs pour le contexte observé.

```text
configuration valide
≠
configuration autorisée
≠
configuration pertinente
```

Sous les hypothèses `TA7` et `TA11`, une configuration autorisée et valide peut rester inadaptée ou résulter d’une erreur de l’opérateur non hostile, malgré l’application correcte des mesures prévues. Cette limite ne dispense pas des contrôles d’autorité nécessaires et ne qualifie pas leur absence de risque résiduel.

Le contrôle hostile d’une autorité de configuration supposée légitime relève d’une rupture des hypothèses concernées. Aucun accès administratif arbitraire n’est ainsi accordé à l’attaquant réseau `AC1` à `AC10`, et aucune persistance de configuration en base n’est supposée.

### Compromission complète de l’hôte

L’hypothèse `TA1` suppose une intégrité suffisante de l’hôte d’exécution.

Un attaquant disposant d’un contrôle complet tel que :

```text
administrateur/root arbitraire
contrôle du kernel
lecture ou écriture arbitraire
de la mémoire du processus
contrôle complet du runtime
```

sort du modèle d’attaque principal de NetGuard V1.

Dans une telle situation, l’attaquant peut potentiellement :

```text
modifier les observations
modifier le code en mémoire
modifier les résultats
lire les secrets
supprimer les Alert
modifier l’observabilité
désactiver le système
```

NetGuard V1 ne prétend donc pas maintenir ses garanties applicatives face à un environnement d’exécution entièrement compromis.

Cette situation constitue :

```text
rupture de TA1
```

et non une menace que l’architecture applicative prétend neutraliser seule.

### Compromission du code exécuté

L’hypothèse `TA2` suppose que le code NetGuard exécuté correspond à la version attendue.

Si le code exécuté est arbitrairement remplacé par un code hostile :

```text
NetGuard compromis
→
NetGuard ne peut plus être
sa propre racine de confiance
```

Un système ne peut pas raisonnablement garantir son propre comportement lorsque son implémentation elle-même est entièrement contrôlée par l’attaquant.

Cette situation constitue :

```text
rupture de TA2
```

NetGuard V1 ne prétend pas fournir seul un mécanisme complet de protection contre toute compromission de sa supply chain ou de son artefact exécutable.

### Compromission arbitraire des dépendances

L’hypothèse `TA3` suppose que les dépendances techniques utilisées respectent suffisamment les contrats techniques sur lesquels NetGuard repose.

La maîtrise des dépendances réduit la surface technique et facilite leur maintenance.

Elle ne garantit pas l’absence totale de vulnérabilité.

Le principe est :

```text
dépendances maîtrisées
≠
dépendances sans vulnérabilité
```

Une vulnérabilité exploitable dans une dépendance peut donc rester un risque.

Une dépendance entièrement remplacée ou volontairement hostile peut également constituer une rupture de l’hypothèse `TA3`, voire de `TA2` selon le mode de compromission.

NetGuard V1 ne prétend pas résoudre seul l’ensemble des problèmes possibles de supply chain.

### Administrateur totalement malveillant

L’hypothèse `TA11` considère que l’opérateur légitime n’est pas volontairement hostile dans le modèle principal.

Un administrateur disposant de privilèges suffisants peut potentiellement :

```text
modifier la configuration
désactiver des détecteurs
arrêter NetGuard
supprimer les données persistées
modifier l’environnement
modifier les logs
remplacer certains artefacts
```

NetGuard V1 n’est pas conçu comme un système capable de rester fiable face à son propre administrateur totalement privilégié et volontairement malveillant.

Cette situation constitue :

```text
rupture de TA11
```

Elle doit rester distincte d’une erreur opérateur.

```text
erreur opérateur
≠
administrateur hostile
```

Les validations, diagnostics et erreurs explicites restent utiles pour réduire les conséquences d’erreurs légitimes sans prétendre résister à un administrateur disposant volontairement de tous les moyens nécessaires pour contourner le système.

### Contrôle total de l’horloge système non couvert

L’hypothèse `TA6` ne suppose pas une synchronisation temporelle parfaite.

Elle suppose néanmoins que les sources temporelles techniques nécessaires au fonctionnement restent suffisamment correctes pour les garanties utilisées.

Un attaquant contrôlant arbitrairement l’horloge système ou les sources temporelles de l’environnement pourrait perturber certaines propriétés temporelles.

Ce contrôle arbitraire n’appartient pas aux capacités du modèle principal.

Il constitue une rupture de l’hypothèse temporelle applicable plutôt qu’une capacité implicitement accordée à tout attaquant réseau.

Cette distinction n’empêche pas NetGuard de considérer les timestamps contenus dans une entrée externe, notamment un PCAP, comme potentiellement non fiables.

### Contrôle direct du stockage non accordé par défaut

Le threat model protège l’intégrité, la confidentialité et la disponibilité des données persistées.

Il ne suppose cependant pas que l’attaquant réseau principal possède automatiquement un accès arbitraire direct à la base de données ou au stockage.

Les menaces concernant l’altération ou l’exposition du stockage dépendent donc :

```text
de son exposition réelle
des contrôles du déploiement
d’une compromission préalable
ou d’une rupture d’hypothèse
```

Cette distinction évite d’accorder implicitement à l’attaquant des capacités qui n’ont pas été définies dans `AC1` à `AC10`.

### Absence de couverture universelle

NetGuard V1 ne cherche pas à constituer un système universel de sécurité réseau.

Il ne garantit notamment pas :

```text
détection de toute activité malveillante
inspection exhaustive de tous les protocoles
inspection exhaustive de tous les payloads
identification certaine des attaquants
attribution forensique complète
analyse complète de tous les comportements possibles
```

NetGuard détecte les comportements pour lesquels :

```text
un détecteur existe
+
les observations nécessaires sont disponibles
+
les conditions de la règle sont satisfaites
```

Le périmètre de détection doit donc rester explicite.

Une absence de détecteur pour un comportement donné constitue une limite de couverture et non un résultat négatif prouvant l’absence de ce comportement.

### Absence de réponse automatique

NetGuard V1 est un système de surveillance et de détection.

Il ne cherche pas à devenir automatiquement :

```text
firewall
IPS
système de quarantaine
moteur de réponse automatique
```

La production d’une Alert ne signifie donc pas que NetGuard :

```text
bloque la source
coupe une connexion
modifie le firewall
isole une machine
```

L’absence de réponse automatique constitue une fonctionnalité volontairement hors périmètre de la V1 et non une vulnérabilité du moteur de détection.

La distinction est :

```text
détecter
≠
bloquer
```

### Absence de fonction antivirus ou d’analyse universelle de malware

NetGuard V1 n’est pas conçu comme un antivirus généraliste.

Il peut éventuellement observer des comportements réseau associés à certaines activités hostiles lorsque des règles correspondantes existent.

Il ne garantit pas :

```text
détection de tout malware
analyse complète des exécutables
analyse comportementale locale des processus
désinfection d’une machine
```

Ces capacités appartiennent à d’autres catégories de produits de sécurité et restent hors du périmètre défini pour la V1.

### Absence de DPI universel

NetGuard ne garantit pas une inspection profonde exhaustive de tous les protocoles applicatifs et de tous les contenus transportés.

Le modèle canonique privilégie les informations nécessaires aux objectifs analytiques définis et n’impose pas la conservation générale des payloads bruts.

Le principe reste :

```text
surveillance réseau utile
≠
inspection exhaustive
de chaque octet transporté
```

Cette limitation réduit également la quantité de données sensibles que NetGuard doit manipuler.

### Absence de garanties de SIEM complet

NetGuard V1 ne cherche pas à fournir l’ensemble des capacités d’un SIEM d’entreprise.

Il ne garantit notamment pas :

```text
corrélation universelle
entre sources hétérogènes
gestion complète d’incidents
workflow SOC complet
collecte distribuée à grande échelle
rétention réglementaire universelle
analyse multi-tenant avancée
```

Les capacités de persistance, de consultation et d’Alert de NetGuard doivent rester interprétées dans le périmètre du produit défini.

### Surface résiduelle d’une interface exposée

Une interface réellement exposée reste une surface d’attaque concernée par `T16`, même lorsque validation, bornage, contrôle du coût, autorisation lorsque nécessaire et moindre privilège sont correctement appliqués.

La réduction de ce risque dépend également du contexte d’exposition, de la configuration, du déploiement et des contrôles applicables, conformément notamment à `TA10`. Ces mesures ne garantissent pas l’absence de tout abus ; leur absence ou leur mauvaise application ne doit toutefois pas être présentée comme le risque restant après leur application correcte.

### Limites liées au déploiement

Certaines propriétés de sécurité dépendent nécessairement du contexte dans lequel NetGuard est exécuté.

Cela concerne notamment :

```text
droits système
exposition réseau des interfaces
protection du stockage
provisionnement des secrets
permissions sur les fichiers
position de capture
ressources disponibles
isolation du processus
```

Le Core ne peut pas compenser seul un déploiement qui viole les hypothèses nécessaires à son fonctionnement.

La relation est :

```text
garanties applicatives
+
hypothèses de déploiement satisfaites
→
garanties globales attendues
```

et non :

```text
application correcte
→
environnement automatiquement sûr
```

Les exigences de déploiement devront donc rester cohérentes avec les hypothèses de confiance du threat model.

### Distinction entre risque résiduel, rupture d’hypothèse et hors périmètre

Les trois situations peuvent être illustrées ainsi.

Risque résiduel :

```text
T06

règle correctement implémentée
+
mesures temporelles correctes
+
attaquant adaptant son rythme
→
évasion toujours possible
```

Rupture d’hypothèse :

```text
TA1 violée

attaquant possédant
un contrôle root complet
→
garanties applicatives
non maintenues
```

Fonctionnalité hors périmètre :

```text
Alert correctement produite
+
aucune action de blocage
→
comportement attendu
de NetGuard V1
```

Cette distinction doit être conservée lors de l’interprétation des limites du système.

Une fonctionnalité absente volontairement ne doit pas être présentée comme une vulnérabilité.

Une rupture d’hypothèse ne doit pas être présentée comme une capacité déjà accordée à l’attaquant principal.

Un risque résiduel ne doit pas être présenté comme supprimé uniquement parce qu’une mesure de réduction existe.

### Synthèse des non-garanties principales

NetGuard V1 ne garantit pas :

```text
une visibilité complète du réseau

l’absence totale de pertes

le traitement sans dégradation
d’une charge arbitraire

la détection de toute activité hostile

l’absence de faux positifs

l’absence de faux négatifs

l’identité réelle de l’auteur
d’un trafic observé

l’authenticité de toutes
les informations réseau

l’exactitude absolue
de toutes les sources temporelles

une disponibilité absolue

une persistance parfaite
face à toute défaillance

une confidentialité maintenue
après compromission complète
de l’environnement

une observabilité omnisciente

la sécurité après remplacement
arbitraire du code exécuté

la résistance à un administrateur
totalement privilégié et hostile

une couverture IDS universelle

une réponse automatique
aux comportements détectés
```

Ces non-garanties ne réduisent pas les objectifs de qualité de NetGuard.

Elles définissent les limites dans lesquelles ses résultats peuvent être interprétés correctement.

Le principe central est :

```text
NetGuard cherche à être
correct sur ce qu’il sait

et explicite
sur ce qu’il ne sait pas
```

### Portée de 0.5.8

Cette étape explicite les risques qui subsistent malgré les mesures de réduction ainsi que les garanties que NetGuard V1 ne prétend pas fournir. Elle formalise notamment les limites de visibilité, les pertes possibles sous saturation, l’évasion analytique, les faux positifs et faux négatifs, l’absence d’attribution certaine, les limites temporelles, de disponibilité, de persistance et d’observabilité, les ruptures des hypothèses de confiance et les fonctionnalités volontairement hors périmètre, afin que les résultats de NetGuard puissent être interprétés sans leur attribuer des garanties supérieures à celles réellement fournies.



