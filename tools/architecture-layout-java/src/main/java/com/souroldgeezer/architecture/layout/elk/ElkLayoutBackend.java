package com.souroldgeezer.architecture.layout.elk;

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
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.eclipse.elk.alg.layered.options.LayeredOptions;
import org.eclipse.elk.core.RecursiveGraphLayoutEngine;
import org.eclipse.elk.core.options.CoreOptions;
import org.eclipse.elk.core.options.Direction;
import org.eclipse.elk.core.options.EdgeRouting;
import org.eclipse.elk.core.util.NullElkProgressMonitor;
import org.eclipse.elk.graph.ElkBendPoint;
import org.eclipse.elk.graph.ElkEdge;
import org.eclipse.elk.graph.ElkEdgeSection;
import org.eclipse.elk.graph.ElkNode;
import org.eclipse.elk.graph.util.ElkGraphUtil;

public final class ElkLayoutBackend {
    private static final String VERSION = "0.11.0";

    private final LayoutResultBuilder builder = new LayoutResultBuilder();

    public String backendName() {
        return "elk-layered";
    }

    public boolean supports(JsonNode request) {
        String viewpoint = request.path("view").path("viewpoint").asText();
        return viewpoint.contains("Service Realization")
                || viewpoint.contains("Application Cooperation")
                || viewpoint.contains("Technology Usage");
    }

    public ObjectNode layout(JsonNode request) {
        ArrayNode warnings = JsonFiles.MAPPER.createArrayNode();
        if (!supports(request)) {
            warnings.add(WarningFactory.warning(
                    "LAYOUT_UNSUPPORTED_VIEWPOINT",
                    "warning",
                    "The generated-layout backend does not force unsupported viewpoints through layered layout.",
                    List.of(request.path("view").path("id").asText())));
        }
        ElkGraph graph = supports(request) ? runElk(request, warnings) : null;
        Map<String, Rectangle> geometry = graph == null ? generatedGeometry(request, false) : graph.geometry();
        List<LayoutResultBuilder.EdgeLayout> edges = new ArrayList<>();
        for (JsonNode edge : request.path("edges")) {
            if (edge.path("visible").asBoolean(true) && geometry.containsKey(edge.path("source").asText()) && geometry.containsKey(edge.path("target").asText())) {
                ElkEdge elkEdge = graph == null ? null : graph.edges().get(edge.path("id").asText());
                edges.add(elkEdge == null
                        ? LayoutResultBuilder.edge(edge, geometry, supports(request) ? "routed" : "unsupported")
                        : edgeFromElk(edge, elkEdge, geometry, graph.shiftX(), graph.shiftY()));
            }
        }
        return builder.build(backendName(), VERSION, "generated-layout", request, geometry, edges, warnings);
    }

    private static ElkGraph runElk(JsonNode request, ArrayNode warnings) {
        ElkNode root = ElkGraphUtil.createGraph();
        root.setIdentifier(request.path("requestId").asText());
        root.setProperty(CoreOptions.ALGORITHM, LayeredOptions.ALGORITHM_ID);
        root.setProperty(CoreOptions.DIRECTION, direction(request.path("view").path("direction").asText()));
        root.setProperty(CoreOptions.EDGE_ROUTING, EdgeRouting.ORTHOGONAL);
        root.setProperty(CoreOptions.RANDOM_SEED, 1);
        root.setProperty(CoreOptions.SPACING_NODE_NODE, 80.0);
        root.setProperty(CoreOptions.SPACING_EDGE_NODE, 30.0);
        root.setProperty(CoreOptions.SPACING_EDGE_EDGE, 20.0);

        Map<String, JsonNode> requestNodes = requestNodes(request);
        Map<String, ElkNode> elkNodes = new HashMap<>();
        requestNodes.keySet().stream().sorted().forEach(id -> createNode(id, requestNodes, elkNodes, root));

        Map<String, ElkEdge> elkEdges = new LinkedHashMap<>();
        List<JsonNode> sortedEdges = new ArrayList<>();
        request.path("edges").forEach(sortedEdges::add);
        sortedEdges.sort(Comparator.comparing(edge -> edge.path("id").asText()));
        for (JsonNode edge : sortedEdges) {
            if (!edge.path("visible").asBoolean(true)) {
                continue;
            }
            ElkNode source = elkNodes.get(edge.path("source").asText());
            ElkNode target = elkNodes.get(edge.path("target").asText());
            if (source == null || target == null) {
                continue;
            }
            ElkEdge elkEdge = ElkGraphUtil.createSimpleEdge(source, target);
            elkEdge.setIdentifier(edge.path("id").asText());
            elkEdge.setProperty(CoreOptions.PRIORITY, edge.path("priority").asInt(0));
            ElkGraphUtil.updateContainment(elkEdge);
            elkEdges.put(edge.path("id").asText(), elkEdge);
        }

        new RecursiveGraphLayoutEngine().layout(root, new NullElkProgressMonitor());

        Map<String, Rectangle> rawGeometry = new LinkedHashMap<>();
        for (String id : requestNodes.keySet().stream().sorted().toList()) {
            ElkNode node = elkNodes.get(id);
            JsonNode requestNode = requestNodes.get(id);
            int x = round(absoluteX(node));
            int y = round(absoluteY(node));
            if (requestNode.path("locked").asBoolean(false) && requestNode.has("x") && requestNode.has("y")
                    && (x != requestNode.path("x").asInt() || y != requestNode.path("y").asInt())) {
                warnings.add(WarningFactory.warning(
                        "LAYOUT_LOCKED_NODE_RESTORED",
                        "warning",
                        "ELK moved a locked node; the packaged runtime restored the request coordinate and capped readiness.",
                        List.of(id)));
                x = requestNode.path("x").asInt();
                y = requestNode.path("y").asInt();
            }
            rawGeometry.put(id, new Rectangle(x, y, requestNode.path("width").asInt(), requestNode.path("height").asInt()));
        }

        boolean hasLockedGeometry = request.path("nodes").findValues("locked").stream().anyMatch(JsonNode::asBoolean);
        int minX = rawGeometry.values().stream().mapToInt(Rectangle::x).min().orElse(40);
        int minY = rawGeometry.values().stream().mapToInt(Rectangle::y).min().orElse(40);
        int shiftX = hasLockedGeometry ? 0 : 40 - minX;
        int shiftY = hasLockedGeometry ? 0 : 40 - minY;
        Map<String, Rectangle> normalized = new LinkedHashMap<>();
        rawGeometry.forEach((id, rectangle) -> normalized.put(id, new Rectangle(
                rectangle.x() + shiftX,
                rectangle.y() + shiftY,
                rectangle.width(),
                rectangle.height())));
        return new ElkGraph(normalized, elkEdges, shiftX, shiftY);
    }

