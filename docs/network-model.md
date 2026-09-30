# Modèle réseau

Statut : modèle réseau sémantique conçu pendant l’étape 0 ; topologie concrète du laboratoire à préparer au début de l’étape 1.

Les [modèles métier](data-models.md) définissent les observations, identités, endpoints, scopes, provenance, PacketObservation, Flow, FlowObservation, temps et états analytiques. Ces contrats s’inscrivent dans les frontières de l’[architecture](architecture.md).

À préciser au début de l’étape 1 : topologie du laboratoire, réseaux supervisé et de management, ports exposés et capabilities nécessaires. Cette topologie doit assurer l’isolation, la visibilité effective du sensor, des privilèges de capture maîtrisés, une exposition contrôlée et une reproductibilité raisonnable.

Critère indispensable : démontrer que le sensor observe réellement le trafic entre le générateur et la cible. Le simple partage d’un réseau Docker ne constitue pas cette preuve.
