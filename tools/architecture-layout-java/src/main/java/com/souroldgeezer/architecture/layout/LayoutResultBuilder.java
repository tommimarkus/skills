package com.souroldgeezer.architecture.layout;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.geometry.Port;
import com.souroldgeezer.architecture.layout.geometry.PortAssigner;
import com.souroldgeezer.architecture.layout.geometry.Rectangle;
import com.souroldgeezer.architecture.layout.geometry.Route;
import com.souroldgeezer.architecture.layout.metrics.LayoutMetrics;
import com.souroldgeezer.architecture.layout.metrics.LayoutMetricsCalculator;
import com.souroldgeezer.architecture.layout.metrics.LayoutResultValidator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class LayoutResultBuilder {
    private final LayoutMetricsCalculator metrics = new LayoutMetricsCalculator();
    private final LayoutResultValidator resultValidator = new LayoutResultValidator();

    public ObjectNode build(String backendName, String backendVersion, String mode, JsonNode request, Map<String, Rectangle> geometry, List<EdgeLayout> edgeLayouts, ArrayNode warnings) {
        ObjectNode result = JsonFiles.MAPPER.createObjectNode();
        result.put("schemaVersion", "1.0");
        result.put("requestId", request.path("requestId").asText());
        ObjectNode backend = result.putObject("backend");
        backend.put("name", backendName);
        backend.put("version", backendVersion);
        backend.put("mode", mode);
        backend.put("deterministic", true);
        result.put("mode", mode);
        result.put("deterministic", true);

        ArrayNode nodes = result.putArray("nodeGeometry");
        geometry.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry -> {
            Rectangle rectangle = entry.getValue();
            ObjectNode node = nodes.addObject();
            node.put("id", entry.getKey());
            node.put("x", rectangle.x());
            node.put("y", rectangle.y());
            node.put("w", rectangle.width());
            node.put("h", rectangle.height());
            findRequestNode(request, entry.getKey()).ifPresent(requestNode -> node.put("locked", requestNode.path("locked").asBoolean(false)));
        });

        ArrayNode edges = result.putArray("edges");
        edgeLayouts.stream().sorted((a, b) -> a.id().compareTo(b.id())).forEach(edgeLayout -> {
            ObjectNode edge = edges.addObject();
            edge.put("id", edgeLayout.id());
            edge.put("source", edgeLayout.source());
            edge.put("target", edgeLayout.target());
            edge.put("sourcePort", edgeLayout.sourcePort().side().wireName());
            edge.put("targetPort", edgeLayout.targetPort().side().wireName());
            edge.set("bendpoints", LayoutMetricsCalculator.bendpoints(edgeLayout.route()));
            ObjectNode route = edge.putObject("route");
            route.put("status", edgeLayout.status());
            route.put("style", "orthogonal");
        });

        LayoutMetrics computed = metrics.compute(request, result);
        result.set("metrics", metrics.toJson(computed));
        ArrayNode allWarnings = JsonFiles.MAPPER.createArrayNode();
        warnings.forEach(allWarnings::add);
        resultValidator.warnings(request, result).forEach(allWarnings::add);
        if (!allWarnings.isEmpty()) {
            result.set("warnings", allWarnings);
        }
        boolean hasError = false;
        for (JsonNode warning : allWarnings) {
            hasError = hasError || "error".equals(warning.path("severity").asText());
        }
        result.put("readiness", allWarnings.isEmpty() ? "success" : "capped");
        result.putObject("validation").put("state", hasError ? "invalid" : (allWarnings.isEmpty() ? "valid" : "warning"));
        return result;
    }

    public static Map<String, Rectangle> requestGeometry(JsonNode request, int startX, int startY, int xGap, int yGap) {
        Map<String, Rectangle> geometry = new LinkedHashMap<>();
        int index = 0;
        for (JsonNode node : request.path("nodes")) {
            int x = node.has("x") ? node.path("x").asInt() : startX + (index % 3) * xGap;
            int y = node.has("y") ? node.path("y").asInt() : startY + (index / 3) * yGap;
            geometry.put(node.path("id").asText(), new Rectangle(x, y, node.path("width").asInt(), node.path("height").asInt()));
            index++;
        }
        return geometry;
    }

    public static EdgeLayout edge(JsonNode edge, Map<String, Rectangle> geometry, String status) {
        Rectangle source = geometry.get(edge.path("source").asText());
        Rectangle target = geometry.get(edge.path("target").asText());
        Port sourcePort = PortAssigner.portToward(source, target);
        Port targetPort = PortAssigner.portToward(target, source);
        int midY = (sourcePort.point().y() + targetPort.point().y()) / 2;
        Route route = new Route(List.of(sourcePort.point(), new com.souroldgeezer.architecture.layout.geometry.Point(sourcePort.point().x(), midY), new com.souroldgeezer.architecture.layout.geometry.Point(targetPort.point().x(), midY), targetPort.point())).withoutRedundantPoints();
        return new EdgeLayout(edge.path("id").asText(), edge.path("source").asText(), edge.path("target").asText(), sourcePort, targetPort, route, status);
    }

    private static java.util.Optional<JsonNode> findRequestNode(JsonNode request, String id) {
        for (JsonNode node : request.path("nodes")) {
            if (id.equals(node.path("id").asText())) {
                return java.util.Optional.of(node);
            }
        }
        return java.util.Optional.empty();
    }

    public record EdgeLayout(String id, String source, String target, Port sourcePort, Port targetPort, Route route, String status) {
    }
}
