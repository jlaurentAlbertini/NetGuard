# Développement


Conventions initiales : code Python sous `backend/src/netguard/`, tests séparés par niveau, format des fichiers défini par `.editorconfig`. Le packaging minimal est décrit ci-dessous ; les règles d’import sont définies ci-dessous ; les conventions de modules et de types sont définies ci-dessous ; l’outillage de qualité reste aux étapes suivantes.

Avancer par petits incréments fonctionnels et commits cohérents. Chaque changement important doit inclure sa documentation et les tests adaptés. Les exigences expriment la cible ; leur présence dans la documentation ne vaut pas validation fonctionnelle.

## Structure Python — 0.4.1

Le projet Python est défini par `backend/pyproject.toml`, avec découverte des
packages `netguard` et `netguard.*` sous `backend/src/`. La racine du dépôt et
`frontend/` ne font pas partie du package Python.

Choix minimaux : `setuptools>=61` comme dépendance de construction uniquement,
aucune dépendance runtime et version statique `0.0.0` pour le squelette (pas une
release fonctionnelle). Python ≥ 3.11 constitue le plancher initial retenu en
l’absence de version déjà fixée ; la matrice de compatibilité sera validée avec
l’outillage ultérieur. Configuration conforme à la
[documentation setuptools](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).

Vérification ponctuelle des imports depuis la racine, sans installation :

```sh
PYTHONPATH=backend/src python3 -B -c "import netguard.core.network; import netguard.core.detection.rules; import netguard.core.alerts; import netguard.application; import netguard.infrastructure.capture; import netguard.infrastructure.persistence; import netguard.infrastructure.observability; import netguard.interfaces.api; import netguard.interfaces.cli"
```

Ce `PYTHONPATH` ne vaut que pour la commande ; ce n’est pas une configuration
globale ni un mécanisme de validation des dépendances. Les règles de 0.4.2
ci-dessous encadrent les futures implémentations ; aucun outil de contrôle
architectural n’est installé à cette étape.

## Dépendances et imports Python — 0.4.2

Cette section est la référence pratique pour décider si un module peut importer
un autre module. Elle applique l’[architecture](architecture.md), notamment ses
sections 7 à 10, 12 et 28, ainsi que
[ADR-003](decisions/ADR-003-inward-dependencies.md). Elle ne redéfinit pas les
[modèles domaine](data-models.md) ni le [moteur](detection-engine.md).

### Direction des dépendances et matrice

La direction concerne les dépendances du code, pas le sens des appels à
l’exécution ou de circulation des données. Les noms de couches ci-dessous
correspondent aux packages `netguard.core`, `netguard.application`,
`netguard.infrastructure` et `netguard.interfaces`.

| Depuis / vers | Core | Application | Infrastructure | Interfaces |
|---|---|---|---|---|
| Core | Oui | Non | Non | Non |
| Application | Oui | Oui | Non | Non |
| Infrastructure | Oui | Oui si nécessaire | Oui | Non |
| Interfaces | Oui si nécessaire | Oui | Non | Oui |

« Oui » signifie autorisé **lorsque nécessaire**, jamais obligatoire. La diagonale
n’autorise ni les cycles ni des dépendances internes sans justification. La seule
exception d’assemblage est le Composition Root décrit plus bas.

- **D1 — Core indépendant.** Aucun import d’Application, Infrastructure ou
  Interfaces. La bibliothèque standard est autorisée. Une bibliothèque tierce
  future doit répondre à une nécessité domaine réelle sans coupler le Core à
  la capture, au stockage, à un framework HTTP ou à un framework CLI.
- **D2 — Application vers Core.** Application orchestre les cas d’utilisation
  et peut importer le Core. Elle n’importe ni Infrastructure ni Interfaces ;
  ses besoins externes sont exprimés par des contrats internes.
- **D3 — Infrastructure vers les couches internes.** Infrastructure importe
  les contrats qu’elle implémente et les modèles nécessaires à ses adaptations.
  Elle contient les mécanismes de capture, lecture PCAP, persistance et
  observabilité technique. Leurs objets natifs restent à cette frontière.
- **D4 — Interfaces vers Application.** API et CLI traduisent les interactions
  externes en appels applicatifs. Elles peuvent utiliser des modèles du Core
  pour l’adaptation ou la sérialisation, sans implémenter de détection ni
  contourner les cas d’utilisation par cette autorisation.
- **D5 — Pas de dépendance entre Infrastructure et Interfaces.** Aucun import
  dans un sens ou dans l’autre hors assemblage explicitement identifié. Un
  besoin futur contraire exige une réévaluation documentée ; un import indirect
  ou un réexport ne constitue pas un contournement acceptable.

### Propriété des contrats et inversion des dépendances

Un contrat appartient à la couche qui **exprime le besoin**, près de la capacité
concernée. Son implémentation technique appartient à la couche externe adaptée.

Par exemple, si Application demande la persistance d’une Alert :

```text
Application → contrat AlertRepository possédé par Application
Infrastructure.persistence → implémente ce contrat
```

Application ne dépend pas de `infrastructure.persistence` pour connaître son
contrat. Un futur `application/alert_repository.py` peut suffire. Un regroupement
local `application/ports/` n’est pertinent que si plusieurs contrats cohérents
le justifient réellement. Un contrat de domaine appartient de même à la zone
concernée du Core.

Aucun package global `ports/`, `contracts/`, `common/` ou `shared/` n’est créé
pour centraliser indistinctement les abstractions. `Protocol`, ABC, callable ou
une autre forme seront choisis lors d’un besoin concret, pas à cette étape.

L’inversion des dépendances protège une frontière ou un besoin de substitution
et de testabilité. Elle n’impose ni interface par classe, ni repository par
modèle, ni service par fonction, ni abstraction autour de chaque bibliothèque.

### Composition Root : exception d’assemblage

Un Composition Root peut importer les couches et implémentations nécessaires
pour construire les composants et fournir les adaptateurs aux contrats attendus :

```text
AlertRepository ← SqlAlertRepository
```

Ces noms sont illustratifs, sans choix de technologie supplémentaire. Cette
exception concerne uniquement la frontière d’assemblage, pas tous les modules
voisins ni les cas d’utilisation Application. Aucun composant interne ne doit
importer le Composition Root pour récupérer un service ou une implémentation.

Les contrats et le code applicatif ordinaire restent indépendants des types
concrets d’infrastructure. Plusieurs modes exécutables peuvent avoir des points
d’assemblage distincts. Leur emplacement concret sera défini ultérieurement ;
aucun fichier `composition_root.py` n’est créé pour 0.4.2.

### Normalisation : adaptation dans Infrastructure, invariants dans Core

La traduction dépendante d’une source ou d’un format appartient à Infrastructure,
près de l’adaptateur qui connaît cette représentation. Pour une source de capture,
elle pourra rester locale à `infrastructure.capture` tant que cela suffit.

```text
Représentation externe
    ↓ adaptateur / normalisation dans Infrastructure
Observation conforme au contrat du Core
    ↓ Application / analyse
Détecteur
```

Le Core définit la signification, les types et les invariants des observations.
Infrastructure interprète la source et construit ces valeurs en respectant ces
invariants ; elle n’invente pas les faits manquants. Les validations du format
externe restent dans l’adaptateur, celles du contrat métier appartiennent au Core.

Un objet de bibliothèque de capture, une session SQL ou un objet de requête HTTP
ne traverse pas la frontière pour devenir une observation domaine. Application
et les détecteurs ne décodent pas directement ces objets techniques.

Aucun package global `normalization/` n’est nécessaire. Une factorisation entre
sources sera décidée seulement si une logique réellement commune apparaît, en
plaçant cette logique selon ses dépendances et sa responsabilité.

### Représentations aux frontières

Modèles de capture, domaine, persistance et API ne sont pas automatiquement le
même objet. Les conversions vers le stockage appartiennent à Infrastructure ;
les adaptations HTTP appartiennent à Interfaces. Une représentation distincte
est introduite lorsque les contraintes de la frontière la justifient, sans créer
systématiquement des variantes DTO, Entity, Schema et Model de chaque concept.

Le frontend reste dans `frontend/`, hors du package Python. `interfaces/api/`
est uniquement le futur adaptateur HTTP backend.

### Conventions d’import et packages

- Privilégier les imports absolus entre packages NetGuard, par exemple
  `import netguard.core.network`, puis des imports explicites depuis les modules
  concrets lorsqu’ils existeront.
- Les imports relatifs locaux restent possibles dans un package cohérent si cela
  améliore la lisibilité. Éviter les remontées sur plusieurs niveaux.
- Les `__init__.py` restent minimaux, actuellement vides. Aucun import `*`, aucune
  façade globale ni réexport massif pour cacher ou raccourcir les dépendances.
  Les API publiques seront définies au besoin.
- Les règles s’appliquent aussi aux dépendances de typage et aux imports locaux
  ou dynamiques : leur syntaxe ne modifie pas leur sens architectural.

Les cycles entre couches sont interdits. Un cycle interne à une zone fonctionnelle
signale une séparation à revoir ; il ne doit pas être masqué par un import tardif,
un import dans une fonction, un réexport ou `TYPE_CHECKING`. Ce dernier reste
légitime pour le typage si la dépendance elle-même respecte l’architecture.

Le code NetGuard ne modifie pas `sys.path` (`append`, `insert` ou autre mécanisme).
Les imports fonctionnent grâce au packaging et à un environnement approprié au
src layout. Le `PYTHONPATH` ponctuel montré en 0.4.1 est un moyen de vérification,
pas une réparation d’une structure incorrecte ni une dépendance cachée du code.

### Relations à l’intérieur des couches

- **Core :** `detection` peut utiliser les observations de `network` ; `alerts`
  peut utiliser les concepts analytiques nécessaires à son interprétation. Pas
  de matrice plus rigide sans implémentation concrète. Respecter les responsabilités
  et éviter les cycles ; les détecteurs restent indépendants les uns des autres.
- **Infrastructure :** `capture`, `persistence` et `observability` sont des
  capacités distinctes. `capture` n’importe pas `persistence` pour organiser
  directement le stockage des paquets : ce workflow relève d’Application.
  Une intégration technique d’observabilité pourra être définie au besoin,
  sans mécanisme partagé ajouté maintenant.
- **Interfaces :** API et CLI appellent les mêmes cas d’utilisation Application
  sans s’appeler mutuellement. Ni API → CLI ni CLI → API HTTP locale ne sert
  d’architecture interne par défaut. Un partage éventuel relève de la capacité
  applicative ou d’une abstraction commune réellement justifiée.

### Placement des dépendances tierces

Les bibliothèques sont importées par la couche qui utilise leur mécanisme :

| Mécanisme futur | Couche |
|---|---|
| Capture, décodage de formats externes, lecture PCAP | Infrastructure |
| Driver SQL, ORM, observabilité technique | Infrastructure |
| Framework HTTP ou CLI | Interfaces |
| Bibliothèque répondant à un besoin domaine justifié | Core, sans couplage infrastructure |

Ces exemples ne sélectionnent ni n’installent de nouveaux outils. Application
ne dépend pas d’un framework HTTP ou d’une bibliothèque de capture. Un besoin
externe est fourni via le contrat interne approprié, sans imposer une abstraction
à chaque opération.

### Vérification du squelette et portée

À l’issue de 0.4.2, les 14 `__init__.py` de 0.4.1 sont toujours vides : aucun
import, réexport, cycle ou accès technique n’est présent. `pyproject.toml` et
l’arborescence Python restent inchangés, sans dépendance runtime.

La vérification de cette étape est une inspection du squelette et une revue de
cohérence documentaire. Aucun contrôleur AST, import-linter, hook, test fictif,
configuration CI ou package anticipé n’est ajouté. Les contrats Python concrets,
les Composition Roots, les outils de qualité et les implémentations sont reportés
aux étapes correspondantes.

## Conventions de modules et de types — 0.4.3

Cette section définit les conventions de modules, de typage et de représentation
Python retenues pour NetGuard.

Elle complète les règles de structure et de dépendances précédentes. Son objectif
n’est pas d’imposer une représentation Python unique à tous les concepts, mais
de préserver les distinctions sémantiques définies par le projet, de maintenir
la lisibilité du code et d’éviter les abstractions prématurées.

### Vocabulaire canonique du domaine

Les noms du code utilisent autant que possible le vocabulaire canonique défini
par la documentation NetGuard.

Les synonymes susceptibles d’introduire une ambiguïté sémantique sont évités.

Les distinctions documentées suivantes doivent notamment rester visibles dans
le vocabulaire du code :

```text
PacketObservation ≠ FlowObservation ≠ Flow
DetectionResult ≠ Alert
sensor_id ≠ network_scope_id
observation time ≠ processing time
```

Une abréviation reste acceptable lorsqu’elle est conventionnelle dans le domaine
ou clairement locale et qu’elle ne réduit pas la compréhension.

Des termes tels que `ip`, `tcp`, `udp`, `ipv4` ou `ipv6` sont naturels. Une
variable locale telle que `src` ou `dst` peut également être acceptable dans un
contexte suffisamment restreint et évident.

La documentation définit la sémantique canonique du projet ; elle n’impose pas
qu’un concept documenté corresponde systématiquement à une classe ou à un module
Python portant exactement le même nom.

### Cohésion des modules

Les modules sont organisés d’abord selon leur cohésion fonctionnelle et
sémantique.

