package com.souroldgeezer.architecture.layout.ir;

import com.fasterxml.jackson.databind.JsonNode;
import com.souroldgeezer.architecture.layout.ValidationResult;
import com.souroldgeezer.architecture.layout.schema.LayoutSchemaValidator;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

public final class ArchitectureIrValidator {
    public ValidationResult validate(Path archDir) throws IOException {
        ValidationResult result = new ValidationResult();
        ArchitectureIrPaths paths = new ArchitectureIrPaths(archDir);
        requireReadable(paths.model(), "model", result);
        requireReadable(paths.views(), "views", result);
        requireReadable(paths.layout(), "layout", result);
        if (!result.ok()) {
            return result;
        }

        JsonNode model = YamlFiles.read(paths.model());
        JsonNode views = YamlFiles.read(paths.views());
        JsonNode layout = YamlFiles.read(paths.layout());
        LayoutSchemaValidator schemaValidator = new LayoutSchemaValidator();
        addPrefixed(result, "model", schemaValidator.validateArchitectureModel(model));
        addPrefixed(result, "views", schemaValidator.validateArchitectureViews(views));
        addPrefixed(result, "layout", schemaValidator.validateArchitectureLayout(layout));
        validateCrossReferences(model, views, layout, result);
        return result;
    }

    private static void requireReadable(Path path, String label, ValidationResult result) {
        if (!Files.isRegularFile(path) || !Files.isReadable(path)) {
            result.add(label + ": required file is not readable: " + path);
        }
    }

    private static void addPrefixed(ValidationResult target, String prefix, ValidationResult source) {
        for (String diagnostic : source.diagnostics()) {
            target.add(prefix + ": " + diagnostic);
        }
    }

    private static void validateCrossReferences(JsonNode model, JsonNode views, JsonNode layout, ValidationResult result) {
        Set<String> elementIds = ids(model.path("elements"), "element", result);
        Set<String> relationshipIds = ids(model.path("relationships"), "relationship", result);
        validateRelationshipEndpoints(model, elementIds, result);

        Map<String, Set<String>> viewNodeIds = new LinkedHashMap<>();
        Map<String, Set<String>> viewConnectionIds = new LinkedHashMap<>();
        Set<String> viewIds = new HashSet<>();
        for (JsonNode view : views.path("views")) {
            String viewId = text(view, "id");
            if (viewId == null) {
                continue;
            }
            if (!viewIds.add(viewId)) {
                result.add("cross-ref: duplicate view id " + viewId);
            }
            Map<String, String> nodeElementRefs = validateViewNodes(view, viewId, elementIds, result);
            viewNodeIds.put(viewId, nodeElementRefs.keySet());
            Set<String> connectionIds = validateViewConnections(view, viewId, relationshipIds, nodeElementRefs.keySet(), result);
            viewConnectionIds.put(viewId, connectionIds);
            validateHiddenRelationships(view, viewId, relationshipIds, result);
        }
        validateLayout(layout, viewIds, viewNodeIds, viewConnectionIds, result);
    }

    private static Set<String> ids(JsonNode values, String label, ValidationResult result) {
        Set<String> ids = new HashSet<>();
        if (!values.isArray()) {
            return ids;
        }
        for (JsonNode value : values) {
            String id = text(value, "id");
            if (id == null) {
                continue;
            }
            if (!ids.add(id)) {
                result.add("cross-ref: duplicate " + label + " id " + id);
            }
        }
        return ids;
    }

    private static void validateRelationshipEndpoints(JsonNode model, Set<String> elementIds, ValidationResult result) {
        for (JsonNode relationship : model.path("relationships")) {
            String id = text(relationship, "id");
            validateElementReference("relationship " + id + " source", text(relationship, "source"), elementIds, result);
            validateElementReference("relationship " + id + " target", text(relationship, "target"), elementIds, result);
        }
    }

    private static Map<String, String> validateViewNodes(JsonNode view, String viewId, Set<String> elementIds, ValidationResult result) {
        Map<String, String> nodeElementRefs = new LinkedHashMap<>();
        for (JsonNode node : view.path("nodes")) {
            String nodeId = text(node, "id");
            if (nodeId == null) {
                continue;
            }
            if (nodeElementRefs.containsKey(nodeId)) {
                result.add("cross-ref: view " + viewId + " duplicate node id " + nodeId);
            }
            String elementRef = text(node, "elementRef");
            nodeElementRefs.put(nodeId, elementRef);
            validateElementReference("view " + viewId + " node " + nodeId + " elementRef", elementRef, elementIds, result);
        }
        return nodeElementRefs;
    }

