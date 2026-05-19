# Фаза 9. Расчетная модель v2

## Текущая модель

Сейчас EcoLogist рассчитывает маршрут как образовательный прогноз. Провайдер возвращает
`RouteCandidate` с расстоянием, временем, геометрией и `fuel_multiplier`, после чего
`RouteCalculationService` сохраняет снимок `RouteOption`.

Текущая формула топлива:

```text
fuel_liters =
    distance_km
    * vehicle_fuel_consumption_l_per_100km / 100
    * load_factor
    * fuel_multiplier
```

Текущая формула стоимости:

```text
cost_rub =
    fuel_liters * fuel_price_rub_per_liter
    + distance_km * service_tariff_rub_per_km
```

Текущие выбросы:

- CO2 считается от литров дизеля.
- NOx/PM считаются через упрощенную работу двигателя `engine_work_kwh_per_km` и `EcoStandard`.
- `eco_rating` объединяет CO2, NOx и PM через веса из `EcoCalculationSettings`.

## Почему CO2 считается в кг/литр

Для дизельного топлива CO2 корректно считать через объем сожженного топлива: углерод в топливе
после сгорания превращается в CO2, поэтому коэффициент `diesel_co2_kg_per_liter` описывает массу
CO2 на один литр топлива. Это лучше, чем считать CO2 напрямую от расстояния, потому что расход
у разных транспортов, загрузок и маршрутов отличается.

Текущий коэффициент `2.69 кг/л` остается допустимым образовательным default. Его изменение должно
создавать новый `EcoCalculationSettings` и влиять только на новые расчеты.

## Ограничения текущей модели

- Для GraphHopper сейчас `fuel_multiplier = 1.00`, поэтому реальная геометрия влияет на расчет
  через расстояние, но не через дорожные условия.
- Время маршрута не влияет на расход топлива.
- Пробки, задержки, дорожные работы и инциденты не влияют на расход.
- Платные дороги не входят в стоимость.
- Не учитываются доли город/трасса, класс дороги, покрытие, средняя скорость по участкам,
  остановки, разгоны/торможения, eco zones и зоны с ограниченным доступом.
- Не учитываются protected areas и природоохранные территории.
- Модель не является строгой EN 16258 / EMEP / EEA методикой.

## Какие данные нужны для v2

Минимальный набор route facts, который стоит пытаться получить от провайдера или вычислить из
ответа:

- `distance_km` и `duration_minutes`;
- `base_duration_minutes` или `no_traffic_duration_minutes`, если провайдер умеет;
- `traffic_delay_minutes` или производное значение из real/historic/no-traffic duration;
- `road_class_shares`: доли `motorway`, `primary`, `secondary`, `local`, `urban`, `unpaved`;
- `average_speed_kmh` по маршруту и/или по segments;
- `toll_road_distance_km`, `has_tolls`, `toll_cost_rub`;
- `low_emission_zone_distance_km` или `low_emission_zone_entries`;
- `restricted_zone_entries` и `restriction_warnings`;
- `incident_count`, `roadworks_count`, `closed_road_warnings`;
- `protected_area_distance_km` или flags пересечения природоохранных зон;
- `route_details_json` как нормализованный, provider-independent JSON для будущих расчетов.

Провайдер должен отдавать факты, которые он реально поддерживает. Если данных нет, модель v2
должна использовать нейтральное значение, а не выдумывать точность.

## Что приходит от провайдера, а что считается локально

От провайдера:

- геометрия, расстояние, длительность;
- альтернативы;
- traffic-aware duration и traffic delay, если поддерживается;
- road/section/path details, если поддерживаются;
- toll/LEZ/restriction/incidents flags, если поддерживаются;
- toll cost только если провайдер официально возвращает стоимость для нужного региона.

Локально в EcoLogist:

- `load_factor` на основе веса груза и грузоподъемности;
- приведение provider facts к единому JSON;
- educational multipliers;
- расчет топлива, стоимости и оценок;
- сохранение снимка в `RouteOption`;
- агрегирование analytics/reports/PDF только из сохраненных snapshots.

## Формула топлива v2

Предлагаемая educational formula:

```text
base_fuel_liters =
    distance_km
    * vehicle_fuel_consumption_l_per_100km / 100

fuel_liters_v2 =
    base_fuel_liters
    * load_factor
    * provider_fuel_multiplier
    * traffic_factor
    * road_type_factor
    * stop_and_delay_factor
```

Где:

- `provider_fuel_multiplier` остается текущим `fuel_multiplier`; для GraphHopper без доп.
  формулы остается `1.00`.
- `traffic_factor`:
  - если есть `traffic_delay_minutes` и `no_traffic_duration_minutes`, использовать
    `1 + min(traffic_delay_minutes / no_traffic_duration_minutes, 1) * 0.15`;
  - если traffic данных нет, использовать `1.00`;
  - предел v2: `1.00..1.15`.
