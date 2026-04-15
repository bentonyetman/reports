# ADR-65 Gap Analysis: Shared Domain Objects vs. Bifrost Implementation

**Date:** 2026-04-01
**Author:** Benton Yetman
**Subject:** Policy gaps remaining in ADR-65, implementation gaps in Bifrost, and terminology collisions between the two

---

## Executive Summary

ADR-65 establishes the *policy* for shared Domain Objects at OpenGov. Bifrost was built as the *implementation platform* to realize those principles. This analysis identifies three categories of issues:

1. **Policy gaps in ADR-65** -- decisions the ADR must make that Bifrost cannot invent on its own (lifecycle stages, breaking change policy, governance processes, analytical sinks)
2. **Implementation gaps in Bifrost** -- ADR principles that Bifrost doesn't yet model (Suite dependencies, analytical data products, cross-functional team composition)
3. **Terminology collisions** -- words used differently across the ADR, Bifrost, and the broader OpenGov platform that will cause cross-team confusion at scale

The structural detail that Bifrost adds (domain hierarchy, CQRS, properties, invariants, relationships, context mappings) is not a gap in the ADR -- ADR-65 intentionally stays at the principle level. **However, the ADR's single biggest gap is that it does not reference Bifrost at all.** Teams reading ADR-65 today don't know the implementation exists and risk building parallel solutions.

---

## Part 1: Policy Gaps in ADR-65

These are decisions only the ADR can make. Bifrost can model the result, but the policy must be defined first.

### 1.1 No Lifecycle / Maturity Model

**What the ADR says:** "Domain Objects are always versioned." No further detail.

**What is missing from both the ADR and Bifrost:** A lifecycle model:
- **Proposed** -- Under discussion, no implementation
- **Draft** -- Initial schema, unstable, expect breaking changes
- **Alpha** -- API available in staging, limited consumers
- **Stable** -- Production, versioned contracts, breaking changes require migration plan
- **Deprecated** -- Consumers migrating off, sunset date set

**Why this matters:** "Versioned" is necessary but not sufficient. A version number doesn't tell consumers whether it's safe to depend on. The ADR's own Chart of Accounts example ("currently going through a new rewrite") illustrates the problem -- is it safe to integrate with CoA right now? A lifecycle stage answers that question; a version number does not.

**Recommendation:** Define lifecycle stages with clear promotion criteria. Bifrost can model this via badges or a dedicated field, but the policy must come from the ADR.

---

### 1.2 No Breaking Change Policy

**What the ADR says:** "Contracts in place to ensure stability of use."

**What is undefined:** What constitutes a breaking change? What's the migration process? What's the deprecation timeline?

**Why this matters:** Adding an optional field to Vendor is non-breaking. Removing a field or renaming an event topic breaks every consumer. Without a policy, the "contracts" principle is aspirational. Bifrost can enforce version bumps, but it can't decide what merits a major vs. minor version -- that's a policy call.

**Recommendation:** Define breaking vs. non-breaking changes, required deprecation notice periods, and consumer migration support obligations.

---

### 1.3 No Context Mapping Policy

**What the ADR says:** The governance section discusses cross-team coordination informally (Vendor ownership, Chart of Accounts cross-Suite representation).

**What Bifrost already provides:** Formal DDD Context Mapping types:
- SharedKernel, CustomerSupplier, Conformist, ACL (Anti-Corruption Layer), OpenHost, PublishedLanguage

**What the ADR needs to decide:** When two domains both need the same concept (Vendor in Financials vs. Procurement), which integration pattern should they use? The ADR says "work together to align" but doesn't give teams a vocabulary for the *outcome* of that alignment. An ACL (Procurement maintains its own Supplier model that translates to/from Financials' Vendor) is a fundamentally different answer than SharedKernel (one shared Vendor definition owned jointly).

**Recommendation:** Add a section on context mapping patterns with guidance on when to use each. Bifrost already models these -- the ADR just needs to adopt the vocabulary and provide selection criteria.

---

### 1.4 Analytical Sink is Principle-Only

**What the ADR says:** Domain Objects "should have one or more analytical data sinks (analytical data products)."

**What Bifrost models:** Nothing. There is no analytical data product schema in BifrostSpec.

**Why this matters:** This is the one ADR principle where both the policy and the implementation are incomplete. The ADR's own examples acknowledge the gap: "User Analytics (missing today, but important)" and "Entity Analytics (missing today)."

