package com.souroldgeezer.architecture.layout.router;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.LayoutResultBuilder;
import com.souroldgeezer.architecture.layout.WarningFactory;
import com.souroldgeezer.architecture.layout.geometry.Point;
import com.souroldgeezer.architecture.layout.geometry.Port;
import com.souroldgeezer.architecture.layout.geometry.PortAssigner;
import com.souroldgeezer.architecture.layout.geometry.Rectangle;
import com.souroldgeezer.architecture.layout.geometry.Route;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

public final class RouteRepairBackend {
    private final LayoutResultBuilder builder = new LayoutResultBuilder();

    public ObjectNode repair(JsonNode request) {
        ArrayNode warnings = JsonFiles.MAPPER.createArrayNode();
        Map<String, Rectangle> geometry = LayoutResultBuilder.requestGeometry(request, 40, 40, 220, 160);
        List<JsonNode> requestEdges = new ArrayList<>();
        request.path("edges").forEach(requestEdges::add);
        requestEdges.sort(Comparator
                .comparing((JsonNode edge) -> -edge.path("priority").asInt(0))
                .thenComparing(edge -> edge.path("id").asText()));

        List<LayoutResultBuilder.EdgeLayout> edges = new ArrayList<>();
        int parallelOffset = 0;
        for (JsonNode edge : requestEdges) {
            Rectangle source = geometry.get(edge.path("source").asText());
            Rectangle target = geometry.get(edge.path("target").asText());
            if (source == null || target == null) {
                continue;
            }
            Port sourcePort = PortAssigner.portToward(source, target);
            Port targetPort = PortAssigner.portToward(target, source);
            Route route = edge.path("routeLocked").asBoolean(false) && hasExistingRoute(edge)
                    ? existingRoute(edge, sourcePort, targetPort)
                    : orthogonalRoute(sourcePort, targetPort, geometry, edge.path("id").asText(), parallelOffset);
            String status = "routed";
            if (edge.path("routeLocked").asBoolean(false)) {
                if (routeIntersectsUnrelated(route, geometry, edge.path("source").asText(), edge.path("target").asText())) {
                    status = "locked-invalid";
                    warnings.add(WarningFactory.warning(
                            "LAYOUT_LOCKED_ROUTE_INVALID",
                            "error",
                            "A locked route violates node-body avoidance and was not silently repaired.",
                            List.of(edge.path("id").asText())));
                } else {
                    status = "locked-preserved";
                }
            } else if (request.path("constraints").path("noRoutePossible").asBoolean(false)) {
                status = "failed";
                warnings.add(WarningFactory.warning(
                        "LAYOUT_NO_ROUTE",
                        "error",
                        "No deterministic orthogonal route was possible within configured limits.",
                        List.of(edge.path("id").asText())));
            } else if (routeIntersectsUnrelated(route, geometry, edge.path("source").asText(), edge.path("target").asText())) {
                route = detour(sourcePort, targetPort, geometry);
                if (routeIntersectsUnrelated(route, geometry, edge.path("source").asText(), edge.path("target").asText())) {
                    status = "warned";
                    warnings.add(WarningFactory.warning(
                            "LAYOUT_CONNECTOR_NODE_INTERSECTION",
                            "warning",
                            "Route repair could not avoid every unrelated node body.",
                            List.of(edge.path("id").asText())));
                }
            }
            edges.add(new LayoutResultBuilder.EdgeLayout(edge.path("id").asText(), edge.path("source").asText(), edge.path("target").asText(), sourcePort, targetPort, route.withoutRedundantPoints(), status));
            parallelOffset += 18;
        }
        return builder.build("route-repair", "1.0", "route-repair", request, geometry, edges, warnings);
    }

    private static boolean hasExistingRoute(JsonNode edge) {
        return edge.has("existingRoute") && edge.get("existingRoute").isArray() && edge.get("existingRoute").size() >= 2;
    }

    private static Route existingRoute(JsonNode edge, Port sourcePort, Port targetPort) {
        List<Point> points = new ArrayList<>();
        points.add(sourcePort.point());
        for (JsonNode point : edge.path("existingRoute")) {
            points.add(new Point(point.path("x").asInt(), point.path("y").asInt()));
        }
        points.add(targetPort.point());
        return new Route(points);
    }

    private static Route orthogonalRoute(Port sourcePort, Port targetPort, Map<String, Rectangle> geometry, String edgeId, int offset) {
        int midX = (sourcePort.point().x() + targetPort.point().x()) / 2 + offset;
        int midY = (sourcePort.point().y() + targetPort.point().y()) / 2 + offset;
        if (Math.abs(sourcePort.point().x() - targetPort.point().x()) > Math.abs(sourcePort.point().y() - targetPort.point().y())) {
            return new Route(List.of(sourcePort.point(), new Point(midX, sourcePort.point().y()), new Point(midX, targetPort.point().y()), targetPort.point()));
        }
        return new Route(List.of(sourcePort.point(), new Point(sourcePort.point().x(), midY), new Point(targetPort.point().x(), midY), targetPort.point()));
    }

    private static Route detour(Port sourcePort, Port targetPort, Map<String, Rectangle> geometry) {
        int laneY = geometry.values().stream().mapToInt(Rectangle::bottom).max().orElse(200) + 40;
        return new Route(List.of(
                sourcePort.point(),
                new Point(sourcePort.point().x(), laneY),
                new Point(targetPort.point().x(), laneY),
                targetPort.point()));
    }

    private static boolean routeIntersectsUnrelated(Route route, Map<String, Rectangle> geometry, String source, String target) {
        return route.segments().stream().anyMatch(segment -> geometry.entrySet().stream()
                .filter(entry -> !entry.getKey().equals(source) && !entry.getKey().equals(target))
                .anyMatch(entry -> segment.intersects(entry.getValue())));
    }
}
