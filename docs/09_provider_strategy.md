# Фаза 9. Стратегия маршрутизаторов

## Краткое резюме

EcoLogist уже имеет рабочую границу провайдера: `MockRouteProvider` нужен для демо и
fallback-сценариев, `GraphHopperRouteProvider` уже возвращает реальные маршруты в общий
внутренний формат `RouteCandidate`, а остальная система работает со снимками `RouteOption`.

В фазе 9 не нужно сразу заменять GraphHopper. Правильная стратегия: сохранить текущую
интеграцию, формализовать capability-модель провайдеров и подготовить следующий эксперимент с
провайдером, который лучше отвечает российскому контексту. Для EcoLogist ближайший кандидат -
Yandex Maps API, потому что проект ориентирован на Россию, Москву и Московскую область, а
официальная документация Yandex описывает маршруты для легковых авто и грузовиков, учет пробок,
альтернативы, параметры грузовика и российские правила для грузового режима.

PTV, HERE и TomTom лучше рассматривать как последующие enterprise-кандидаты: они сильнее по
коммерческой логистике, truck routing, traffic/toll/eco-zone данным и расширенной аналитике, но
для России, лицензирования, стоимости и доступности отдельных данных нужен отдельный ручной
коммерческий due diligence.

## Официальные источники

- GraphHopper Directions API: https://docs.graphhopper.com/openapi/routing
- Yandex Retrieving Route Details API: https://yandex.com/maps-api/docs/router-api/index.html
- Yandex Router API examples/request/response:
  - https://yandex.com/maps-api/docs/router-api/examples.html
  - https://yandex.com/maps-api/docs/router-api/request.html
  - https://yandex.com/maps-api/docs/router-api/response.html
- HERE Routing API v8: https://docs.here.com/routing/docs/routing-intro
- HERE navigable countries: https://docs.here.com/routing/docs/navigable-countries
- HERE truck routing coverage: https://docs.here.com/routing/docs/truck-routing-coverage
- TomTom Routing API Calculate Route:
  https://developer.tomtom.com/routing-api/documentation/tomtom-maps/calculate-route
- PTV Developer Routing API: https://developer.myptv.com/en/documentation/routing-api

Все пункты по цене, юридическим условиям, приватности, российскому покрытию на уровне улиц,
платным дорогам, ограничениям грузовиков и account-gated функциям ниже считаются предварительными
и помечены как "требует ручной проверки", если официальная публичная документация не дает
достаточно точного ответа для внедрения.

## Сравнение провайдеров

