import Alert from "../ui/Alert.jsx";
import Badge from "../ui/Badge.jsx";
import Button from "../ui/Button.jsx";
import Card from "../ui/Card.jsx";
import RouteCalculationDetails from "./RouteCalculationDetails.jsx";
import RouteMetricGrid from "./RouteMetricGrid.jsx";

function badgesForRoute(route) {
  const badges = [...(route.badges || [])];
  if (route.has_unpriced_tolls && !badges.includes("Платная дорога")) {
    badges.push("Платная дорога");
  }
  return badges;
}

export default function RouteOptionCard({ route, isApproving, onApprove }) {
  return (
    <Card className={`route-option-card ${route.is_selected ? "selected-route" : ""}`}>
      <div className="route-option-heading">
        <div>
          <p className="eyebrow">{route.provider_display || route.provider}</p>
          <h3>{route.display_name || route.name}</h3>
        </div>
        {route.is_selected ? <Badge tone="success">Утвержден</Badge> : null}
      </div>

      <div className="route-badges">
        {badgesForRoute(route).map((badge) => (
          <Badge key={badge} tone={badge === "Платная дорога" ? "danger" : "info"}>
            {badge}
          </Badge>
        ))}
      </div>

      <RouteMetricGrid route={route} />

      {route.warnings?.length ? (
        <Alert tone="info">
          {route.warnings.map((warning) => (
            <span className="warning-line" key={warning}>
              {warning}
            </span>
          ))}
        </Alert>
      ) : null}

      <RouteCalculationDetails details={route.calculation_details} />

      <div className="form-actions">
        <Button disabled={isApproving || route.is_selected} onClick={() => onApprove(route)}>
          {route.is_selected ? "Маршрут выбран" : isApproving ? "Утверждаем..." : "Утвердить"}
        </Button>
      </div>
    </Card>
  );
}
