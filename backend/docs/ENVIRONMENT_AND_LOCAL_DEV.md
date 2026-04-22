# PubPlus Backend Environment and Local Development

## Purpose

Define the backend environment model, configuration principles, and local development assumptions for PubPlus so implementation can proceed consistently and safely from the beginning.

## Current stage

Foundation planning before backend implementation begins.

## Summary

The PubPlus backend should be designed for:

- Docker-friendly local development
- explicit environment configuration
- development-first implementation against the current Supabase project
- future-safe separation for local, dev, staging, and production environments later

The environment model should remain minimal, explicit, and operationally clear.

Do not rely on hidden configuration, ad hoc local machine setup, or vague assumptions about environment parity.

---

## Core principles

### 1. Configuration must be explicit

All important backend runtime behaviour should come from explicit environment configuration.

Avoid hidden local defaults for anything security-sensitive or integration-critical.

### 2. Local development must be easy to reproduce

A new developer or worker agent should be able to run the backend locally with a small, documented setup process.

The backend should assume Docker-based local development is welcome and preferred.

### 3. One current Supabase project does not mean one forever

Even though there is currently one Supabase project, backend documentation and configuration should assume eventual separation of:

- local
- development
- staging
- production

Do not hardcode a one-environment worldview into the repo structure or settings model.

### 4. Secrets must stay out of source control

Environment secrets must not be committed into the repository.

Use `.env`-style local configuration and documented variable expectations.

### 5. Django remains the application runtime boundary

Even when Supabase provides database/auth/storage infrastructure, Django still needs its own explicit runtime configuration for:

- app settings
- environment mode
- Supabase integration
- auth verification
- database connectivity
- internal/admin protections

---

## Expected environment tiers

The backend should be documented as if these tiers exist or will exist:

## Local

Developer machine and local Docker setup.

## Development

Shared development environment aligned to the active Supabase development project.

## Staging

Pre-production verification environment, added later.

## Production

Launch/live environment, added later.

### Current practical reality

Right now, implementation is working against the development Supabase project.

That is acceptable, but the backend should not be structured in a way that makes later staging/production separation awkward.

---

## Recommended repo shape

Suggested root structure:

