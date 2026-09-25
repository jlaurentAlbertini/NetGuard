# ADR-001 — Use a Modular Monolith Architecture

## Status

Accepted

## Context

NetGuard requires several distinct responsibilities:

- network ingestion;
- normalization;
- state management;
- detection;
- alert generation;
- persistence;
- presentation.

These responsibilities require clear boundaries, but NetGuard V1 does
not currently require independent deployment, independent scaling, or
distributed ownership of these components.

Introducing microservices would add network communication, distributed
failure modes, serialization boundaries, deployment complexity, and
distributed observability before those costs are justified.

## Decision

NetGuard V1 will be implemented as a modular monolith.

The application will preserve explicit boundaries between:

- Core;
- Application;
- Infrastructure;
- Interfaces.

Modules shall communicate through deliberate contracts rather than
through uncontrolled cross-module dependencies.

The modular monolith refers to the NetGuard application, not to a requirement
that the database, lab targets and application share one container. Deployment
topology and capture privilege boundaries are defined separately.

The architecture may permit future extraction of components, but it
will not introduce distributed boundaries before a demonstrated need
exists.

## Consequences

### Positive

- simpler development and deployment;
- easier local debugging;
- lower operational complexity;
- easier deterministic testing;
- architectural boundaries can still be enforced in code;
- future distribution remains possible if justified.

### Negative

- components initially share the same deployment lifecycle;
- resource isolation is weaker than with independent services;
- scaling individual components independently would require future
  architectural work.

## Rejected Alternative

A microservice architecture was rejected for V1 because its operational
and development costs are not justified by current requirements.
