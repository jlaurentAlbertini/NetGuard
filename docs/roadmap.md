# Roadmap

Statut actuel : étape 0 en cours. Arborescence, exigences, architecture et quatre ADR rédigés ; modèles métier, topologie de capture et threat model détaillé restent à définir. Aucune fonctionnalité implémentée.

La progression suit le cahier des charges :

0. Conception et décisions architecturales.
1. Laboratoire Docker isolé.
2. Sensor et preuve de capture réelle.
3. Normalisation vers NetworkEvent.
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
