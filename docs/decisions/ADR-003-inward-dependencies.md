# ADR-003 — Keep Source-Code Dependencies Directed Toward the Domain

## Status

Accepted

## Context

NetGuard will interact with replaceable technical systems such as:

- capture libraries;
- persistent storage;
- HTTP frameworks;
- CLI mechanisms;
- presentation layers.

If domain logic directly depends on these technologies, infrastructure
choices would propagate throughout the codebase and make the detection
engine difficult to test or evolve independently.

Runtime call direction does not require source-code dependencies to
follow the same direction.

For example, the Application layer may request persistence while the
concrete persistence implementation depends on a contract owned by the
Application layer.

## Decision

Source-code dependencies shall point toward the inner architectural
layers.

The dependency relationship is conceptually:

```text
                Core
                 ▲
                 │
             Application
                 ▲
                 │
       ┌─────────┴─────────┐
       │                   │
Infrastructure         Interfaces
```

The Core shall not depend on:

- Application;
- Infrastructure;
- Interfaces.

Application may depend on Core.

Infrastructure and Interfaces may depend on contracts exposed by the
appropriate inner layers.

Contracts are owned by the layer expressing the requirement, while
concrete adapters belong to the corresponding outer layer.

Abstractions shall only be introduced when they protect a meaningful
architectural boundary.

Concrete dependencies are assembled at application entry points through
a Composition Root.

## Consequences

### Positive

- domain logic remains independent from infrastructure;
- Core unit tests require no real infrastructure;
- infrastructure technologies can be replaced with limited impact;
- dependencies communicate architectural responsibilities clearly.

### Negative

- explicit adapters and mappings are required at some boundaries;
- developers must respect dependency rules during implementation;
- some workflows require dependency inversion rather than direct calls
  to concrete implementations.

## Rejected Alternative

Direct dependencies from Core or Application logic to concrete
infrastructure implementations were rejected because they would couple
the domain to replaceable technical decisions.
