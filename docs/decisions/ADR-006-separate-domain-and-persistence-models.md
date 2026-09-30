# ADR-006 — Separate Domain Models from Persistence Representations

## Status

Accepted

## Context

NetGuard must preserve domain concepts such as observations, detection results, evidence and alerts while also storing selected information beyond process lifetime.

Persistent storage technologies impose concerns that do not belong to the domain itself, including:

- schemas;
- indexes;
- database identifiers;
- serialization formats;
- migration mechanisms;
- storage-specific relationships;
- ORM or driver requirements.

Reusing storage representations as canonical domain models would allow these technical concerns to influence Core semantics.

It would also make changes to persistence technology or schema more likely to propagate into detection logic.

Conversely, a persisted representation cannot automatically be treated as valid domain state merely because it was successfully read from storage.

## Decision

NetGuard shall keep canonical domain models distinct from persistence-specific representations.

The Core owns the semantic meaning and invariants of domain objects.

Infrastructure owns persistence-specific representations and mappings.

Conceptually:

```text
Domain object
     │
     ▼
Persistence mapping
     │
     ▼
Stored representation
```

and when reconstructing:

```text
Stored representation
     │
     ▼
Persistence mapping / validation
     │
     ▼
Domain object
```

Persistence-specific models shall not become the canonical representation of NetGuard domain concepts.

The Core shall not require:

- ORM base classes;
- database sessions;
- storage-specific annotations;
- database-generated semantics;
- concrete persistence drivers.

Storage identifiers may exist when required, but they shall not silently replace domain identities whose semantics are different.

Reading a record from storage shall not bypass domain invariants that are required for safe reconstruction.

```text
successfully persisted
≠
automatically valid domain truth
```

Mappings may evolve independently when storage schemas change, provided the domain meaning required by supported versions is preserved.

Persistence mechanisms may store additional technical metadata when necessary, but such metadata shall not become part of the Core unless it has genuine domain meaning.

## Consequences

### Positive

- Core models remain independent from database and ORM technologies;
- persistence technologies can evolve with limited impact on detector logic;
- storage migrations do not automatically redefine domain semantics;
- reconstruction boundaries provide a deliberate location for validation and compatibility handling;
- tests of domain behaviour do not require a database;
- domain identities and storage identifiers remain conceptually distinct.

### Negative

- explicit mappings between domain and persistence representations are required;
- some fields may appear in both representations;
- persistence code cannot rely on domain objects being directly writable by every storage technology;
- schema evolution requires deliberate compatibility work.

## Rejected Alternatives

Using ORM or database models directly as canonical Core models was rejected because it would couple domain semantics to replaceable infrastructure.

Treating every record successfully read from persistence as an already-valid domain object was rejected because stored data may be stale, incompatible, incomplete or corrupted.

Designing Core models around the needs of a particular database schema was rejected because persistence is an implementation concern rather than the authority over NetGuard domain semantics.