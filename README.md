# NetGuard

Plateforme de supervision et de détection d’anomalies réseau, à vocation défensive et conçue comme projet portfolio.

## État du projet

Étape 0 — conception rédigée : exigences, architecture, modèles métier M1–M140, conventions de développement, threat model et sept décisions architecturales (ADR). Les corrections de l’audit 0.7 sont intégrées ; la dernière validation de clôture reste à effectuer. L’étape 0.4.1 matérialise uniquement les packages Python du backend ; leur implémentation reste à réaliser. Le cadrage (1.1) et la topologie (1.2) sont documentés. Un montage Docker spécialisé prouve la visibilité réseau (1.3) et ses frontières d’isolation et de permissions (1.4). Le laboratoire minimal est consolidé en 1.5 : lancement unifié, image versionnée et dépendances verrouillées. Le sensor NetGuard, le moteur de détection et le dashboard ne sont pas encore implémentés. La preuve du laboratoire dispose d’une commande dédiée ; la suite standard des tests backend reste à construire.

## Preuves du laboratoire

Avec Docker Linux local, Docker Compose et Python ≥ 3.11 sur l’hôte :

```sh
python3 -B scripts/lab.py verify
```

La commande construit l’image d’outillage, vérifie 35 contrôles d’isolation et de permissions, puis deux captures réelles avec recréation de la cible. Chaque preuve nettoie ses conteneurs et réseaux temporaires. La [consolidation Compose (1.5)](docs/lab-compose.md) fournit une image versionnée, un verrou complet des paquets et le contrôle des images périmées. Ajouter `--rebuild` pour reconstruire sans cache avant les preuves. Les résultats restent dans `artifacts/lab/`, ignoré par Git et limité par les pilotes à 20 dossiers et un budget de 128 Mio. Voir les protocoles et limites de [visibilité (1.3)](docs/lab-visibility.md) et d’[isolation (1.4)](docs/lab-isolation.md).

## Premier objectif

Construire progressivement une chaîne vérifiable :

```text
Trafic réel du laboratoire → Sensor → Parsing → Normalisation
    → NetworkObservation → Detection Engine → NG-NET-001
    → DetectionResult (Evidence) → Alert → PostgreSQL → API FastAPI → Dashboard
```

Les scénarios de test cibleront exclusivement le laboratoire local NetGuard. Les alertes affichées devront provenir du trafic réellement observé.

## Organisation

```text
NetGuard/
├── backend/
│   ├── pyproject.toml            # Packaging Python, sans dépendance runtime
│   ├── tests/                   # Racine canonique des tests backend
│   └── src/netguard/            # Packages uniquement à l’étape 0.4.1
│       ├── core/
│       │   ├── network/
│       │   ├── detection/rules/
│       │   └── alerts/
│       ├── application/
│       ├── infrastructure/
│       │   ├── capture/
│       │   ├── persistence/
│       │   └── observability/
│       └── interfaces/
│           ├── api/
│           └── cli/
├── frontend/                    # Interface consommant exclusivement l’API
├── lab/
│   ├── visibility/              # Preuves de visibilité et d’isolation (1.3–1.4)
│   ├── traffic-generator/       # Scénarios locaux de trafic réel
│   └── targets/target-web/      # Première cible du laboratoire
├── deploy/docker/              # Images et déploiement de NetGuard
├── config/                     # Configuration documentée, sans secrets
├── migrations/                 # Évolution du schéma de base de données
├── scripts/                    # Commandes de développement et démonstration
├── docs/
│   ├── decisions/              # Décisions architecturales et compromis
│   └── requirements/           # Exigences fonctionnelles et non fonctionnelles
└── .github/workflows/           # Automatisation CI à venir
```

Les dossiers matérialisent des responsabilités, pas nécessairement des services ou conteneurs distincts. Les packages Python sont matérialisés par des `__init__.py` vides, sans réexports. Les `.gitkeep` restent utilisés pour les autres dossiers encore vides. L’ancien squelette `src/netguard/`, composé uniquement de `.gitkeep`, est remplacé par `backend/src/netguard/`.

## Documentation

- [Exigences fonctionnelles](docs/requirements/functional.md)
- [Exigences non fonctionnelles](docs/requirements/non-functional.md)
- [Architecture et invariants](docs/architecture.md)
- [Décisions architecturales](docs/decisions/README.md)
- [Modèle réseau et topologie du laboratoire](docs/network-model.md)
- [Laboratoire : cadrage et prérequis (1.1)](docs/lab-environment.md)
- [Laboratoire : topologie réseau (1.2)](docs/lab-topology.md)
- [Laboratoire : preuve de visibilité (1.3)](docs/lab-visibility.md)
- [Laboratoire : isolation et permissions (1.4)](docs/lab-isolation.md)
- [Laboratoire : Docker Compose et image verrouillée (1.5)](docs/lab-compose.md)
- [Modèles internes](docs/data-models.md)
- [Moteur de détection](docs/detection-engine.md)
- [API](docs/api.md)
- [Sécurité](docs/security.md)
- [Threat model](docs/threat-model.md)
- [Développement](docs/development.md)
- [Stratégie de tests](docs/testing.md)
- [Roadmap](docs/roadmap.md)

L’architecture, les modèles, le threat model et les ADR définissent les contrats de conception retenus. Python, FastAPI, PostgreSQL et Docker Compose sont les orientations du cahier des charges : FastAPI relève des Interfaces, PostgreSQL de l’Infrastructure de persistance et Docker Compose du déploiement et du laboratoire, sans dépendance du Core envers ces technologies. La topologie initiale est définie en 1.2 et sa visibilité est éprouvée par le montage 1.3 ; ses frontières d’isolation et permissions sont éprouvées en 1.4. La technologie de capture, les versions des dépendances, le frontend et les détails de déploiement restent à définir.

Le premier incrément complet vise une seule règle, NG-NET-001. PCAP, agrégation de flows et détecteurs supplémentaires arrivent ensuite. Les exigences décrivent la cible, pas des fonctionnalités déjà disponibles.