Un module peut contenir plusieurs types ou fonctions lorsqu’ils représentent un
même concept ou une même responsabilité cohérente.

Inversement, un concept complexe peut évoluer d’un module vers un package lorsque
plusieurs responsabilités internes deviennent clairement séparables.

La taille d’un fichier constitue un signal de complexité, mais aucune limite
arbitraire de lignes n’est imposée.

Par exemple, une règle de détection peut initialement être représentée par :

```text
port_scan.py
```

puis évoluer, si sa complexité réelle le justifie, vers :

```text
port_scan/
├── detector.py
├── state.py
└── config.py
```

Cette évolution doit répondre à une complexité réelle et non à une architecture
hypothétique anticipée.

### API publique et éléments internes

Le préfixe Python `_` signale un détail d’implémentation ou une API qui n’est pas
destinée à constituer un contrat public stable.

Par exemple :

```python
def _decode_tcp_flags(...):
    ...
```

ou :

```python
class _MutablePortScanState:
    ...
```

peuvent représenter des détails internes.

Ce préfixe :

- n’est pas un mécanisme de sécurité ;
- ne crée pas une frontière architecturale ;
- n’autorise pas le contournement des règles de dépendance.

Un composant du Core ne peut donc pas dépendre d’un composant Infrastructure
simplement parce que celui-ci commence par `_`.

Les `__init__.py` restent minimaux et ne doivent pas être utilisés pour masquer
les dépendances par des réexports massifs.

### Typage explicite aux interfaces significatives

Les interfaces significatives du code NetGuard sont explicitement typées.

Cela concerne notamment :

- les fonctions et méthodes publiques ou structurantes ;
- les modèles domaine ;
- les contrats entre composants ;
- les frontières entre couches ;
- les attributs dont le type porte une distinction sémantique importante.

L’inférence locale reste utilisée lorsqu’elle est évidente. Il n’est pas
nécessaire d’annoter explicitement une variable locale lorsque son type est
trivialement déterminé par son initialisation.

NetGuard utilise la syntaxe de typage moderne compatible avec sa version minimale
de Python.

Par exemple :

```python
def process(
    observation: PacketObservation,
) -> DetectionResult | None:
    ...
```

et :

```python
list[Evidence]
dict[str, DetectorConfig]
set[int]
```

sont préférés aux anciennes formes équivalentes issues de `typing` lorsque la
version minimale de Python permet la syntaxe moderne.

`Any` ne doit pas être utilisé pour contourner une difficulté de modélisation.

Son usage peut néanmoins être nécessaire à certaines frontières avec des
bibliothèques externes insuffisamment typées. Dans ce cas, il doit rester
localisé à la frontière technique et ne pas contaminer inutilement les couches
internes.

Le choix d’un vérificateur statique tel que mypy ou Pyright n’est pas effectué
dans cette étape.

### Immutabilité sémantique

Les faits, valeurs, identifiants, clés et résultats stabilisés sont conçus comme
immuables lorsque leur sémantique l’exige.

Cela concerne notamment les catégories de concepts déjà identifiées dans le
modèle NetGuard, telles que :

- les observations stabilisées ;
- les identifiants et clés ;
- les résultats analytiques stabilisés ;
- les Evidence stabilisées.

L’immutabilité doit concerner les données internes pertinentes et ne doit pas
être uniquement superficielle.

Par exemple, une dataclass `frozen=True` contenant une `list` mutable ne garantit
pas à elle seule une véritable immutabilité de son contenu.

Des structures telles que :

```python
tuple[int, ...]
frozenset[int]
```

peuvent être utilisées lorsqu’elles correspondent réellement à la sémantique
attendue. Elles ne sont toutefois pas imposées systématiquement.

La mutabilité reste autorisée lorsqu’elle fait explicitement partie de la
responsabilité du composant.

C’est notamment le cas potentiel :

- d’un état analytique actif ;
- d’un état de construction de Flow ;
- d’autres structures de travail dont la fonction est précisément d’évoluer.

Cette mutabilité doit rester locale, contrôlée et possédée par le composant
responsable.

### Utilisation de `dataclass`

`dataclass` est une option naturelle pour représenter certaines structures de
données domaine simples.

Elle peut notamment convenir à :

- des objets valeur ;
- des observations ;
- des résultats stabilisés ;
- de petites structures possédant principalement des données et des invariants
  simples.

Elle n’est cependant pas imposée comme représentation universelle des modèles
NetGuard.

Une classe classique ou une autre représentation peut être plus appropriée
lorsqu’un type possède :

- des invariants complexes ;
- une construction contrôlée ;
- un comportement important ;
- une représentation interne qui doit rester cachée.

De même, `frozen=True` ou `slots=True` ne sont pas appliqués mécaniquement à
toutes les dataclasses.

Le mécanisme Python choisi doit servir la sémantique et les contraintes réelles
du type.

NetGuard ne définit pas de `BaseModel` domaine universel.

### `Enum`, `Literal` et ensembles fermés

`Enum` ou `Literal` ne sont utilisés que lorsque l’ensemble de valeurs est
réellement fermé pour le contrat concerné.

Une limitation actuelle d’implémentation ne doit pas fermer artificiellement
le modèle.

Par exemple :

```text
le détecteur actuel analyse TCP et UDP
```

ne signifie pas nécessairement :

```text
le modèle réseau NetGuard ne peut représenter que TCP et UDP
```

Cette règle préserve la distinction entre :

```text
ce que le modèle peut représenter
≠
ce que l’adapter peut observer ou décoder
≠
ce que le détecteur peut analyser
```

Un `Enum` convient particulièrement lorsqu’une notion domaine possède un
ensemble fermé, nommé et stable de valeurs.

`Literal` peut convenir à une contrainte locale ou légère principalement utile
au typage.

Si une notion initialement légère acquiert une sémantique propre, un usage
transversal, des invariants ou un comportement, elle peut évoluer vers un type
domaine dédié.

Les paramètres métier configurables ne doivent pas être remplacés par des
nombres ou chaînes magiques codés en dur.

Par exemple, un seuil de détection ne doit pas être dispersé dans l’algorithme
sous la forme :

```python
if count >= 20:
    ...
```

si `20` représente un paramètre métier configurable.

La configuration de ces paramètres est traitée plus précisément dans l’étape
dédiée à la configuration.

### `None` et absence d’information

`None` n’est utilisé que lorsque son sens d’absence est unique et non ambigu
dans le contrat concerné.

NetGuard distingue conceptuellement plusieurs situations possibles, notamment :

```text
non applicable
≠
inconnu
≠
non fourni
≠
non observable
```

Ces distinctions ne doivent cependant pas produire automatiquement une
hiérarchie complexe de types pour chaque champ.

Plusieurs formes d’absence sont représentées distinctement uniquement lorsqu’elles
ont une conséquence :

- sémantique ;
- analytique ;
- de validation ;
- d’explicabilité.

Lorsqu’une seule forme d’absence est pertinente pour un champ donné, une
annotation telle que :

```python
int | None
```

peut être parfaitement appropriée, à condition que la signification de `None`
soit définie par le contrat du type.

La même règle s’applique aux collections.

Une collection vide ne doit pas être utilisée pour représenter simultanément
plusieurs états sémantiquement différents tels que :

```text
aucune valeur observée
```

et :

```text
information indisponible
```

lorsque cette distinction influence l’analyse.

### Forme des contrats Python

Lorsqu’une abstraction est nécessaire, sa représentation Python est choisie
selon le besoin concret.

Un contrat peut notamment être représenté par :

- `Protocol` ;
- une classe abstraite ;
- un callable typé ;
- une fonction ;
- une autre abstraction appropriée.

Aucun mécanisme unique n’est imposé à l’ensemble du projet.

Par exemple, un contrat très simple peut être représenté plus naturellement par
un callable qu’en créant une hiérarchie de classes.

Inversement, une abstraction plus riche peut justifier un `Protocol` ou une
autre représentation explicite.

Cette convention complète le principe défini lors de 0.4.2 :

> le contrat appartient à la couche qui exprime le besoin.

La forme Python de ce contrat dépend de sa sémantique réelle.

### Abstractions proportionnées au besoin

NetGuard n’introduit pas de hiérarchie ou d’abstraction uniquement pour anticiper
une extensibilité hypothétique.

La forme la plus simple qui préserve correctement :

- la sémantique ;
- la testabilité ;
- les frontières architecturales ;
- l’évolution raisonnablement prévisible du composant

est préférée.

Cette convention interdit notamment de considérer comme obligatoires :

- une interface pour chaque classe ;
- un repository pour chaque modèle ;
- un service pour chaque fonction ;
- une classe abstraite pour chaque composant ;
- un wrapper autour de chaque fonction de la bibliothèque standard.

Elle n’interdit pas une abstraction complexe lorsqu’une complexité réelle du
domaine ou de l’architecture la justifie.

### Objets valeur

Un objet valeur spécifique est introduit lorsqu’il apporte une protection ou
une sémantique réelle.

Cela peut notamment être justifié lorsqu’il :

- protège un invariant ;
- distingue des valeurs autrement facilement confondables ;
- centralise une validation intrinsèque ;
- porte une sémantique propre utilisée à plusieurs endroits.

Des concepts tels que :

```text
NetworkScopeId
SensorId
RuleId
```

peuvent par exemple justifier des types distincts s’il est nécessaire d’empêcher
leur confusion.

À l’inverse, les rôles purement contextuels restent généralement exprimés par
le nom du champ.

Par exemple, une adresse IP n’a pas intrinsèquement le rôle de source ou de
destination.

Il est donc généralement préférable de représenter :

```python
source_ip: IPAddress
destination_ip: IPAddress
```

plutôt que de créer artificiellement :

```text
SourceIPAddress
DestinationIPAddress
```

Cette convention respecte le principe selon lequel source et destination
décrivent la direction de l’observation et non une propriété intrinsèque de
l’adresse.

Les types standards de Python restent utilisés lorsqu’ils expriment déjà
correctement la sémantique.

Pour les adresses IP, les types appropriés de la bibliothèque standard peuvent
donc être préférés à une réimplémentation NetGuard sans valeur ajoutée.

### Alias de types

Un alias de type peut être utilisé pour nommer une structure complexe ou une
union et améliorer la lisibilité.

Par exemple :

```python
IPAddress = IPv4Address | IPv6Address
```

peut exprimer clairement qu’une API accepte les deux familles d’adresses.

Un alias ne doit cependant pas être présenté comme une protection contre la
confusion entre valeurs sémantiquement différentes lorsqu’il ne crée pas
réellement de nouveau type.

Par exemple :

```python
SensorId = str
NetworkScopeId = str
RuleId = str
```

améliorerait éventuellement la documentation du code, mais ne permettrait pas
à lui seul au système de types d’empêcher le mélange de ces valeurs.

Lorsqu’une distinction doit être réellement protégée, une représentation de
type appropriée doit être choisie.

### Validation des invariants à la frontière du type

Les invariants intrinsèques à un type sont validés à la frontière de construction
appropriée de ce type.

Une fois un objet domaine valide construit, les couches internes peuvent
s’appuyer sur son contrat sans répéter systématiquement les mêmes validations.

Le principe général est :

```text
donnée externe ou non fiable
        ↓
adaptation / construction
        ↓
validation des invariants intrinsèques
        ↓
objet domaine valide
        ↓
utilisation interne
```

Cette convention ne signifie pas que NetGuard doit effectuer une validation
exhaustive de la réalité réseau.

La validation garantit la cohérence du contrat du modèle, pas des propriétés que
l’observation ne permet pas de connaître.

Par exemple, la construction d’un objet représentant un port peut vérifier son
domaine de valeurs si cette responsabilité appartient à ce type.

Elle ne peut pas conclure qu’un service particulier fonctionne réellement
derrière ce port.

Les règles de validation doivent donc respecter la distinction fondamentale :

```text
cohérence du modèle
≠
vérité complète sur le réseau observé
```

La normalisation dépendante d’une source technique reste placée à la frontière
Infrastructure/Core conformément aux règles de dépendance définies précédemment.

### Portée de 0.4.3

Ces conventions complètent les règles de structure et de dépendances sans
imposer prématurément :

- un framework de modèles ;
- une bibliothèque de validation ;
- un outil de vérification statique ;
- une hiérarchie universelle de classes ;
- un système générique de DTO ;
- une architecture de contrats uniforme.

Les décisions concernant les erreurs et résultats, la configuration, le logging,
l’observabilité et l’architecture des tests appartiennent aux sous-étapes
suivantes.

## Erreurs et résultats — 0.4.4

Cette section définit la manière dont NetGuard distingue les résultats métier
normaux, les entrées rejetées, les défaillances techniques et les violations
d'invariants.

L'objectif n'est pas d'introduire un framework générique de gestion des erreurs,
mais de préserver la sémantique de chaque situation et de permettre à la couche
responsable d'appliquer une politique explicite.

Les distinctions fondamentales sont :

```text
résultat métier normal
≠
branche normale sans résultat positif
≠
entrée externe rejetée
≠
défaillance d'une opération
≠
violation d'un invariant interne
```

La représentation Python choisie dépend du contrat concerné. NetGuard n'impose
donc ni exception pour toute situation non positive, ni wrapper de résultat pour
toute opération.

### Non-éligibilité et absence de détection

La non-éligibilité d'une observation et l'absence de déclenchement d'une règle
sont des situations normales du traitement.

Elles ne constituent pas des exceptions.