- `road_type_factor`:
  - базовое значение `1.00`;
  - городские/низкоскоростные участки повышают коэффициент;
  - автомагистрали без пробок могут слегка снижать коэффициент;
  - грунтовые/плохие дороги повышают коэффициент;
  - если road details нет, использовать `1.00`.
- `stop_and_delay_factor`:
  - в MVP v2 default `1.00`;
  - позже можно учитывать stop count, инциденты и ожидание.

Эти коэффициенты должны быть сохранены в snapshot или в нормализованном JSON, чтобы старые
маршруты не менялись после изменения настроек.

## Формула стоимости v2

Предлагаемая formula:

```text
cost_rub_v2 =
    fuel_liters_v2 * fuel_price_rub_per_liter
    + distance_km * service_tariff_rub_per_km
    + toll_cost_rub
    + driver_time_cost_rub
    + restriction_penalty_rub
```

Где:

- `toll_cost_rub`:
  - брать из провайдера только при официально подтвержденной поддержке стоимости для региона;
  - если есть только `has_tolls`, но нет суммы, использовать `0.00` и сохранять warning;
  - ручной тарифный справочник не вводить без отдельной фазы.
- `driver_time_cost_rub`:
  - `duration_hours * driver_hourly_cost_rub`;
  - в MVP v2 можно оставить disabled/default `0.00`, пока нет ставки в settings.
- `restriction_penalty_rub`:
  - не должен означать реальный штраф;
  - это внутренний penalty для сравнения маршрутов;
  - если провайдер сообщает violation/restriction warning, добавить configurable penalty;
  - если данных нет, использовать `0.00`.

## Eco rating v2

Текущий один `eco_rating` стоит разделить концептуально на две оценки:

```text
emissions_score =
    100 - normalized_weighted(CO2, NOx, PM)

environmental_risk_score =
    100 - normalized_weighted(
        low_emission_zone_penalty,
        restriction_penalty,
        protected_area_penalty,
        roadworks_or_incident_penalty
    )

eco_rating_v2 =
    emissions_score * 0.70
    + environmental_risk_score * 0.30
```

Правила:

- `emissions_score` зависит от топлива и экологического стандарта транспорта.
- `environmental_risk_score` зависит от route facts и предупреждений.
- Если у провайдера нет LEZ/restriction/protected-area данных, risk-score не должен
  искусственно ухудшаться: использовать нейтральное значение `100` и пометку о неполных данных.
- Protected areas лучше рассчитывать локально позже через отдельный справочник/геослой; PostGIS
  в фазе 9 не внедряется.

## Будущие поля и миграции

В фазе 9 миграции не создаются. Для будущей фазы внедрения могут понадобиться:

- `calculation_model_version`;
- `provider_route_id` или `external_route_reference`, если разрешено условиями провайдера;
- `route_details_json` для нормализованных facts;
- `traffic_delay_minutes`;
- `no_traffic_duration_minutes`;
- `road_type_factors_json` или агрегированные shares;
- `toll_cost_rub` и `has_tolls`;
- `driver_time_cost_rub`;
- `emissions_score`;
- `environmental_risk_score`;
- `restriction_warnings_json`;
- `calculation_breakdown_json` для объяснимости расчета.

Альтернатива: сначала добавить один `calculation_details_json`/`route_facts_json`, а отдельные
колонки выделять только после стабилизации модели и отчетов.

## Сохранение snapshot-подхода

Неизменные правила:

- Все расчеты продолжают использовать `EcoCalculationSettings.get_current()`.
- `RouteOption` хранит snapshot рассчитанных значений.
- Начиная с фазы 10, `RouteOption` также хранит нормализованный `route_facts_json` как
  подготовку к будущим провайдерам и расчетной модели v2.
- Старые `RouteOption` не пересчитываются автоматически при смене настроек.
- Trips, analytics, reports и PDF читают сохраненные значения из `RouteOption`.
- Raw provider response нельзя передавать в UI, PDF, reports или analytics.
- В UI показывать русские labels и объяснимые предупреждения о неполных данных.

## Поэтапный план внедрения

1. Фаза 9: только документы и спецификация.
2. Фаза 10: capability-модель провайдеров и нормализованный route facts contract без нового
   провайдера или с минимальным adapter-интерфейсом. Эта фаза сохраняет факты маршрута как JSON
   snapshot, но не меняет формулы расчета.
3. Фаза 11: экспериментальный Yandex provider для России с traffic/truck/alternatives, без
   замены GraphHopper.
4. Фаза 12: расчет v2 в shadow mode: сохранить старый `eco_rating`, рядом считать breakdown для
   новых маршрутов.
5. Фаза 13: расширить отчеты/PDF/analytics на новые snapshot-поля.
6. Позже: comparison spike по PTV/HERE/TomTom для enterprise truck/toll/eco-zone задач.
