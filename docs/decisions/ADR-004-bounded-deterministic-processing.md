# ADR-004 — Use Bounded and Deterministic Processing by Default

## Status

Accepted

## Context

Network traffic may arrive faster than NetGuard can process it.

Unbounded buffering would convert sustained overload into uncontrolled
memory growth.

Aggressive parallelism could increase throughput but would introduce
complexity around:

- event ordering;
- shared detection state;
- temporal windows;
- reproducibility;
- shutdown;
- failure handling.

Temporal analysis also requires distinguishing when an observation
occurred from when NetGuard happened to process it.

## Decision

NetGuard's initial processing architecture shall prioritize bounded
resource usage, explicit overload behaviour, and deterministic analysis.

Pipeline buffers, when needed, shall be bounded; a queue is not mandatory at
every module boundary. Temporal analysis state shall also be bounded in duration
and quantity, with explicit ownership, expiration and eviction policies.

Each buffer shall define:

- capacity;
- saturation behaviour;
- observable overload behaviour.

Known data loss and known saturation shall be observable.

The initial analysis pipeline shall preserve required ordering and avoid
additional parallelism until measured performance requirements justify
it.

Future parallelization must preserve the ordering and grouping
guarantees required by detectors.

NetGuard shall distinguish event time from processing time.

Temporal network detections shall normally operate on event time.

Policies for late or out-of-order observations shall be explicit where
relevant.

Core logic shall not depend implicitly on the system wall clock.
Controllable time dependencies shall be used when current time is
required.

Slow infrastructure operations may be isolated from the critical
analysis path when justified, but any resulting asynchronous boundary
must retain:

- bounded capacity;
- explicit delivery semantics;
- explicit failure behaviour;
- explicit persistence semantics;
- explicit shutdown behaviour with a bounded graceful-shutdown deadline.

Abrupt termination can lose volatile work. Accepted, analysed and committed
work must not be treated as equivalent. Determinism assumes the same ordered
observations, relevant temporal inputs, configuration, initial state and
engine/rule versions.

## Consequences

### Positive

- memory consumption cannot grow indefinitely solely because of queues;
- overload becomes observable;
- deterministic behaviour is easier to reason about and test;
- PCAP replay can use the same temporal detection semantics as live
  processing;
- concurrency complexity is introduced only when justified by evidence.

### Negative

- bounded buffers require explicit behaviour when capacity is exhausted;
- the initial architecture may provide less throughput than a highly
  parallel implementation;
- handling late or out-of-order observations requires explicit detector
  policies;
- future performance requirements may require controlled
  parallelization.

## Rejected Alternatives

Unbounded queues were rejected because they transform sustained
overload into uncontrolled memory growth.

Parallel processing by default was rejected because current
requirements do not justify the additional ordering and state-management
complexity.

Using processing time implicitly for network detection windows was
rejected because it would make replay and delayed processing produce
different domain behaviour.
