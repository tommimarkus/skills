package com.souroldgeezer.architecture.layout.schema;

import com.fasterxml.jackson.databind.JsonNode;
import com.networknt.schema.Error;
import com.networknt.schema.Schema;
import com.networknt.schema.SchemaRegistry;
import com.networknt.schema.SpecificationVersion;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.LayoutPaths;
import com.souroldgeezer.architecture.layout.ValidationResult;
import java.io.IOException;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class LayoutSchemaValidator {
    private static final Set<String> REQUEST_MODES = Set.of("generated-layout", "route-repair", "global-polish");
    private static final Set<String> RESULT_MODES = Set.of("generated-layout", "route-repair", "global-polish");

    public ValidationResult validateRequest(Path requestPath) throws IOException {
        JsonNode request = JsonFiles.read(requestPath);
        return validateRequest(request);
    }

    public ValidationResult validateResult(Path resultPath) throws IOException {
        JsonNode result = JsonFiles.read(resultPath);
        return validateResult(result);
    }

    public ValidationResult validateProvenance(JsonNode provenance) {
        ValidationResult result = new ValidationResult();
        validateAgainstSchema("layout-provenance.schema.json", provenance, result);
        return result;
    }

    public ValidationResult validateRequest(JsonNode request) {
        ValidationResult result = new ValidationResult();
        validateAgainstSchema("layout-request.schema.json", request, result);
        requireObject(request, "", result);
        requireText(request, "schemaVersion", result);
        requireText(request, "requestId", result);
        requireConst(request, "archimateTarget", "3.2", result);
        requireOneOf(request, "mode", REQUEST_MODES, result);
        if (!request.has("view") || !request.get("view").isObject()) {
            result.add("/view is required");
        } else {
            JsonNode view = request.get("view");
            for (String field : List.of("id", "name", "viewpoint", "direction", "qualityTarget")) {
                requireText(view, field, result, "/view/" + field);
            }
        }
        if (!request.has("nodes") || !request.get("nodes").isArray() || request.get("nodes").isEmpty()) {
            result.add("/nodes must contain at least one node");
            return result;
        }
        Set<String> nodeIds = new HashSet<>();
        Map<String, JsonNode> nodesById = new LinkedHashMap<>();
        for (JsonNode node : request.get("nodes")) {
            String id = requireText(node, "id", result, "/nodes/id");
            if (id != null && !nodeIds.add(id)) {
                result.add("duplicate node id " + id);
            } else if (id != null) {
                nodesById.put(id, node);
            }
            requirePositiveInt(node, "width", result, "/nodes/" + id + "/width");
            requirePositiveInt(node, "height", result, "/nodes/" + id + "/height");
            validateOptionalInt(node, "x", result, "/nodes/" + id + "/x");
            validateOptionalInt(node, "y", result, "/nodes/" + id + "/y");
            validateOptionalBoolean(node, "locked", result, "/nodes/" + id + "/locked");
            validateOptionalBoolean(node, "generated", result, "/nodes/" + id + "/generated");
            validateOptionalBoolean(node, "inferred", result, "/nodes/" + id + "/inferred");
            validateStringArray(node, "ports", "id", result, "/nodes/" + id + "/ports");
            if (node.has("x") != node.has("y")) {
                result.add("/nodes/" + id + " must provide x and y together");
            }
            if (node.path("locked").asBoolean(false) && (!hasInt(node, "x") || !hasInt(node, "y"))) {
                result.add("/nodes/" + id + " locked geometry requires x and y");
            }
        }
        validateParentReferences(nodesById, nodeIds, result);
        validateContainers(request, nodeIds, result);
        validateLocks(request, nodeIds, result);
        if (!request.has("edges") || !request.get("edges").isArray()) {
            result.add("/edges must be an array");
        } else {
            Set<String> edgeIds = new HashSet<>();
            for (JsonNode edge : request.get("edges")) {
                String id = requireText(edge, "id", result, "/edges/id");
                if (id != null && !edgeIds.add(id)) {
                    result.add("duplicate edge id " + id);
                }
                String source = requireText(edge, "source", result, "/edges/" + id + "/source");
                String target = requireText(edge, "target", result, "/edges/" + id + "/target");
                if (source != null && !nodeIds.contains(source)) {
                    result.add("edge " + id + " references missing source " + source);
                }
                if (target != null && !nodeIds.contains(target)) {
                    result.add("edge " + id + " references missing target " + target);
                }
                validateOptionalBoolean(edge, "visible", result, "/edges/" + id + "/visible");
                validateOptionalBoolean(edge, "generated", result, "/edges/" + id + "/generated");
                validateOptionalBoolean(edge, "locked", result, "/edges/" + id + "/locked");
                validateOptionalBoolean(edge, "routeLocked", result, "/edges/" + id + "/routeLocked");
                validateOptionalInt(edge, "priority", result, "/edges/" + id + "/priority");
                validatePointArray(edge, "existingRoute", edge.path("routeLocked").asBoolean(false) ? 2 : 0, result, "/edges/" + id + "/existingRoute");
                validatePointArray(edge, "priorBendpoints", 0, result, "/edges/" + id + "/priorBendpoints");
                validateStringArray(edge, "preferredSourcePorts", result, "/edges/" + id + "/preferredSourcePorts");
                validateStringArray(edge, "preferredTargetPorts", result, "/edges/" + id + "/preferredTargetPorts");
            }
        }
        if (!request.has("constraints") || !request.get("constraints").isObject()) {
            result.add("/constraints is required");
        } else {
            JsonNode constraints = request.get("constraints");
            validateOptionalBoolean(constraints, "noRoutePossible", result, "/constraints/noRoutePossible");
            validateOptionalNonNegativeInt(constraints, "maxNodeDisplacement", result, "/constraints/maxNodeDisplacement");
            validateOptionalNonNegativeInt(constraints, "maxBends", result, "/constraints/maxBends");
        }
        validateOptionalBoolean(request, "preserveExistingGeometry", result, "/preserveExistingGeometry");
        validatePriorGeometry(request, nodeIds, result);
        validateSemanticBands(request, result);
        return result;
    }

    public ValidationResult validateResult(JsonNode layoutResult) {
        ValidationResult result = new ValidationResult();
        validateAgainstSchema("layout-result.schema.json", layoutResult, result);
        requireObject(layoutResult, "", result);
        requireText(layoutResult, "schemaVersion", result);
        requireText(layoutResult, "requestId", result);
        requireOneOf(layoutResult, "mode", RESULT_MODES, result);
        if (!layoutResult.path("deterministic").isBoolean()) {
            result.add("/deterministic must be boolean");
        }
        requireText(layoutResult, "readiness", result);
        if (!layoutResult.has("backend") || !layoutResult.get("backend").isObject()) {
            result.add("/backend is required");
        } else {
            JsonNode backend = layoutResult.get("backend");
            requireText(backend, "name", result, "/backend/name");
            requireText(backend, "version", result, "/backend/version");
            requireText(backend, "mode", result, "/backend/mode");
            if (!backend.path("deterministic").isBoolean()) {
                result.add("/backend/deterministic must be boolean");
            }
        }
        Set<String> nodeIds = new HashSet<>();
        if (!layoutResult.has("nodeGeometry") || !layoutResult.get("nodeGeometry").isArray() || layoutResult.get("nodeGeometry").isEmpty()) {
            result.add("/nodeGeometry must contain node geometry");
        } else {
            for (JsonNode node : layoutResult.get("nodeGeometry")) {
                String id = requireText(node, "id", result, "/nodeGeometry/id");
                if (id != null && !nodeIds.add(id)) {
                    result.add("duplicate node geometry id " + id);
                }
                for (String field : List.of("x", "y", "w", "h")) {
                    if (!node.path(field).canConvertToInt()) {
                        result.add("/nodeGeometry/" + id + "/" + field + " must be integer");
                    }
                }
            }
        }
        if (!layoutResult.has("edges") || !layoutResult.get("edges").isArray()) {
            result.add("/edges must be an array");
        } else {
            Set<String> edgeIds = new HashSet<>();
            for (JsonNode edge : layoutResult.get("edges")) {
                String id = requireText(edge, "id", result, "/edges/id");
                if (id != null && !edgeIds.add(id)) {
                    result.add("duplicate edge id " + id);
                }
                requireText(edge, "source", result, "/edges/" + id + "/source");
                requireText(edge, "target", result, "/edges/" + id + "/target");
                requireText(edge, "sourcePort", result, "/edges/" + id + "/sourcePort");
                requireText(edge, "targetPort", result, "/edges/" + id + "/targetPort");
                if (!edge.has("bendpoints") || !edge.get("bendpoints").isArray()) {
                    result.add("/edges/" + id + "/bendpoints must be array");
                }
                if (!edge.has("route") || !edge.get("route").isObject()) {
                    result.add("/edges/" + id + "/route is required");
                } else {
                    requireText(edge.get("route"), "status", result, "/edges/" + id + "/route/status");
                }
            }
        }
        if (!layoutResult.has("metrics") || !layoutResult.get("metrics").isObject()) {
            result.add("/metrics is required");
        }
        if (!layoutResult.has("validation") || !layoutResult.get("validation").isObject()) {
            result.add("/validation is required");
        } else {
            requireText(layoutResult.get("validation"), "state", result, "/validation/state");
        }
        if (layoutResult.has("warnings")) {
            validateWarnings(layoutResult.get("warnings"), result);
        }
        return result;
    }

    private static void validateWarnings(JsonNode warnings, ValidationResult result) {
        if (!warnings.isArray()) {
            result.add("/warnings must be array");
            return;
        }
        for (JsonNode warning : warnings) {
            requireText(warning, "code", result, "/warnings/code");
            requireText(warning, "severity", result, "/warnings/severity");
            requireText(warning, "message", result, "/warnings/message");
            if (!warning.has("subjectIds") || !warning.get("subjectIds").isArray()) {
                result.add("/warnings/subjectIds must be array");
            }
        }
    }

    private static void validateParentReferences(Map<String, JsonNode> nodesById, Set<String> nodeIds, ValidationResult result) {
        for (Map.Entry<String, JsonNode> entry : nodesById.entrySet()) {
            String id = entry.getKey();
            JsonNode node = entry.getValue();
            String parentId = optionalText(node, "parentId", result, "/nodes/" + id + "/parentId");
            if (parentId == null) {
                continue;
            }
            if (id.equals(parentId)) {
                result.add("/nodes/" + id + "/parentId must not reference itself");
            }
            if (!nodeIds.contains(parentId)) {
                result.add("/nodes/" + id + "/parentId references missing node " + parentId);
            }
        }
        validateParentCycles(nodesById, result);
    }

    private static void validateParentCycles(Map<String, JsonNode> nodesById, ValidationResult result) {
        for (String id : nodesById.keySet()) {
            Set<String> seen = new HashSet<>();
            String current = id;
            while (current != null && nodesById.containsKey(current)) {
                if (!seen.add(current)) {
                    result.add("parentId cycle involving node " + id);
                    break;
                }
                JsonNode node = nodesById.get(current);
                JsonNode parent = node.get("parentId");
                current = parent != null && parent.isTextual() && !parent.asText().isBlank() ? parent.asText() : null;
            }
        }
    }

    private static void validateContainers(JsonNode request, Set<String> nodeIds, ValidationResult result) {
        if (!request.has("containers")) {
            return;
        }
        JsonNode containers = request.get("containers");
        if (!containers.isArray()) {
            result.add("/containers must be array");
            return;
        }
        int index = 0;
        for (JsonNode container : containers) {
            String path = "/containers/" + index;
            String parent = requireText(container, "parent", result, path + "/parent");
            if (parent != null && !nodeIds.contains(parent)) {
                result.add(path + "/parent references missing node " + parent);
            }
            if (!container.has("children") || !container.get("children").isArray() || container.get("children").isEmpty()) {
                result.add(path + "/children must contain at least one node id");
            } else {
                int childIndex = 0;
                for (JsonNode child : container.get("children")) {
                    if (!child.isTextual() || child.asText().isBlank()) {
                        result.add(path + "/children/" + childIndex + " must be text");
                    } else if (!nodeIds.contains(child.asText())) {
                        result.add(path + "/children/" + childIndex + " references missing node " + child.asText());
                    } else if (child.asText().equals(parent)) {
                        result.add(path + "/children/" + childIndex + " must not repeat the parent node");
                    }
                    childIndex++;
                }
            }
            validateOptionalPositiveInt(container, "maxDepth", result, path + "/maxDepth");
            validateOptionalBoolean(container, "mayHideEdge", result, path + "/mayHideEdge");
            index++;
        }
    }

    private static void validateLocks(JsonNode request, Set<String> nodeIds, ValidationResult result) {
        if (!request.has("locks")) {
            return;
        }
        JsonNode locks = request.get("locks");
        if (!locks.isArray()) {
            result.add("/locks must be array");
            return;
        }
        int index = 0;
        for (JsonNode lock : locks) {
            String path = "/locks/" + index;
            String node = optionalText(lock, "node", result, path + "/node");
            optionalText(lock, "edge", result, path + "/edge");
            optionalText(lock, "reason", result, path + "/reason");
            if (node == null && !lock.has("edge")) {
                result.add(path + " must reference node or edge");
            }
            if (node != null && !nodeIds.contains(node)) {
                result.add(path + "/node references missing node " + node);
            }
            index++;
        }
    }

    private static void validatePriorGeometry(JsonNode request, Set<String> nodeIds, ValidationResult result) {
        if (!request.has("priorGeometry")) {
            return;
        }
        JsonNode prior = request.get("priorGeometry");
        if (!prior.isObject()) {
            result.add("/priorGeometry must be object");
            return;
        }
        if (prior.has("nodes")) {
            if (!prior.get("nodes").isArray()) {
                result.add("/priorGeometry/nodes must be array");
            } else {
                int index = 0;
                for (JsonNode node : prior.get("nodes")) {
                    String path = "/priorGeometry/nodes/" + index;
                    String id = requireText(node, "id", result, path + "/id");
                    if (id != null && !nodeIds.contains(id)) {
                        result.add(path + "/id references missing node " + id);
                    }
                    for (String field : List.of("x", "y", "w", "h")) {
                        validateOptionalInt(node, field, result, path + "/" + field);
                    }
                    index++;
                }
            }
        }
        if (prior.has("edges") && !prior.get("edges").isArray()) {
            result.add("/priorGeometry/edges must be array");
        }
    }

    private static void validateSemanticBands(JsonNode request, ValidationResult result) {
        if (!request.has("semanticBands")) {
            return;
        }
        JsonNode bands = request.get("semanticBands");
        if (!bands.isArray()) {
            result.add("/semanticBands must be array");
            return;
        }
        int index = 0;
        for (JsonNode band : bands) {
            String path = "/semanticBands/" + index;
            optionalText(band, "id", result, path + "/id");
            optionalText(band, "axis", result, path + "/axis");
            validateOptionalInt(band, "order", result, path + "/order");
            index++;
        }
    }

    private static void validateAgainstSchema(String fileName, JsonNode instance, ValidationResult result) {
        Path schema = LayoutPaths.referencesDir().resolve("schemas").resolve(fileName);
        try {
            Schema jsonSchema = SchemaRegistry
                    .withDefaultDialect(SpecificationVersion.DRAFT_2020_12)
                    .getSchema(JsonFiles.read(schema));
            for (Error error : jsonSchema.validate(instance)) {
                result.add(error.getInstanceLocation() + " " + error.getMessage());
            }
        } catch (IOException ex) {
            result.add("schema not readable: " + schema + " (" + ex.getMessage() + ")");
        }
    }

    private static void requireObject(JsonNode node, String path, ValidationResult result) {
        if (node == null || !node.isObject()) {
            result.add(path + " must be object");
        }
    }

    private static String optionalText(JsonNode node, String field, ValidationResult result, String path) {
        if (node == null || !node.has(field)) {
            return null;
        }
        if (!node.get(field).isTextual() || node.get(field).asText().isBlank()) {
            result.add(path + " must be text");
            return null;
        }
        return node.get(field).asText();
    }

    private static String requireText(JsonNode node, String field, ValidationResult result) {
        return requireText(node, field, result, "/" + field);
    }

    private static String requireText(JsonNode node, String field, ValidationResult result, String path) {
        if (node == null || !node.has(field) || !node.get(field).isTextual() || node.get(field).asText().isBlank()) {
            result.add(path + " is required");
            return null;
        }
        return node.get(field).asText();
    }

    private static void requireConst(JsonNode node, String field, String expected, ValidationResult result) {
        String actual = requireText(node, field, result);
        if (actual != null && !expected.equals(actual)) {
            result.add("/" + field + " must be " + expected);
        }
    }

    private static void requireOneOf(JsonNode node, String field, Set<String> values, ValidationResult result) {
        String actual = requireText(node, field, result);
        if (actual != null && !values.contains(actual)) {
            result.add("/" + field + " has unsupported value " + actual);
        }
    }

    private static void requirePositiveInt(JsonNode node, String field, ValidationResult result, String path) {
        if (!node.has(field) || !node.get(field).canConvertToInt() || node.get(field).asInt() <= 0) {
            result.add(path + " must be positive integer");
        }
    }

    private static void validateOptionalPositiveInt(JsonNode node, String field, ValidationResult result, String path) {
        if (node.has(field) && (!node.get(field).canConvertToInt() || node.get(field).asInt() <= 0)) {
            result.add(path + " must be positive integer");
        }
    }

    private static void validateOptionalNonNegativeInt(JsonNode node, String field, ValidationResult result, String path) {
        if (node.has(field) && (!node.get(field).canConvertToInt() || node.get(field).asInt() < 0)) {
            result.add(path + " must be non-negative integer");
        }
    }

    private static void validateOptionalInt(JsonNode node, String field, ValidationResult result, String path) {
        if (node.has(field) && !node.get(field).canConvertToInt()) {
            result.add(path + " must be integer");
        }
    }

    private static void validateOptionalBoolean(JsonNode node, String field, ValidationResult result, String path) {
        if (node.has(field) && !node.get(field).isBoolean()) {
            result.add(path + " must be boolean");
        }
    }

    private static void validateStringArray(JsonNode node, String field, ValidationResult result, String path) {
        if (!node.has(field)) {
            return;
        }
        JsonNode values = node.get(field);
        if (!values.isArray()) {
            result.add(path + " must be array");
            return;
        }
        int index = 0;
        for (JsonNode value : values) {
            if (!value.isTextual() || value.asText().isBlank()) {
                result.add(path + "/" + index + " must be text");
            }
            index++;
        }
    }

    private static void validateStringArray(JsonNode node, String field, String itemField, ValidationResult result, String path) {
        if (!node.has(field)) {
            return;
        }
        JsonNode values = node.get(field);
        if (!values.isArray()) {
            result.add(path + " must be array");
            return;
        }
        int index = 0;
        for (JsonNode value : values) {
            if (!value.isObject()) {
                result.add(path + "/" + index + " must be object");
            } else {
                optionalText(value, itemField, result, path + "/" + index + "/" + itemField);
                optionalText(value, "side", result, path + "/" + index + "/side");
            }
            index++;
        }
    }

    private static void validatePointArray(JsonNode node, String field, int minimumSize, ValidationResult result, String path) {
        if (!node.has(field)) {
            if (minimumSize > 0) {
                result.add(path + " must contain at least " + minimumSize + " points");
            }
            return;
        }
        JsonNode points = node.get(field);
        if (!points.isArray()) {
            result.add(path + " must be array");
            return;
        }
        if (points.size() < minimumSize) {
            result.add(path + " must contain at least " + minimumSize + " points");
        }
        int index = 0;
        for (JsonNode point : points) {
            validateOptionalInt(point, "x", result, path + "/" + index + "/x");
            validateOptionalInt(point, "y", result, path + "/" + index + "/y");
            if (!hasInt(point, "x") || !hasInt(point, "y")) {
                result.add(path + "/" + index + " must provide x and y");
            }
            index++;
        }
    }

    private static boolean hasInt(JsonNode node, String field) {
        return node != null && node.has(field) && node.get(field).canConvertToInt();
    }
}