**Recommendation:** Either flesh out the analytical sink requirements (what warehouse, what refresh cadence, what dimensions) in a follow-up ADR, or explicitly mark this principle as aspirational with a timeline for definition.

---

### 1.5 MCP / Agent Contract Policy is Undefined

**What the ADR says:** Domain Objects "*should* have basic operations exposed via internal MCP Server" following "guidance for Agent Contracts."

**What Bifrost provides:** Commands and Queries with full API mappings, input/output schemas, and required claims -- everything needed to *generate* an MCP tool definition.

**What the ADR needs to decide:** Which operations should be exposed as MCP tools? All commands? Only idempotent queries? What's the naming convention? What's the authorization model for AI-invoked operations vs. human-invoked ones?

**Recommendation:** Define the MCP tool derivation policy. Bifrost has the raw material; the ADR needs to define which operations get exposed and how.

---

### 1.6 ADR Does Not Reference Bifrost

**The single biggest gap.** Bifrost was built to implement ADR-65's principles, but the ADR makes no mention of Bifrost, Logos, BifrostSpec, specgen, or any of the infrastructure that already exists.

**Consequences:**
- Teams reading ADR-65 don't know the implementation platform exists
- Teams may build parallel domain catalogs, parallel spec formats, parallel search systems
- New domain object onboarding has no documented process (specgen extracts from 10+ frameworks today)
- The principles feel abstract when there's a concrete, running system behind them

**Recommendation:** Add a "Implementation" or "Tooling" section to ADR-65 that references Bifrost as the platform for registering, cataloging, and discovering shared Domain Objects. Map each principle to its Bifrost implementation:

| ADR Principle | Bifrost Implementation |
|---------------|----------------------|
| Owned by one domain team | BifrostSpec `team` with members |
| Service / APIs | BifrostSpec `commands` + `queries` with API mappings |
| Eventing | BifrostSpec `events` with CloudEvents types + `channels` |
| Versioning | BifrostSpec `version` field + `specVersion` |
| Documented | Logos catalog API + search |
| MCP Server tools | Derivable from Commands/Queries (policy TBD) |
| Government App Builder | BifrostSpec `deeplinkURI` + `servers`/`uiServers` |
| Analytical sink | *Not yet modeled* |

---

## Part 2: Implementation Gaps in Bifrost

These are ADR requirements that Bifrost, as the implementation platform, doesn't yet support.

### 2.1 No Suite Concept

**ADR requirement:** The governance model is built around Suite dynamics -- Suites consume shared Domain Objects, domain teams are explicitly "not a single Suite team," Chart of Accounts needs "representation from ALL Suites."

**Bifrost gap:** There is no concept of Suite in BifrostSpec. There is no way to declare "this domain object is consumed by Financials and Procurement Suites" or to model cross-Suite team composition.

**Impact:** The ADR's core governance model (who owns what, who consumes what, how conflicts are resolved) cannot be represented in the system that was built to implement it.

**Recommendation:** Add a `consumers` or `suites` concept to BifrostSpec -- either as a field on Domain/Entity (which Suites consume this?) or as a property of Team (which Suites are represented on this domain team?).

---

### 2.2 Team Model Doesn't Capture Cross-Functional Composition

**ADR requirement:** "A domain team does not mean a single Suite team. These teams should ideally be cross-functional."

**Bifrost gap:** Team has `id`, `name`, `summary`, `email`, `slackChannel`, and `members` (with name and role). There's no way to model which Suites or functional areas are represented, or to enforce that a team is cross-functional.

**Impact:** Bifrost teams today map to engineering squads, not the cross-functional domain teams the ADR envisions.

**Recommendation:** Either extend TeamMember with a `suite` or `organization` field, or add a `representedSuites` field to Team.

---

### 2.3 No Analytical Data Product Schema

As noted in 1.4, the ADR requires analytical sinks. Bifrost has no modeling for analytical data products -- no warehouse table references, no refresh cadency, no dimension declarations. This is both a policy gap (the ADR doesn't define what a sink looks like) and an implementation gap (Bifrost can't model it even if the policy existed).

---

### 2.4 Channel vs. Topic Inconsistency Within Bifrost

