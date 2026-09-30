# Roadmap

Statut actuel : conception de l’étape 0 rédigée, corrections de l’audit 0.7 intégrées et dernière validation de clôture à effectuer. Arborescence, exigences, architecture, modèles métier M1–M140, conventions de développement, threat model et sept ADR sont documentés. La topologie concrète du laboratoire sera préparée au début de l’étape 1 sur la base du modèle réseau sémantique déjà conçu. Aucune fonctionnalité implémentée.

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
