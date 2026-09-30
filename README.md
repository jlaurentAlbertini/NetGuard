# NetGuard

Plateforme de supervision et de détection d’anomalies réseau, à vocation défensive et conçue comme projet portfolio.

## État du projet

Étape 0 — conception rédigée : exigences, architecture, modèles métier M1–M140, conventions de développement, threat model et sept décisions architecturales (ADR). Les corrections de l’audit 0.7 sont intégrées ; la dernière validation de clôture reste à effectuer. L’étape 0.4.1 matérialise uniquement les packages Python du backend ; leur implémentation reste à réaliser. Aucun service, moteur de détection, dashboard ou environnement Docker n’est encore implémenté. Il n’existe pas encore de commande de lancement ou de suite de tests exécutable.

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
- [Modèles internes](docs/data-models.md)
- [Moteur de détection](docs/detection-engine.md)
- [API](docs/api.md)
- [Sécurité](docs/security.md)
- [Threat model](docs/threat-model.md)
- [Développement](docs/development.md)
- [Stratégie de tests](docs/testing.md)
- [Roadmap](docs/roadmap.md)

L’architecture, les modèles, le threat model et les ADR définissent les contrats de conception retenus. Python, FastAPI, PostgreSQL et Docker Compose sont les orientations du cahier des charges : FastAPI relève des Interfaces, PostgreSQL de l’Infrastructure de persistance et Docker Compose du déploiement et du laboratoire, sans dépendance du Core envers ces technologies. La technologie de capture, la topologie concrète du laboratoire (étape 1), les versions des dépendances, le frontend et les détails de déploiement restent à définir.

Le premier incrément complet vise une seule règle, NG-NET-001. PCAP, agrégation de flows et détecteurs supplémentaires arrivent ensuite. Les exigences décrivent la cible, pas des fonctionnalités déjà disponibles.