Ces deux situations restent néanmoins conceptuellement distinctes :

```text
observation non éligible
≠
observation éligible mais règle non déclenchée
```

Par exemple, un détecteur limité à certaines observations ne doit pas lever une
exception chaque fois qu'il reçoit une observation qui ne satisfait pas ses
préconditions analytiques.

De même, l'absence de détection signifie uniquement que la règle concernée n'a
pas produit de conclusion positive pour les entrées considérées. Elle ne constitue
pas une preuve d'absence de comportement malveillant.

Cette distinction n'impose pas la création d'un objet résultat pour chaque
observation ignorée ou chaque règle non déclenchée. Le contrat concret du
détecteur peut utiliser la représentation la plus simple qui conserve la
sémantique nécessaire.

### `DetectionResult` reste un résultat métier

`DetectionResult` désigne une conclusion métier positive produite par un
détecteur.

Il appartient au modèle de détection :

```text
Observation
    ↓
Detector
    ↓
DetectionResult
    ↓
Alert
```

Il ne constitue pas un wrapper générique indiquant le succès ou l'échec d'une
opération technique.

Il ne doit donc pas être transformé en structure générale contenant par exemple :

```text
success
error
exception
technical_status
```

Les erreurs de capture, de persistance, de configuration ou d'autres mécanismes
techniques restent distinctes du résultat analytique produit par un détecteur.

### Pas de type `Result` universel

NetGuard n'impose pas de type générique tel que :

```text
Result[T, E]
Either[T, E]
Success[T] / Failure[E]
```

à l'ensemble du code.

Une branche attendue d'un contrat peut être représentée explicitement lorsqu'une
telle représentation améliore réellement la sémantique ou oblige l'appelant à
prendre une décision pertinente.

Les défaillances exceptionnelles peuvent utiliser les exceptions Python.

Le choix dépend donc de la nature de l'opération :

```text
branche attendue du contrat
→ valeur ou résultat explicite lorsque nécessaire

impossibilité exceptionnelle d'honorer le contrat
→ exception appropriée
```

Cette convention n'interdit pas l'introduction future d'un type de résultat local
pour une capacité qui en aurait réellement besoin. Elle interdit seulement d'en
faire une abstraction universelle sans nécessité démontrée.

### Usage des exceptions

Une exception représente une impossibilité exceptionnelle de respecter le
contrat de l'opération en cours.

Des situations telles que :

```text
fichier PCAP demandé mais illisible
connexion nécessaire au stockage perdue
configuration requise impossible à charger
invariant interne impossible rencontré
```

peuvent justifier une exception.

À l'inverse, des situations telles que :

```text
observation non éligible
aucune détection produite
seuil analytique non atteint
absence explicitement autorisée par le contrat
```

ne doivent normalement pas être représentées comme des exceptions.

Une exception n'indique pas nécessairement un bug dans NetGuard. Une dépendance
externe indisponible peut produire une situation exceptionnelle sans constituer
une erreur de programmation.

La distinction pertinente est donc :

```text
branche normale prévue par le contrat
≠
impossibilité exceptionnelle d'exécuter ce contrat
```

### Rejet des données externes invalides

Les données provenant du réseau, d'un fichier, d'une API ou de toute autre source
externe sont considérées comme non fiables tant qu'elles n'ont pas satisfait les
validations nécessaires.

Lorsqu'une donnée externe ne permet pas de construire une représentation domaine
conforme à son contrat, NetGuard ne fabrique pas de valeur de remplacement.

Le principe est :

```text
donnée externe
    ↓
adaptation / décodage
    ↓
validation
    ↓
    ├── objet domaine valide
    │
    └── rejet explicite
```

Une information manquante ou invalide ne doit donc pas être remplacée par une
valeur fictive telle que `0`, une adresse arbitraire ou une chaîne vide lorsque
cette valeur modifierait la sémantique de l'observation.

Le rejet d'une entrée ne détermine pas à lui seul si l'ensemble du traitement
doit s'arrêter.

La politique dépend du niveau concerné.

Par exemple :

```text
élément individuel malformé
→ rejet possible de cet élément
→ poursuite possible de la source

source entière inutilisable
→ impossibilité de poursuivre cette opération
```

Le caractère récupérable ou fatal d'une erreur dépend donc du contexte et de la
politique du composant responsable. Il n'est pas encodé comme propriété
universelle de toute exception.

Les rejets significatifs doivent pouvoir être rendus observables conformément
aux conventions d'observabilité qui seront précisées dans l'étape dédiée.

### Validation des objets domaine

Les invariants intrinsèques aux objets domaine sont validés conformément aux
conventions de 0.4.3.

Pour des violations simples du contrat de construction, les exceptions standards
de Python, telles que `ValueError` ou `TypeError`, peuvent être suffisantes
lorsqu'elles expriment correctement le problème.

NetGuard ne crée pas automatiquement une exception spécifique pour chaque objet
valeur ou chaque champ invalide.

Une exception domaine spécifique devient pertinente lorsqu'elle représente une
distinction sémantique que l'appelant doit réellement reconnaître ou traiter
différemment.

Cette convention évite d'introduire prématurément des hiérarchies telles que :

```text
NetGuardError
└── DomainError
    └── ValidationError
        └── NetworkValidationError
            └── PortValidationError
```

sans besoin concret.

### Pas de hiérarchie globale d'exceptions imposée

NetGuard n'impose pas de classe racine universelle telle que :

```python
class NetGuardError(Exception):
    ...
```

pour toutes les erreurs du projet.

Les exceptions spécifiques sont définies près de la capacité ou du contrat qui
leur donne un sens.

Une hiérarchie commune pourra être introduite ultérieurement si plusieurs
composants ont réellement besoin de traiter un ensemble cohérent d'erreurs de
manière commune.

La hiérarchie d'exceptions doit donc émerger d'un besoin de traitement réel et
non d'une volonté de classifier à l'avance toutes les défaillances possibles.

### Propriété de la sémantique d'échec

Lorsqu'un contrat abstrait possède des catégories d'échec significatives pour
son appelant, leur sémantique appartient à la couche qui possède ce contrat.

Cette règle prolonge la convention de 0.4.2 selon laquelle le contrat appartient
à la couche qui exprime le besoin.

Par exemple, si Application possède un contrat de persistance d'Alert :

```text
Application
    ↓
contrat de persistance
    ↑
Infrastructure
```

Application ne doit pas dépendre directement des exceptions spécifiques d'un
driver SQL pour comprendre qu'une opération de persistance a échoué.

Cela n'impose pas de créer une exception par méthode ou par implémentation. Une
catégorie d'échec n'est introduite dans le contrat que si l'appelant a réellement
besoin de cette distinction.

### Traduction des exceptions aux frontières

Une exception issue d'une technologie externe peut être traduite lorsqu'elle
traverse une frontière qui doit masquer cette technologie et que l'appelant a
besoin d'une sémantique d'échec appartenant à son propre contrat.

Le principe est :

```text
exception technique externe
        ↓
adaptateur
        ↓
traduction si nécessaire
        ↓
erreur exprimée dans le vocabulaire du contrat
```

Cette traduction n'est pas mécanique.

Les captures d'exceptions doivent rester aussi étroites que possible afin de ne
pas transformer accidentellement une erreur de programmation en erreur technique
attendue.

Par exemple, un `KeyError` inattendu provoqué par un bug interne ne doit pas être
automatiquement converti en « stockage indisponible » simplement parce qu'il est
survenu dans un adaptateur de persistance.

Lorsqu'une exception est traduite, la cause originale peut être conservée pour
le diagnostic à l'aide du chaînage d'exceptions Python :

```python
raise PersistenceUnavailable(...) from exc
```

Le nom ci-dessus est illustratif ; aucune hiérarchie d'exceptions de persistance
n'est imposée à cette étape.

### Le texte d'une exception n'est pas un contrat

Le programme ne doit pas déterminer sa logique en analysant le texte destiné à
l'affichage humain d'une exception.

Un traitement tel que :

```python
if "invalid port" in str(exc):
    ...
```

ne constitue pas un contrat stable.

Lorsqu'un appelant doit distinguer plusieurs situations, cette distinction doit
être représentée explicitement par le type, une donnée structurée ou une valeur
prévue par le contrat.

Le message d'une exception reste destiné principalement au diagnostic humain.

### `assert` et validation runtime

`assert` n'est pas utilisé pour valider les données externes, la configuration
ou les invariants runtime dont dépend la correction de NetGuard.

Une assertion Python peut être désactivée et ne constitue donc pas un mécanisme
de validation fiable pour une donnée non fiable.

Par exemple :

```python
assert 0 <= port <= 65535
```

ne doit pas constituer la validation d'un port provenant d'une source externe.

Les assertions peuvent éventuellement documenter certaines hypothèses internes
de développement dont la violation indique un défaut de programmation, mais
elles ne remplacent pas une validation nécessaire au fonctionnement correct du
programme.

### Captures larges et confinement des défaillances

Une capture large telle que :

```python
except Exception:
    ...
```

n'est acceptable qu'à une frontière explicite de confinement ou de cycle de vie
où une politique de défaillance est définie.

Elle ne doit jamais transformer silencieusement une défaillance en succès.

Le comportement suivant est donc interdit :

```python
try:
    detector.process(observation)
except Exception:
    pass
```

Une frontière supérieure peut en revanche avoir besoin d'empêcher la défaillance
d'un composant de provoquer immédiatement la perte de contrôle de l'ensemble du
processus.

Dans ce cas, la capture doit être associée à une politique explicite, par exemple :

```text
défaillance identifiée
        ↓
confinement
        ↓
état évalué
        ↓
politique de reprise, isolation ou arrêt
```

La journalisation précise et les métriques associées seront définies lors de
l'étape d'observabilité.

### Défaillance d'un composant avec état

La capture d'une exception provenant d'un composant stateful ne permet pas de
supposer que son état interne reste valide.

Un détecteur peut, par exemple, avoir modifié une partie de son état avant de
rencontrer une erreur :

```text
observation
    ↓
modification partielle de l'état
    ↓
exception
```

Continuer immédiatement avec le même état pourrait alors produire des résultats
incorrects ou non déterministes.

Une politique de reprise doit donc soit garantir explicitement que l'opération
n'a pas compromis l'état, soit appliquer une mesure appropriée telle que :

```text
réinitialisation
isolation
désactivation contrôlée
arrêt du traitement concerné
```

selon les garanties du composant.

NetGuard n'impose pas de mécanisme transactionnel générique aux détecteurs. La
convention interdit uniquement de considérer :

```text
exception capturée
=
état nécessairement sain
```

### Défaillance technique après un résultat métier

Une défaillance d'infrastructure ne réécrit pas rétroactivement un résultat
métier déjà établi.

Par exemple :

```text
Detector
    ↓
DetectionResult
    ↓
Alert
    ↓
tentative de persistance
    ↓
échec du stockage
```

L'échec du stockage ne signifie pas que la conclusion analytique n'a jamais
existé.

Il signifie que la garantie de persistance attendue n'a pas été satisfaite.

Inversement, NetGuard ne doit pas prétendre qu'une Alert est durablement stockée
lorsque l'opération de persistance a échoué.

Cette séparation préserve la distinction entre :

```text
validité de la décision métier
≠
succès d'une opération technique ultérieure
```

### Saturation, limites et éviction

Les mécanismes prévus de saturation, limitation de capacité ou éviction ne sont
pas automatiquement représentés comme des exceptions pour chaque élément
concerné.

NetGuard possède des états et buffers bornés. Une politique de capacité peut donc
prévoir explicitement des situations telles que :

```text
buffer saturé
état évincé pour contrainte de capacité
entrée abandonnée selon une politique définie
```

Ces situations restent distinctes de l'expiration analytique normale et des bugs
internes.

En particulier :

```text
expiration analytique
≠
éviction pour contrainte de ressources
≠
défaillance interne
```

Les pertes ou dégradations connues susceptibles d'affecter l'analyse doivent
rester observables.

Si une saturation rend impossible la poursuite correcte d'une opération plus
large, cette opération peut elle-même échouer. La simple existence d'une limite
prévue ne constitue toutefois pas automatiquement une exception par élément.

### Arrêt contrôlé et annulation

Un arrêt contrôlé, une demande d'annulation ou un autre signal de cycle de vie
ne constitue pas une erreur métier.

Ces situations doivent rester distinctes :

```text
arrêt demandé
≠
entrée invalide
≠
échec analytique
≠
défaillance technique
```

Les mécanismes techniques précis dépendront du modèle d'exécution retenu.

NetGuard ne choisit pas à cette étape un framework asynchrone ni une primitive
particulière d'annulation. Les futures implémentations devront néanmoins préserver
la sémantique propre des signaux de cycle de vie au lieu de les absorber comme
des erreurs génériques.

### Reprises automatiques et retries

NetGuard n'applique pas de retry générique à toutes les erreurs techniques.

La sûreté d'une reprise dépend notamment :

- des effets déjà produits par l'opération ;
- de son éventuelle idempotence ;
- de l'état interne du composant ;
- de la nature de la défaillance ;
- des garanties fournies par le contrat.

Une réévaluation automatique d'un détecteur stateful après une exception pourrait,
par exemple, appliquer deux fois une observation si la première tentative avait
déjà modifié une partie de son état.

Une politique de retry appartient donc au composant ou à la couche qui possède
suffisamment d'information pour déterminer si la reprise est sûre.

Aucune politique globale du type :