    private static ElkNode createNode(String id, Map<String, JsonNode> requestNodes, Map<String, ElkNode> elkNodes, ElkNode root) {
        if (elkNodes.containsKey(id)) {
            return elkNodes.get(id);
        }
        JsonNode requestNode = requestNodes.get(id);
        String parentId = requestNode.path("parentId").asText("");
        ElkNode parent = parentId.isBlank() || !requestNodes.containsKey(parentId)
                ? root
                : createNode(parentId, requestNodes, elkNodes, root);
        ElkNode node = ElkGraphUtil.createNode(parent);
        node.setIdentifier(id);
        node.setDimensions(requestNode.path("width").asDouble(), requestNode.path("height").asDouble());
        if (requestNode.has("x") && requestNode.has("y")) {
            node.setLocation(requestNode.path("x").asDouble(), requestNode.path("y").asDouble());
        }
        ElkGraphUtil.createLabel(requestNode.path("label").asText(id), node);
        elkNodes.put(id, node);
        return node;
    }

    private static Map<String, Rectangle> generatedGeometry(JsonNode request, boolean supported) {
        List<JsonNode> nodes = new ArrayList<>();
        request.path("nodes").forEach(nodes::add);
        nodes.sort(Comparator.comparing(node -> node.path("id").asText()));
        LinkedHashMap<String, Rectangle> geometry = new LinkedHashMap<>();
        int layer = 0;
        for (JsonNode node : nodes) {
            int x = node.has("x") && node.path("locked").asBoolean(false) ? node.path("x").asInt() : 40 + (layer % 3) * 240;
            int y = node.has("y") && node.path("locked").asBoolean(false) ? node.path("y").asInt() : 40 + (layer / 3) * 180;
            if (!supported && node.has("x") && node.has("y")) {
                x = node.path("x").asInt();
                y = node.path("y").asInt();
            }
            geometry.put(node.path("id").asText(), new Rectangle(x, y, node.path("width").asInt(), node.path("height").asInt()));
            layer++;
        }
        return geometry;
    }

    private static Map<String, JsonNode> requestNodes(JsonNode request) {
        Map<String, JsonNode> nodes = new LinkedHashMap<>();
        List<JsonNode> sorted = new ArrayList<>();
        request.path("nodes").forEach(sorted::add);
        sorted.sort(Comparator.comparing(node -> node.path("id").asText()));
        for (JsonNode node : sorted) {
            nodes.put(node.path("id").asText(), node);
        }
        return nodes;
    }

    private static Direction direction(String value) {
        return switch (value) {
            case "RIGHT" -> Direction.RIGHT;
            case "LEFT" -> Direction.LEFT;
            case "UP" -> Direction.UP;
            default -> Direction.DOWN;
        };
    }

    private static LayoutResultBuilder.EdgeLayout edgeFromElk(JsonNode edge, ElkEdge elkEdge, Map<String, Rectangle> geometry, int shiftX, int shiftY) {
        Rectangle source = geometry.get(edge.path("source").asText());
        Rectangle target = geometry.get(edge.path("target").asText());
        Port sourcePort = PortAssigner.portToward(source, target);
        Port targetPort = PortAssigner.portToward(target, source);
        List<Point> points = new ArrayList<>();
        points.add(sourcePort.point());
        if (!elkEdge.getSections().isEmpty()) {
            ElkEdgeSection section = elkEdge.getSections().get(0);
            for (ElkBendPoint bendPoint : section.getBendPoints()) {
                points.add(new Point(round(bendPoint.getX()) + shiftX, round(bendPoint.getY()) + shiftY));
            }
        }
        points.add(targetPort.point());
        Route route = new Route(points).withoutRedundantPoints();
        return new LayoutResultBuilder.EdgeLayout(
                edge.path("id").asText(),
                edge.path("source").asText(),
                edge.path("target").asText(),
                sourcePort,
                targetPort,
                route,
                "routed");
    }

    private static double absoluteX(ElkNode node) {
        double x = node.getX();
        ElkNode parent = node.getParent();
        while (parent != null && parent.getParent() != null) {
            x += parent.getX();
            parent = parent.getParent();
        }
        return x;
    }

    private static double absoluteY(ElkNode node) {
        double y = node.getY();
        ElkNode parent = node.getParent();
        while (parent != null && parent.getParent() != null) {
            y += parent.getY();
            parent = parent.getParent();
        }
        return y;
    }

    private static int round(double value) {
        return (int) Math.round(value);
    }

    private record ElkGraph(Map<String, Rectangle> geometry, Map<String, ElkEdge> edges, int shiftX, int shiftY) {
    }
}