BifrostSpec uses `Channel` (protocol-agnostic transport abstraction). Wayfinder -- in the same monorepo -- uses `sourceTopic` and `targetTopic`. This internal inconsistency will confuse teams onboarding to the ecosystem.

**Recommendation:** Align the terminology. If multi-protocol support is real, keep Channel but ensure Wayfinder references channels, not topics. If Kafka is the only protocol in practice, consider aligning to Topic everywhere.

---

## Part 3: Terminology Collisions

These are the terms that mean different things to different audiences. Each collision is ranked by risk of miscommunication.

### CRITICAL: "Entity"

| Context | Meaning |
|---------|---------|
| **ADR-65** | "Government Entity" = a customer organization using OpenGov |
| **Bifrost (bifrost-spec, Logos)** | A domain model type with identity, properties, commands, queries |
| **DDD** | An object with identity that persists through state changes |
| **Wayfinder** | `entityId` / `ogentitiesOfInterest` = government organization UUID |
| **Maestro** | `entity` table / `entityUuid` = government organization tenant |

This is the single most dangerous terminology clash in the ecosystem. When a developer says "entity," four different audiences hear four different things. Bifrost chose "Entity" for its DDD concept knowing the platform already used "Government Entity" for customer orgs. The ADR itself uses "Government Entity" as a named example of a shared Domain Object, then Bifrost stores domain model entities in `logos_entities`. Wayfinder filters events by `ogentitiesOfInterest` (government orgs) while Logos searches across entities (domain model types).

**Resolution options:**
1. Always qualify: "Government Entity" (org), "Domain Entity" (model) -- relies on discipline
2. Rename Bifrost's concept to **Domain Type** or **Resource** -- high migration cost but eliminates ambiguity
3. Rename the platform concept to **Organization** or **Tenant** -- breaking change to existing APIs but arguably more accurate

**Recommendation:** Option 1 as an immediate convention; evaluate option 3 as a longer-term migration since "Organization" is already used informally and is less overloaded than "Entity."

---

### HIGH: "Domain" -- Triple Overload

| Context | Meaning |
|---------|---------|
| **ADR-65** | Used loosely for business area ("domain team", "across a domain") |
| **Bifrost** | A bounded context container (PascalCase ID, e.g., `AccountsPayable`) containing Services, Entities, Value Objects |
| **OpenGov general** | A product area, sometimes synonymous with "Suite" |

**Example sentence that uses all three meanings:** "The Vendor domain object is owned by a domain team from the Procurement domain." Each "domain" means something different.

**Resolution:** The ADR should consistently use **Bounded Context** or **Domain** (capitalized) for the Bifrost concept, **Domain Object** for the shared data model, and **Domain Team** for the owning group. Never use bare "domain" without qualification.

---

### HIGH: "Domain Object" (ADR) vs. "Entity" (Bifrost)

| Context | Meaning |
|---------|---------|
| **ADR-65** | A shared, authoritative data model (Vendor, User, Chart of Accounts) |
| **Bifrost** | No direct equivalent. Closest: Entity + its Commands + Queries + Properties + Invariants |

The ADR's "Domain Object" is a higher-level concept than Bifrost's Entity. An ADR Domain Object implies a whole package: the data model, its APIs, its events, its authorization, its documentation, its analytical sink. Bifrost's Entity is just one piece of that package.

**Resolution:** Explicitly define the mapping: "A Shared Domain Object, as defined in ADR-65, is realized in Bifrost as a Domain containing one or more Entities, each with their Commands, Queries, Events, Properties, and Invariants."

---

### HIGH: "Service" -- Triple Overload

| Context | Meaning |
|---------|---------|
| **ADR-65** | The authoritative API wrapping a Domain Object ("User Service", "Entity Service") |
| **Bifrost** | A logical grouping of operations within a domain that produces/consumes events |
| **Infrastructure** | A deployed microservice (K8s Service, Docker container) |

The ADR says "all shared Domain Objects are wrapped in an authoritative service." Bifrost's Service is not the deployed thing -- it's a logical grouping. The deployed artifact is represented by `ServerEntry` (URL + environment).

**Resolution:** Use **Authoritative Service** in the ADR, and note that Bifrost models the logical operations as a `Service` and the deployment endpoints as `ServerEntry`.

---

### HIGH: "Suite" Not Modeled in Bifrost