```text
toute erreur technique
→ trois nouvelles tentatives
```

n'est définie.

### Erreurs exposées par les Interfaces

Les détails d'implémentation internes ne constituent pas directement le contrat
d'une API ou d'une CLI.

Une Interface traduit les résultats et erreurs applicatifs vers les concepts de
son protocole externe.

Pour une future API HTTP :

```text
résultat ou erreur Application
        ↓
Interfaces / API
        ↓
statut HTTP + représentation externe
```

Core et Application ne dépendent donc pas de codes HTTP pour exprimer leurs
erreurs.

De même, une API ne doit pas exposer comme contrat public les noms des exceptions
d'un driver SQL, d'une bibliothèque de capture ou d'une autre technologie
interne.

Aucun catalogue de codes d'erreur externes n'est défini à cette étape. Ces codes
seront introduits avec le contrat de l'Interface concernée lorsqu'un besoin réel
apparaîtra.

### Contexte porté par les erreurs

Une erreur peut contenir le contexte structuré nécessaire à son traitement ou à
son diagnostic.

Ce contexte reste toutefois proportionné au besoin.

Une exception ne doit pas devenir un conteneur arbitraire pour :

```text
payload réseau complet
secrets ou credentials
contenu externe sans limite
informations techniques sans utilité pour le diagnostic
```

Les mêmes principes de minimisation appliqués aux données NetGuard s'appliquent
au contexte d'erreur.

Cette convention ne définit pas encore quelles informations sont journalisées.
Les règles de logging, de redaction et d'observabilité sont traitées lors de
l'étape dédiée.

### Résultats partiels

Certaines opérations peuvent légitimement produire un résultat partiel.

Par exemple, le traitement d'une source contenant plusieurs éléments peut
éventuellement produire :

```text
éléments acceptés
+
éléments rejetés
```

lorsque la politique de la source autorise la poursuite.

Si cette information est pertinente pour l'appelant, le caractère partiel du
résultat doit être exprimé explicitement par le contrat de l'opération.

NetGuard n'impose cependant pas un wrapper universel tel que :

```text
BatchResult
PartialSuccess
OperationReport
```

à toutes les opérations.

Une telle structure n'est introduite que lorsqu'un cas d'utilisation concret la
rend nécessaire.

### Portée de 0.4.4

Les conventions de cette étape établissent une séparation claire entre :

```text
traitement normal
rejet d'une entrée
défaillance exceptionnelle
violation d'un invariant
politique de récupération
```

## Configuration — 0.4.5

Cette section définit la manière dont NetGuard charge, valide, distribue et
consomme sa configuration.

L'objectif est de conserver des dépendances explicites, de préserver le
déterminisme du Core et de distinguer les paramètres métier des mécanismes
techniques utilisés pour les fournir.

Les distinctions fondamentales sont :

```text
source de configuration
≠
configuration validée

configuration analytique
≠
configuration technique

valeur par défaut
≠
fallback silencieux après erreur

configuration globale d'assemblage
≠
état global consulté par les composants
```

Aucun format de fichier, framework de configuration ou bibliothèque spécialisée
n'est imposé à cette étape.

### Sources externes et Core

Le Core ne lit directement aucune source externe de configuration.

Il ne dépend notamment pas :

- des variables d'environnement ;
- des arguments CLI ;
- d'un fichier de configuration ;
- d'un framework de configuration ;
- d'un mécanisme de déploiement ;
- d'un secret manager.

Un détecteur ne doit donc pas contenir une logique telle que :

```python
threshold = int(os.getenv("PORT_SCAN_THRESHOLD", "20"))
```

La configuration brute est chargée et interprétée à une frontière appropriée
avant d'être transmise au composant métier.

Le flux attendu est :

```text
CLI / environnement / fichier / déploiement
                    ↓
            chargement externe
                    ↓
                  parsing
                    ↓
                validation
                    ↓
        configuration structurée
                    ↓
             composant concerné
```

Cette séparation garantit que le comportement du Core ne dépend pas implicitement
de l'environnement du processus.

Elle contribue notamment à la testabilité, au déterminisme et à la
reproductibilité des analyses.

### Configuration brute et configuration structurée

Les représentations brutes de configuration restent limitées aux frontières qui
les chargent ou les interprètent.

Des structures telles que :

```python
dict[str, object]
```

peuvent être adaptées à une étape de parsing, mais ne constituent pas par défaut
le contrat interne des composants NetGuard.

Un composant reçoit une représentation structurée correspondant à ses besoins
lorsque ses paramètres possèdent une sémantique ou des invariants propres.

Par exemple, une future règle de détection peut recevoir conceptuellement :

```text
PortScanConfig
├── threshold
└── window
```

plutôt que de rechercher ses valeurs dans une configuration globale.

Cela ne signifie pas qu'une classe `Config` doit être créée pour chaque fonction
ou chaque paramètre.

Une représentation dédiée est introduite lorsqu'elle protège une sémantique,
regroupe des paramètres cohérents ou porte des invariants utiles.

### Propriété de la configuration

Une configuration appartient conceptuellement au composant ou à la capacité
dont elle contrôle le comportement.

Par exemple :

```text
paramètres d'une règle de détection
→ Core / capacité de détection concernée

paramètres d'un adaptateur de capture
→ Infrastructure / capture

paramètres de persistance
→ Infrastructure / persistence

paramètres d'une API
→ Interfaces / API
```

Cette propriété ne dépend pas de l'endroit où les valeurs ont été initialement
chargées.

Un fichier unique peut éventuellement contenir plusieurs catégories de paramètres
sans que toutes ces catégories deviennent pour autant un seul modèle partagé par
l'ensemble de NetGuard.

### Pas de configuration globale comme dépendance implicite

NetGuard n'utilise pas un singleton global de configuration consulté
implicitement par les composants.

Une logique telle que :

```python
from netguard.config import settings

if count >= settings.port_scan_threshold:
    ...
```

créerait une dépendance cachée entre le comportement du composant et l'état
global du processus.

Les dépendances de configuration nécessaires au comportement d'un composant sont
rendues explicites lors de sa construction ou de l'appel approprié.

Par exemple :

```python
detector = PortScanDetector(config=port_scan_config)
```

peut être une représentation adaptée pour un détecteur dont la configuration
reste stable pendant sa durée de vie.

La forme exacte dépendra du composant concret ; l'injection explicite de la
configuration constitue la convention, pas cette syntaxe particulière.

### Configuration d'assemblage et configurations locales

Le point d'assemblage peut connaître plusieurs catégories de configuration afin
de construire l'application.

Conceptuellement :

```text
configuration chargée
        ↓
Composition Root
        ├── configuration analytique → Core
        ├── configuration capture    → Infrastructure
        ├── configuration stockage   → Infrastructure
        └── configuration interface  → Interfaces
```

Une représentation globale peut donc exister à la frontière d'assemblage si elle
simplifie réellement le chargement.

Elle ne devient pas pour autant un objet universel transmis à tous les
composants.

La distinction reste :

```text
configuration globale d'assemblage
≠
configuration consommée par chaque composant
```

Chaque composant reçoit uniquement les paramètres dont il a besoin.

### Configuration analytique et configuration technique

NetGuard distingue les paramètres qui modifient la sémantique d'une analyse des
paramètres qui contrôlent son exécution technique.

Par exemple :

```text
seuil de détection
fenêtre temporelle d'une règle
nombre minimal d'éléments distincts
```

sont des candidats naturels à une configuration analytique.

À l'inverse :

```text
capacité d'un buffer
timeout d'une connexion technique
adresse d'écoute d'une API
paramètre d'un driver de stockage
```

relèvent principalement de la configuration technique.

Un détecteur ne reçoit pas une configuration technique globale contenant des
paramètres sans rapport avec son comportement.

Cette séparation préserve le principe :

```text
configuration analytique
≠
configuration d'exécution
```

### Configuration technique affectant l'analyse

Une configuration techniquement motivée peut néanmoins avoir des conséquences
sur les garanties analytiques.

Par exemple, une limite sur la quantité d'état conservée peut provoquer une
éviction pour contrainte de ressources :

```text
limite de capacité
        ↓
état analytique évincé
        ↓
information potentiellement perdue
        ↓
analyse potentiellement dégradée
```

Cette limite ne devient pas pour autant un seuil métier.

La configuration technique reste distincte de la configuration analytique, mais
les conséquences connues d'une saturation, d'une éviction ou d'une perte de
données doivent pouvoir être rendues observables.

Cette convention complète les règles déjà définies pour les états bornés et les
dégradations connues de l'analyse.

### Parsing technique et validation métier

Le chargement d'une configuration peut nécessiter plusieurs niveaux de
validation.

Par exemple, pour une valeur fournie sous forme de texte :

```text
"20"
 ↓
parsing
 ↓
20
 ↓
validation de l'invariant
 ↓
valeur métier valide
```

Le parsing dépend de la représentation externe.

Les invariants intrinsèques à une configuration métier appartiennent au type ou
au composant métier concerné.

Ainsi :

```text
"abc" impossible à convertir en entier
```

et :

```text
-1 correctement converti mais interdit par le contrat métier
```

sont deux problèmes conceptuellement différents, même s'ils peuvent tous deux
empêcher le démarrage.

Cette séparation suit les conventions de validation définies en 0.4.3 et les
conventions d'erreurs définies en 0.4.4.

### Validation avant disponibilité du composant

Une configuration nécessaire au fonctionnement initial d'un composant est
validée avant que ce composant soit considéré prêt.

Le principe général est :

```text
chargement
    ↓
parsing
    ↓
validation
    ↓
construction
    ↓
readiness
```

Une configuration requise connue comme invalide ne doit pas être conservée
silencieusement jusqu'à ce qu'un chemin d'exécution particulier l'utilise.

Pour le premier incrément, une configuration requise invalide peut donc faire
échouer explicitement l'initialisation du composant ou du mode d'exécution
concerné.

Cela ne signifie pas que toute erreur de configuration future devra
nécessairement arrêter l'ensemble de NetGuard.

Un composant optionnel pourra éventuellement être désactivé selon une politique
explicite.

La politique doit toutefois être définie par le niveau qui possède le cycle de
vie concerné et ne doit pas transformer silencieusement une configuration
invalide en fonctionnement nominal.

### Valeurs par défaut

Une valeur par défaut est autorisée lorsqu'elle fait explicitement partie du
contrat de configuration.

Il faut distinguer :

```text
aucune valeur fournie
→ valeur par défaut documentée
```

de :

```text
valeur explicitement fournie mais invalide
→ erreur de configuration
```

Une valeur invalide ne doit pas être silencieusement remplacée par le défaut.

Par exemple :

```text
threshold absent
→ default documenté éventuel

threshold = "invalid"
→ erreur
```

Cette règle évite qu'une faute de configuration modifie silencieusement le
comportement analytique de NetGuard.

Les valeurs par défaut ayant une signification métier doivent être définies près
du contrat métier concerné plutôt que dispersées dans le code de chargement.

### Plusieurs sources et ordre de priorité

NetGuard ne définit pas encore les sources concrètes qui pourront simultanément
participer à sa configuration.

Un futur mode d'exécution pourra par exemple combiner certaines sources telles
que :

```text
valeurs par défaut
fichier
environnement
arguments CLI
```

Si plusieurs sources peuvent fournir une même valeur, leur ordre de priorité doit
être explicite et documenté au niveau du chargement ou de l'assemblage.

Chaque composant consommateur ne définit pas sa propre priorité.

Une situation où deux sources se remplacent mutuellement selon une règle cachée
est interdite.

Aucun ordre concret tel que :

```text
CLI > environnement > fichier > défaut
```

n'est imposé à cette étape.

### Format de configuration

Aucun format de configuration utilisateur n'est sélectionné en 0.4.5.

NetGuard ne choisit donc pas encore entre :

```text
TOML
YAML
JSON
.env
arguments CLI
variables d'environnement
```

ou une combinaison de ces mécanismes.

Le choix sera effectué lorsqu'un mode d'exécution concret aura suffisamment de
besoins pour justifier ce contrat externe.

Les composants internes doivent rester indépendants de ce choix.

Une configuration métier ne doit donc pas dépendre directement d'une structure
spécifique à YAML, TOML ou à une bibliothèque de chargement.

### Pas de framework de configuration imposé

Aucune bibliothèque spécialisée de configuration n'est introduite par principe.

Des outils tels que Pydantic Settings, Dynaconf, Hydra ou une autre bibliothèque
pourront être évalués lorsqu'un besoin concret apparaîtra.

Leur éventuelle adoption devra apporter une valeur réelle en matière de parsing,
validation, ergonomie ou intégration sans faire fuiter inutilement leur modèle
dans le Core.

La configuration domaine reste définie par les besoins de NetGuard, pas par les
capacités d'un framework externe.

De même, aucun package global `netguard.config` ou `netguard.common.config` n'est
créé uniquement pour anticiper de futurs besoins.

Les éléments de configuration restent proches des capacités qui les possèdent
tant qu'une factorisation plus large n'est pas justifiée.

### Stabilité de la configuration validée

Une configuration validée représentant le contrat courant d'un composant est
considérée comme sémantiquement stable pendant la période où ce contrat
s'applique.

Cette stabilité évite qu'un composant voie son comportement changer à cause
d'une mutation externe invisible.

Elle ne prescrit pas une représentation Python particulière.