| Критерий | GraphHopper | Yandex Maps API | HERE | TomTom | PTV |
| --- | --- | --- | --- | --- | --- |
| Россия / Москва / регионы | Базируется на OSM по умолчанию; качество по РФ зависит от данных OSM, требует ручной проверки. | Официально важен для РФ: Router API описывает грузовой режим с учетом ПДД РФ. Детальное коммерческое покрытие требует ручной проверки. | Россия указана в navigable countries; truck restrictions для России указаны как full motorway coverage, не полное покрытие. | Покрытие РФ и доступность traffic/truck/LEZ данных требует ручной проверки. | Покрытие РФ и локальная детализация требует ручной проверки. |
| Альтернативные маршруты | Есть `alternative_route` с настройками `max_paths`, `max_weight_factor`, `max_share_factor`. | Есть параметр `results` для альтернативных маршрутов. | В документации есть раздел альтернативных маршрутов. | `maxAlternatives` 0-5, сервис может вернуть меньше. | В документации есть Alternative Routes. |
| Traffic-aware duration | В открытой странице Routing API явной traffic-модели не найдено; требует ручной проверки. | `departure_time` и `traffic`; ответ содержит `traffic_type` (`realtime`, `forecast`, `disabled`). | В Routing API есть traffic in routing и traffic incidents in route spans. | `traffic=true`, `computeTravelTimeFor=all`, поля traffic/noTraffic/historic/live travel time. | Traffic modes, historical/live traffic and construction zones описаны в официальном guide. |
| Дорожные работы / инциденты | Не подтверждено публичной Routing API страницей; требует ручной проверки. | Не подтверждено для автомобильного Router API; требует ручной проверки. | Есть traffic incidents in route spans. | Traffic sections включают события; `simpleCategory` может быть `ROAD_WORK`, `ROAD_CLOSURE`, `JAM`, `OTHER`. | Guide упоминает live updates on traffic and construction zones; детали требуют ручной проверки. |
| Truck routing | Публичная страница описывает custom model и constraints, но готовый truck-профиль/РФ покрытие требует ручной проверки. | Есть `mode=truck`. | Есть truck routing. | Есть `travelMode=truck` и параметры транспортного средства. | Сильная сторона: truck routing для коммерческого транспорта. |
| Ограничения грузовика | Path details включают `max_weight`, `max_width`, `road_access`, `hazmat`; custom model может учитывать height/weight. РФ надежность требует ручной проверки. | Для `mode=truck` есть `weight`, `axle_weight`, `max_weight`, `height`, `width`, `length`, `payload`, `eco_class`, `has_trailer`; документация указывает учет отдельных знаков ПДД РФ. | Есть vehicle properties, truck restrictions и coverage-страница; в РФ ограничения указаны только для motorway/main roads. | Есть `vehicleWeight`, `vehicleAxleWeight`, `vehicleLength`, `vehicleWidth`, `vehicleHeight`, commercial/load/tunnel params. | Guide явно описывает учет размера, веса, speed profiles, access restrictions. |
| Платные дороги / стоимость | Есть path detail `toll` и упоминание toll information; расчет стоимости требует ручной проверки. | Есть `avoid_tolls`; расчет стоимости платных дорог не подтвержден. | Есть toll costs, но supported toll systems нужно уточнять у HERE account executive. | Есть `sectionType=tollRoad/toll/tollVignette` и типы оплаты; расчет стоимости требует ручной проверки. | Toll calculation и monetary costs описаны как ключевая функция; РФ/тарифы требуют ручной проверки. |
| Low-emission / eco zones | Не подтверждено; можно моделировать через custom areas позже, требует ручной проверки. | Есть `eco_class` для truck и российские знаки экологических ограничений в описании truck mode; практическое покрытие требует ручной проверки. | Routing zones/geofencing и route matching docs упоминают environmental zone rules; покрытие требует ручной проверки. | Есть `sectionType=lowEmissionZone`. | Есть Low-Emission Zones. |
| Route details / road class / surface / speed | Path details: `road_class`, `surface`, `max_speed`, `road_environment`, `toll`, `country`, `distance`, `time` и др. | Ответ разбит на legs/steps; есть length, duration, polyline, road quality. Детальность road class/speed требует ручной проверки. | Sections/spans, shape и дополнительные route properties; конкретный набор для РФ требует ручной проверки. | Sections: motorway, urban, unpaved, speedLimit, traffic, toll, lowEmissionZone и др. | Results, events, speeds, toll, emissions, violations, guided navigation; детали требуют ручной проверки. |
| Pricing / limits / quota | Официально credit-based; страница содержит daily credits, credits/min, requests/sec и стоимость routing credits. | Request limits: 50 rps и до 50 waypoint для driving/truck; цена/лицензия требует ручной проверки. | Pricing/limits/account model требует ручной проверки. | Pricing/limits/account model требует ручной проверки. | Pricing/limits/account model требует ручной проверки. |
| API key / auth complexity | API key query parameter. | API key issued in Developer Dashboard; key activation may take time. | Auth/account setup требует ручной проверки. | API key in request. | API key/account setup; детали требуют ручной проверки. |
| Документация | Хорошая OpenAPI-страница, удобно маппить JSON. | Хорошая HTTP-документация, есть request/response/examples. | Обширная enterprise-документация. | Подробная REST-документация. | Богатая logistics-документация, но часть деталей требует отдельного изучения. |
| Django-интеграция | Уже интегрирован; низкий риск. | Средняя сложность: HTTP-клиент, нормализация steps/polyline, traffic/truck params. | Средняя/высокая: больше объектов response/capabilities. | Средняя/высокая: много параметров/sections. | Высокая: enterprise-domain, toll/emissions/working-hours модели. |
| Юридические / privacy последствия | Terms/attribution/OSM/TomTom data требуют ручной проверки перед production. | Лицензия, персональные данные маршрутов и ограничения хранения требуют ручной проверки. | Enterprise terms/privacy/storage требуют ручной проверки. | Terms/privacy/storage требуют ручной проверки. | Enterprise terms/privacy/storage требуют ручной проверки. |
| Подходит для следующей фазы EcoLogist | Да, оставить как текущий real provider. | Лучший следующий эксперимент для РФ. | Позже, если нужен enterprise routing и truck coverage. | Позже, если нужен traffic/incidents/sections. | Позже, если нужен тяжелый truck/toll/emissions продукт. |

