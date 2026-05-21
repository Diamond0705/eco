# CHANGELOG

## Phase 15 - In-App Admin Panel CRUD

- Added in-application administrator pages for users, transport, locations, eco standards and calculation settings.
- Cleaned up the admin dashboard KPI grid and added admin-panel navigation.
- Kept Django Admin available for extended editing.
- Kept providers, calculation formulas, dependencies, migrations and old `RouteOption` snapshots unchanged.

## Phase 14 - Reports Explainability

- Added compact route calculation summaries to waybill PDFs from saved `RouteOption` snapshots.
- Added emissions intensity, average eco-rating and toll-route indicators to reports and analytics.
- Added vehicle Euro class to waybill and emissions report outputs.
- Kept formulas, providers, dependencies, migrations and old route snapshots unchanged.

## Phase 13 - Calculation Model v2.1

- Added route distance scope with `MAX_ROUTE_DISTANCE_KM=2000` for new calculations.
- Added Calculation Model v2.1 with intensity-based educational eco-rating and saved intensity details.
- Added deduplicated calculation warnings for traffic gaps, toll cost gaps and unknown speed data.
- Updated route comparison to show calculation details and deterministic best eco badge handling.
- Kept GraphHopper, MockRouteProvider, existing snapshots, reports, PDFs, analytics and migrations stable.

## Reference Data Expansion

- Added `seed_reference_expansion` command for additional route-testing reference data.
- Added legacy Euro I-II standards, expanded Russian locations and five demo transports.
- Kept routing logic, calculation formulas, models and migrations unchanged.

## Phase 12 - Calculation Model v2

- Added Calculation Model v2 for new route calculations from saved normalized route facts.
- Added route calculation metadata snapshots with model version and calculation details JSON.
- Added driver time tariff to eco calculation settings and v2 route cost.
- Kept old RouteOption snapshots, providers, reports, PDFs and analytics behavior stable.

## Phase 11 - GraphHopper Route Facts

- Added optional GraphHopper path details requests for normalized route facts.
- Enriched `RouteOption.route_facts_json` with road class, environment, surface, speed and toll summaries.
- Kept emission, cost, eco-rating, reports, PDFs and analytics behavior unchanged.

## Phase 8.1 - GraphHopper Alternatives

- Added standard and extended route calculation modes for GraphHopper alternatives.
- Tuned GraphHopper alternative route settings and capped real candidates at five.
- Added deduplication and best-effort strategy requests without fabricating route options.
- Added route comparison diagnostics for requested and found alternatives.

## Phase 8 - Real Routing Provider

- Added optional GraphHopper routing behind the existing provider boundary.
- Kept mock routing as the default and fallback provider.
- Updated route comparison to support a variable number of real alternatives.

## MVP Final Polish

- Added case-insensitive duplicate email validation to profile editing.
- Clarified implemented MVP documentation, mock routing status and Phase 8 provider boundary.
- Added a concise post-MVP security and deployment checklist.

## Phase 7 - Analytics And MVP Polish

- Added manager analytics at `/analytics/`.
- Enhanced admin dashboard with company-wide counters and delivered-trip totals.
- Replaced placeholder dashboard cards with real counters.
- Improved waybill and emissions PDF visual layout.
- Updated MVP documentation and final scope guards.

## Phase 6 - PDF Reports

- Added PDF waybill download for trips.
- Added manager emissions report page and PDF.
- Added ReportLab Cyrillic font helper.

## Phase 5 - Trips

- Added route approval.
- Added Trip and TripStatusEvent lifecycle from planned to delivered.
- Added trip list, trip detail and status actions.

## Phase 4 - Mock Routing

- Added RouteOption snapshots.
- Added deterministic mock route calculation.
- Added route comparison page with Leaflet map and route table.

## Phase 3 - Orders

- Added ShipmentOrder and OrderPoint.
- Added order list, create, detail, edit, cancel and status filter.

## Phase 2 - Fleet And Locations

- Added eco standards, transports, eco calculation settings and locations.
- Added demo seed command and admin registrations.

## Phase 1 - Accounts

- Added custom user flows, profile, login/logout, manager registration and role dashboards.

## Phase 0 - Skeleton

- Added Django monolith skeleton, custom user model, PostgreSQL settings, docs, tests and ruff setup.
