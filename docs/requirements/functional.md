# NetGuard — Functional Requirements

## Purpose

This document defines the target functional scope and staged delivery of NetGuard.
Requirements describe intended behaviour, not implemented capabilities.

The first vertical slice covers real lab traffic, capture, normalization,
NG-NET-001 vertical port-scan detection, alert persistence, a versioned API and
a dashboard. PCAP, flow aggregation and additional detectors are subsequent
increments, not prerequisites for this first slice. See [roadmap](../roadmap.md).

NetGuard is a defensive network monitoring and detection system designed
to observe network traffic, transform raw observations into structured
network information, detect suspicious behaviours, and generate
explainable alerts.

The initial version focuses on passive monitoring and detection rather
than active prevention.

---

## Functional Requirements

### FR-001 — Network interface selection

NetGuard shall allow the operator to configure the capture interface within
the isolated local NetGuard lab. Test traffic generation must target only lab
services; selecting an interface does not authorize scanning external systems.

### FR-002 — Live traffic capture

NetGuard shall passively capture network traffic visible from the
selected interface.

### FR-003 — Network metadata extraction

NetGuard shall extract metadata required for analysis, including where
applicable:

- timestamp;
- source and destination addresses;
- source and destination ports;
- network and transport protocols;
- packet size;
- relevant protocol information such as TCP flags.

### FR-004 — Normalized internal representation

Captured data shall be converted into a normalized internal
representation independent from the capture mechanism.

Detection components shall not depend directly on capture-library
specific packet objects.

### FR-005 — Network flow aggregation

Deferred increment: NetGuard may aggregate observations into flows when a
detector or consultation use case requires it. Flow semantics and identity must
then be defined explicitly; aggregation is not required for NG-NET-001.

### FR-006 — Temporal network state

NetGuard shall maintain sufficient temporal state to analyse network
activity over bounded time windows.

### FR-007 — Independent detectors

NetGuard shall support multiple independent detection components.

### FR-008 — Suspicious behaviour detection

The first vertical slice shall implement NG-NET-001: vertical port scanning
using distinct destination ports per source/destination pair in a bounded
sliding window, with configurable threshold and cooldown. Event eligibility,
retransmissions and late-event handling shall be defined before implementation.
Additional behaviours are subsequent increments with their own acceptance criteria.

### FR-009 — Detector configuration

Each detector shall be independently configurable, including its
activation state and relevant thresholds or parameters.

### FR-010 — Structured alerts

A successful detection shall generate a structured alert containing at
least:

- detection type;
- severity;
- timestamp;
- affected or involved network entities;
- supporting detection information.

### FR-011 — Explainable alerts

Alerts shall contain sufficient evidence to explain why the detection
was triggered.

### FR-012 — Alert persistence

The Application shall persist generated alerts in PostgreSQL through a
repository contract. Successfully committed alerts shall be available through
the API. Failed or pending writes must not be presented as durable success.

### FR-013 — Activity consultation

Users shall inspect persisted alerts through a dashboard that communicates
exclusively with the versioned `/api/v1/` API. Alert consultation shall support
validated filters and bounded pagination. Detailed activity views may follow
in subsequent increments; the interface shall not fabricate detection results.

### FR-014 — Operational status

NetGuard shall expose sufficient operational information to determine
whether the system and its major components are functioning correctly.

### FR-015 — Offline capture analysis

NetGuard should support analysis of previously recorded network captures,
such as PCAP files.

### FR-016 — Source-independent analysis

Equivalent supported domain observations, in the same order and with equivalent
configuration, initial state, temporal inputs and rule versions, shall produce
equivalent detection decisions regardless of technical source. A packet and a
flow summary are not assumed to be equivalent observations.

### FR-017 — Detector activation

Operators shall enable or disable detectors through validated configuration,
as required by FR-009. Runtime toggling and a management UI are deferred; no
dynamic configuration mechanism is required for the first slice.

### FR-018 — Network activity history

Subsequent increment: NetGuard should maintain activity summaries useful for
consultation. Before storing observations or summaries, define retention,
storage limits and cleanup; indefinite storage of every packet is not required.

### FR-019 — Host visibility

Subsequent increment: NetGuard should provide observed-host information and
activity statistics once their state, aggregation and retention semantics are defined.

### FR-020 — Detection extensibility

The system should allow new categories of detectors to be introduced
without requiring modifications to the packet capture pipeline.

---

## Initial Detection Scope

NetGuard V1 will initially focus on deterministic and heuristic
detections.

The first required detector is vertical port scanning (NG-NET-001).

Candidates for later increments include horizontal scanning, unusually high
connection activity and selected TCP behaviours. These examples are not
committed detectors until their telemetry, semantics and tests are specified.

Statistical anomaly detection may be introduced later without replacing
the existing detection architecture.

---

## Out of Scope for V1

NetGuard V1 is not intended to provide:

- automatic traffic blocking;
- firewall functionality;
- automated attack response;
- malware analysis;
- antivirus functionality;
- exhaustive deep packet inspection;
- enterprise-wide distributed monitoring;
- full SIEM functionality;
- advanced multi-user management;
- machine-learning-based universal attack detection.

These capabilities may be considered in future versions, but the V1
architecture should not unnecessarily prevent future extensions.
