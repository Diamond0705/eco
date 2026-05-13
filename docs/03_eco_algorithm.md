# Упрощенный экологический расчет

В MVP используется упрощенная расчетная модель для дизельных грузовиков. Строгая EN 16258 / EMEP / EEA методика не реализуется.

## Seed-значения

- `diesel_co2_kg_per_liter = 2.69`
- Euro III: NOx `5.00 g/kWh`, PM `160 mg/kWh`
- Euro IV: NOx `3.50 g/kWh`, PM `30 mg/kWh`
- Euro V: NOx `2.00 g/kWh`, PM `30 mg/kWh`
- Euro VI: NOx `0.46 g/kWh`, PM `10 mg/kWh`
- `engine_work_kwh_per_km = 1.20`
- `fuel_price_rub_per_liter = 78.15`
- `service_tariff_rub_per_km = 175.00`
- `full_load_fuel_increase_percent = 20.00`
- `co2_weight / nox_weight / pm_weight = 0.50 / 0.30 / 0.20`
- `co2_critical_kg / nox_critical_g / pm_critical_g = 100 / 300 / 10`

## Правило настроек

`EcoCalculationSettings` хранит историю настроек, но активной может быть только одна запись.

Все новые расчеты должны использовать `EcoCalculationSettings.get_current()`.

Старые рассчитанные `RouteOption` не пересчитываются автоматически при изменении настроек.