```text
backend/
  docs/
  config/
  src/
  tests/
  .env.example
  Dockerfile
  docker-compose.yml


This may evolve, but backend documentation should assume a clear place for:

settings/config
application code
tests
environment example files
container/runtime setup
Environment variable principles

Environment variables should be:

clearly named
documented in .env.example
grouped by concern
minimal but complete
consistent across local/dev/staging/prod

Avoid vague names or one-off variables without documentation.

Configuration domains

The backend will likely need environment variables across these domains.

1. Django app configuration

Examples of likely needs:

environment name
debug mode
secret key
allowed hosts
CORS/CSRF settings where applicable

These should be explicit and environment-dependent.

2. Database connectivity

The backend needs explicit database connection configuration.

Because Supabase Postgres is the system of record, backend configuration should allow Django to connect safely to the appropriate Postgres instance.

Guidance:

use explicit database URL or equivalent structured settings
keep development and future environment separation straightforward
document SSL/connection expectations if required by Supabase
3. Supabase integration

The backend needs configuration for integrating with Supabase services, including:

Supabase project URL
JWT verification-related configuration
storage bucket or media configuration where needed

The exact set may depend on implementation strategy, but the integration layer should be explicit rather than magical.

4. Auth and JWT verification

Because the mobile app authenticates via Supabase Auth and Django verifies the resulting JWT, the backend needs environment/config support for token verification.

This configuration should support:

validation against the correct Supabase project
environment-correct auth verification behaviour
future environment separation later

Do not bury auth verification assumptions inside undocumented code.

5. Storage/media configuration

Because venue photos are delivered via Supabase Storage URLs, the backend may need configuration related to:

bucket names
public bucket assumptions
signed URL behaviour where applicable

The default posture is:

direct asset URLs from Supabase Storage
no Django media proxy by default
6. Internal/admin protection settings

Internal/admin tooling lives inside the same Django project.

The backend should therefore document any environment-linked assumptions relevant to:

internal auth enablement
admin host/origin controls if needed later
secure defaults across environments

The exact mechanism may evolve, but the environment model should leave room for it.

Local development goals

Local backend development should support:

running Django locally
connecting to the current development Supabase project
testing public API development
testing authenticated API behaviour
testing internal/admin API behaviour where possible
running with Docker-friendly commands and documented setup
Recommended local development posture
Preferred

Use Docker-friendly local development with the Django app running locally in a predictable containerized or reproducible environment.

Acceptable

Non-Docker local run commands may exist for convenience, but Docker-oriented setup should be documented as the baseline expectation.

Minimum local development documentation expectations

The backend repo should eventually document:

required environment variables
how to copy .env.example to .env
how to start the backend locally
how to run tests
how to call the health endpoint
how to verify auth-protected endpoints locally
how to point at the current Supabase project safely
.env.example guidance

The backend should include a .env.example file with placeholder variable names only.

It should not include real secrets.

The example file should be sufficient for a developer to understand what must be set.

Suggested sections in .env.example
Django/runtime
database
Supabase
auth verification
storage
optional local overrides

The exact variable names can be finalized during implementation.

Docker guidance

The backend should be planned with Docker support from the beginning.

Recommended files
backend/Dockerfile
backend/docker-compose.yml
Docker goals
reproducible local startup
predictable dependency/runtime environment
less machine-specific setup drift
easier worker-agent and developer onboarding

The exact compose stack can stay minimal in early phases if Supabase services are external.

Settings structure guidance

Django settings should remain explicit and maintainable.

A sensible pattern is to keep a structured settings/config area such as:

base settings
environment overrides if needed
environment variable loading layer

The exact file pattern is flexible, but the backend should avoid one giant opaque settings file if it becomes unwieldy.

CORS and client integration guidance

Because the frontend is a mobile app using Django as the public application API, CORS and allowed origin settings should be documented where relevant for development and web tooling.

Do not leave client integration behaviour to guesswork.

The exact mobile runtime behaviour may reduce some CORS concerns, but admin/internal web tooling and local development may still care.

Secrets handling rules
Required
keep secrets in environment files or secret managers, not source control
provide placeholder-only example files
document which variables are required vs optional
rotate or replace values if secrets are ever exposed
Avoid
hardcoding secrets in code
committing populated .env files
relying on undocumented machine-local configuration
Initial configuration checklist

When implementation begins, the backend should be able to answer clearly:

what variables are required to boot
how Django connects to Supabase Postgres
how Supabase JWTs are verified
how photo/storage URLs are resolved
how the health endpoint is run locally
how internal/admin routes are protected in development
how test execution uses environment configuration
Current recommended environment posture

For now, the backend should be built and documented as:

development-first
connected to the existing development Supabase project
ready for later environment separation
Docker-friendly
explicit in all settings

This is the correct balance between current reality and clean long-term structure.

Key decisions
local development should be Docker-friendly
environment configuration must be explicit
one current Supabase project is a temporary operational reality, not a permanent architectural assumption
Django runtime settings must be documented clearly
Supabase integration and JWT verification must be explicitly configurable
direct Supabase Storage URLs are the default media delivery posture
Assumptions
the backend repo structure is being created now
a .env.example file will be added during setup
implementation will initially target the current shared development Supabase project
staging and production environment separation will come later
Open questions
exact final environment variable names
exact Django settings file layout
exact Docker compose services needed in the first backend phase
whether any local-only mock/integration toggles are useful early on

These are implementation decisions, not blockers for environment planning.

Dependencies
backend/docs/BACKEND_ARCHITECTURE_OVERVIEW.md
backend/docs/AUTH_MODEL.md
backend repo initialization decisions
Supabase integration strategy
deployment/release planning later
Downstream use

This document should guide:

backend foundation workers
repo setup and Docker setup
environment file creation
local onboarding documentation
QA/release environment planning