ADR-65 references Suites extensively (Financials, Procurement, B&P, PLC, Utility Billing, Asset Management). Bifrost has no representation of Suite. This isn't a terminology *collision* -- it's a terminology *gap*. The ADR's governance model depends on Suite-level reasoning that the implementation platform cannot express.

---

### MEDIUM: "Team" vs. "Domain Team"

| Context | Meaning |
|---------|---------|
| **ADR-65** | Cross-functional owner group, explicitly not Suite-aligned |
| **Bifrost** | Spec-owning group with id, name, members |
| **Org chart** | Engineering squad |

These are compatible in theory but divergent in practice. Today's Bifrost teams are engineering squads, not the cross-functional domain teams the ADR envisions.

---

### MEDIUM: "Workflow"

| Context | Meaning |
|---------|---------|
| **ADR-65** | "Core workflows" = business processes (budgeting, procurement, permitting) |
| **Bifrost** | `workflowVisible` = flag for Maestro orchestration engine visibility |
| **Maestro** | Conductor workflow definition with steps, triggers, runtime instances |

When the ADR says domain objects support "core workflows," it means business processes. When Bifrost marks something `workflowVisible: true`, it means Maestro can orchestrate it. These are related but not identical.

---

### MEDIUM: "Channel" vs. "Topic"

Bifrost uses `Channel` (protocol-agnostic). Wayfinder (same monorepo) uses `Topic`. OpenGov teams say "topic" when they mean Kafka topics. Internal inconsistency that will confuse onboarding teams.

---

### LOW: "Aggregate Root"

Bifrost uses this DDD term. The ADR doesn't use DDD vocabulary at all. Not a collision, but a jargon gap for non-DDD-fluent teams who encounter the field in BifrostSpec.

---

## Terminology Alignment Matrix

| Term | ADR-65 Meaning | Bifrost Meaning | Platform Meaning | Risk |
|------|---------------|-----------------|------------------|------|
| Entity | Government org | Domain model type | Government org | **CRITICAL** |
| Domain | Business area (loose) | Bounded context (strict) | Product area | **HIGH** |
| Domain Object | Shared data model | (no equivalent) | Varies | **HIGH** |
| Service | Authoritative API | Logical operation group | Deployed microservice | **HIGH** |
| Suite | Product line | (not modeled) | Product line | **HIGH** |
| Team | Cross-functional domain team | Spec-owning group | Engineering squad | **MEDIUM** |
| Workflow | Business process | Maestro visibility flag | Conductor definition | **MEDIUM** |
| Channel / Topic | (not used) | Channel (Bifrost) / Topic (Wayfinder) | Kafka topic | **MEDIUM** |
| Aggregate Root | (not used) | DDD write boundary | (not used) | **LOW** |

---

## Recommendations Summary

### Immediate: ADR-65 v2 Updates

1. **Add a "Tooling" section referencing Bifrost** as the implementation platform, with a principle-to-implementation mapping table. This is the single highest-value change.
2. **Publish a glossary** resolving Entity, Domain, Service, and Suite terminology. The "Entity" collision is the most urgent.
3. **Define lifecycle stages** (Proposed / Draft / Alpha / Stable / Deprecated) with promotion criteria.
4. **Define a breaking change policy** -- what's breaking, deprecation timelines, migration obligations.
5. **Adopt context mapping vocabulary** for cross-domain integration patterns.

### Near-Term: Bifrost Implementation

6. **Add Suite modeling** to BifrostSpec -- consumer Suites on Domain/Entity, or represented Suites on Team.
7. **Extend Team** to capture cross-functional composition per the ADR's intent.
8. **Resolve Channel/Topic inconsistency** between BifrostSpec and Wayfinder.

### Follow-Up ADRs

9. **Analytical data product standard** -- define what a "sink" looks like, then extend BifrostSpec.
10. **MCP tool derivation policy** -- which Domain Object operations get AI-agent exposure.
11. **"Entity" naming migration** -- evaluate renaming the platform concept to Organization/Tenant.

---

*This analysis was produced by comparing ADR-65 (Oct 27, 2025) against the running Bifrost infrastructure at BifrostSpec v1.3.0. Bifrost was built as the implementation platform for ADR-65's principles. Components analyzed: bifrost-spec (schema), logos (catalog API), specgen (code extraction), wayfinder (event routing), maestro (workflow orchestration).*
