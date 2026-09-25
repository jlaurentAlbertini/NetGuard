# Stratégie de tests

Statut : tests à implémenter avec les fonctionnalités correspondantes.

- Unitaires : validation des modèles, parsing, normalisation, fenêtre temporelle, seuil, cooldown et expiration de l’état.
- Intégration : acquisition vers normalisation, service applicatif orchestrant moteur et repository et API vers PostgreSQL.
- End-to-end : trafic réel du laboratoire, capture, détection, persistance puis vérification de l’alerte par l’API.

Les tests du Core ne nécessitent ni réseau, ni DB, ni serveur HTTP, ni attente réelle. Vérifier aussi la saturation, les évictions, les données invalides, les événements désordonnés, les pannes de stockage et l’arrêt avec du travail en attente. Distinguer les tests métier avec observations synthétiques du test E2E validant effectivement la capture.

Les fixtures doivent être déterministes et exemptes de données sensibles. Aucun résultat E2E ne doit être remplacé par une alerte fabriquée directement en base ou dans l’interface.