    private static Set<String> validateViewConnections(
            JsonNode view,
            String viewId,
            Set<String> relationshipIds,
            Set<String> nodeIds,
            ValidationResult result) {
        Set<String> connectionIds = new HashSet<>();
        for (JsonNode connection : view.path("connections")) {
            String connectionId = text(connection, "id");
            if (connectionId == null) {
                continue;
            }
            if (!connectionIds.add(connectionId)) {
                result.add("cross-ref: view " + viewId + " duplicate connection id " + connectionId);
            }
            String relationshipRef = text(connection, "relationshipRef");
            if (relationshipRef != null && !relationshipIds.contains(relationshipRef)) {
                result.add("cross-ref: view " + viewId + " connection " + connectionId + " references missing relationship " + relationshipRef);
            }
            validateNodeReference("view " + viewId + " connection " + connectionId + " source", text(connection, "source"), nodeIds, result);
            validateNodeReference("view " + viewId + " connection " + connectionId + " target", text(connection, "target"), nodeIds, result);
        }
        return connectionIds;
    }

    private static void validateHiddenRelationships(JsonNode view, String viewId, Set<String> relationshipIds, ValidationResult result) {
        for (JsonNode hidden : view.path("hiddenRelationships")) {
            String relationshipRef = text(hidden, "relationshipRef");
            if (relationshipRef != null && !relationshipIds.contains(relationshipRef)) {
                result.add("cross-ref: view " + viewId + " hidden relationship references missing relationship " + relationshipRef);
            }
        }
    }

    private static void validateLayout(
            JsonNode layout,
            Set<String> viewIds,
            Map<String, Set<String>> viewNodeIds,
            Map<String, Set<String>> viewConnectionIds,
            ValidationResult result) {
        Set<String> seenViews = new HashSet<>();
        for (JsonNode layoutView : layout.path("views")) {
            String viewId = text(layoutView, "view");
            if (viewId == null) {
                continue;
            }
            if (!seenViews.add(viewId)) {
                result.add("cross-ref: duplicate layout view " + viewId);
            }
            if (!viewIds.contains(viewId)) {
                result.add("cross-ref: layout references missing view " + viewId);
                continue;
            }
            Set<String> nodeIds = viewNodeIds.getOrDefault(viewId, Set.of());
            Set<String> connectionIds = viewConnectionIds.getOrDefault(viewId, Set.of());
            validateNodeLocks(layoutView, viewId, nodeIds, result);
            validateRouteLocks(layoutView, viewId, connectionIds, result);
            validateLayoutPolicy(layoutView, viewId, nodeIds, connectionIds, result);
        }
    }

    private static void validateNodeLocks(JsonNode layoutView, String viewId, Set<String> nodeIds, ValidationResult result) {
        for (JsonNode lock : layoutView.path("nodeLocks")) {
            validateNodeReference("layout view " + viewId + " nodeLock", text(lock, "node"), nodeIds, result);
        }
    }

    private static void validateRouteLocks(JsonNode layoutView, String viewId, Set<String> connectionIds, ValidationResult result) {
        for (JsonNode lock : layoutView.path("routeLocks")) {
            String connection = text(lock, "connection");
            if (connection != null && !connectionIds.contains(connection)) {
                result.add("cross-ref: layout view " + viewId + " routeLock references missing connection " + connection);
            }
        }
    }

    private static void validateLayoutPolicy(
            JsonNode layoutView,
            String viewId,
            Set<String> nodeIds,
            Set<String> connectionIds,
            ValidationResult result) {
        JsonNode policy = layoutView.path("layoutPolicy");
        if (!policy.isObject()) {
            return;
        }
        for (JsonNode constraint : policy.path("constraints")) {
            validateArrayReferences("layout view " + viewId + " policy nodeIds", constraint.path("nodeIds"), nodeIds, result);
            validateArrayReferences("layout view " + viewId + " policy edgeIds", constraint.path("edgeIds"), connectionIds, result);
        }
    }

    private static void validateArrayReferences(String label, JsonNode values, Set<String> allowed, ValidationResult result) {
        if (!values.isArray()) {
            return;
        }
        for (JsonNode value : values) {
            if (value.isTextual() && !allowed.contains(value.asText())) {
                result.add("cross-ref: " + label + " references missing id " + value.asText());
            }
        }
    }

    private static void validateElementReference(String label, String value, Set<String> allowed, ValidationResult result) {
        if (value != null && !allowed.contains(value)) {
            result.add("cross-ref: " + label + " references missing element " + value);
        }
    }

    private static void validateNodeReference(String label, String value, Set<String> allowed, ValidationResult result) {
        if (value != null && !allowed.contains(value)) {
            result.add("cross-ref: " + label + " references missing node " + value);
        }
    }

    private static String text(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || !value.isTextual() || value.asText().isBlank()) {
            return null;
        }
        return value.asText();
    }
}
