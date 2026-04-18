# PubPlus — Decisions Still Worth Escalating

## Purpose

This file lists only decisions that appear meaningfully worth Database Manager approval before detailed table design starts.

## Assessment

The Stage 1–5 architecture appears sufficiently locked for schema planning to begin.

## No Material Blockers Identified

Based on the approved consolidation brief and stage summary pack:
- the core domain separations are already fixed
- the core authority chain is already fixed
- the moderation/publish model is already fixed
- the dynamic-content trust posture is already fixed
- the account-domain separation is already fixed

## Optional Clarifications Later, Not Blocking Now

These are implementation details that later workers may refine without reopening architecture:

### 1. Exact first-wave boundary for Stage 5
The architecture is locked, but later planning may choose whether specials and tap lists enter the same initial schema wave or follow immediately after core workflow and authority waves.

### 2. Exact depth of venue-scoped owner permissions in the first implementation pass
The need for explicit venue-scoped permissions is locked; only the initial granularity may need later practical scoping.

### 3. Exact minimum evidence metadata required per proposal family
The requirement for evidence/provenance is locked; the exact first-pass metadata depth can be determined during schema design.

## Recommendation

Proceed to detailed schema/entity planning without requesting further Database Manager approvals unless a later worker discovers a genuine conflict that cannot be resolved within the existing locked architecture.
