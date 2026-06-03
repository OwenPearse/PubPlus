# PubPlus — Non-Negotiable Rules for Schema Workers

## Purpose

This file is the concise rule sheet that later schema, SQL, migration, and RLS workers must obey.

## Core Rules

1. **No direct write path into published truth**
   - Published truth must only change through the formal publish workflow.

2. **Do not collapse public truth, workflow, private data, owner-private data, and commercial state**
   - These are separate domains and must remain separately modeled.

3. **Canonical venue identity anchors venue-linked state**
   - Venue-linked truth, workflow, saved references, specials, tap offerings, and managed-venue relationships must anchor to canonical venue identity.

4. **Source IDs do not define venue identity**
   - Canonical identity must be durable and source-agnostic.

5. **Submission is not truth**
   - User, owner, and source submissions are workflow inputs, not live truth objects.

6. **Workflow history is not live authority**
   - Claim history, review history, and prior decisions must not be treated as current access rights or current truth.

7. **Do not collapse consumer, owner, and admin into one logical role model**
   - Separate logical account domains are required.

8. **Auth identity is not the permission model**
   - Access must flow through explicit business membership, managed-venue relationships, and venue-scoped permissions where applicable.

9. **Do not shortcut claim, verification, management rights, and permissions**
   - These are distinct concepts and must remain distinct.

10. **Business entity is first-class**
    - Subscriptions and core commercial entitlements attach primarily to the business entity, not to individual owner users.

11. **Commercial/sponsored state is not truth**
    - Subscription status, boosts, and sponsorship must remain separate from truth/confidence/publishability.

12. **Structured discovery-driving claims must remain structured**
    - Filters, badges, counts, grouping, and ranking-safe claims cannot rely on free text alone.

13. **Unknown is not closed**
    - Missing or weak hours truth must not be converted into a closed-state claim.

14. **Weak/stale hours are not open-now**
    - Derived present-tense operational claims need stronger truth than raw or stale schedules.

15. **Exceptions override regular hours for affected periods**
    - Hours logic must support temporary overrides explicitly.

16. **Venue-open truth must not imply other availability truth**
    - Open status does not prove food, event, special, or access availability.

17. **Structured specials are separate from descriptive promo copy**
    - Discovery-safe specials require structured timing/offer state.

18. **Recurring offers and one-off promotions must remain distinct**
    - They have different timing and lifecycle patterns.

19. **Published, valid-current, discovery-eligible, and active-now are distinct**
    - Do not collapse these lifecycle layers for dynamic content.

20. **Tap offering state is separate from beverage product identity**
    - Venue-specific availability must not be merged into product reference/catalog identity.

21. **Rotating/guest/limited are offering traits, not proof of specific current-product availability**
    - Do not overclaim current tap truth.

22. **Saved venues are list-native**
    - Do not reduce saved state to a flat favorite flag model.

23. **Default location and notification settings are first-class private domains**
    - Do not hide them in an unstructured profile blob.

24. **Geography is high-risk and must remain clean**
    - One authoritative published map point and structured address hierarchy for live discovery; weak/disputed geography stays outside published truth.

25. **History must be preserved**
    - Rollback and correction flows must preserve lineage and auditability rather than destroy prior states.

## Implementation Posture

When schema convenience conflicts with domain clarity, choose domain clarity.
When a shortcut would blur truth, authority, or lifecycle boundaries, do not use it.
