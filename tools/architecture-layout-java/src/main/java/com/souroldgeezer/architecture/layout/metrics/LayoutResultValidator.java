package com.souroldgeezer.architecture.layout.metrics;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.WarningFactory;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class LayoutResultValidator {
    private final LayoutMetricsCalculator metrics = new LayoutMetricsCalculator();

    public ArrayNode warnings(JsonNode request, JsonNode result) {
        ArrayNode warnings = JsonFiles.MAPPER.createArrayNode();
        Set<String> nodeIds = new HashSet<>();
        for (JsonNode node : result.path("nodeGeometry")) {
            String id = node.path("id").asText();
            if (!nodeIds.add(id)) {
                warnings.add(WarningFactory.warning("LAYOUT_DUPLICATE_ID", "error", "Duplicate node id in result geometry.", List.of(id)));
            }
        }
        Set<String> edgeIds = new HashSet<>();
        for (JsonNode edge : result.path("edges")) {
            String id = edge.path("id").asText();
            if (!edgeIds.add(id)) {
                warnings.add(WarningFactory.warning("LAYOUT_DUPLICATE_ID", "error", "Duplicate edge id in result routes.", List.of(id)));
            }
            if (!nodeIds.contains(edge.path("source").asText()) || !nodeIds.contains(edge.path("target").asText())) {
                warnings.add(WarningFactory.warning("LAYOUT_EDGE_ENDPOINT_MISSING", "error", "Edge endpoint does not resolve to a visible node.", List.of(id)));
            }
        }
        metrics.firstConnectorNodeIntersection(result)
                .ifPresent(edgeId -> warnings.add(WarningFactory.warning(
                        "LAYOUT_CONNECTOR_NODE_INTERSECTION",
                        "warning",
                        "Route crosses an unrelated node body.",
                        List.of(edgeId))));
        LayoutMetrics computed = metrics.compute(request, result);
        if (computed.lockedNodeDisplacement() > 0) {
            warnings.add(WarningFactory.warning(
                    "LAYOUT_LOCKED_NODE_MOVED",
                    "error",
                    "A locked node moved during layout.",
                    List.of()));
        }
        return warnings;
    }
}