Une configuration peut par exemple être implémentée par une dataclass immutable,
un objet valeur ou une autre structure appropriée lorsque le code concret le
justifie.

Le principe porte sur la sémantique :

```text
configuration validée utilisée par le composant
→ pas de mutation implicite derrière son dos
```

### Configuration analytique fixe pendant une exécution

La V1 n'impose pas de rechargement dynamique de la configuration analytique.

Une configuration de détecteur peut rester fixe pendant toute la durée d'une
exécution.

Cette décision est particulièrement importante pour les composants possédant un
état analytique.

Par exemple :

```text
état accumulé avec threshold = 20
                ↓
threshold devient 5
```

ou :

```text
état accumulé avec window = 60 s
                ↓
window devient 10 s
```

ne permettent pas de supposer que l'état existant conserve automatiquement une
sémantique valide.

Toute modification d'un paramètre susceptible de changer la signification d'un
état analytique exige une politique explicite pour cet état.

Une évolution future pourra notamment choisir selon le besoin :

```text
réinitialisation
finalisation
migration
nouvelle instance
```

Aucun de ces mécanismes n'est imposé maintenant.

Pour le premier incrément, conserver la configuration analytique fixe pendant
l'exécution constitue la politique la plus simple et la plus déterministe.

### Configuration et reproductibilité

Les paramètres qui influencent une décision analytique font partie des entrées
contrôlées nécessaires à son interprétation.

Conceptuellement :

```text
observations
+
configuration analytique pertinente
+
autres entrées contrôlées
        ↓
décision analytique
```

La reproductibilité d'une analyse suppose donc de connaître suffisamment la
configuration analytique qui a influencé cette décision.

Cela ne signifie pas que toute la configuration du processus doit être copiée
dans chaque `DetectionResult`, `Evidence` ou `Alert`.

Les résultats stabilisés conservent seulement les paramètres nécessaires à leur
interprétation conformément aux modèles déjà définis.

Par exemple, une Evidence liée à une règle de seuil peut conserver :

```text
threshold utilisé
fenêtre temporelle pertinente
```

sans embarquer :

```text
adresse de la base de données
niveau de logging
port de l'API
credentials
```

Aucun mécanisme global de snapshot, hash ou versionnement de toute la
configuration n'est imposé à cette étape.

### Secrets

Les secrets sont distincts de la configuration analytique.

Un secret n'est transmis qu'aux composants techniques qui en ont réellement
besoin.

Il ne doit pas être inclus dans une configuration domaine simplement parce qu'un
objet de configuration global existe au point d'assemblage.

Les secrets ne doivent pas apparaître par défaut dans :

- `DetectionResult` ;
- `Evidence` ;
- `Alert` ;
- les représentations publiques d'API ;
- les représentations textuelles destinées au diagnostic ;
- les structures transmises à des composants qui n'en ont pas besoin.

Les règles précises de redaction et de journalisation seront définies dans
l'étape dédiée à l'observabilité.

### Secrets et dépôt

Les secrets, tokens, mots de passe et credentials réels ne sont pas versionnés
dans le dépôt NetGuard.

Des exemples de configuration peuvent être versionnés lorsqu'ils utilisent
uniquement des valeurs fictives ou explicitement prévues pour le développement.

Le dépôt public peut donc contenir à terme :

```text
configuration d'exemple
documentation des paramètres
valeurs de développement non sensibles
```

mais pas des credentials réels.

La source technique utilisée pour fournir un secret n'est pas imposée à cette
étape.

Variables d'environnement, fichiers montés ou mécanismes spécialisés pourront
être utilisés selon le contexte de déploiement sans que le Core connaisse leur
origine.

### Clés inconnues

Lorsqu'une structure de configuration possède un schéma explicitement contrôlé
par NetGuard, une clé inconnue susceptible de signaler une faute utilisateur
n'est pas silencieusement ignorée par défaut.

Par exemple :

```text
port_scan_thresold
```

à la place de :

```text
port_scan_threshold
```

ne doit pas conduire silencieusement à l'utilisation d'une autre valeur ou d'un
défaut si NetGuard possède le schéma de cette section.

Cette règle s'applique uniquement aux structures dont NetGuard définit le
contrat.

Elle n'impose pas de rejeter des données supplémentaires appartenant légitimement
à un format externe ou à un système extensible dont NetGuard ne possède pas
l'intégralité du schéma.

### Évolution du contrat de configuration

Une modification incompatible du sens d'un paramètre de configuration doit être
explicite et documentée.

Une ancienne clé ne doit pas être conservée tout en changeant silencieusement de
signification.

De même, une valeur précédemment exprimée dans une unité donnée ne doit pas être
réinterprétée dans une autre unité sans évolution explicite du contrat.

Les politiques détaillées de migration et de dépréciation seront définies
lorsqu'un contrat de configuration utilisateur stable existera.

À cette étape, la convention fondamentale est :

```text
évolution de représentation
≠
changement silencieux de sémantique
```

### Configuration et état analytique

La configuration qui influence la sémantique d'un état analytique fait partie du
contrat sous lequel cet état a été construit.

Il n'est donc pas valide de supposer automatiquement :

```text
état construit sous configuration A
+
configuration B
=
état valide sous configuration B
```

Lorsqu'un paramètre change la manière dont un état est regroupé, expiré, compté
ou interprété, son évolution exige une politique explicite.

Cette convention complète directement les règles de cycle de vie des états
analytiques.

Pour la V1, l'absence de hot reload analytique évite volontairement cette
complexité.

### Portée de 0.4.5

Les conventions de cette étape permettent de construire ultérieurement un
système de configuration sans introduire de dépendance globale ou de couplage
entre le Core et les mécanismes de déploiement.

Elles établissent notamment que :

```text
Core
← configuration métier validée

Infrastructure
← configuration technique adaptée

Interfaces
← configuration de leurs mécanismes externes

Composition Root
← chargement et assemblage des configurations nécessaires
```



## Logging et observabilité — 0.4.6

Cette section définit la manière dont NetGuard rend son fonctionnement observable
sans confondre les informations opérationnelles avec les faits métier produits
par l'analyse réseau.

L'observabilité doit permettre de comprendre l'état du système, d'identifier les
dégradations, de diagnostiquer les défaillances et de mesurer le fonctionnement
du pipeline sans devenir elle-même une source importante de surcharge ou de
couplage architectural.

Les distinctions fondamentales sont :

```text
fait réseau / métier
≠
DetectionResult
≠
Alert
≠
événement opérationnel
≠
log technique
```

Ainsi que :

```text
sévérité d'une Alert
≠
niveau d'un log

temps métier
≠
timestamp d'observabilité

observable
≠
un log par occurrence
```

### Observabilité et modèle métier

L'observabilité décrit le fonctionnement de NetGuard.

Elle ne remplace ni les modèles métier, ni `DetectionResult`, ni `Evidence`, ni
`Alert`.

Le chemin métier reste :

```text
Observation
    ↓
Detector
    ↓
DetectionResult
    ↓
Evidence
    ↓
Alert
```

Un log peut signaler qu'une Alert a été créée ou qu'un détecteur a rencontré une
défaillance, mais il ne devient pas la représentation canonique de cette Alert ou
de cette détection.

Les informations nécessaires à l'interprétation historique d'une décision
analytique restent portées par les modèles métier prévus à cet effet.

Les logs ne constituent donc pas un event store métier implicite.

### Indépendance du Core

Le comportement métier du Core ne dépend pas d'un mécanisme de logging, d'un
backend de métriques ou d'un framework d'observabilité externe.

Une décision analytique ne doit jamais dépendre :

- de la présence d'un logger ;
- du niveau de logging actif ;
- du succès d'un export de métriques ;
- d'un timestamp produit par l'observabilité ;
- de la disponibilité d'un système externe de monitoring.

Le flux autorisé est :

```text
décision métier
      ↓
observabilité
```

et non :

```text
observabilité
      ↓
décision métier
```

Une instrumentation locale du Core pourra être introduite lorsqu'elle possède une
utilité réelle, mais elle ne doit pas devenir une dépendance fonctionnelle du
domaine.

Aucun framework d'observabilité externe n'est imposé au Core.

### `print()` et présentation utilisateur

Les composants internes n'utilisent pas `print()` comme mécanisme de
journalisation.

Une future CLI peut naturellement produire une sortie destinée à l'utilisateur,
mais cette présentation reste distincte de l'observabilité technique.

La distinction est :

```text
sortie utilisateur
≠
logging
```

Une information importante pour le diagnostic ou l'exploitation de NetGuard ne
doit donc pas exister uniquement sous la forme d'un `print()` dispersé dans un
composant interne.

### Événements opérationnels structurables

Les événements opérationnels importants doivent pouvoir transporter des
informations structurées lorsque ces informations sont utiles au filtrage, au
diagnostic, à la corrélation ou à la production de métriques.

Par exemple, une défaillance de détecteur peut conceptuellement exposer :

```text
event = detector_failure
detector_id = NG-NET-001
network_scope_id = ...
error_type = ...
```

plutôt que d'exister uniquement sous la forme d'une phrase libre.

Le message humain reste utile, mais il ne doit pas être la seule représentation
des informations nécessaires à un traitement automatique.

Cette convention n'impose pas la création d'un modèle domaine universel tel que :

```text
OperationalEvent
TelemetryEvent
LogEvent
```

et n'impose pas non plus un format de sortie particulier.

Elle définit uniquement la propriété recherchée : les informations
opérationnelles importantes doivent pouvoir être représentées de manière
structurée lorsque cela apporte une valeur réelle.

### Identifiants stables dans l'observabilité

Lorsqu'un identifiant métier ou opérationnel stable existe déjà, il est préféré
comme référence principale à un détail d'implémentation Python.

Par exemple :

```text
detector_id = NG-NET-001
```

est une référence plus stable que :

```text
detector_class = PortScanDetectorV2Impl
```

pour identifier la règle concernée.

Un nom de classe, de module ou d'implémentation peut rester utile au diagnostic
technique, mais il ne remplace pas les identifiants sémantiques déjà définis par
NetGuard.

Cette convention facilite la corrélation entre :

```text
règle
↔
événement opérationnel
↔
DetectionResult
↔
Alert
```

sans transformer l'organisation du code Python en contrat d'observabilité.

### Corrélation et tracing

NetGuard réutilise les identifiants sémantiques déjà disponibles lorsque ceux-ci
suffisent à corréler des événements.

L'observabilité n'impose pas un `trace_id` universel à chaque objet du domaine.

Un futur mécanisme de tracing technique pourra être introduit si l'évolution du
système le justifie, notamment pour suivre des interactions entre plusieurs
composants ou processus.

Un éventuel identifiant de trace technique restera toutefois distinct des
identités métier et de la provenance réseau :

```text
trace_id technique
≠
identité métier
≠
identité d'une observation
≠
provenance réseau
```

L'ajout futur d'un système de tracing ne doit donc pas modifier la sémantique des
objets domaine uniquement pour satisfaire un outil d'observabilité.

### Niveaux de logs

Les niveaux de logs décrivent l'importance opérationnelle d'un événement pour le
fonctionnement de NetGuard.

Ils ne décrivent pas la dangerosité supposée d'un comportement réseau.

La convention générale est la suivante.

`DEBUG` correspond aux informations détaillées utiles au diagnostic ou au
développement et normalement inutiles en fonctionnement courant.

`INFO` correspond aux événements normaux importants du cycle de vie ou du
fonctionnement du système, par exemple :

```text
démarrage
source ouverte
composant initialisé
détecteur activé
arrêt contrôlé
```

`WARNING` correspond à une situation inattendue ou dégradée dans laquelle le
traitement peut néanmoins continuer selon une politique définie, par exemple :

```text
perte connue de données
éviction pour contrainte de capacité
source partiellement exploitable
dégradation opérationnelle
```

`ERROR` correspond à l'échec d'une opération ou d'un composant qui n'a pas pu
respecter son contrat, par exemple :

```text
persistance d'une Alert échouée
détecteur ayant rencontré une défaillance
source devenue inutilisable
```

`CRITICAL` est réservé aux situations dans lesquelles NetGuard ou une capacité
essentielle ne peut plus assurer le fonctionnement attendu et nécessite un arrêt
ou une intervention majeure.

La sélection précise d'un niveau dépend du contexte et de la conséquence
opérationnelle de l'événement.

### Sévérité d'une Alert et niveau de log

La sévérité métier d'une Alert est indépendante du niveau du log éventuellement
associé à sa création.

Une Alert de sévérité élevée peut être produite alors que NetGuard fonctionne
parfaitement normalement.

Par exemple :

```text
INFO
event = alert_created
security_severity = high
```

peut être parfaitement cohérent.

La relation suivante est donc interdite comme règle générale :

```text
Alert HIGH
→
log ERROR
```

La sévérité d'une Alert décrit une propriété métier de la conclusion de sécurité.

Le niveau du log décrit une propriété opérationnelle du fonctionnement de
NetGuard.

Ces deux axes restent indépendants.

### Une détection n'est pas une erreur de fonctionnement

La production d'une détection signifie normalement que le détecteur a rempli son
rôle.

Un comportement réseau considéré comme suspect ne constitue donc pas, à lui
seul, une erreur opérationnelle de NetGuard.

Le fait qu'une règle se déclenche ne justifie pas automatiquement un niveau
`WARNING`, `ERROR` ou `CRITICAL`.

La journalisation éventuelle de la création d'une détection ou d'une Alert suit
la politique d'observabilité du système et reste indépendante de la gravité
métier attribuée au comportement observé.

