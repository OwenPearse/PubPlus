# Stage 8 — Photos & media (implemented)

## Purpose

Let verified owners upload, view, reorder, replace/deactivate, and select venue photos (profile + gallery) through a permission-checked Supabase Storage flow.

## Current stage

**Implemented (Stage 8).** Owner hub Photos row is active when `venue_published_media` exists. Upload uses backend-issued signed URLs; metadata commits write published rows + audit events.

## Decisions

| Topic | Decision |
|-------|----------|
| Storage bucket | `venue-media` (public read for listing URLs) |
| Object path | `venues/{venue_id}/profile/{media_id}.{ext}` or `.../gallery/...` |
| Metadata table | `venue_published_media` |
| Upload gate | `owner_venue_media_upload_intent` — backend issues path + signed URL |
| Profile cardinality | **One active profile image** — new profile upload retires previous |
| Admin review | **None** for normal venue photos in MVP |
| Public URL | `{SUPABASE_URL}/storage/v1/object/public/venue-media/{path}` |
| Out of scope | Menus, event posters, videos, cropping, bulk upload, moderation queue |

## Storage setup

Migration `0034_venue_published_media.sql`:

- Creates `venue-media` bucket when `storage` schema exists (public, 5MB, jpeg/png/webp)
- Client writes are **not** open — owners upload via signed URL from backend
- `SUPABASE_SERVICE_ROLE_KEY` required on backend for signed upload + existence checks

Env:

```text
SUPABASE_STORAGE_BUCKET_VENUE_MEDIA=venue-media
SUPABASE_SERVICE_ROLE_KEY=<server-side only>
```

## Upload flow

1. Owner selects image (client validates type/size)
2. `POST .../media/upload-intent` → `media_id`, `storage_path`, `signed_upload_url`
3. Frontend `PUT` file to `signed_upload_url`
4. `POST .../media` → metadata row + audit (`owner_direct_edit`, `field_family=media`)
5. Listing reads active rows via `published_venue_read` → `venue_media.resolve_hero_and_gallery`

## Acceptance

- [x] `venue-media` bucket strategy documented/implemented
- [x] Metadata in Postgres (`venue_published_media`)
- [x] Owner hub Photos row active when schema present
- [x] `/owner/venues/:venueId/photos` page
- [x] Profile + gallery upload through permission-checked flow
- [x] View / deactivate / patch metadata
- [x] Audit rows on metadata changes
- [x] Capability guard returns 403 without `manage_published_venue_operations`

## Manual validation

1. Apply migration `0034` (or full Supabase migrate)
2. Confirm `venue-media` bucket exists
3. Set `SUPABASE_SERVICE_ROLE_KEY` on backend
4. Sign in as approved owner with direct-edit capability
5. Upload profile + gallery images; refresh persists
6. Remove image; confirm soft retire (`catalog_record_status=retired`)
7. Confirm `audit_event` rows with `field_family=media`

## Known gaps / future

- Physical Storage object deletion on retire (deferred)
- Image moderation queue
- Menu PDF / event poster media types
- Drag-and-drop reorder UI
