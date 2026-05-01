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
import java.util.HashSet;
import java.util.List;
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
        for (JsonNode node : request.get("nodes")) {
            String id = requireText(node, "id", result, "/nodes/id");
            if (id != null && !nodeIds.add(id)) {
                result.add("duplicate node id " + id);
            }
            requirePositiveInt(node, "width", result, "/nodes/" + id + "/width");
            requirePositiveInt(node, "height", result, "/nodes/" + id + "/height");
        }
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
            }
        }
        if (!request.has("constraints") || !request.get("constraints").isObject()) {
            result.add("/constraints is required");
        }
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
}
