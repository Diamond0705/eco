def trip_route_display_name(trip):
    points = sorted(trip.order.points.all(), key=lambda point: point.sequence)
    if len(points) >= 2:
        return f"{points[0].location.name} — {points[-1].location.name}"
    return trip.route_option.name


def attach_route_display_names(trips):
    for trip in trips:
        trip.display_route_name = trip_route_display_name(trip)