### Pas de logs nominaux par observation

Le chemin nominal à haute fréquence ne produit pas de log `INFO` pour chaque
observation réseau.

Une stratégie telle que :

```text
INFO packet received
INFO packet normalized
INFO detector evaluated packet
```

pour chaque paquet créerait :

- un volume important d'I/O ;
- une consommation inutile de stockage ;
- du bruit opérationnel ;
- un risque accru d'exposition de données réseau ;
- une perturbation des performances du système observé.

Les détails par observation peuvent éventuellement être rendus disponibles dans
des mécanismes de diagnostic ciblés lorsque cela est réellement nécessaire.

Le niveau `DEBUG` ne constitue toutefois pas une autorisation à produire sans
limite des données sensibles ou un volume non maîtrisé d'événements.

### Événements répétitifs

Une situation observable ne nécessite pas nécessairement un log individuel pour
chaque occurrence.

Des événements répétitifs à haute fréquence peuvent être représentés selon le
besoin par :

```text
compteur
agrégation
rate limiting
résumé périodique
échantillonnage contrôlé
```

ou une combinaison appropriée de ces mécanismes.

Par exemple, un grand nombre d'observations rejetées ne doit pas nécessairement
produire autant de `WARNING`.

La propriété importante est que le phénomène reste observable sans que
l'observabilité ne devienne elle-même une source de surcharge.

### Observabilité bornée

Les mécanismes d'observabilité ne doivent pas introduire de croissance mémoire
non bornée dans le chemin d'exécution.

Une future file d'événements, queue de logs ou structure d'agrégation devra donc
respecter les mêmes principes généraux de capacité explicite que le reste de
NetGuard.

Une instrumentation qui accumule indéfiniment des événements en mémoire
violerait les garanties de bornage du système même si le pipeline analytique
lui-même était correctement borné.

La stratégie technique précise dépendra du mécanisme d'observabilité réellement
retenu.

### Défaillance de l'observabilité

Une défaillance du mécanisme d'observabilité ne réécrit pas rétroactivement les
résultats métier déjà établis.

Par exemple :

```text
DetectionResult produit
        ↓
Alert créée
        ↓
export de métrique échoué
```

ne signifie pas que la détection ou l'Alert n'a jamais existé.

Pour la V1, une défaillance de logging, de métriques ou d'un futur exporter ne
doit pas, par défaut, empêcher l'analyse lorsque celle-ci peut continuer
correctement.

Une perte significative d'observabilité doit néanmoins pouvoir être signalée
autant que possible par un mécanisme approprié.

Cette politique ne doit pas provoquer de récursion incontrôlée dans laquelle le
système tente indéfiniment de journaliser la défaillance de son propre mécanisme
de journalisation.

### Métriques opérationnelles

Les métriques servent à mesurer le fonctionnement du système et les phénomènes
opérationnels importants.

Le catalogue exact des métriques n'est pas figé à cette étape, mais plusieurs
catégories doivent pouvoir être représentées lorsque l'implémentation
correspondante existe.

Pour les entrées :

```text
observations reçues
observations acceptées
observations rejetées
```

Pour le pipeline :

```text
éléments traités
pertes connues
saturations
évictions de capacité
```

Pour la détection :

```text
résultats de détection produits
défaillances de détecteurs
```

Pour l'alerting et la persistance :

```text
Alert créées
persistance réussie
persistance échouée
```

Pour le cycle de vie :

```text
sources actives
readiness
dégradations
défaillances significatives
```

Des métriques de performance telles que les durées de traitement, latences ou
profondeurs de buffers pourront être introduites lorsque leur utilité sera
démontrée.

### Sémantique et unités des métriques

Une métrique possède une signification et une unité explicites.

Une valeur telle que :

```text
rejection_rate = 3.7
```

est ambiguë si la fenêtre temporelle, l'unité ou la méthode de calcul ne sont pas
définies.

Pour les événements dénombrables, des compteurs cumulatifs peuvent être
privilégiés lorsque cela suffit.

Par exemple :

```text
observations_rejected_total
```

possède une sémantique plus stable qu'un taux calculé sans contrat explicite.

Les taux, moyennes et autres agrégations peuvent ensuite être calculés par les
outils appropriés lorsque leurs fenêtres et méthodes sont clairement définies.

Cette convention prolonge les règles déjà établies sur la sémantique explicite
des compteurs et agrégats réseau.

### Cardinalité des métriques

Les dimensions utilisées pour segmenter une métrique doivent avoir une
cardinalité maîtrisée.

Des valeurs potentiellement non bornées telles que :

```text
source_ip
destination_ip
flow_id
alert_id
```

ne doivent pas devenir par défaut des labels de métriques.

Une telle utilisation pourrait créer un nombre très important de séries et faire
de l'observabilité une source de consommation mémoire ou de stockage non
maîtrisée.

Des dimensions naturellement bornées, telles qu'un ensemble limité
d'identifiants de détecteurs, peuvent être appropriées lorsqu'elles apportent une
valeur opérationnelle.

La présence d'une donnée dans un log ponctuel ne signifie pas qu'elle constitue
une dimension acceptable pour une métrique.

Ainsi :

```text
champ de log
≠
label de métrique
```

### Minimisation des données réseau

Les logs et métriques ne contiennent que les données réseau nécessaires à leur
objectif opérationnel.

NetGuard peut manipuler des informations telles que :

```text
adresses IP
ports
identifiants de sources
adresses MAC futures
payload éventuel
```

mais leur disponibilité dans le pipeline ne justifie pas leur inclusion
systématique dans l'observabilité.

Le payload réseau brut n'est pas journalisé par défaut.

Une donnée réseau identifiable n'est ajoutée à un événement opérationnel que si
elle est réellement utile au diagnostic ou au suivi de la situation concernée.

Le niveau `DEBUG` ne supprime pas cette exigence de minimisation.

### Secrets et observabilité

Les secrets, credentials et tokens ne sont jamais journalisés
intentionnellement.

Ils ne doivent pas apparaître dans les champs structurés, messages ou métriques
produits par NetGuard.

Une attention particulière doit être portée aux exceptions provenant de
bibliothèques ou de systèmes externes, car leur représentation textuelle peut
elle-même contenir des informations sensibles.

La présence d'une exception dans le chaînage interne ne signifie donc pas que
l'intégralité de son texte est automatiquement sûre à exposer dans toutes les
sorties d'observabilité.

### Redaction

Lorsqu'un contexte utile au diagnostic peut contenir une information sensible,
sa représentation observable doit être limitée au strict nécessaire.

Selon le besoin, cette information peut être :

```text
omise
réduite
masquée
redacted
```

La stratégie dépend de la nature de la donnée et de l'objectif opérationnel.

Cette convention n'impose pas un moteur générique de redaction ni un type
universel représentant toutes les valeurs sensibles.

Un tel mécanisme ne sera introduit que si les besoins concrets du projet le
justifient.

### Stack traces

Les stack traces sont utilisées lorsqu'elles apportent une information utile au
diagnostic d'une défaillance Python ou d'une situation inattendue.

Elles ne sont pas produites mécaniquement pour chaque branche normale ou chaque
rejet attendu.

Par exemple :

```text
observation externe rejetée selon une politique normale
→ pas nécessairement de stack trace
```

alors que :

```text
exception inattendue dans un détecteur
→ stack trace potentiellement utile
```

Cette distinction évite de transformer des situations attendues à haute fréquence
en bruit diagnostique coûteux.

### Journalisation des erreurs aux frontières

Une même défaillance n'est pas journalisée mécaniquement à chaque couche qu'elle
traverse.

Par exemple :

```text
Infrastructure
      ↓
Application
      ↓
Interfaces
```

ne doit pas nécessairement produire trois logs `ERROR` et trois stack traces
pour la même cause.

Une erreur peut être enrichie ou traduite lorsqu'elle traverse une frontière
sans être immédiatement journalisée.

Elle est journalisée au niveau qui possède suffisamment de contexte pour
comprendre sa conséquence opérationnelle et appliquer la politique appropriée.

Le chaînage d'exceptions permet de conserver la cause technique lorsqu'elle est
utile au diagnostic sans obliger chaque couche intermédiaire à produire son
propre log.

### Temps métier et temps d'observabilité

Les timestamps produits par l'observabilité ne remplacent jamais les timestamps
métier des observations ou des résultats analytiques.

Un événement opérationnel peut posséder un temps de production correspondant au
moment où NetGuard l'a généré.

Une observation réseau possède son propre temps métier.

Ces deux valeurs restent distinctes :

```text
observed_at
≠
logged_at / processing time
```

Lorsque les deux sont présentes dans un même contexte, leur signification doit
rester explicite.

Cette distinction est particulièrement importante lors du replay d'un PCAP.

Par exemple :

```text
observation capturée en 2025
        ↓
PCAP rejoué en 2026
        ↓
log produit en 2026
```

Le timestamp du log ne modifie pas le temps métier de l'observation.

### Observabilité et déterminisme

L'observabilité peut utiliser des informations propres à l'exécution réelle,
telles que :

```text
heure courante
durée réelle
identifiant de processus
informations techniques de runtime
```

sans remettre en cause le déterminisme analytique.

La condition est que ces informations ne soient pas réinjectées dans les
décisions métier.

Ainsi :

```text
décision analytique
        ↓
instrumentation
```

est valide, alors que :

```text
timestamp du logger
        ↓
décision du détecteur
```

ne l'est pas.

Les résultats analytiques restent déterminés par leurs entrées contrôlées et non
par le comportement de l'infrastructure d'observabilité.

### Liveness, readiness et état opérationnel

NetGuard distingue conceptuellement plusieurs aspects de son état de
fonctionnement.

La liveness répond à la question :

```text
le processus fonctionne-t-il encore ?
```

La readiness répond à la question :

```text
le système ou le mode d'exécution concerné
est-il prêt à assurer le fonctionnement attendu ?
```

L'état opérationnel permet de représenter plus largement :

```text
initialisation
fonctionnement normal
dégradation
défaillance
arrêt contrôlé
```

Ces concepts restent indépendants de leur future exposition.

Ils ne supposent donc pas l'existence immédiate d'endpoints HTTP tels que
`/health` ou `/ready`.

L'état opérationnel doit pouvoir être représenté avant de décider comment une
API, une CLI ou un autre mécanisme le rendra accessible.

Aucun enum global ou machine d'état universelle n'est imposé à tous les
composants.

### Observabilité des rejets

Un rejet connu doit pouvoir être observé conformément aux garanties déjà définies
pour l'admission et la normalisation des données.

Cela ne signifie pas :

```text
un rejet
=
un WARNING
```

Un compteur, un résumé agrégé, un état opérationnel ou un autre signal peut être
plus approprié.

Le choix dépend notamment :

- de la fréquence du phénomène ;
- de son importance opérationnelle ;
- du besoin de diagnostic ;
- de son impact potentiel sur l'analyse.

La propriété fondamentale est que les rejets significatifs ne disparaissent pas
silencieusement du fonctionnement observable du système.

### Observabilité des pertes et évictions

Toute perte connue de données ou d'état susceptible d'affecter l'analyse doit
produire un signal opérationnel identifiable.

Cela concerne notamment des situations telles que :

```text
élément abandonné pour saturation
état évincé pour contrainte de capacité
données perdues à une frontière
```

Ces situations restent distinctes de l'expiration analytique normale.

Le signal peut prendre selon le contexte la forme d'un log, d'une métrique, d'un
état opérationnel ou d'une combinaison de ces mécanismes.

La perte connue ne doit pas être silencieuse lorsque celle-ci réduit les
garanties analytiques de NetGuard.

### Observabilité des défaillances confinées

Le confinement d'une défaillance ne doit pas transformer cette défaillance en
silence opérationnel.

Lorsqu'un composant tel qu'un détecteur échoue et qu'une politique permet au
reste du système de continuer, l'observabilité doit permettre d'identifier au
minimum les informations nécessaires pour comprendre :

```text
quel composant a échoué
quand la défaillance a été constatée
quelle conséquence opérationnelle connue a été appliquée
```

Par exemple :

```text
detector failure
        ↓
état considéré incertain
        ↓
detector disabled
```

doit rester identifiable même si le reste du pipeline continue à fonctionner.

Cette règle complète les conventions de 0.4.4 concernant les composants stateful
et le confinement des exceptions.

### Implémentation technique de l'observabilité

Les mécanismes techniques d'observabilité appartiennent aux frontières
appropriées.

Le package :

```text
infrastructure/
└── observability/
```

peut accueillir les implémentations techniques nécessaires lorsqu'elles
apparaissent, par exemple :

```text
configuration du logging
handlers
exporters
adaptateurs de métriques
intégrations externes
```

Cela ne signifie pas que toutes les couches doivent dépendre directement de ce
package.

Lorsqu'une couche exprime un besoin abstrait d'observabilité nécessitant un
contrat, ce contrat suit les règles de dépendances déjà établies : il appartient
à la couche qui exprime le besoin et son implémentation technique reste à la
frontière appropriée.

Aucun contrat générique `Telemetry`, `Metrics` ou `Observability` n'est créé
uniquement par anticipation.

### Choix des technologies

Aucune technologie d'observabilité n'est imposée par cette étape.

Le projet ne sélectionne donc pas encore comme contrainte architecturale :

```text
stdlib logging
structlog
Loguru
Prometheus
OpenTelemetry
StatsD
```

