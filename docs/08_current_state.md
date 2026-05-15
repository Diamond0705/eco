# Current MVP State

EcoLogist MVP is complete through Phase 7.

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

## Demo Flow

1. Run `python manage.py seed_demo`.
2. Log in as `manager_demo` / `Manager12345!`.
3. Create an order, calculate routes and compare route options.
4. Approve a route, start the trip and deliver it.
5. Download the waybill PDF.
6. Review reports and analytics.

## Known Limits

- Routes are mock routes, not real road routing.
- GraphHopper is not implemented in the MVP.
- Traffic, roadworks, truck restrictions and GPS tracking are out of scope.
- Excel export and production deployment are not implemented.
- Environmental calculations are intentionally simplified for educational use.
