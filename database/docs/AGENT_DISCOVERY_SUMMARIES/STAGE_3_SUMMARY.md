Stage 3 — Auth, User Data & Permissions

Purpose
Define separate account domains, private user data, saved lists, preferences, and permission boundaries.

Locked outcomes

Anonymous users can browse and search.
Consumer, owner, and admin are separate logical account domains.
One account belongs to one logical domain only.
Consumer accounts are for the mobile app.
Owner accounts are for the separate web portal and require mandatory 2FA.
Admin accounts are internal only.
Saved venues are list-native from the start.
Default location is a first-class private preference.
Notification consent/settings are an explicit structured private domain.
Consumer-authenticated submissions feed workflow only; they do not mutate public truth.
Venue-linked private and submission records must attach to canonical venue identity.

Manager refinements / approvals

Shared auth infrastructure is allowed but not required.
The non-negotiable rule is separate logical domains, not one flexible multi-role account model.
Owner accounts are not upgrades from consumer accounts.
Same human or same email does not imply shared authority.
Consumer profile should stay minimal initially; enrichment can happen later.

Main guardrails

No blurred role model.
No auth identity as permission model.
No public/private data mixing.
No UI-only enforcement; backend/data-layer enforcement is required.
No admin read access to private consumer data by default unless later explicitly justified.