ou un autre système particulier.

Les technologies seront choisies lorsqu'un besoin concret permettra d'évaluer
leur valeur, leur coût et leur impact sur les dépendances du projet.

Les conventions définies ici portent sur la sémantique et les garanties de
l'observabilité, indépendamment du backend qui les implémentera.

### Portée de 0.4.6

Les conventions de cette étape établissent une séparation claire entre les faits
métier et l'observabilité technique, définissent une sémantique cohérente pour
les logs et les métriques, imposent la maîtrise du volume et de la cardinalité,
préservent la minimisation des données sensibles et garantissent que les rejets,
pertes, dégradations et défaillances confinées restent observables sans faire de
l'instrumentation une dépendance du comportement analytique de NetGuard.


## Architecture des tests — 0.4.7

Cette section définit la stratégie de test du backend NetGuard.

L'objectif est de construire une suite de tests rapide, déterministe et
reproductible qui vérifie les contrats et invariants du système sans dépendre
inutilement du réseau réel, du temps réel, de privilèges élevés ou de détails
internes d'implémentation.

Le principe général est :

```text
comportement observable
+
contrat
+
invariant
>
détail interne d'implémentation
```

Les tests doivent permettre de faire évoluer l'organisation interne du code sans
casser artificiellement tant que le comportement contractuel reste identique.

### Niveaux de tests

NetGuard distingue conceptuellement plusieurs niveaux de tests :

```text
tests unitaires
tests d'intégration
tests de contrat
tests end-to-end
```

Ces catégories décrivent des responsabilités de test.

Elles n'imposent pas nécessairement une arborescence distincte ou un mécanisme
technique différent pour chaque catégorie.

Les tests unitaires vérifient un composant ou une propriété isolée avec des
entrées contrôlées.

Ils sont particulièrement adaptés aux :

```text
objets valeur
invariants domaine
normalisations sémantiques
détecteurs
états analytiques
DetectionResult
Evidence
```

Les tests d'intégration vérifient la collaboration entre plusieurs composants
réels ou l'intégration avec une technologie concrète.

Ils peuvent notamment couvrir :

```text
adaptateur PCAP + normalisation
repository + stockage réel de test
Application + Core
```

Les tests de contrat vérifient qu'une implémentation respecte le contrat possédé
par une autre couche.

Les tests end-to-end vérifient un parcours significatif à travers plusieurs
parties du système.

Aucun ratio artificiel entre ces catégories n'est imposé.

Le niveau de test le plus petit capable de vérifier correctement une propriété
est privilégié.

### Tests du Core

Les comportements métier du Core doivent pouvoir être testés sans infrastructure
réelle.

Un test de détecteur doit pouvoir suivre conceptuellement le chemin :

```text
observations contrôlées
        ↓
Detector
        ↓
DetectionResult
+
Evidence
```

sans nécessiter :

- d'interface réseau réelle ;
- de base de données réelle ;
- d'API HTTP ;
- d'accès Internet ;
- d'horloge système implicite ;
- de privilèges réseau élevés.

Cette propriété constitue également une vérification pratique de l'indépendance
architecturale du Core.

### Capture réseau et tests unitaires

Les tests unitaires de détection ne dépendent pas du trafic réseau réellement
présent sur la machine exécutant la suite.

Ils ne supposent pas l'existence d'une interface particulière telle que :

```text
eth0
wlan0
en0
```

et ne dépendent pas du trafic Internet courant.

Les scénarios métier utilisent des observations construites explicitement afin
de maîtriser exactement les entrées fournies au composant testé.

La capture réseau réelle appartient aux tests d'intégration spécialisés ou aux
scénarios du laboratoire lorsqu'elle est nécessaire.

### PCAP comme fixture

Les fichiers PCAP peuvent servir de fixtures reproductibles lorsqu'ils permettent
de vérifier une propriété qu'une construction synthétique représenterait moins
correctement ou moins simplement.

Ils sont particulièrement pertinents pour tester :

```text
lecture PCAP
normalisation depuis une capture réelle
replay
intégration ingestion → analyse
```

Les PCAP utilisés par la suite automatisée doivent être :

- suffisamment petits ;
- déterministes ;
- compréhensibles ;
- adaptés au scénario testé ;
- légalement et techniquement publiables.

Un test de logique métier simple ne doit pas utiliser un PCAP uniquement parce
que le domaine de NetGuard est le réseau.

Lorsque quelques `PacketObservation` construites explicitement suffisent, cette
forme est généralement préférée pour rendre le scénario plus lisible.

### Données de test publiables

Les données de test versionnées dans le dépôt doivent pouvoir être publiées sans
exposer de données réelles sensibles.

Une fixture ne doit pas contenir accidentellement :

```text
credentials
tokens
cookies
payload privé
trafic personnel
données réseau sensibles réelles
```

Les captures et données réseau versionnées sont synthétiques, générées
spécifiquement pour le projet ou explicitement assainies et autorisées à être
publiées.

Une capture issue d'un réseau personnel ou professionnel n'est pas ajoutée au
dépôt uniquement parce qu'elle permet de reproduire rapidement un scénario.

### Temps contrôlé

Les tests métier ne dépendent pas de l'écoulement réel du temps lorsqu'un temps
contrôlé peut représenter le scénario.

Un comportement temporel doit pouvoir être exprimé par des entrées explicites,
par exemple :

```text
t = 0 s
observation A

t = 2 s
observation B

t = 11 s
signal temporel contrôlé
```

plutôt que par :

```python
time.sleep(11)
```

Cette convention s'applique notamment :

- aux fenêtres analytiques ;
- aux expirations ;
- aux données tardives ;
- aux transitions temporelles d'état ;
- aux scénarios de replay.

Elle préserve la distinction entre temps métier et temps réel d'exécution.

### `sleep()` et synchronisation

`sleep()` n'est pas utilisé comme mécanisme principal de synchronisation d'un
test.

Une construction telle que :

```python
sleep(0.5)
assert operation_completed
```

est fragile lorsque la réussite du test dépend simplement de la vitesse de la
machine.

Si de l'asynchronisme est introduit ultérieurement, les tests attendront autant
que possible une condition déterministe, un événement ou une primitive de
synchronisation appropriée.

Un test technique spécifique peut exceptionnellement dépendre d'une durée réelle
lorsque cette durée constitue précisément la propriété testée.

### Déterminisme

Un test doit produire le même résultat lorsque ses entrées contrôlées sont
identiques.

Le principe est :

```text
mêmes observations
+
même configuration
+
mêmes signaux temporels contrôlés
+
mêmes dépendances contractuelles
=
même résultat attendu
```

La suite standard ne dépend donc pas implicitement :

- de l'heure actuelle ;
- du trafic réseau environnant ;
- d'un service Internet externe ;
- de l'ordre arbitraire d'une structure lorsque cet ordre n'appartient pas au contrat ;
- d'une configuration personnelle du développeur.

Les tests spécialisés d'intégration peuvent dépendre d'un environnement
particulier uniquement lorsque cette dépendance constitue explicitement l'objet
du test.

### Aléatoire reproductible

L'utilisation d'aléatoire dans les tests n'est pas interdite lorsqu'elle apporte
une valeur réelle.

Toute valeur aléatoire susceptible d'influencer un échec doit cependant pouvoir
être reproduite.

Le scénario, la seed ou une information équivalente doit permettre de rejouer
l'entrée ayant provoqué l'échec.

Une génération aléatoire opaque qui produit des tests impossibles à reproduire
n'est pas acceptable.

### Tests des détecteurs

Une règle de détection n'est pas uniquement testée sur un scénario qui déclenche
une détection.

Ses tests doivent couvrir selon sa sémantique :

```text
déclenchement
non-déclenchement
éligibilité
non-éligibilité
informations insuffisantes
limites de seuil
limites temporelles
```

Une observation non éligible constitue une branche normale et doit rester
distincte d'une défaillance du détecteur.

Une absence de `DetectionResult` ne doit pas être interprétée par le test comme
une preuve générale que le comportement réseau est bénin.

Le test vérifie uniquement le contrat de la règle concernée.

### Tests des résultats et Evidence

Un test de détection ne doit pas se limiter à vérifier qu'un résultat existe.

Une assertion telle que :

```python
assert len(results) == 1
```

peut être utile mais ne suffit généralement pas à vérifier la sémantique de la
détection.

Les tests doivent inspecter les éléments structurants pertinents du
`DetectionResult` et de l'`Evidence`, par exemple :

```text
rule_id
version ou contexte de règle pertinent
faits observés
agrégats calculés
seuil utilisé
fenêtre temporelle
période couverte
```

selon le contrat réel de la règle.

Cette stratégie protège l'explicabilité des détections et garantit que le
résultat contient bien les faits nécessaires à son interprétation.

### Présentation textuelle

Les tests métier privilégient les données structurées aux chaînes de présentation
humaines.

Un test ne doit pas figer une phrase complète telle que :

```python
assert alert.message == "..."
```

si cette phrase n'appartient pas explicitement à un contrat externe.

Les données métier structurées constituent la source principale des assertions.

Une représentation textuelle pourra avoir ses propres tests lorsqu'une API, une
CLI ou une autre interface promettra réellement un format stable.

### Frontières métier

Les limites significatives d'une règle doivent être testées explicitement.

Pour un seuil :

```text
threshold - 1
threshold
threshold + 1
```

peuvent constituer des cas pertinents.

Pour une fenêtre temporelle :

```text
juste avant la limite
exactement à la limite
juste après la limite
```

doivent être considérés lorsque leur distinction influence le comportement.

Ces tests permettent notamment de détecter les erreurs de frontière telles que :

```text
<
vs
<=
```

La sélection exacte des cas dépend de la sémantique définie par chaque règle.

### Ordre temporel et données tardives

Lorsqu'un comportement dépend de l'ordre ou du temps des observations, ses tests
doivent vérifier les situations pertinentes définies par sa politique.

Cela peut inclure :

```text
ordre nominal
ordre d'admission différent de l'ordre temporel
timestamps identiques
observation tardive
```

Ces scénarios ne sont pas imposés à chaque composant.

Ils deviennent obligatoires lorsqu'une politique concrète de gestion de l'ordre
ou des données tardives influence le comportement testé.

Les tests doivent préserver la distinction entre :

```text
event time
≠
processing order
```

### Capacité et éviction

Une structure d'état annoncée comme bornée doit posséder des tests vérifiant sa
politique de capacité lorsque cette capacité influence son comportement ou les
garanties analytiques.

Les scénarios pertinents peuvent inclure :

```text
capacité non atteinte
capacité exactement atteinte
capacité dépassée
éviction
signal de perte ou de dégradation
```

L'expiration analytique normale reste distincte d'une éviction provoquée par une
contrainte de ressources.

Les tests doivent préserver cette distinction lorsqu'elle appartient au contrat
du composant.

### Tests des défaillances

Les chemins d'erreur significatifs doivent être testés lorsqu'ils influencent le
contrat ou l'état du système.

Les scénarios peuvent notamment couvrir :

```text
repository indisponible
source PCAP invalide ou illisible
configuration invalide
détecteur en échec
persistance d'une Alert échouée
```

Un test ne se limite pas nécessairement à vérifier qu'une exception est levée.

Selon le contrat, il peut également vérifier :

```text
traduction correcte de l'erreur
état conservé ou invalidé
composant désactivé
traitement arrêté
résultat métier déjà produit préservé
```

Les tests doivent refléter la politique réelle du composant et ne pas supposer
implicitement qu'un état reste valide après une exception.

### État après défaillance

Lorsqu'un composant stateful rencontre une défaillance susceptible de compromettre
son état, les tests doivent vérifier la politique explicitement définie.

Par exemple :

```text
exception
→ reset
```

ou :

```text
exception
→ disable
```

ou :

```text
exception
→ arrêt contrôlé
```

selon la politique retenue.

Une exception capturée ne constitue pas à elle seule une preuve que l'état peut
être réutilisé sans risque.

### Tests de configuration

Les contrats de configuration doivent être testés indépendamment de
l'environnement réel du développeur.

Les cas pertinents comprennent notamment :

```text
configuration valide
valeur absente avec défaut documenté
valeur explicitement invalide
clé inconnue dans un schéma contrôlé
```

Lorsqu'une configuration pourra être chargée depuis plusieurs sources, les tests
vérifieront également leur ordre de priorité documenté.

La distinction suivante doit rester testable :

```text
valeur absente
≠
valeur fournie mais invalide
```

Une valeur invalide ne doit pas être transformée silencieusement en valeur par
défaut.

### Tests d'observabilité

Les tests d'observabilité vérifient les garanties structurantes qui possèdent une
importance fonctionnelle, opérationnelle ou de sécurité.

Ils peuvent notamment vérifier qu'une :

```text
perte significative est observable
défaillance confinée reste observable
information sensible n'est pas exposée
métrique conserve une cardinalité maîtrisée
```

lorsque ces propriétés sont implémentées.

Ils ne doivent pas figer inutilement chaque phrase de log ou chaque détail de
présentation.

Le logging doit pouvoir évoluer sans casser les tests tant que les garanties
contractuelles restent respectées.

### Doubles de test

Mocks, stubs, fakes et autres doubles de test sont utilisés lorsqu'ils permettent
d'isoler utilement une frontière ou un comportement.

Les vrais objets domaine simples sont préférés lorsqu'ils peuvent être construits
directement.