## Рекомендация для EcoLogist

1. Не заменять GraphHopper немедленно.
2. Сохранить `MockRouteProvider` как deterministic demo/fallback.
3. Следующим провайдером исследовать и прототипировать Yandex Router API, но только после
   утверждения отдельной фазы внедрения.
4. До реализации нового провайдера ввести только спецификацию capability-модели:
   - `supports_alternatives`;
   - `supports_traffic_duration`;
   - `supports_truck_mode`;
   - `supports_truck_dimensions`;
   - `supports_toll_avoidance`;
   - `supports_toll_cost`;
   - `supports_road_details`;
   - `supports_low_emission_zones`;
   - `supports_incidents`;
   - `supports_route_restriction_warnings`.
5. Любой новый провайдер обязан возвращать только внутренний `RouteCandidate`-подобный формат и
   отдельные нормализованные route facts. Raw provider response нельзя передавать в views,
   templates, reports, analytics или PDF.

## Что сохранить от GraphHopper

- Текущую границу `GraphHopperClient` -> `GraphHopperRouteProvider` -> `RouteCandidate`.
- Поведение: реальный провайдер возвращает 1..N доступных маршрутов без искусственного
  дублирования геометрии.
- `geometry_json` во внутреннем формате `[[lat, lon], ...]`.
- `RouteOption` как immutable snapshot для всех downstream-сценариев.
- Fallback к mock только как явно настроенный runtime-путь, не как способ скрывать ошибки данных.

## Что отложить

- Реальную интеграцию Yandex/HERE/TomTom/PTV.
- Изменение моделей и миграции.
- PostGIS, Celery/Redis, background jobs, production deploy.
- Строгую официальную методику EN 16258 / EMEP / EEA.
- Покупку/подключение коммерческих тарифов без отдельного юридического и privacy review.
- Полную оптимизацию многоточечных рейсов и fleet scheduling.

## Риски и открытые вопросы

- `.env.example` сейчас указывает `ROUTE_PROVIDER=graphhopper` и fallback disabled, хотя проектная
  договоренность говорит, что default routing - mock. Это существующая заметка, не исправление
  фазы 9.
- Для Yandex нужно вручную проверить коммерческие условия, хранение route/traffic данных,
  разрешенность использования в образовательном web-приложении и фактическое покрытие грузовых
  ограничений Москвы/МО.
- Для HERE нужно вручную проверить toll systems и российское покрытие truck restrictions за
  пределами motorway/main roads.
- Для TomTom нужно вручную проверить coverage РФ, доступность traffic/incidents/lowEmissionZone
  sections и toll cost именно для нужных регионов.
- Для PTV нужно вручную проверить доступность РФ, стоимость и применимость emissions/toll/truck
  функций для российского MVP.
- Для всех провайдеров нужно отдельно подтвердить SLA, rate limits, правила кэширования,
  хранение геометрии маршрутов и персональных данных.
