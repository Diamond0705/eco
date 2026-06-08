import { divIcon } from "leaflet";
import { useEffect } from "react";
import { MapContainer, Marker, Polyline, TileLayer, useMap } from "react-leaflet";

const routeColors = ["#1f7a4d", "#2f74c0", "#c9891f", "#7e57c2", "#c14e70"];

function isPoint(point) {
  return Array.isArray(point) && point.length === 2 && point.every((value) => Number.isFinite(Number(value)));
}

function validGeometry(route) {
  return Array.isArray(route.geometry_json) ? route.geometry_json.filter(isPoint) : [];
}

function FitRouteBounds({ routes }) {
  const map = useMap();

  useEffect(() => {
    const points = routes.flatMap(validGeometry);
    if (points.length > 1) {
      map.fitBounds(points, { padding: [28, 28] });
    }
  }, [map, routes]);

  return null;
}

function markerIcon(label, className) {
  return divIcon({
    className: `route-marker ${className}`,
    html: `<span>${label}</span>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });
}

export default function RouteMap({ routes }) {
  const geometries = routes.map(validGeometry).filter((geometry) => geometry.length > 1);
  const firstGeometry = geometries[0] || [
    [55.7558, 37.6173],
    [55.7558, 37.6173]
  ];
  const startPoint = firstGeometry[0];
  const endPoint = firstGeometry[firstGeometry.length - 1];

  return (
    <div className="route-map">
      <MapContainer center={startPoint} zoom={9} scrollWheelZoom className="leaflet-map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitRouteBounds routes={routes} />
        {routes.map((route, index) => {
          const geometry = validGeometry(route);
          if (geometry.length < 2) {
            return null;
          }
          return (
            <Polyline
              key={route.id}
              pathOptions={{ color: routeColors[index % routeColors.length], weight: 5, opacity: 0.82 }}
              positions={geometry}
            />
          );
        })}
        <Marker icon={markerIcon("A", "route-marker-start")} position={startPoint} />
        <Marker icon={markerIcon("B", "route-marker-end")} position={endPoint} />
      </MapContainer>
    </div>
  );
}
