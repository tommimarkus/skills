package com.souroldgeezer.architecture.layout.policy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.WarningFactory;
import com.souroldgeezer.architecture.layout.geometry.Rectangle;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class LayoutPolicyDiagnostics {
    private LayoutPolicyDiagnostics() {
    }

    public static Map<String, Rectangle> applyPostProcessing(JsonNode request, Map<String, Rectangle> geometry) {
        if (!request.has("layoutPolicy")) {
            return geometry;
        }
        Map<String, Rectangle> adjusted = new LinkedHashMap<>(geometry);
        for (JsonNode constraint : request.path("layoutPolicy").path("constraints")) {
            if ("rank-alignment".equals(constraint.path("kind").asText())) {
                applyRankAlignment(request, constraint, adjusted);
            }
        }
        return adjusted;
    }

    public static ObjectNode evaluate(JsonNode request, Map<String, Rectangle> geometry, ArrayNode warnings) {
        if (!request.has("layoutPolicy")) {
            return null;
        }
        JsonNode policy = request.path("layoutPolicy");
        ObjectNode result = JsonFiles.MAPPER.createObjectNode();
        result.put("name", policy.path("name").asText());
        if (policy.has("strictness")) {
            result.put("strictness", policy.path("strictness").asText());
        }
        ArrayNode constraints = result.putArray("constraints");
        for (JsonNode constraint : policy.path("constraints")) {
            ObjectNode diagnostic = diagnostic(request, constraint, geometry, warnings);
            constraints.add(diagnostic);
        }
        return result;
    }

    private static void applyRankAlignment(JsonNode request, JsonNode constraint, Map<String, Rectangle> geometry) {
        String axis = constraint.path("axis").asText("x");
        for (JsonNode pair : constraint.path("pairs")) {
            String upperId = pair.path("upper").asText();
            String lowerId = pair.path("lower").asText();
            if (isLocked(request, upperId) || !geometry.containsKey(upperId) || !geometry.containsKey(lowerId)) {
                continue;
            }
            Rectangle upper = geometry.get(upperId);
            Rectangle lower = geometry.get(lowerId);
            if ("y".equals(axis)) {
                int y = centerY(lower) - upper.height() / 2;
                geometry.put(upperId, new Rectangle(upper.x(), y, upper.width(), upper.height()));
            } else {
                int x = centerX(lower) - upper.width() / 2;
                geometry.put(upperId, new Rectangle(x, upper.y(), upper.width(), upper.height()));
            }
        }
    }

    private static ObjectNode diagnostic(JsonNode request, JsonNode constraint, Map<String, Rectangle> geometry, ArrayNode warnings) {
        String id = constraint.path("id").asText();
        String kind = constraint.path("kind").asText();
        ObjectNode diagnostic = JsonFiles.MAPPER.createObjectNode();
        diagnostic.put("id", id);
        diagnostic.put("kind", kind);
        if (constraint.has("role")) {
            diagnostic.put("role", constraint.path("role").asText());
        }
        ObjectNode evidence = diagnostic.putObject("evidence");
        copyText(constraint, evidence, "direction");
        copyText(constraint, evidence, "axis");
        copyStringArray(constraint, evidence, "nodeIds");
        copyStringArray(constraint, evidence, "edgeIds");

        boolean honored;
        switch (kind) {
            case "rank-chain" -> {
                honored = rankChainHonored(request, constraint, geometry);
                writeStatus(request, diagnostic, warnings, id, kind, "elk-layered", honored);
            }
            case "rank-alignment" -> {
                honored = rankAlignmentHonored(constraint, geometry);
                writeStatus(request, diagnostic, warnings, id, kind, "elk-layered+postprocess", honored);
            }
            case "compound-boundary" -> {
                honored = compoundBoundaryHonored(constraint, geometry);
                writeStatus(request, diagnostic, warnings, id, kind, "elk-layered", honored);
            }
            default -> {
                diagnostic.put("status", "unsupported");
                diagnostic.put("loweredBy", "none");
                diagnostic.put("postChecked", false);
                warnings.add(policyWarning(
                        request,
                        id,
                        "LAYOUT_POLICY_CONSTRAINT_UNSUPPORTED",
                        "Layout policy constraint kind is not supported by the packaged runtime."));
            }
        }
        return diagnostic;
    }

    private static void writeStatus(JsonNode request, ObjectNode diagnostic, ArrayNode warnings, String id, String kind, String loweredBy, boolean honored) {
        diagnostic.put("status", honored ? "honored" : "weakened");
        diagnostic.put("loweredBy", loweredBy);
        diagnostic.put("postChecked", true);
        if (!honored) {
            warnings.add(policyWarning(
                    request,
                    id,
                    "LAYOUT_POLICY_CONSTRAINT_WEAKENED",
                    "Layout policy constraint was lowered but the produced geometry did not satisfy the post-check."));
        }
    }

    private static ObjectNode policyWarning(JsonNode request, String id, String code, String message) {
        String severity = request != null && "strict".equals(request.path("layoutPolicy").path("strictness").asText())
                ? "error"
                : "warning";
        ObjectNode warning = WarningFactory.warning(code, severity, message, List.of(id));
        warning.put("constraintId", id);
        return warning;
    }

    private static boolean rankChainHonored(JsonNode request, JsonNode constraint, Map<String, Rectangle> geometry) {
        String direction = constraint.path("direction").asText(request.path("view").path("direction").asText("DOWN"));
        JsonNode nodeIds = constraint.path("nodeIds");
        if (!nodeIds.isArray() || nodeIds.size() < 2) {
            return false;
        }
        for (int index = 0; index < nodeIds.size() - 1; index++) {
            Rectangle first = geometry.get(nodeIds.get(index).asText());
            Rectangle second = geometry.get(nodeIds.get(index + 1).asText());
            if (first == null || second == null || !ordered(first, second, direction)) {
                return false;
            }
        }
        return true;
    }

    private static boolean rankAlignmentHonored(JsonNode constraint, Map<String, Rectangle> geometry) {
        String axis = constraint.path("axis").asText("x");
        JsonNode pairs = constraint.path("pairs");
        if (!pairs.isArray() || pairs.isEmpty()) {
            return false;
        }
        for (JsonNode pair : pairs) {
            Rectangle upper = geometry.get(pair.path("upper").asText());
            Rectangle lower = geometry.get(pair.path("lower").asText());
            if (upper == null || lower == null) {
                return false;
            }
            if ("y".equals(axis)) {
                if (centerY(upper) != centerY(lower)) {
                    return false;
                }
            } else if (centerX(upper) != centerX(lower)) {
                return false;
            }
        }
        return true;
    }

    private static boolean compoundBoundaryHonored(JsonNode constraint, Map<String, Rectangle> geometry) {
        Rectangle parent = geometry.get(constraint.path("parentId").asText());
        JsonNode nodeIds = constraint.path("nodeIds");
        if (parent == null || !nodeIds.isArray() || nodeIds.isEmpty()) {
            return false;
        }
        for (JsonNode nodeId : nodeIds) {
            Rectangle child = geometry.get(nodeId.asText());
            if (child == null
                    || child.left() < parent.left()
                    || child.right() > parent.right()
                    || child.top() < parent.top()
                    || child.bottom() > parent.bottom()) {
                return false;
            }
        }
        return true;
    }

    private static boolean ordered(Rectangle first, Rectangle second, String direction) {
        return switch (direction) {
            case "RIGHT" -> centerX(first) < centerX(second);
            case "LEFT" -> centerX(first) > centerX(second);
            case "UP" -> centerY(first) > centerY(second);
            default -> centerY(first) < centerY(second);
        };
    }

    private static boolean isLocked(JsonNode request, String nodeId) {
        for (JsonNode node : request.path("nodes")) {
            if (nodeId.equals(node.path("id").asText())) {
                return node.path("locked").asBoolean(false);
            }
        }
        return false;
    }

    private static int centerX(Rectangle rectangle) {
        return rectangle.x() + rectangle.width() / 2;
    }

    private static int centerY(Rectangle rectangle) {
        return rectangle.y() + rectangle.height() / 2;
    }

    private static void copyText(JsonNode source, ObjectNode target, String field) {
        if (source.has(field)) {
            target.put(field, source.path(field).asText());
        }
    }

    private static void copyStringArray(JsonNode source, ObjectNode target, String field) {
        if (!source.has(field) || !source.get(field).isArray()) {
            return;
        }
        ArrayNode values = target.putArray(field);
        source.get(field).forEach(value -> values.add(value.asText()));
    }
}
