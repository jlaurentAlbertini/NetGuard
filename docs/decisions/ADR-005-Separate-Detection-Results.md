# ADR-005 — Separate Detection Results from Alerts

## Status

Accepted

## Context

NetGuard detectors analyze domain observations and analytical state in order to determine whether the conditions of a detection rule are satisfied.

A positive detection conclusion and an operational alert are related, but they do not represent the same concept.

A detector needs to express facts such as:

- which rule produced the conclusion;
- which observations or calculated facts support it;
- which analytical configuration influenced it;
- when the relevant activity occurred.

An alert introduces additional concerns such as:

- stable alert identity;
- presentation;
- persistence;
- acknowledgement or tracking status;
- grouping or suppression;
- later operational handling.

If detectors directly create operational alerts, detection semantics become coupled to alert lifecycle, persistence and presentation concerns.

It would also become harder to distinguish:

```text
what the detector concluded
from
how that conclusion is operationally tracked
```

## Decision

NetGuard shall model a positive detection conclusion as a `DetectionResult` that is distinct from an `Alert`.

The conceptual relationship is:

```text
NetworkObservation
        │
        ▼
     Detector
        │
        ▼
 DetectionResult
        │
        ├──► Evidence
        │
        ▼
      Alert
```

A detector is responsible for producing domain detection conclusions.

A detector shall not directly own:

- alert persistence;
- alert delivery;
- acknowledgement state;
- user-facing tracking state;
- interface-specific presentation;
- external notification mechanisms.

A `DetectionResult` shall represent the semantic outcome of a detector and the structured facts required to explain that conclusion.

`Evidence` shall preserve the relevant observed or calculated facts supporting the result without claiming more certainty than those facts provide.

An `Alert` shall represent the security result made available for operational tracking.

Alert identity shall therefore be distinct from detector state identity, observation identity and detection-rule identity.

A positive `DetectionResult` does not imply that the underlying activity has been confirmed as malicious.

Likewise:

```text
DetectionResult
≠
Alert
≠
confirmed incident
```

The Application layer coordinates the transformation of relevant detection results into alerts by invoking the appropriate domain policies. Decisions affecting business meaning, including severity, grouping or suppression when applicable, belong to the domain rather than to technical orchestration.

Application coordinates persistence, publication and other external effects through explicit contracts; it does not define the business meaning of alerting policies.

Future mechanisms such as grouping, suppression, acknowledgement, notification or escalation may evolve without changing detector semantics.

## Consequences

### Positive

- detector logic remains independent from alert lifecycle concerns;
- detection semantics can be tested without persistence or presentation infrastructure;
- Evidence remains tied to the actual analytical conclusion;
- alert tracking can evolve independently from detector implementations;
- replay and deterministic detector tests do not require reproducing operational alert state;
- future grouping, suppression or notification mechanisms do not need to be implemented inside detectors;
- user-facing alert status cannot silently alter the historical meaning of the original detection conclusion.

### Negative

- an explicit transformation exists between detection results and alerts;
- additional domain concepts and mappings are required;
- developers must preserve the distinction when designing persistence and APIs;
- some apparently simple workflows require more than one model instead of a single universal event object.

## Rejected Alternatives

Having detectors directly create and manage alerts was rejected because it would couple analytical logic to operational tracking concerns.

Representing observations, detection conclusions and alerts as one generic event type was rejected because these objects carry different semantics and lifecycle guarantees.

Treating every positive detection result as a confirmed security incident was rejected because NetGuard can report suspicious observed behaviour without proving malicious intent.
