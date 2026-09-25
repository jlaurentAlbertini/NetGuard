# ADR-002 — Normalize External Network Observations Before the Core

## Status

Accepted

## Context

NetGuard may receive network information from multiple sources,
including:

- live packet capture;
- recorded PCAP files;
- future compatible adapters.

External tools and capture libraries expose their own representations.

Allowing those representations to propagate into detection logic would
couple detectors to specific technologies and make testing,
reproducibility, and source replacement more difficult.

At the same time, different observations do not necessarily have the
same semantics.

For example, an observed packet and a connection summary represent
different facts even when they expose similar network fields.

## Decision

All external network observations shall cross a normalization boundary
before entering the Core.

The Core operates exclusively on validated NetGuard domain models.

Capture-library-specific or external-tool-specific objects shall not be
passed to detectors.

Normalization shall preserve semantic differences between observation
types rather than forcing all inputs into a single indistinguishable
structure.

Detectors shall operate only on observation types whose semantics they
support.

Relevant provenance required for interpretation, debugging, audit, and
reproducibility shall also be preserved.

## Consequences

### Positive

- detectors are independent from capture technologies;
- live capture and recorded input can share detection logic;
- synthetic domain observations can be used in unit tests;
- external technologies can be replaced more easily;
- domain semantics remain under NetGuard control;
- future input adapters can be introduced without redesigning every
  detector.

### Negative

- adapters must translate external representations;
- normalization introduces an explicit boundary and additional models;
- careless normalization could discard information required by future
  detectors.

## Rejected Alternative

Passing native capture objects directly to detectors was rejected
because it would couple domain logic to infrastructure.

Using one universal flat event representation for every possible
observation was also rejected because structural similarity must not
erase semantic differences between observation types.
