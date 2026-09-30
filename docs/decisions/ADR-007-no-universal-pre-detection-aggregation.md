# ADR-007 — Do Not Require Universal Aggregation Before Detection

## Status

Accepted

## Context

Network detections may require different forms of information.

Some detectors can operate directly on normalized observations while maintaining only the analytical state they specifically require.

Other detectors may benefit from derived structures such as flows, temporal aggregates or other network state.

Requiring every observation to first pass through one universal aggregate representation would simplify the pipeline superficially, but it would introduce several problems.

Packet-level information may be lost during aggregation.

A flow constructed by NetGuard and a flow-like observation supplied directly by an external source do not necessarily represent the same facts.

Some detectors do not require a completed flow at all.

Forcing all detection through a universal state representation would also introduce unnecessary state, latency and lifecycle requirements for detectors that do not need them.

## Decision

NetGuard shall not require all detection logic to consume one universal precomputed network aggregate.

Normalized observations are valid Core inputs in their own right.

Each detector shall explicitly define:

- the observation types it accepts;
- the semantic preconditions required for analysis;
- the analytical state it owns, when state is necessary;
- the grouping and temporal semantics relevant to that state.

A detector may consume normalized observations directly.

A detector may maintain detector-specific analytical state.

Derived domain structures such as `Flow` may be used when their semantics match the needs of the detector, but they are not a mandatory intermediate representation for every detection.

The architectural concept of Network State therefore represents a responsibility for derived analytical state, not one mandatory global object through which every observation must pass.

```text
normalized observation
        │
        ├──────────────► detector
        │
        └──► derived state / aggregation
                         │
                         └──► detector
```

A `Flow` constructed by NetGuard shall remain semantically distinct from a `FlowObservation` supplied as an already aggregated external observation.

NetGuard shall not fabricate packet-level facts from aggregate observations when those facts were not observed.

Likewise, aggregation shall not silently erase information that a detector contract requires.

Detector-specific state remains subject to the boundedness, ownership, temporal and deterministic-processing requirements defined elsewhere in the architecture.

## Consequences

### Positive

- simple detectors do not require unnecessary global aggregation;
- packet-level detectors can retain packet-level semantics;
- future detectors can choose the minimum state appropriate to their analysis;
- NetGuard does not need one universal state model capable of representing every possible detector;
- externally supplied aggregate observations are not falsely treated as reconstructed packets;
- state ownership remains local and easier to reason about;
- new detector types can be added without redesigning a mandatory global aggregation pipeline.

### Negative

- different detectors may consume different domain inputs;
- there is no single universal structure that represents all analytical state;
- the engine must route supported observation types deliberately;
- some aggregation logic may be specific to particular detectors or reusable analytical components;
- developers must avoid duplicating equivalent aggregation logic unnecessarily.

## Rejected Alternatives

Requiring every observation to be converted into a `Flow` before detection was rejected because not every detector requires flow semantics and aggregation can discard relevant information.

Creating one global mutable Network State object consumed by every detector was rejected because detector state has different ownership, grouping, temporal and capacity requirements.

Reconstructing synthetic packet observations from aggregate flow information was rejected because it would invent facts that were never directly observed.