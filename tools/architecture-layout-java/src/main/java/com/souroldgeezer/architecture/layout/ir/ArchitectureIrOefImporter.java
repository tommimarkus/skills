package com.souroldgeezer.architecture.layout.ir;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.oef.OefDocument;
import java.io.IOException;
import java.nio.file.Path;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public final class ArchitectureIrOefImporter {
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;

    public void importOef(Path oef, Path archDir) throws IOException {
        Document document = OefDocument.parse(oef);
        Element model = document.getDocumentElement();
        YamlFiles.write(new ArchitectureIrPaths(archDir).model(), modelYaml(model, document));
        YamlFiles.write(new ArchitectureIrPaths(archDir).views(), viewsYaml(document));
        YamlFiles.write(new ArchitectureIrPaths(archDir).layout(), layoutYaml(document));
    }

    private static ObjectNode modelYaml(Element model, Document document) {
        ObjectNode root = JSON.objectNode();
        root.put("schemaVersion", "1.0");
        ObjectNode feature = root.putObject("feature");
        feature.put("id", nonBlank(OefDocument.identifier(model), "imported-architecture"));
        feature.put("name", nonBlank(OefDocument.textOfFirst(model, "name"), "Imported Architecture"));
        String documentation = OefDocument.textOfFirst(model, "documentation");
        if (!documentation.isBlank()) {
            feature.put("documentation", documentation);
        }
        feature.put("creator", "architecture-design oef-import");
        root.put("archimateTarget", "3.2");

        ArrayNode elements = root.putArray("elements");
        for (Element element : OefDocument.elements(document, "element")) {
            ObjectNode item = elements.addObject();
            item.put("id", OefDocument.identifier(element));
            item.put("type", OefDocument.archimateType(element));
            item.put("name", nonBlank(OefDocument.textOfFirst(element, "name"), OefDocument.identifier(element)));
            String elementDocumentation = OefDocument.textOfFirst(element, "documentation");
            if (!elementDocumentation.isBlank()) {
                item.put("documentation", elementDocumentation);
            }
            item.put("authority", "architect-approved");
        }

        ArrayNode relationships = root.putArray("relationships");
        for (Element relationship : OefDocument.elements(document, "relationship")) {
            ObjectNode item = relationships.addObject();
            item.put("id", OefDocument.identifier(relationship));
            item.put("type", OefDocument.archimateType(relationship));
            item.put("source", relationship.getAttribute("source"));
            item.put("target", relationship.getAttribute("target"));
            String relationshipDocumentation = OefDocument.textOfFirst(relationship, "documentation");
            if (!relationshipDocumentation.isBlank()) {
                item.put("documentation", relationshipDocumentation);
            }
        }
        return root;
    }

    private static ObjectNode viewsYaml(Document document) {
        ObjectNode root = JSON.objectNode();
        root.put("schemaVersion", "1.0");
        ArrayNode views = root.putArray("views");
        for (Element view : OefDocument.elements(document, "view")) {
            ObjectNode item = views.addObject();
            item.put("id", OefDocument.identifier(view));
            item.put("name", nonBlank(OefDocument.textOfFirst(view, "name"), OefDocument.identifier(view)));
            item.put("viewpoint", nonBlank(view.getAttribute("viewpoint"), "Application Cooperation"));
            item.put("qualityTarget", "review-ready");
            item.put("direction", "DOWN");
            String documentation = OefDocument.textOfFirst(view, "documentation");
            if (!documentation.isBlank()) {
                item.put("documentation", documentation);
            }
            ArrayNode nodes = item.putArray("nodes");
            for (Element node : OefDocument.elements(view, "node")) {
                ObjectNode nodeItem = nodes.addObject();
                nodeItem.put("id", OefDocument.identifier(node));
                nodeItem.put("elementRef", node.getAttribute("elementRef"));
                putOptionalInt(nodeItem, "width", node.getAttribute("w"));
                putOptionalInt(nodeItem, "height", node.getAttribute("h"));
            }
            ArrayNode connections = item.putArray("connections");
            for (Element connection : OefDocument.elements(view, "connection")) {
                ObjectNode connectionItem = connections.addObject();
                connectionItem.put("id", OefDocument.identifier(connection));
                connectionItem.put("relationshipRef", connection.getAttribute("relationshipRef"));
                connectionItem.put("source", connection.getAttribute("source"));
                connectionItem.put("target", connection.getAttribute("target"));
            }
        }
        return root;
    }

    private static ObjectNode layoutYaml(Document document) {
        ObjectNode root = JSON.objectNode();
        root.put("schemaVersion", "1.0");
        ArrayNode views = root.putArray("views");
        for (Element view : OefDocument.elements(document, "view")) {
            ObjectNode item = views.addObject();
            item.put("view", OefDocument.identifier(view));
            item.put("intent", "preserve-authored");
            item.put("geometryPath", "route-repair");
            ArrayNode nodeLocks = item.putArray("nodeLocks");
            for (Element node : OefDocument.elements(view, "node")) {
                ObjectNode lock = nodeLocks.addObject();
                lock.put("node", OefDocument.identifier(node));
                putRequiredInt(lock, "x", node.getAttribute("x"));
                putRequiredInt(lock, "y", node.getAttribute("y"));
                putRequiredInt(lock, "width", node.getAttribute("w"));
                putRequiredInt(lock, "height", node.getAttribute("h"));
                lock.put("source", "architect-edited-oef");
                lock.put("reason", "imported from OEF");
            }
            ArrayNode routeLocks = item.putArray("routeLocks");
            for (Element connection : OefDocument.elements(view, "connection")) {
                var bendpoints = OefDocument.directChildren(connection, "bendpoint");
                if (bendpoints.isEmpty()) {
                    continue;
                }
                ObjectNode lock = routeLocks.addObject();
                lock.put("connection", OefDocument.identifier(connection));
                ArrayNode points = lock.putArray("bendpoints");
                for (Element bendpoint : bendpoints) {
                    ObjectNode point = points.addObject();
                    putRequiredInt(point, "x", bendpoint.getAttribute("x"));
                    putRequiredInt(point, "y", bendpoint.getAttribute("y"));
                }
                lock.put("source", "architect-edited-oef");
                lock.put("reason", "imported from OEF");
            }
        }
        return root;
    }

    private static void putOptionalInt(ObjectNode node, String field, String value) {
        if (value != null && !value.isBlank()) {
            putRequiredInt(node, field, value);
        }
    }

    private static void putRequiredInt(ObjectNode node, String field, String value) {
        node.put(field, Integer.parseInt(value));
    }

    private static String nonBlank(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value;
    }
}