Par exemple, une `PacketObservation` valide ne doit pas être remplacée
systématiquement par un mock uniquement parce qu'elle constitue une dépendance
du détecteur.

À l'inverse, une dépendance telle qu'un repository peut être remplacée par un
double lorsqu'un test Application ne cherche pas à vérifier l'implémentation
réelle du stockage.

Le principe est :

```text
vrai objet simple
→ préféré

frontière externe ou comportement à contrôler
→ double de test si utile
```

### Choix du double de test

Aucun type de double n'est imposé universellement.

Un fake en mémoire peut être plus adapté lorsqu'un test souhaite observer un état
final.

Un mock peut être pertinent lorsque l'interaction elle-même constitue le contrat
à vérifier.

Un stub peut suffire lorsqu'une dépendance doit simplement fournir une réponse
contrôlée.

Le double choisi doit être le plus simple permettant de vérifier correctement la
propriété concernée.

Les doubles de test ne doivent pas devenir une seconde implémentation complexe du
système métier.

### Effets contractuels et appels internes

Les tests privilégient les effets contractuels observables plutôt que les
séquences internes d'appels.

Une assertion telle que :

```python
repository.save.assert_called_once_with(...)
```

est pertinente lorsque l'appel à `save` constitue précisément l'interaction
contractuelle testée.

Lorsque le véritable contrat est plutôt :

```text
l'Alert est disponible après l'exécution du use case
```

une vérification de l'état final peut être plus robuste.

Les tests ne doivent pas empêcher un refactoring interne qui conserve le même
comportement contractuel.

### Tests de contrat des adapters

Lorsqu'une couche définit un contrat implémenté par une autre couche, une suite
de tests commune peut vérifier que les différentes implémentations respectent les
mêmes attentes.

Conceptuellement :

```text
contrat possédé par Application
            ↑
            │
    adapter Infrastructure
            │
            ↓
      contract tests
```

Par exemple, plusieurs implémentations futures d'un repository peuvent être
soumises aux mêmes comportements contractuels.

Cette stratégie n'impose pas immédiatement un framework générique de contract
testing.

Elle sera matérialisée lorsqu'un premier contrat disposera d'une ou plusieurs
implémentations concrètes nécessitant cette garantie.

### Technologies réelles dans les tests d'intégration

Un adapter dont la correction dépend du comportement réel d'une technologie ne
doit pas être validé uniquement avec un mock de cette technologie.

Par exemple, un repository SQL peut nécessiter des tests vérifiant réellement :

```text
mapping
contraintes
transactions
requêtes
```

contre une instance de test suffisamment représentative.

Le degré de réalisme dépend du coût de la technologie et de la propriété à
vérifier.

Les dépendances externes lourdes ne sont pas introduites dans toute la suite
uniquement pour augmenter artificiellement le réalisme.

### Tests end-to-end

NetGuard doit pouvoir posséder un petit nombre de scénarios automatisés couvrant
un parcours représentatif complet.

Le scénario canonique est conceptuellement :

```text
source contrôlée
        ↓
ingestion
        ↓
normalisation
        ↓
détection
        ↓
DetectionResult / Evidence
        ↓
Alert
        ↓
persistance ou consultation
```

Ces scénarios utilisent autant que possible des entrées reproductibles.

Un PCAP contrôlé ou une autre source déterministe est préféré à une dépendance au
trafic réseau réellement présent pendant l'exécution du test.

Les tests end-to-end complètent les tests plus ciblés ; ils ne remplacent pas les
tests unitaires ou d'intégration permettant de localiser précisément une
régression.

### Tests automatisés et laboratoire

Le dossier :

```text
lab/
```

et la suite automatisée ont des responsabilités distinctes.

Le laboratoire peut accueillir :

```text
scénarios manuels
génération contrôlée de trafic
expérimentations
démonstrations réseau
tests nécessitant un environnement particulier
```

La suite automatisée vérifie les propriétés qui doivent rester garanties pendant
le développement et en CI.

La distinction est :

```text
tests automatisés
≠
lab
```

Un scénario manuel ne remplace pas un test automatisé lorsqu'une propriété doit
être vérifiée systématiquement.

Inversement, toute expérimentation du laboratoire n'a pas vocation à devenir un
test automatisé.

### Privilèges réseau

La suite automatisée standard doit pouvoir s'exécuter sans privilèges réseau
élevés.

Elle ne doit pas nécessiter par défaut :

```text
root
CAP_NET_RAW
accès privilégié à une interface réseau
```

Les tests nécessitant réellement de tels privilèges sont considérés comme des
tests spécialisés et doivent être séparables de la suite standard.

Cette convention permet notamment d'exécuter les tests dans des environnements
de développement et de CI ordinaires.

### Accès Internet

La suite automatisée standard ne dépend pas d'un accès Internet externe.

Un test standard ne doit pas échouer parce qu'un service tiers est indisponible,
qu'une résolution DNS varie ou qu'une machine est hors ligne.

Les éventuelles intégrations externes futures pourront posséder des tests
spécialisés lorsque cela sera nécessaire.

Le comportement métier du Core reste entièrement testable hors ligne.

### Isolation entre tests

Un test ne doit pas dépendre implicitement de l'exécution préalable d'un autre
test.

Chaque test construit son propre contexte ou utilise des fixtures dont le cycle
de vie est explicitement géré.

Une situation telle que :

```text
test A crée un état global
        ↓
test B suppose que cet état existe
```

est évitée.

Les tests doivent rester corrects indépendamment de leur ordre d'exécution, sauf
scénario explicitement séquentiel dont la séquence constitue elle-même le contrat
testé.

Même dans ce cas, un scénario autonome est généralement préféré à plusieurs tests
qui dépendent les uns des autres.

### Nettoyage des ressources

Les ressources ouvertes par un test doivent être libérées même lorsque le test
échoue.

Cela concerne notamment :

```text
fichiers temporaires
bases de données de test
sockets
processus
ressources système
```

Les mécanismes de gestion de contexte, fixtures avec nettoyage ou répertoires
temporaires sont privilégiés lorsque cela est approprié.

Un test ne doit pas laisser un état résiduel susceptible de modifier le résultat
des tests suivants.

### Parallélisme futur

La suite n'est pas obligatoirement exécutée en parallèle.

Les tests doivent néanmoins éviter sans nécessité les dépendances globales qui
rendraient leur isolation ou un futur parallélisme difficile.

Sont notamment évités lorsqu'ils ne sont pas justifiés :

```text
port fixe partagé
fichier global mutable
base de données globale mutable
singleton de configuration modifié par les tests
```

Aucun outil d'exécution parallèle n'est imposé à cette étape.

### Organisation des tests backend

Les tests backend sont séparés du code distribué sous `src`.

La racine prévue est :

```text
backend/
├── src/
│   └── netguard/
└── tests/
```

Les tests ne sont donc pas placés systématiquement à côté des modules dans :

```text
backend/src/netguard/
```

Des sous-répertoires tels que :

```text
tests/
├── unit/
├── integration/
└── ...
```

pourront être introduits lorsque le volume réel de tests justifiera cette
structure.

Ils ne sont pas créés uniquement pour anticiper une complexité future.

### Imports dans les tests

Les tests importent NetGuard comme un package Python normal.

Par exemple :

```python
from netguard.core import ...
```

selon les API réellement disponibles.

Ils ne doivent pas fonctionner uniquement grâce à des manipulations locales telles
que :

```python
sys.path.insert(...)
```

destinées à contourner le `src` layout.

L'environnement de développement ou de test doit rendre le package disponible de
la même manière qu'un package correctement installé.

Cette convention permet également de détecter les erreurs de packaging ou de
configuration des imports.

### Framework principal

`pytest` est retenu comme framework principal pour les tests backend.

Il constitue une dépendance de développement et non une dépendance nécessaire à
l'exécution de NetGuard.

Son utilisation permet notamment de disposer d'un mécanisme standard pour :

```text
assertions
fixtures
paramétrisation
sélection des tests
intégration CI
```

Le choix de `pytest` ne modifie pas l'architecture du code métier et ne doit pas
introduire de dépendance de `netguard.core` envers le framework de test.

Aucune bibliothèque complémentaire de test n'est imposée tant qu'un besoin
concret ne la justifie.

### Dépendances de test

Les dépendances nécessaires uniquement à la validation, au développement ou à
l'exécution de la suite de tests restent distinctes des dépendances runtime.

Le principe est :

```text
runtime dependencies
≠
development / test dependencies
```

Une bibliothèque de test n'est pas ajoutée aux dépendances nécessaires au
fonctionnement de NetGuard uniquement parce qu'elle est utilisée dans le dépôt.

La représentation exacte de ces groupes dans `pyproject.toml` sera matérialisée
avec l'outillage de développement correspondant.

### Couverture de code

La couverture de code peut être utilisée comme indicateur pour identifier les
zones qui ne sont pas exercées par la suite.

Elle ne constitue pas une preuve de correction.

Une couverture élevée ne remplace pas les tests des :

```text
invariants
frontières métier
erreurs
états
dégradations
cas négatifs
```

Aucun objectif arbitraire tel que `100 %` ni aucun seuil CI global n'est imposé à
cette étape.

Un seuil pourra être introduit ultérieurement s'il apporte une valeur réelle au
projet.

### Tests de régression

Lorsqu'un bug reproductible est identifié et qu'il possède un risque raisonnable
de réapparition, sa correction doit autant que possible être accompagnée d'un
test reproduisant le comportement défectueux.

Cette règle est particulièrement importante pour :

```text
normalisation
temps
ordre des observations
état analytique
détection
frontières de seuil
persistance
```

Le test de régression doit vérifier la propriété qui était incorrecte plutôt que
figer accidentellement l'ancienne structure interne du code.

### Nommage des tests

Les noms de tests décrivent autant que possible le comportement ou la propriété
vérifiée.

Des noms tels que :

```text
test_rejects_unknown_configuration_key
test_emits_detection_when_threshold_is_reached
test_does_not_emit_detection_below_threshold
```

sont préférés à des noms génériques tels que :

```text
test_detector_1
test_process
test_case_a
```

La suite de tests devient ainsi une documentation complémentaire des comportements
attendus.

### Nombre d'assertions

NetGuard n'impose pas la règle « une assertion par test ».

Un test vérifie une propriété ou un comportement cohérent.

Plusieurs assertions peuvent être nécessaires pour vérifier correctement un même
résultat.

Par exemple :

```python
assert result.rule_id == expected_rule_id
assert result.evidence.threshold == expected_threshold
assert result.evidence.distinct_ports == expected_count
```

peuvent appartenir au même scénario si ces informations décrivent ensemble la
conclusion métier testée.

La lisibilité et la cohérence du comportement vérifié priment sur le nombre brut
d'assertions.

### Fixtures partagées

Les fixtures partagées doivent rester suffisamment petites et explicites pour ne
pas masquer le scénario testé.

Une fixture qui construit implicitement un environnement NetGuard complet pour
chaque test peut rendre les dépendances et les valeurs importantes difficiles à
comprendre.

Les fixtures sont donc placées au niveau le plus local raisonnable et
factorisées lorsqu'une duplication réelle le justifie.

Les valeurs qui déterminent le comportement testé doivent rester visibles dans le
scénario ou facilement identifiables depuis la fixture utilisée.

### Builders de données

Des builders ou fonctions de construction de données de test peuvent être
introduits lorsque la création répétée d'objets domaine nuit à la lisibilité.

Par exemple, une future fonction conceptuelle :

```python
make_tcp_observation(...)
```

peut fournir des valeurs neutres et permettre au test de préciser uniquement les
champs pertinents.

Les valeurs par défaut d'un builder doivent être déterministes et ne doivent pas
masquer une information qui influence le comportement testé.

Un builder de test reste un outil de lisibilité et ne doit pas devenir une
seconde couche de logique métier.

### Snapshot testing

Le snapshot testing n'est pas utilisé comme stratégie principale pour vérifier les
modèles métier.

Un snapshot complet peut rendre un test fragile face à une modification sans
rapport avec la propriété réellement vérifiée.

Les snapshots peuvent devenir pertinents pour une représentation dont la
stabilité globale constitue explicitement un contrat, par exemple certains
formats d'interface futurs.

Leur utilisation doit donc être justifiée par la nature du contrat testé.

### Property-based testing

Le property-based testing pourra compléter les scénarios déterministes lorsqu'il
permettra d'explorer efficacement des invariants sur de nombreux cas.

Le domaine NetGuard pourra notamment présenter des opportunités autour de :

```text
adresses IP
ports
timestamps
ordre des observations
séquences d'événements
```

Une bibliothèque spécialisée n'est pas introduite tant qu'un besoin concret ne
la justifie.

Les propriétés générées ne remplacent pas les scénarios métier explicites qui
documentent les comportements essentiels.

Toute génération susceptible de provoquer un échec doit rester reproductible.

### Portée de 0.4.7

Les conventions de cette étape définissent une architecture de tests centrée sur
les comportements, contrats et invariants de NetGuard, avec un Core testable sans
infrastructure réelle, des scénarios temporels contrôlés, des données de test
publiables, une séparation entre tests automatisés et laboratoire, des tests
d'intégration suffisamment réalistes aux frontières techniques et un petit
nombre de parcours end-to-end reproductibles. La suite standard doit rester
isolée, déterministe, exécutable hors ligne et sans privilèges réseau élevés,
tandis que `pytest` constitue le framework principal des tests backend.
