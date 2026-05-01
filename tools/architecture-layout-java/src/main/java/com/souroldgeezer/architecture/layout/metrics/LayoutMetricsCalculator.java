package com.souroldgeezer.architecture.layout.metrics;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.geometry.Point;
import com.souroldgeezer.architecture.layout.geometry.Rectangle;
import com.souroldgeezer.architecture.layout.geometry.Route;
import com.souroldgeezer.architecture.layout.geometry.Segment;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public final class LayoutMetricsCalculator {
    public LayoutMetrics compute(JsonNode request, JsonNode result) {
        Map<String, Rectangle> nodes = nodeGeometry(result);
        int overlaps = countOverlaps(nodes);
        List<EdgeRoute> routes = edgeRoutes(result);
        int connectorNodeIntersections = countConnectorNodeIntersections(nodes, routes);
        int crossings = countCrossings(routes);
        int maxBends = 0;
        int totalBends = 0;
        for (EdgeRoute route : routes) {
            int bends = route.route().bendCount();
            maxBends = Math.max(maxBends, bends);
            totalBends += bends;
        }
        int canvasWidth = nodes.values().stream().mapToInt(Rectangle::right).max().orElse(0);
        int canvasHeight = nodes.values().stream().mapToInt(Rectangle::bottom).max().orElse(0);
        Displacement displacement = displacement(request, nodes);
        return new LayoutMetrics(
                overlaps,
                connectorNodeIntersections,
                crossings,
                maxBends,
                routes.isEmpty() ? 0.0 : (double) totalBends / routes.size(),
                canvasWidth,
                canvasHeight,
                displacement.locked(),
                displacement.movable());
    }

    public ObjectNode toJson(LayoutMetrics metrics) {
        ObjectNode node = JsonFiles.MAPPER.createObjectNode();
        node.put("nodeOverlaps", metrics.nodeOverlaps());
        node.put("connectorNodeIntersections", metrics.connectorNodeIntersections());
        node.put("connectorCrossings", metrics.connectorCrossings());
        node.put("maxBends", metrics.maxBends());
        node.put("averageBends", metrics.averageBends());
        node.put("canvasWidth", metrics.canvasWidth());
        node.put("canvasHeight", metrics.canvasHeight());
        node.put("lockedNodeDisplacement", metrics.lockedNodeDisplacement());
        node.put("movableNodeDisplacement", metrics.movableNodeDisplacement());
        return node;
    }

    public Map<String, Rectangle> nodeGeometry(JsonNode result) {
        Map<String, Rectangle> nodes = new LinkedHashMap<>();
        for (JsonNode node : result.path("nodeGeometry")) {
            nodes.put(node.path("id").asText(), new Rectangle(
                    node.path("x").asInt(),
                    node.path("y").asInt(),
                    node.path("w").asInt(),
                    node.path("h").asInt()));
        }
        return nodes;
    }

    public List<EdgeRoute> edgeRoutes(JsonNode result) {
        Map<String, Rectangle> nodes = nodeGeometry(result);
        List<EdgeRoute> routes = new ArrayList<>();
        for (JsonNode edge : result.path("edges")) {
            Rectangle source = nodes.get(edge.path("source").asText());
            Rectangle target = nodes.get(edge.path("target").asText());
            if (source == null || target == null) {
                continue;
            }
            List<Point> points = new ArrayList<>();
            points.add(portPoint(source, edge.path("sourcePort").asText()));
            for (JsonNode bendpoint : edge.path("bendpoints")) {
                points.add(new Point(bendpoint.path("x").asInt(), bendpoint.path("y").asInt()));
            }
            points.add(portPoint(target, edge.path("targetPort").asText()));
            routes.add(new EdgeRoute(edge.path("id").asText(), edge.path("source").asText(), edge.path("target").asText(), new Route(points)));
        }
        return routes;
    }

    public static Point portPoint(Rectangle rectangle, String port) {
        return switch (port) {
            case "north" -> new Point(rectangle.center().x(), rectangle.top());
            case "south" -> new Point(rectangle.center().x(), rectangle.bottom());
            case "east" -> new Point(rectangle.right(), rectangle.center().y());
            case "west" -> new Point(rectangle.left(), rectangle.center().y());
            default -> rectangle.center();
        };
    }

    private static int countOverlaps(Map<String, Rectangle> nodes) {
        List<Rectangle> rectangles = new ArrayList<>(nodes.values());
        int overlaps = 0;
        for (int i = 0; i < rectangles.size(); i++) {
            for (int j = i + 1; j < rectangles.size(); j++) {
                if (rectangles.get(i).intersects(rectangles.get(j))) {
                    overlaps++;
                }
            }
        }
        return overlaps;
    }

    private static int countConnectorNodeIntersections(Map<String, Rectangle> nodes, List<EdgeRoute> routes) {
        int intersections = 0;
        for (EdgeRoute edgeRoute : routes) {
            for (Segment segment : edgeRoute.route().segments()) {
                for (Map.Entry<String, Rectangle> node : nodes.entrySet()) {
                    if (node.getKey().equals(edgeRoute.source()) || node.getKey().equals(edgeRoute.target())) {
                        continue;
                    }
                    if (segment.intersects(node.getValue())) {
                        intersections++;
                    }
                }
            }
        }
        return intersections;
    }

    private static int countCrossings(List<EdgeRoute> routes) {
        int crossings = 0;
        for (int i = 0; i < routes.size(); i++) {
            for (int j = i + 1; j < routes.size(); j++) {
                EdgeRoute a = routes.get(i);
                EdgeRoute b = routes.get(j);
                if (a.source().equals(b.source()) || a.source().equals(b.target())
                        || a.target().equals(b.source()) || a.target().equals(b.target())) {
                    continue;
                }
                for (Segment first : a.route().segments()) {
                    for (Segment second : b.route().segments()) {
                        if (first.crosses(second)) {
                            crossings++;
                        }
                    }
                }
            }
        }
        return crossings;
    }

    private static Displacement displacement(JsonNode request, Map<String, Rectangle> current) {
        int locked = 0;
        int movable = 0;
        for (JsonNode node : request.path("nodes")) {
            if (!node.has("x") || !node.has("y")) {
                continue;
            }
            Rectangle now = current.get(node.path("id").asText());
            if (now == null) {
                continue;
            }
            int distance = Math.abs(now.x() - node.path("x").asInt()) + Math.abs(now.y() - node.path("y").asInt());
            if (node.path("locked").asBoolean(false)) {
                locked += distance;
            } else {
                movable += distance;
            }
        }
        return new Displacement(locked, movable);
    }

    public static ObjectNode point(Point point) {
        ObjectNode node = JsonFiles.MAPPER.createObjectNode();
        node.put("x", point.x());
        node.put("y", point.y());
        return node;
    }

    public static ArrayNode bendpoints(Route route) {
        ArrayNode bendpoints = JsonFiles.MAPPER.createArrayNode();
        List<Point> points = route.points();
        for (int i = 1; i < points.size() - 1; i++) {
            bendpoints.add(point(points.get(i)));
        }
        return bendpoints;
    }

    public Optional<String> firstConnectorNodeIntersection(JsonNode result) {
        Map<String, Rectangle> nodes = nodeGeometry(result);
        for (EdgeRoute edgeRoute : edgeRoutes(result)) {
            for (Segment segment : edgeRoute.route().segments()) {
                for (Map.Entry<String, Rectangle> node : nodes.entrySet()) {
                    if (!node.getKey().equals(edgeRoute.source()) && !node.getKey().equals(edgeRoute.target()) && segment.intersects(node.getValue())) {
                        return Optional.of(edgeRoute.id());
                    }
                }
            }
        }
        return Optional.empty();
    }

    public record EdgeRoute(String id, String source, String target, Route route) {
    }

    private record Displacement(int locked, int movable) {
    }
}
