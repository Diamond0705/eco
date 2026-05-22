# Phase 16 Technical Roadmap

Phase 16 keeps the working MVP lightweight: it adds practical Excel export and records the
production-grade improvements that should be implemented later as separate phases.

## MinIO Media Storage And User Avatars

- Why useful: local media is enough for development, but production needs durable object storage
  for generated files and uploaded user assets.
- What it gives EcoLogist: stable storage for avatars, report archives and future document
  attachments without coupling app servers to local disks.
- Phase 17 status: generated PDF/XLSX documents can now be saved to a private document archive
  backed by local storage or MinIO/S3-compatible storage. Downloads still go through authorized
  Django views.
- Still future work: user avatars, company logo upload and broad media migration are intentionally
  not implemented yet. A future company logo upload can reuse the same private storage approach
  after image validation and UI rules are defined.
- Why not Phase 16: Excel exports were generated on demand and were not saved to media, database
  or object storage.
- Risks/complexity: access policies, bucket lifecycle rules, signed URLs, backup strategy and
  migration of existing media files.
- Suggested future phase: Phase 17 for generated document archive; later phase for avatars and
  company logo uploads.

## Production Deploy

- Why useful: the current setup is local/demo oriented and uses Django development tooling.
- What it gives EcoLogist: repeatable deployment with Dockerfile, Gunicorn, Nginx, static/media
  handling, secure settings and environment-based configuration.
- Why not Phase 16: deployment hardening should not be mixed with user-facing export work.
- Risks/complexity: secret management, HTTPS, proxy headers, static files, health checks,
  database backups and rollback procedures.
- Suggested future phase: Phase 18.

## REST API With Django REST Framework

- Why useful: an API would support integrations, mobile clients and future external dashboards.
- What it gives EcoLogist: stable machine-readable endpoints for orders, trips, route snapshots
  and reports.
- Why not Phase 16: the current product is a Django template monolith and this phase explicitly
  avoids introducing REST API or JWT scope.
- Risks/complexity: permission design, serializers, pagination, versioning, throttling and
  compatibility with existing role-based workflows.
- Suggested future phase: Phase 19.

## Celery And Redis For Background Reports

- Why useful: large exports and PDFs may become slow enough to move out of request/response flow.
- What it gives EcoLogist: queued report generation, retryable jobs and better user experience for
  long-running exports.
- Why not Phase 16: current demo-scale XLSX files are generated synchronously in memory.
- Risks/complexity: worker deployment, Redis operations, retry policies, job status UI and cleanup
  of generated artifacts.
- Suggested future phase: Phase 20.

## PostGIS And Geozones

- Why useful: ecological and protected-area checks need reliable spatial queries rather than
  ad-hoc coordinate logic.
- What it gives EcoLogist: geozones for protected areas, low-emission areas, corridor analysis and
  more accurate route risk annotations.
- Why not Phase 16: routing providers and calculation formulas stay unchanged in this phase.
- Risks/complexity: database extension setup, spatial indexes, geometry imports, admin tooling and
  new validation rules.
- Suggested future phase: Phase 21.

## Security Hardening And Personal Data Protection

- Why useful: EcoLogist stores user names, contacts, route history, trip events and operational
  data that require careful protection before public deployment.
- What it gives EcoLogist: clearer data handling, safer authentication/session settings, audit
  readiness and better operational confidence.
- Why not Phase 16: security hardening should be handled as a focused review after deployment
  architecture decisions are made.
- Risks/complexity: policy decisions, logging boundaries, retention rules, access audit, secure
  cookies, HTTPS, backup encryption and incident response.
- Suggested future phase: Phase 22.
