# Développement

Statut : étape 0.4.1 matérialisée ; règles de dépendances et d’imports de 0.4.2 documentées. Packages Python uniquement, sans fonctionnalité métier ni commande de lancement.

Conventions initiales : code Python sous `backend/src/netguard/`, tests séparés par niveau, format des fichiers défini par `.editorconfig`. Le packaging minimal est décrit ci-dessous ; les règles d’import sont définies ci-dessous ; l’outillage de qualité reste aux étapes suivantes.

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

