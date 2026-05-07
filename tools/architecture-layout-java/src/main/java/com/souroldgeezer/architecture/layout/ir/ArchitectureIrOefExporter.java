package com.souroldgeezer.architecture.layout.ir;

import com.fasterxml.jackson.databind.JsonNode;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.ValidationResult;
import com.souroldgeezer.architecture.layout.oef.OefDocument;
import com.souroldgeezer.architecture.layout.schema.LayoutSchemaValidator;
import java.io.IOException;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public final class ArchitectureIrOefExporter {
    private static final String ARCHIMATE_NS = "http://www.opengroup.org/xsd/archimate/3.0/";
    private static final String DC_NS = "http://purl.org/dc/elements/1.1/";

    public void export(Path archDir, Path out) throws IOException {
        ValidationResult irValidation = new ArchitectureIrValidator().validate(archDir);
        if (!irValidation.ok()) {
            throw new IOException("invalid architecture IR: " + String.join("; ", irValidation.diagnostics()));
        }
        ArchitectureIrPaths paths = new ArchitectureIrPaths(archDir);
        JsonNode model = YamlFiles.read(paths.model());
        JsonNode views = YamlFiles.read(paths.views());
        Document document = newDocument();
        Element root = document.createElementNS(ARCHIMATE_NS, "model");
        document.appendChild(root);
        root.setAttribute("identifier", text(model.path("feature"), "id"));
        root.setAttributeNS(XMLConstants.W3C_XML_SCHEMA_INSTANCE_NS_URI, "xsi:schemaLocation",
                ARCHIMATE_NS + " http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd");

        appendText(document, root, "name", text(model.path("feature"), "name"));
        appendText(document, root, "documentation", text(model.path("feature"), "documentation"));
        appendMetadata(document, root, model);
        appendElements(document, root, model);
        appendRelationships(document, root, model);
        appendOrganizations(document, root, model);
        root.appendChild(document.createElementNS(ARCHIMATE_NS, "propertyDefinitions"));
        appendViews(document, root, views, paths);
        OefDocument.write(document, out);
    }

    private static Document newDocument() throws IOException {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            return factory.newDocumentBuilder().newDocument();
        } catch (ParserConfigurationException ex) {
            throw new IOException(ex);
        }
    }

    private static void appendMetadata(Document document, Element root, JsonNode model) {
        Element metadata = document.createElementNS(ARCHIMATE_NS, "metadata");
        appendText(document, metadata, "schema", DC_NS);
        appendText(document, metadata, "schemaversion", "1.1");
        Element title = document.createElementNS(DC_NS, "dc:title");
        title.setTextContent(text(model.path("feature"), "name"));
        metadata.appendChild(title);
        Element creator = document.createElementNS(DC_NS, "dc:creator");
        creator.setTextContent(textOrDefault(model.path("feature"), "creator", "architecture-design"));
        metadata.appendChild(creator);
        root.appendChild(metadata);
    }

    private static void appendElements(Document document, Element root, JsonNode model) {
        Element elements = document.createElementNS(ARCHIMATE_NS, "elements");
        for (JsonNode item : model.path("elements")) {
            Element element = document.createElementNS(ARCHIMATE_NS, "element");
            element.setAttribute("identifier", text(item, "id"));
            element.setAttributeNS(XMLConstants.W3C_XML_SCHEMA_INSTANCE_NS_URI, "xsi:type", text(item, "type"));
            appendText(document, element, "name", text(item, "name"));
            if (hasText(item, "documentation")) {
                appendText(document, element, "documentation", text(item, "documentation"));
            }
            elements.appendChild(element);
        }
        root.appendChild(elements);
    }

    private static void appendRelationships(Document document, Element root, JsonNode model) {
        Element relationships = document.createElementNS(ARCHIMATE_NS, "relationships");
        for (JsonNode item : model.path("relationships")) {
            Element relationship = document.createElementNS(ARCHIMATE_NS, "relationship");
            relationship.setAttribute("identifier", text(item, "id"));
            relationship.setAttribute("source", text(item, "source"));
            relationship.setAttribute("target", text(item, "target"));
            relationship.setAttributeNS(XMLConstants.W3C_XML_SCHEMA_INSTANCE_NS_URI, "xsi:type", text(item, "type"));
            if (hasText(item, "documentation")) {
                appendText(document, relationship, "documentation", text(item, "documentation"));
            }
            relationships.appendChild(relationship);
        }
        root.appendChild(relationships);
    }

    private static void appendOrganizations(Document document, Element root, JsonNode model) {
        Element organizations = document.createElementNS(ARCHIMATE_NS, "organizations");
        Element item = document.createElementNS(ARCHIMATE_NS, "item");
        appendText(document, item, "label", "Elements");
        for (JsonNode element : model.path("elements")) {
            Element ref = document.createElementNS(ARCHIMATE_NS, "item");
            ref.setAttribute("identifierRef", text(element, "id"));
            item.appendChild(ref);
        }
        organizations.appendChild(item);
        root.appendChild(organizations);
    }

    private static void appendViews(Document document, Element root, JsonNode views, ArchitectureIrPaths paths) throws IOException {
        Element viewsElement = document.createElementNS(ARCHIMATE_NS, "views");
        Element diagrams = document.createElementNS(ARCHIMATE_NS, "diagrams");
        LayoutSchemaValidator validator = new LayoutSchemaValidator();
        for (JsonNode view : views.path("views")) {
            String viewId = text(view, "id");
            JsonNode result = JsonFiles.read(paths.result(viewId));
            ValidationResult resultValidation = validator.validateResult(result);
            if (!resultValidation.ok()) {
                throw new IOException("invalid layout result for " + viewId + ": " + String.join("; ", resultValidation.diagnostics()));
            }
            diagrams.appendChild(viewElement(document, view, result));
        }
        viewsElement.appendChild(diagrams);
        root.appendChild(viewsElement);
    }

    private static Element viewElement(Document document, JsonNode view, JsonNode result) {
        Element viewElement = document.createElementNS(ARCHIMATE_NS, "view");
        viewElement.setAttribute("identifier", text(view, "id"));
        viewElement.setAttributeNS(XMLConstants.W3C_XML_SCHEMA_INSTANCE_NS_URI, "xsi:type", "Diagram");
        viewElement.setAttribute("viewpoint", text(view, "viewpoint"));
        appendText(document, viewElement, "name", text(view, "name"));
        if (hasText(view, "documentation")) {
            appendText(document, viewElement, "documentation", text(view, "documentation"));
        }

        Map<String, JsonNode> geometry = byId(result.path("nodeGeometry"));
        for (JsonNode node : view.path("nodes")) {
            JsonNode nodeGeometry = geometry.get(text(node, "id"));
            Element element = document.createElementNS(ARCHIMATE_NS, "node");
            element.setAttribute("identifier", text(node, "id"));
            element.setAttribute("elementRef", text(node, "elementRef"));
            element.setAttributeNS(XMLConstants.W3C_XML_SCHEMA_INSTANCE_NS_URI, "xsi:type", "Element");
            element.setAttribute("x", nodeGeometry.path("x").asText());
            element.setAttribute("y", nodeGeometry.path("y").asText());
            element.setAttribute("w", nodeGeometry.path("w").asText());
            element.setAttribute("h", nodeGeometry.path("h").asText());
            viewElement.appendChild(element);
        }

        Map<String, JsonNode> routes = byId(result.path("edges"));
        for (JsonNode connection : view.path("connections")) {
            JsonNode route = routes.get(text(connection, "id"));
            Element element = document.createElementNS(ARCHIMATE_NS, "connection");
            element.setAttribute("identifier", text(connection, "id"));
            element.setAttribute("relationshipRef", text(connection, "relationshipRef"));
            element.setAttribute("source", text(connection, "source"));
            element.setAttribute("target", text(connection, "target"));
            element.setAttributeNS(XMLConstants.W3C_XML_SCHEMA_INSTANCE_NS_URI, "xsi:type", "Relationship");
            for (JsonNode bendpoint : route.path("bendpoints")) {
                Element point = document.createElementNS(ARCHIMATE_NS, "bendpoint");
                point.setAttribute("x", bendpoint.path("x").asText());
                point.setAttribute("y", bendpoint.path("y").asText());
                element.appendChild(point);
            }
            viewElement.appendChild(element);
        }
        return viewElement;
    }

    private static Map<String, JsonNode> byId(JsonNode values) {
        Map<String, JsonNode> result = new LinkedHashMap<>();
        for (JsonNode value : values) {
            result.put(text(value, "id"), value);
        }
        return result;
    }

    private static Element appendText(Document document, Element parent, String name, String text) {
        Element element = document.createElementNS(ARCHIMATE_NS, name);
        element.setTextContent(text == null ? "" : text);
        parent.appendChild(element);
        return element;
    }

    private static boolean hasText(JsonNode node, String field) {
        return text(node, field) != null;
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
}
