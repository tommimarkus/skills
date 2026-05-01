package com.souroldgeezer.architecture.layout.polish;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.LayoutResultBuilder;
import com.souroldgeezer.architecture.layout.WarningFactory;
import com.souroldgeezer.architecture.layout.geometry.Rectangle;
import com.souroldgeezer.architecture.layout.metrics.LayoutMetrics;
import com.souroldgeezer.architecture.layout.metrics.LayoutMetricsCalculator;
import com.souroldgeezer.architecture.layout.router.RouteRepairBackend;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class GlobalPolishBackend {
    private final LayoutResultBuilder builder = new LayoutResultBuilder();
    private final RouteRepairBackend router = new RouteRepairBackend();
    private final LayoutMetricsCalculator metrics = new LayoutMetricsCalculator();
    private final LayoutScorer scorer = new LayoutScorer();

    public ObjectNode polish(JsonNode request) {
        ObjectNode routedOriginal = router.repair(request);
        LayoutMetrics before = metrics.compute(request, routedOriginal);
        int beforeScore = scorer.score(before);
        Map<String, Rectangle> candidateGeometry = moveCandidates(request, before.nodeOverlaps() > 0 || before.connectorNodeIntersections() > 0);
        List<LayoutResultBuilder.EdgeLayout> edges = new java.util.ArrayList<>();
        for (JsonNode edge : request.path("edges")) {
            edges.add(LayoutResultBuilder.edge(edge, candidateGeometry, "routed"));
        }
        ArrayNode warnings = JsonFiles.MAPPER.createArrayNode();
        ObjectNode candidate = builder.build("global-polish", "1.0", "global-polish", request, candidateGeometry, edges, warnings);
        LayoutMetrics after = metrics.compute(request, candidate);
        int afterScore = scorer.score(after);
        if (afterScore < beforeScore && after.lockedNodeDisplacement() == 0) {
            candidate.set("beforeMetrics", metrics.toJson(before));
            candidate.set("afterMetrics", metrics.toJson(after));
            candidate.set("displacements", displacements(request, candidateGeometry));
            return candidate;
        }

        ArrayNode noImproveWarnings = JsonFiles.MAPPER.createArrayNode();
        noImproveWarnings.add(WarningFactory.warning(
                "LAYOUT_GLOBAL_POLISH_NO_IMPROVEMENT",
                "warning",
                "No bounded mental-map preserving move improved the score.",
                List.of(request.path("requestId").asText())));
        Map<String, Rectangle> originalGeometry = LayoutResultBuilder.requestGeometry(request, 40, 40, 220, 160);
        List<LayoutResultBuilder.EdgeLayout> originalEdges = new java.util.ArrayList<>();
        for (JsonNode edge : request.path("edges")) {
            originalEdges.add(LayoutResultBuilder.edge(edge, originalGeometry, "original"));
        }
        ObjectNode original = builder.build("global-polish", "1.0", "global-polish", request, originalGeometry, originalEdges, noImproveWarnings);
        original.set("beforeMetrics", metrics.toJson(before));
        original.set("afterMetrics", metrics.toJson(before));
        original.set("displacements", JsonFiles.MAPPER.createArrayNode());
        return original;
    }

    private static Map<String, Rectangle> moveCandidates(JsonNode request, boolean needsMove) {
        Map<String, Rectangle> geometry = LayoutResultBuilder.requestGeometry(request, 40, 40, 220, 160);
        if (!needsMove) {
            return geometry;
        }
        int max = request.path("constraints").path("maxNodeDisplacement").asInt(80);
        Map<String, Rectangle> moved = new LinkedHashMap<>();
        int movableIndex = 0;
        for (JsonNode node : request.path("nodes")) {
            String id = node.path("id").asText();
            Rectangle current = geometry.get(id);
            boolean movable = !node.path("locked").asBoolean(false)
                    && (node.path("generated").asBoolean(false) || node.path("inferred").asBoolean(false) || !node.has("locked"));
            if (movable) {
                int delta = Math.min(max, 90);
                int x = movableIndex % 2 == 0 ? current.x() : current.x() + delta;
                int y = movableIndex % 2 == 0 ? current.y() + delta : current.y();
                moved.put(id, new Rectangle(x, y, current.width(), current.height()));
                movableIndex++;
            } else {
                moved.put(id, current);
            }
        }
        return moved;
    }

    private static ArrayNode displacements(JsonNode request, Map<String, Rectangle> geometry) {
        ArrayNode displacements = JsonFiles.MAPPER.createArrayNode();
        for (JsonNode node : request.path("nodes")) {
            if (!node.has("x") || !node.has("y")) {
                continue;
            }
            Rectangle current = geometry.get(node.path("id").asText());
            ObjectNode displacement = displacements.addObject();
            displacement.put("id", node.path("id").asText());
            displacement.put("dx", current.x() - node.path("x").asInt());
            displacement.put("dy", current.y() - node.path("y").asInt());
        }
        return displacements;
    }
}
