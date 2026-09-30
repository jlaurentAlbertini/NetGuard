# Stratégie de tests

Statut : tests à implémenter avec les fonctionnalités correspondantes.

- Unitaires : validation des modèles, parsing, normalisation, fenêtre temporelle, seuil, cooldown et expiration de l’état.
- Intégration : acquisition vers normalisation, service applicatif orchestrant moteur et repository et API vers PostgreSQL.
- End-to-end automatisés déterministes : parcours contrôlés avec observations synthétiques, petits PCAP ou adapters contrôlés ; des fakes aux frontières peuvent isoler les effets externes selon le contrat testé.
- End-to-end d’acceptation du laboratoire : trafic réellement généré dans le lab, capture réelle par NetGuard, normalisation, détection, Alert, persistance puis vérification de l’alerte par l’API, conformément à [NFR-003](requirements/non-functional.md). Un test PCAP ne remplace pas ce scénario.

La suite standard ne nécessite ni réseau réel, ni root, ni Internet, ni laboratoire actif. Le scénario d’acceptation du laboratoire peut être automatisé dans une suite spécialisée séparée avec ses prérequis propres.

La racine canonique des tests backend est `backend/tests/`. Les sous-répertoires ne seront créés que lorsqu’un besoin réel le justifiera, conformément aux [conventions de développement](development.md).

Les tests du Core ne nécessitent ni réseau, ni DB, ni serveur HTTP, ni attente réelle. Vérifier aussi la saturation, les évictions, les données invalides, les événements désordonnés, les pannes de stockage et l’arrêt avec du travail en attente. Distinguer les tests métier avec observations synthétiques du test E2E validant effectivement la capture.

Les fixtures doivent être déterministes et exemptes de données sensibles. Aucun résultat E2E ne doit être remplacé par une alerte fabriquée directement en base ou dans l’interface.
