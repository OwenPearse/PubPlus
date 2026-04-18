-- PubPlus — Wave 10 / Migration 0027
-- Post-wave performance pass: FK join indexes, common workflow lookups, and selective partial indexes.
-- No architecture changes; complements existing indexes from earlier waves.

-- ---------------------------------------------------------------------------
-- Published discovery attributes: reverse lookups from allowed-value rows
-- ---------------------------------------------------------------------------
create index if not exists idx_venue_published_attribute_value_allowed_value_id on public.venue_published_attribute_value (allowed_value_id)
where
  allowed_value_id is not null;

comment on index public.idx_venue_published_attribute_value_allowed_value_id is
'FK support: join/filter published rows from a discrete allowed_value_id (catalog → venues).';

-- ---------------------------------------------------------------------------
-- Staging attributes: definition + discrete value joins for review/publish paths
-- ---------------------------------------------------------------------------
create index if not exists idx_venue_proposal_staging_attribute_definition_id on public.venue_proposal_staging_attribute (attribute_definition_id);

create index if not exists idx_venue_proposal_staging_attribute_allowed_value_id on public.venue_proposal_staging_attribute (allowed_value_id)
where
  allowed_value_id is not null;

-- ---------------------------------------------------------------------------
-- Proposal lineage: supersession chain and publish-event joins
-- ---------------------------------------------------------------------------
create index if not exists idx_venue_change_proposal_superseded_by on public.venue_change_proposal (superseded_by_proposal_id)
where
  superseded_by_proposal_id is not null;

create index if not exists idx_venue_publish_event_venue_change_proposal on public.venue_publish_event (venue_change_proposal_id)
where
  venue_change_proposal_id is not null;

create index if not exists idx_venue_publish_event_proposal_review on public.venue_publish_event (proposal_review_id)
where
  proposal_review_id is not null;

-- ---------------------------------------------------------------------------
-- Authority chain: verification snapshot keyed by optional claim context
-- ---------------------------------------------------------------------------
create index if not exists idx_venue_verification_state_context_claim on public.venue_verification_state (context_venue_claim_request_id)
where
  context_venue_claim_request_id is not null;

-- ---------------------------------------------------------------------------
-- Authority events: filter by linked entities (venue already indexed separately)
-- ---------------------------------------------------------------------------
create index if not exists idx_venue_authority_event_business_id on public.venue_authority_event (business_id)
where
  business_id is not null;

create index if not exists idx_venue_authority_event_owner_account_id on public.venue_authority_event (owner_account_id)
where
  owner_account_id is not null;

create index if not exists idx_venue_authority_event_venue_claim_request_id on public.venue_authority_event (venue_claim_request_id)
where
  venue_claim_request_id is not null;

create index if not exists idx_venue_authority_event_bvm_relationship_id on public.venue_authority_event (business_venue_management_relationship_id)
where
  business_venue_management_relationship_id is not null;

-- ---------------------------------------------------------------------------
-- Audit log: actor-scoped reads (entity composite index remains primary)
-- ---------------------------------------------------------------------------
create index if not exists idx_audit_event_actor_consumer on public.audit_event (actor_consumer_account_id)
where
  actor_consumer_account_id is not null;

create index if not exists idx_audit_event_actor_owner on public.audit_event (actor_owner_account_id)
where
  actor_owner_account_id is not null;

create index if not exists idx_audit_event_actor_admin on public.audit_event (actor_admin_account_id)
where
  actor_admin_account_id is not null;

-- ---------------------------------------------------------------------------
-- Dynamic published catalogs: “active” rows per venue (common read path)
-- ---------------------------------------------------------------------------
create index if not exists idx_venue_published_structured_special_venue_active_catalog on public.venue_published_structured_special (venue_id)
where
  catalog_record_status = 'active';

create index if not exists idx_venue_published_tap_offering_venue_active_catalog on public.venue_published_tap_offering (venue_id)
where
  catalog_record_status = 'active';
