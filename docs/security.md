# Sécurité

Statut : exigences initiales, mesures non encore implémentées.

Les scénarios de trafic doivent cibler uniquement le laboratoire local. Minimiser les privilèges du sensor et documenter les capabilities ; ne pas utiliser `privileged: true` par commodité.

Prévoir : isolation réseau, services non-root lorsque possible, validation des entrées, secrets hors Git, dépendances verrouillées et ports exposés limités. Les captures réseau peuvent contenir des données sensibles : elles sont ignorées par défaut dans Git.
