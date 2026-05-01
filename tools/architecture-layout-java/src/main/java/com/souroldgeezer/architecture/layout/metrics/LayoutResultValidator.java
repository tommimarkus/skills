package com.souroldgeezer.architecture.layout.metrics;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
        metrics.firstConnectorNodeIntersection(request, result)
                .ifPresent(intersection -> {
                    ObjectNode warning = WarningFactory.warning(
                        "LAYOUT_CONNECTOR_NODE_INTERSECTION",
                        "warning",
                        "Route crosses an unrelated node body.",
                        List.of(intersection.edgeId()));
                    warning.put("edgeId", intersection.edgeId());
                    warning.put("nodeId", intersection.nodeId());
                    warning.set("segment", WarningFactory.segment(intersection.segment()));
                    warning.set("nodeBounds", WarningFactory.rectangle(intersection.nodeBounds()));
                    warning.put("relationship", intersection.relationship());
                    warnings.add(warning);
                });
        metrics.firstConnectorContainerBoundaryCrossing(request, result)
                .ifPresent(intersection -> {
                    ObjectNode warning = WarningFactory.warning(
                        "LAYOUT_CONNECTOR_CONTAINER_BOUNDARY_CROSSING",
                        "warning",
                        "Route crosses a container boundary.",
                        List.of(intersection.edgeId(), intersection.nodeId()));
                    warning.put("edgeId", intersection.edgeId());
                    warning.put("nodeId", intersection.nodeId());
                    warning.set("segment", WarningFactory.segment(intersection.segment()));
                    warning.set("nodeBounds", WarningFactory.rectangle(intersection.nodeBounds()));
                    warning.put("relationship", intersection.relationship());
                    warnings.add(warning);
                });
        metrics.nodeOverlaps(request, result).forEach(overlap -> {
            ObjectNode warning = WarningFactory.warning(
                    "LAYOUT_NODE_OVERLAP",
                    "warning",
                    "Node rectangles overlap.",
                    List.of(overlap.firstId(), overlap.secondId()));
            ArrayNode overlapNodeIds = warning.putArray("nodeIds");
            overlapNodeIds.add(overlap.firstId());
            overlapNodeIds.add(overlap.secondId());
            ArrayNode nodeBounds = warning.putArray("nodeBounds");
            nodeBounds.add(WarningFactory.rectangle(overlap.firstBounds()));
            nodeBounds.add(WarningFactory.rectangle(overlap.secondBounds()));
            warnings.add(warning);
        });
        metrics.childOutsideParentBounds(request, result).forEach(containment -> {
            ObjectNode warning = WarningFactory.warning(
                    "LAYOUT_CHILD_OUTSIDE_PARENT_BOUNDS",
                    "warning",
                    "A nested child node extends outside its parent container.",
                    List.of(containment.parentId(), containment.childId()));
            warning.put("parentId", containment.parentId());
            warning.put("childId", containment.childId());
            warning.set("parentBounds", WarningFactory.rectangle(containment.parentBounds()));
            warning.set("childBounds", WarningFactory.rectangle(containment.childBounds()));
            warnings.add(warning);
        });
        for (LayoutMetricsCalculator.LockedNodeDisplacement displacement : metrics.lockedNodeDisplacements(request, result)) {
            ObjectNode warning = WarningFactory.warning(
                    "LAYOUT_LOCKED_NODE_MOVED",
                    "error",
                    "A locked node moved during layout.",
                    List.of(displacement.nodeId()));
            warning.put("nodeId", displacement.nodeId());
            warning.set("requested", WarningFactory.point(displacement.requested()));
            warning.set("produced", WarningFactory.point(displacement.produced()));
            warnings.add(warning);
        }
        return warnings;
    }
}
