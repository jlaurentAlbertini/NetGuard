# Modèle réseau

Statut : modèle réseau sémantique conçu pendant l’étape 0 ; cadrage (1.1) et topologie concrète (1.2) documentés ; visibilité et isolation à valider.

Les [modèles métier](data-models.md) définissent les observations, identités, endpoints, scopes, provenance, PacketObservation, Flow, FlowObservation, temps et états analytiques. Ces contrats s’inscrivent dans les frontières de l’[architecture](architecture.md).

La [topologie du laboratoire (1.2)](lab-topology.md) définit trois services sur un bridge interne : générateur, cible web et capteur partageant l’espace réseau de la cible. Aucun port n’est publié sur l’hôte ; l’administration passe par Docker, sans réseau de management dédié à ce stade. Les permissions de capture, la visibilité, l’isolation et la reproductibilité restent à vérifier dans les sous-étapes suivantes.

Critère indispensable : démontrer que le sensor observe réellement le trafic entre le générateur et la cible. Le simple partage d’un réseau Docker ne constitue pas cette preuve.

Le [cadrage et les prérequis du laboratoire (1.1)](lab-environment.md) définissent un environnement de conteneurs Linux orchestrés avec Docker Compose. Docker Desktop constitue l'environnement initial de qualification ; la visibilité du point de capture sera éprouvée en 1.3.
