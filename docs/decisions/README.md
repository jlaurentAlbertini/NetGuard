# Décisions architecturales

Les ADR enregistrent les choix retenus et leurs compromis. « Accepted » désigne
une décision de conception, pas une fonctionnalité implémentée.

| ADR | Décision | Statut |
| --- | --- | --- |
| [ADR-001](ADR-001-Modular-Monolith.md) | Monolithe modulaire | Accepted |
| [ADR-002](ADR-002-normalized-domain-observation.md) | Observations normalisées et sémantique explicite | Accepted |
| [ADR-003](ADR-003-inward-dependencies.md) | Dépendances vers les couches internes | Accepted |
| [ADR-004](ADR-004-bounded-deterministic-processing.md) | Traitement borné et déterministe | Accepted |

Les [invariants d’architecture](../architecture.md) et les ADR doivent rester
cohérents. Toute décision qui en remplace une autre doit identifier explicitement
la décision remplacée et expliquer le changement. Les précisions apportées pendant
la conception initiale ne constituent pas des preuves d’implémentation.
