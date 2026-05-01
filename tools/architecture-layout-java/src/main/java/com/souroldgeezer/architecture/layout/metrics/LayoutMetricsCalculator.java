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
        ParentIndex parents = ParentIndex.from(request);
        OverlapStats overlaps = classifyOverlaps(nodes, parents);
        List<EdgeRoute> routes = edgeRoutes(result);
        ConnectorStats connectorStats = classifyConnectorIntersections(nodes, routes, parents);
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
                overlaps.defects(),
                overlaps.sameParent(),
                overlaps.parentChildContainments(),
                overlaps.childOutsideParentBounds(),
                connectorStats.unrelatedIntersections(),
                connectorStats.unrelatedIntersections(),
                connectorStats.containerBoundaryCrossings(),
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
        node.put("sameParentNodeOverlaps", metrics.sameParentNodeOverlaps());
        node.put("parentChildContainments", metrics.parentChildContainments());
        node.put("childOutsideParentBounds", metrics.childOutsideParentBounds());
        node.put("connectorNodeIntersections", metrics.connectorNodeIntersections());
        node.put("connectorUnrelatedNodeIntersections", metrics.connectorUnrelatedNodeIntersections());
        node.put("connectorContainerBoundaryCrossings", metrics.connectorContainerBoundaryCrossings());
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

    private static ConnectorStats classifyConnectorIntersections(Map<String, Rectangle> nodes, List<EdgeRoute> routes, ParentIndex parents) {
        int unrelatedIntersections = 0;
        int containerBoundaryCrossings = 0;
        for (EdgeRoute edgeRoute : routes) {
            for (Segment segment : edgeRoute.route().segments()) {
                for (Map.Entry<String, Rectangle> node : nodes.entrySet()) {
                    String relationship = parents.relationshipToEndpoint(edgeRoute.source(), edgeRoute.target(), node.getKey());
                    if ("source".equals(relationship) || "target".equals(relationship)) {
                        continue;
                    }
                    if (segment.intersects(node.getValue())) {
                        if ("ancestor".equals(relationship) || "descendant".equals(relationship)) {
                            containerBoundaryCrossings++;
                        } else {
                            unrelatedIntersections++;
                        }
                    }
                }
            }
        }
        return new ConnectorStats(unrelatedIntersections, containerBoundaryCrossings);
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

    public Optional<ConnectorNodeIntersection> firstConnectorNodeIntersection(JsonNode request, JsonNode result) {
        return firstConnectorIntersection(request, result, "unrelated");
    }

    public Optional<ConnectorNodeIntersection> firstConnectorContainerBoundaryCrossing(JsonNode request, JsonNode result) {
        Optional<ConnectorNodeIntersection> ancestor = firstConnectorIntersection(request, result, "ancestor");
        return ancestor.isPresent() ? ancestor : firstConnectorIntersection(request, result, "descendant");
    }

    private Optional<ConnectorNodeIntersection> firstConnectorIntersection(JsonNode request, JsonNode result, String wantedRelationship) {
        Map<String, Rectangle> nodes = nodeGeometry(result);
        ParentIndex parents = ParentIndex.from(request);
        for (EdgeRoute edgeRoute : edgeRoutes(result)) {
            for (Segment segment : edgeRoute.route().segments()) {
                for (Map.Entry<String, Rectangle> node : nodes.entrySet()) {
                    String relationship = parents.relationshipToEndpoint(edgeRoute.source(), edgeRoute.target(), node.getKey());
                    if (wantedRelationship.equals(relationship) && segment.intersects(node.getValue())) {
                        return Optional.of(new ConnectorNodeIntersection(
                                edgeRoute.id(),
                                edgeRoute.source(),
                                edgeRoute.target(),
                                node.getKey(),
                                segment,
                                node.getValue(),
                                relationship));
                    }
                }
            }
        }
        return Optional.empty();
    }

    public List<NodeOverlap> nodeOverlaps(JsonNode result) {
        return nodeOverlaps(nodeGeometry(result));
    }

    public List<NodeOverlap> nodeOverlaps(JsonNode request, JsonNode result) {
        ParentIndex parents = ParentIndex.from(request);
        return nodeOverlaps(nodeGeometry(result)).stream()
                .filter(overlap -> !parents.isContainedPair(overlap.firstId(), overlap.secondId()))
                .toList();
    }

    public List<ChildOutsideParentBounds> childOutsideParentBounds(JsonNode request, JsonNode result) {
        Map<String, Rectangle> nodes = nodeGeometry(result);
        ParentIndex parents = ParentIndex.from(request);
        List<ChildOutsideParentBounds> bounds = new ArrayList<>();
        for (NodeOverlap overlap : nodeOverlaps(nodes)) {
            String parentId = parents.parentOfPair(overlap.firstId(), overlap.secondId());
            if (parentId == null) {
                continue;
            }
            String childId = parentId.equals(overlap.firstId()) ? overlap.secondId() : overlap.firstId();
            Rectangle parent = nodes.get(parentId);
            Rectangle child = nodes.get(childId);
            if (!contains(parent, child)) {
                bounds.add(new ChildOutsideParentBounds(parentId, parent, childId, child));
            }
        }
        return bounds;
    }

    private static List<NodeOverlap> nodeOverlaps(Map<String, Rectangle> nodes) {
        List<Map.Entry<String, Rectangle>> entries = new ArrayList<>(nodes.entrySet());
        List<NodeOverlap> overlaps = new ArrayList<>();
        for (int i = 0; i < entries.size(); i++) {
            for (int j = i + 1; j < entries.size(); j++) {
                Map.Entry<String, Rectangle> first = entries.get(i);
                Map.Entry<String, Rectangle> second = entries.get(j);
                if (first.getValue().intersects(second.getValue())) {
                    overlaps.add(new NodeOverlap(first.getKey(), first.getValue(), second.getKey(), second.getValue()));
                }
            }
        }
        return overlaps;
    }

    private static OverlapStats classifyOverlaps(Map<String, Rectangle> nodes, ParentIndex parents) {
        int sameParent = 0;
        int parentChildContainments = 0;
        int childOutsideParentBounds = 0;
        int unrelated = 0;
        for (NodeOverlap overlap : nodeOverlaps(nodes)) {
            String parentId = parents.parentOfPair(overlap.firstId(), overlap.secondId());
            if (parentId != null) {
                String childId = parentId.equals(overlap.firstId()) ? overlap.secondId() : overlap.firstId();
                Rectangle parent = nodes.get(parentId);
                Rectangle child = nodes.get(childId);
                if (contains(parent, child)) {
                    parentChildContainments++;
                } else {
                    childOutsideParentBounds++;
                }
            } else if (parents.sameParent(overlap.firstId(), overlap.secondId())) {
                sameParent++;
            } else {
                unrelated++;
            }
        }
        return new OverlapStats(sameParent + unrelated, sameParent, parentChildContainments, childOutsideParentBounds);
    }

    private static boolean contains(Rectangle outer, Rectangle inner) {
        return inner.x() >= outer.x()
                && inner.y() >= outer.y()
                && inner.right() <= outer.right()
                && inner.bottom() <= outer.bottom();
    }

    public List<LockedNodeDisplacement> lockedNodeDisplacements(JsonNode request, JsonNode result) {
        Map<String, Rectangle> current = nodeGeometry(result);
        List<LockedNodeDisplacement> displacements = new ArrayList<>();
        for (JsonNode node : request.path("nodes")) {
            String id = node.path("id").asText();
            if (!node.path("locked").asBoolean(false) || !node.has("x") || !node.has("y") || !current.containsKey(id)) {
                continue;
            }
            Rectangle produced = current.get(id);
            Point requested = new Point(node.path("x").asInt(), node.path("y").asInt());
            if (produced.x() != requested.x() || produced.y() != requested.y()) {
                displacements.add(new LockedNodeDisplacement(id, requested, new Point(produced.x(), produced.y())));
            }
        }
        return displacements;
    }

    public record EdgeRoute(String id, String source, String target, Route route) {
    }

    public record ConnectorNodeIntersection(String edgeId, String sourceId, String targetId, String nodeId, Segment segment, Rectangle nodeBounds, String relationship) {
    }

    public record NodeOverlap(String firstId, Rectangle firstBounds, String secondId, Rectangle secondBounds) {
    }

    public record ChildOutsideParentBounds(String parentId, Rectangle parentBounds, String childId, Rectangle childBounds) {
    }

    public record LockedNodeDisplacement(String nodeId, Point requested, Point produced) {
    }

    private record Displacement(int locked, int movable) {
    }

    private record OverlapStats(
            int defects,
            int sameParent,
            int parentChildContainments,
            int childOutsideParentBounds) {
    }

    private record ConnectorStats(int unrelatedIntersections, int containerBoundaryCrossings) {
    }

    private record ParentIndex(Map<String, String> parents) {
        static ParentIndex from(JsonNode request) {
            Map<String, String> parents = new LinkedHashMap<>();
            for (JsonNode node : request.path("nodes")) {
                String id = node.path("id").asText("");
                String parentId = node.path("parentId").asText("");
                if (!id.isBlank() && !parentId.isBlank()) {
                    parents.put(id, parentId);
                }
            }
            return new ParentIndex(parents);
        }

        boolean isContainedPair(String first, String second) {
            return parentOfPair(first, second) != null;
        }

        String parentOfPair(String first, String second) {
            if (isAncestor(first, second)) {
                return first;
            }
            if (isAncestor(second, first)) {
                return second;
            }
            return null;
        }

        boolean sameParent(String first, String second) {
            return parents.getOrDefault(first, "").equals(parents.getOrDefault(second, ""));
        }

        String relationshipToEndpoint(String source, String target, String node) {
            if (source.equals(node)) {
                return "source";
            }
            if (target.equals(node)) {
                return "target";
            }
            if (isAncestor(node, source) || isAncestor(node, target)) {
                return "ancestor";
            }
            if (isAncestor(source, node) || isAncestor(target, node)) {
                return "descendant";
            }
            return "unrelated";
        }

        private boolean isAncestor(String possibleAncestor, String node) {
            String current = parents.get(node);
            while (current != null) {
                if (possibleAncestor.equals(current)) {
                    return true;
                }
                current = parents.get(current);
            }
            return false;
        }
    }
}
