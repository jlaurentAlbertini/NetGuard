# Roadmap

Statut actuel : conception de l’étape 0 rédigée, corrections de l’audit 0.7 intégrées et dernière validation de clôture à effectuer. Arborescence, exigences, architecture, modèles métier M1–M140, conventions de développement, threat model et sept ADR sont documentés. Le cadrage (1.1) et la topologie concrète (1.2) du laboratoire sont documentés sur la base du modèle réseau sémantique déjà conçu. La preuve de visibilité du montage spécialisé (1.3) est réalisée ; les contrôles d’isolation et de permissions (1.4) sont validés pour ce montage. Le laboratoire minimal est consolidé en 1.5 avec une image versionnée, ses dépendances verrouillées et un lancement unifié. Aucune fonctionnalité métier NetGuard n’est implémentée.

La progression suit le cahier des charges :

0. Conception et décisions architecturales.
1. Préparation de la topologie concrète et construction du laboratoire Docker isolé.
2. Sensor et preuve de capture réelle.
3. Normalisation vers NetworkObservation.
4. Moteur générique de détection.
5. Première règle de scan de ports.
6. PostgreSQL et migrations.
7. API FastAPI versionnée.
8. Dashboard consommant l’API.
9. Consolidation des tests unitaires, d’intégration et E2E.
10. CI GitHub Actions.
11. Consolidation du durcissement et des scans de sécurité.
12. Analyse PCAP.
13. Détections supplémentaires.
14. Adaptateur Zeek.
15. Adaptateur Suricata.
16. Corrélation.
17. Observabilité approfondie.
18. Évaluation d’une intégration SIEM selon les besoins.
19. Déploiement portable.
20. Stabilisation et release v1.0.

Tests, sécurité et documentation accompagnent chaque incrément dès le départ ; les étapes dédiées servent à les consolider. Ne pas entreprendre les extensions avant d’avoir validé la première chaîne complète sur du trafic réel.

## Suivi du laboratoire — étape 1

- **1.1 — Cadrage et prérequis : terminé.** [Prérequis du laboratoire](lab-environment.md), périmètre et critères de qualification définis. Le montage initial est éprouvé en 1.3 ; ses frontières d’isolation sont éprouvées en 1.4.
- **1.2 — Topologie réseau concrète : définie.** [Schéma, adressage et flux](lab-topology.md) : bridge interne, trois services, capteur dans l’espace réseau de la cible et administration via Docker. Visibilité éprouvée en 1.3 ; conflits d’adressage contrôlés avant chaque essai, frontières d’isolation éprouvées en 1.4.
- **1.3 — Positionnement du capteur et preuve de visibilité : validée.** [Deux captures réelles](lab-visibility.md) vérifient HTTP, ports fermés, adresses, timestamps et rétablissement après recréation de la cible ; ressources temporaires nettoyées.
- **1.4 — Isolation et permissions : validée pour le montage spécialisé.** [35 contrôles réels](lab-isolation.md), absence de route externe, DNS limité, privilèges minimaux et stockage borné ; capture 1.3 revérifiée et ressources temporaires nettoyées.
- **1.5 — Construction avec Docker Compose : validée pour Linux/ARM64 avec Docker Desktop.** [Lancement, verrou et qualification](lab-compose.md) : image versionnée, 44 paquets fixés, refus des images périmées et preuves après reconstruction sans cache.
- **1.6 — Scénarios de trafic contrôlés : à réaliser.**
- **1.7 — Captures de référence : à réaliser.**
- **1.8 — Vérifications automatiques et reproductibilité : à réaliser.**
- **1.9 — Documentation et validation finale : à réaliser.**

Ces sous-étapes détaillent le laboratoire sans renuméroter les étapes principales. La preuve de capture du lab prépare l’implémentation du sensor de l’étape 2. Les captures témoins ne constituent pas l’implémentation de l’analyse PCAP de l’étape 12. La clôture finale de l’étape 0 reste à confirmer séparément.
