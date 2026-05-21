# Current MVP State

EcoLogist MVP is complete through Phase 8.1. Phase 9 is a documentation/specification phase and does not change application behavior.
Фаза 12 включает расчетную модель v2 для новых маршрутов: она использует сохраненные
`route_facts_json`, сохраняет версию модели и детали расчета, но не пересчитывает старые
`RouteOption` и не меняет поведение отчетов, PDF, аналитики или рейсов.
Фаза 10 добавляет внутренний контракт capabilities/facts и JSON-снимок фактов маршрута; она не
меняет пользовательский сценарий, формулы расчета, отчеты, PDF или аналитику.
Фаза 11 обогащает `route_facts_json` нормализованными дорожными деталями GraphHopper; формулы,
отчеты, PDF, аналитика и пользовательский сценарий остаются прежними.

This file is the current implementation snapshot. Docs `00` through `07` are historical and
planning notes for earlier phases, so they may describe target behavior or old phase boundaries.
Фаза 9 является исследовательской и спецификационной: она описывает стратегию провайдеров и
расчетную модель v2, но сама по себе не меняет поведение приложения.

## Implemented

- Russian-only Django monolith with custom `accounts.User`.
- Manager registration, login/logout, profile and role-based access.
- Fleet, eco standards, calculation settings singleton and demo locations.
- Shipment orders with ordered points, edit/cancel rules and status filtering.
- Deterministic mock route calculation with Leaflet route comparison.
- Route approval that creates one Trip per order.
- Trip lifecycle: planned, in progress, delivered.
- PDF waybill and emissions PDF through ReportLab.
- Manager emissions report and analytics.
- Admin company dashboard with real counters.

## Routing And Snapshots

- Default routing uses deterministic `MockRouteProvider` data.
- Phase 8 adds optional `GraphHopperRouteProvider` real routing.
- `MockRouteProvider` returns three demo routes.
- `GraphHopperRouteProvider` returns the available real alternatives from the provider and does
  not duplicate routes to force three options.
- Standard GraphHopper calculation requests up to 3 real alternatives.
- Extended GraphHopper calculation requests up to 5 real alternatives and may run limited
  best-effort strategy requests.
- `GraphHopperRouteProvider` returns the same internal `RouteCandidate` format.
- Views, templates, trips, reports and analytics must not consume raw external routing responses.
- Analytics and reports use saved `RouteOption` snapshots, including distance, duration, fuel,
  cost, emissions, eco-rating, geometry and calculation settings reference.
- The best eco route is determined after calculation from saved route facts, not assigned before
  the environmental calculation.
- Existing `RouteOption` values must not be recalculated automatically when settings change.
- GraphHopper route facts may include normalized road details from path details, but raw provider
  responses are still not stored or exposed.
- New calculations use Calculation Model v2 by default and store `calculation_model_version` and
  `calculation_details_json` as part of the route snapshot.
- Phase 13 updates new calculations to Calculation Model v2.1. Routes above
  `MAX_ROUTE_DISTANCE_KM=2000` are filtered or rejected before replacing old options.
- v2.1 stores emissions intensity fields in `calculation_details_json` and uses them for an
  educational comparative eco-rating while keeping absolute CO2/NOx/PM snapshot values unchanged.
- Route comparison shows compact Russian calculation details, deduplicated warnings and one
  deterministic best eco route badge.
- Phase 14 extends waybill PDFs, emissions reports and analytics with compact explainability
  metrics from saved `RouteOption` snapshots and `calculation_details_json`.
- Reports now show average CO2 intensity, average eco-rating, toll-route counts and vehicle Euro
  class where relevant, without recalculating old route options.
- Phase 15 expands the in-application administrator panel with CRUD pages for common reference
  data and calculation settings while keeping Django Admin available for extended editing.
- Existing saved `RouteOption` rows remain historical snapshots and are not recalculated
  automatically.

## Demo Flow

1. Run `python manage.py seed_demo`.
2. Log in as `manager_demo` / `Manager12345!`.
3. Create an order, calculate routes and compare route options.
4. Approve a route, start the trip and deliver it.
5. Download the waybill PDF.
6. Review reports and analytics.

## Known Limits

- Mock routes remain the default for local demos.
- GraphHopper is optional and requires an API key.
- Traffic, roadworks, truck restrictions and GPS tracking are out of scope.
- Excel export and production deployment are not implemented.
- Environmental calculations are intentionally simplified for educational use.

## Before Public Deployment

- Set `DEBUG=False`.
- Read `SECRET_KEY` from the environment only.
- Configure `ALLOWED_HOSTS`.
- Review HTTPS, secure cookies and HSTS settings.
- Keep `.env` out of git.
- Keep the GraphHopper API key out of git when Phase 8 is implemented.
- Protect media and PDF access behind authorization.
- Configure PostgreSQL backups.
- Consider the personal data policy for names, email, phone, route history and trip history.
- Review tile, CDN and provider privacy before using real routes.
