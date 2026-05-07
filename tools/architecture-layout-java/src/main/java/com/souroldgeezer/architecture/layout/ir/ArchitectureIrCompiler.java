package com.souroldgeezer.architecture.layout.ir;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.ValidationResult;
import com.souroldgeezer.architecture.layout.schema.LayoutSchemaValidator;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ArchitectureIrCompiler {
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;

    public List<Path> compile(Path archDir) throws IOException {
        ValidationResult irValidation = new ArchitectureIrValidator().validate(archDir);
        if (!irValidation.ok()) {
            throw new IOException("invalid architecture IR: " + String.join("; ", irValidation.diagnostics()));
        }

        ArchitectureIrPaths paths = new ArchitectureIrPaths(archDir);
        JsonNode model = YamlFiles.read(paths.model());
        JsonNode views = YamlFiles.read(paths.views());
        JsonNode layout = YamlFiles.read(paths.layout());
        Map<String, JsonNode> elements = byId(model.path("elements"));
        Map<String, JsonNode> relationships = byId(model.path("relationships"));
        Map<String, JsonNode> layoutByView = layoutByView(layout);

        List<Path> requests = new ArrayList<>();
        for (JsonNode view : views.path("views")) {
            String viewId = text(view, "id");
            JsonNode layoutView = layoutByView.get(viewId);
            ObjectNode request = compileView(model, view, layoutView, elements, relationships);
            Path requestPath = paths.request(viewId);
            ValidationResult requestValidation = new LayoutSchemaValidator().validateRequest(request);
            if (!requestValidation.ok()) {
                throw new IOException("invalid compiled layout request " + viewId + ": " + String.join("; ", requestValidation.diagnostics()));
            }
            JsonFiles.write(requestPath, request);
            requests.add(requestPath);
        }
        return requests;
    }

    private static ObjectNode compileView(
            JsonNode model,
            JsonNode view,
            JsonNode layoutView,
            Map<String, JsonNode> elements,
            Map<String, JsonNode> relationships) {
        ObjectNode request = JSON.objectNode();
        String featureId = text(model.path("feature"), "id");
        String viewId = text(view, "id");
        String geometryPath = text(layoutView, "geometryPath");
        request.put("schemaVersion", "1.0");
        request.put("requestId", featureId + "-" + viewId);
        request.put("archimateTarget", "3.2");
        request.put("mode", modeFor(geometryPath));
        request.put("preserveExistingGeometry", preservesExistingGeometry(text(layoutView, "intent")));
        request.put("layoutIntent", text(layoutView, "intent"));
        request.put("selectedGeometryPath", geometryPath);

        ObjectNode requestView = request.putObject("view");
        requestView.put("id", viewId);
        requestView.put("name", text(view, "name"));
        requestView.put("viewpoint", text(view, "viewpoint"));
        requestView.put("direction", textOrDefault(view, "direction", "DOWN"));
        requestView.put("qualityTarget", textOrDefault(view, "qualityTarget", "diagram-readable"));

        Map<String, JsonNode> nodeLocks = locksByField(layoutView.path("nodeLocks"), "node");
        ArrayNode nodes = request.putArray("nodes");
        for (JsonNode viewNode : view.path("nodes")) {
            JsonNode element = elements.get(text(viewNode, "elementRef"));
            JsonNode nodeLock = nodeLocks.get(text(viewNode, "id"));
            ObjectNode node = nodes.addObject();
            node.put("id", text(viewNode, "id"));
            node.put("elementRef", text(viewNode, "elementRef"));
            node.put("type", text(element, "type"));
            node.put("semanticLayer", semanticLayer(text(element, "type")));
            node.put("semanticAspect", semanticAspect(text(element, "type")));
            node.put("label", text(element, "name"));
            node.put("width", intOrDefault(nodeLock, "width", intOrDefault(viewNode, "width", 160)));
            node.put("height", intOrDefault(nodeLock, "height", intOrDefault(viewNode, "height", 72)));
            node.put("generated", nodeLock == null);
            if (nodeLock != null) {
                node.put("x", intOrDefault(nodeLock, "x", 0));
                node.put("y", intOrDefault(nodeLock, "y", 0));
                node.put("locked", true);
            } else {
                node.put("locked", false);
            }
        }

        Map<String, JsonNode> routeLocks = locksByField(layoutView.path("routeLocks"), "connection");
        ArrayNode edges = request.putArray("edges");
        for (JsonNode viewConnection : view.path("connections")) {
            JsonNode relationship = relationships.get(text(viewConnection, "relationshipRef"));
            JsonNode routeLock = routeLocks.get(text(viewConnection, "id"));
            ObjectNode edge = edges.addObject();
            edge.put("id", text(viewConnection, "id"));
            edge.put("relationshipRef", text(viewConnection, "relationshipRef"));
            edge.put("relationshipType", text(relationship, "type"));
            edge.put("source", text(viewConnection, "source"));
            edge.put("target", text(viewConnection, "target"));
            edge.put("visible", viewConnection.path("visible").asBoolean(true));
            edge.put("priority", intOrDefault(viewConnection, "priority", 0));
            edge.put("generated", routeLock == null);
            if (routeLock != null) {
                edge.put("locked", true);
                copyPoints(edge, "priorBendpoints", routeLock.path("bendpoints"));
                if (routeLock.path("bendpoints").isArray() && routeLock.path("bendpoints").size() >= 2) {
                    edge.put("routeLocked", true);
                    copyPoints(edge, "existingRoute", routeLock.path("bendpoints"));
                }
            }
        }

        if (layoutView.has("layoutPolicy")) {
            request.set("layoutPolicy", layoutView.get("layoutPolicy").deepCopy());
        }
        ArrayNode locks = request.putArray("locks");
        appendLocks(locks, layoutView.path("nodeLocks"), "node", "node");
        appendLocks(locks, layoutView.path("routeLocks"), "connection", "edge");
        if (layoutView.has("constraints")) {
            request.set("constraints", layoutView.get("constraints").deepCopy());
        } else {
            request.set("constraints", JSON.objectNode());
        }
        return request;
    }

    private static Map<String, JsonNode> byId(JsonNode values) {
        Map<String, JsonNode> result = new LinkedHashMap<>();
        for (JsonNode value : values) {
            result.put(text(value, "id"), value);
        }
        return result;
    }

    private static Map<String, JsonNode> layoutByView(JsonNode layout) {
        Map<String, JsonNode> result = new HashMap<>();
        for (JsonNode view : layout.path("views")) {
            result.put(text(view, "view"), view);
        }
        return result;
    }

    private static Map<String, JsonNode> locksByField(JsonNode locks, String field) {
        Map<String, JsonNode> result = new HashMap<>();
        for (JsonNode lock : locks) {
            result.put(text(lock, field), lock);
        }
        return result;
    }

    private static void appendLocks(ArrayNode output, JsonNode locks, String sourceField, String targetField) {
        for (JsonNode lock : locks) {
            ObjectNode item = output.addObject();
            item.put(targetField, text(lock, sourceField));
            String reason = text(lock, "reason");
            if (reason != null) {
                item.put("reason", reason);
            }
        }
    }

    private static void copyPoints(ObjectNode target, String field, JsonNode points) {
        ArrayNode output = target.putArray(field);
        for (JsonNode point : points) {
            ObjectNode item = output.addObject();
            item.put("x", point.path("x").asInt());
            item.put("y", point.path("y").asInt());
        }
    }

    private static String modeFor(String geometryPath) {
        return switch (geometryPath) {
            case "route-repair" -> "route-repair";
            case "global-polish" -> "global-polish";
            default -> "generated-layout";
        };
    }

    private static boolean preservesExistingGeometry(String intent) {
        return "preserve-authored".equals(intent) || "route-repair-only".equals(intent);
    }

    private static String semanticLayer(String type) {
        if (type == null) {
            return "Unknown";
        }
        if (type.startsWith("Business")) {
            return "Business";
        }
        if (type.startsWith("Application")) {
            return "Application";
        }
        if (type.equals("Node")
                || type.equals("Device")
                || type.equals("SystemSoftware")
                || type.equals("TechnologyService")
                || type.equals("CommunicationNetwork")
                || type.equals("Path")
                || type.equals("Artifact")) {
            return "Technology";
        }
        if (type.equals("WorkPackage")
                || type.equals("Plateau")
                || type.equals("Gap")
                || type.equals("ImplementationEvent")
                || type.equals("Deliverable")) {
            return "Implementation & Migration";
        }
        if (type.equals("Stakeholder")
                || type.equals("Driver")
                || type.equals("Assessment")
                || type.equals("Goal")
                || type.equals("Outcome")
                || type.equals("Principle")
                || type.equals("Requirement")
                || type.equals("Constraint")
                || type.equals("Meaning")
                || type.equals("Value")) {
            return "Motivation";
        }
        return "Core";
    }

    private static String semanticAspect(String type) {
        if (type == null) {
            return "Unknown";
        }
        if (type.endsWith("Service")
                || type.endsWith("Function")
                || type.endsWith("Process")
                || type.endsWith("Interaction")
                || type.endsWith("Event")) {
            return "Behavior";
        }
        if (type.endsWith("Object") || type.equals("Artifact") || type.equals("Contract") || type.equals("Product")) {
            return "Passive";
        }
        return "Active";
    }

    private static String textOrDefault(JsonNode node, String field, String fallback) {
        String value = text(node, field);
        return value == null ? fallback : value;
    }

    private static String text(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        if (value == null || !value.isTextual() || value.asText().isBlank()) {
            return null;
        }
        return value.asText();
    }

    private static int intOrDefault(JsonNode node, String field, int fallback) {
        JsonNode value = node == null ? null : node.get(field);
        return value != null && value.canConvertToInt() ? value.asInt() : fallback;
    }
}
