# NetGuard — Non-Functional Requirements

## Purpose

This document defines the primary quality, maintainability, security,
portability, and operational requirements of NetGuard.

---

## NFR-001 — Modularity

Major responsibilities shall be separated into clearly defined
components.

Capture, normalization, network state management, detection, alerting,
persistence, and presentation shall not be unnecessarily coupled.

## NFR-002 — Extensibility

New detectors should be addable without requiring changes to unrelated
components such as capture, persistence, or presentation.

## NFR-003 — Testability

Core unit tests shall require no live network, database, HTTP server, frontend
or real-time waiting. Integration tests exercise concrete boundaries; the
reference E2E test verifies real lab traffic through capture, detection,
persistence and API consultation.

Synthetic or recorded normalized network events shall be usable as test
inputs.

## NFR-004 — Deterministic detection

Given the same ordered observations, relevant temporal inputs, configuration,
initial state and engine/rule versions, detectors shall produce equivalent
decisions. Technical identifiers do not affect those decisions.

## NFR-005 — Explainability

Every generated detection alert shall expose sufficient evidence to
understand why it was triggered.

## NFR-006 — External configuration

Operational parameters shall not be unnecessarily hard-coded.

The first vertical slice shall externalize the relevant parameters, including:

- capture source;
- enabled detectors;
- detector thresholds;
- logging level;
- storage configuration.

## NFR-007 — Internal observability

NetGuard shall provide sufficient logging and operational information to
diagnose its own behaviour.

Significant lifecycle events, failures, and component states shall be
observable.

## NFR-008 — Robustness

Expected malformed or unsupported observations shall be rejected or skipped
under an explicit, observable policy. Internal errors that compromise analysis
integrity may require controlled shutdown; the system must not catch every
exception and continue silently. Recovery must respect bounded resources.

## NFR-009 — Performance

NetGuard shall be capable of processing realistic traffic volumes for
its intended workstation and laboratory environments without obviously
inefficient per-packet operations.

Concrete performance targets will be established after the architecture
and processing model are defined.

## NFR-010 — Bounded memory usage

Long-running monitoring shall not require retaining all observed packets
or events indefinitely in memory.

Temporal state shall be bounded in both duration and quantity. Queues shall
have explicit capacities and saturation policies, accounting for variable item
size where relevant. Known drops, evictions and saturation shall be observable;
limits on measuring upstream loss shall be documented.

## NFR-011 — Portability

The core analysis and detection logic should remain independent from
operating-system-specific capture mechanisms where reasonably possible.

Platform-specific behaviour shall be isolated behind appropriate boundaries.
The lab shall be reproducible with Docker Compose; the supported host platforms,
capture visibility, required capabilities and exposed ports must be documented
and verified rather than assuming identical native capture behaviour everywhere.

## NFR-012 — Untrusted network input

All network-derived data shall be considered untrusted input.

Parsing and processing components shall be designed accordingly.

## NFR-013 — Least privilege

Components shall operate with the minimum privileges required for their
responsibilities.

If packet capture requires elevated privileges, this requirement should
not automatically extend to unrelated NetGuard components.

## NFR-014 — Data minimization

NetGuard should collect and persist only network information necessary
for its monitoring and detection objectives.

V1 shall favour network metadata over unnecessary long-term storage of
packet payloads.

## NFR-015 — Reproducibility

Recorded-input analysis shall follow the reproducibility conditions in NFR-004.
Observation provenance sufficient to interpret the input shall be preserved,
without requiring unnecessary packet payloads or sensitive local paths.

This requirement supports testing, debugging, demonstrations, and
detector validation.

## NFR-016 — Lifecycle and durability

Readiness, graceful shutdown deadlines and failure termination shall be explicit.
Accepted, analysed and persisted work shall be distinguished. Volatile results
must not be reported as durable; abrupt-termination limitations must be documented.

## NFR-017 — Persistent retention

Before introducing event/history storage, define retention, capacity and cleanup
policies. Alert retention and local capture artifacts require explicit policies
as well; bounded memory alone does not bound disk growth.

## NFR-018 — Quality automation

Tests, documentation and security checks accompany each implemented increment.
CI shall progressively verify formatting/lint, unit and integration tests,
container builds, dependency auditing and image scanning. Tools and versions
are selected when introduced, with failures made visible. The real-traffic E2E
scenario must be reproducible and documented.
