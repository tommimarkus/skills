package com.souroldgeezer.architecture.layout;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

public final class OefMaterializer {
    public ValidationResult materialize(Path oefPath, String viewId, JsonNode layoutResult, Path outPath, Options options) throws IOException {
        ValidationResult result = new ValidationResult();
        try {
            Document document = parse(oefPath);
            Element view = findByIdentifier(document, "view", viewId);
            if (view == null) {
                result.add("view not found: " + viewId);
                return result;
            }

            Map<String, Element> nodes = descendantsByIdentifier(view, "node");
            Map<String, Element> connections = descendantsByIdentifier(view, "connection");
            materializeNodes(layoutResult, options, nodes, result);
            materializeConnections(document, layoutResult, options, connections, result);
            if (!result.ok()) {
                return result;
            }

            Path parent = outPath.toAbsolutePath().getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            write(document, outPath);
            return result;
        } catch (ParserConfigurationException | SAXException | TransformerException ex) {
            throw new IOException(ex);
        }
    }

    private static Document parse(Path oefPath) throws ParserConfigurationException, IOException, SAXException {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        return factory.newDocumentBuilder().parse(oefPath.toFile());
    }

    private static void write(Document document, Path outPath) throws TransformerException {
        TransformerFactory factory = TransformerFactory.newInstance();
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        var transformer = factory.newTransformer();
        transformer.setOutputProperty(OutputKeys.INDENT, "yes");
        transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
        transformer.transform(new DOMSource(document), new StreamResult(outPath.toFile()));
    }

    private static void materializeNodes(JsonNode layoutResult, Options options, Map<String, Element> nodes, ValidationResult result) {
        for (JsonNode geometry : layoutResult.path("nodeGeometry")) {
            String id = geometry.path("id").asText();
            Element node = nodes.get(id);
            if (node == null) {
                result.add("node geometry does not resolve to OEF node: " + id);
                continue;
            }
            if (options.preserveLockedNodes() && geometry.path("locked").asBoolean(false)) {
                continue;
            }
            setInt(node, "x", geometry.path("x").asInt(), options);
            setInt(node, "y", geometry.path("y").asInt(), options);
            setInt(node, "w", geometry.path("w").asInt(), options);
            setInt(node, "h", geometry.path("h").asInt(), options);
        }
    }

    private static void materializeConnections(Document document, JsonNode layoutResult, Options options, Map<String, Element> connections, ValidationResult result) {
        for (JsonNode edge : layoutResult.path("edges")) {
            String id = edge.path("id").asText();
            Element connection = connections.get(id);
            if (connection == null) {
                result.add("edge route does not resolve to OEF connection: " + id);
                continue;
            }
            removeBendpoints(connection);
            for (JsonNode bendpoint : edge.path("bendpoints")) {
                Element element = document.createElementNS(connection.getNamespaceURI(), "bendpoint");
                element.setAttribute("x", Integer.toString(snap(bendpoint.path("x").asInt(), options.snapGrid())));
                element.setAttribute("y", Integer.toString(snap(bendpoint.path("y").asInt(), options.snapGrid())));
                connection.appendChild(element);
            }
        }
    }

    private static Element findByIdentifier(Document document, String localName, String id) {
        NodeList all = document.getElementsByTagNameNS("*", localName);
        for (int index = 0; index < all.getLength(); index++) {
            Node node = all.item(index);
            if (node instanceof Element element && id.equals(element.getAttribute("identifier"))) {
                return element;
            }
        }
        return null;
    }

    private static Map<String, Element> descendantsByIdentifier(Element root, String localName) {
        Map<String, Element> result = new LinkedHashMap<>();
        collectDescendants(root, localName, result);
        return result;
    }

    private static void collectDescendants(Element root, String localName, Map<String, Element> result) {
        NodeList children = root.getChildNodes();
        for (int index = 0; index < children.getLength(); index++) {
            Node child = children.item(index);
            if (child instanceof Element element) {
                if (localName.equals(element.getLocalName())) {
                    result.put(element.getAttribute("identifier"), element);
                }
                collectDescendants(element, localName, result);
            }
        }
    }

    private static void removeBendpoints(Element connection) {
        NodeList children = connection.getChildNodes();
        for (int index = children.getLength() - 1; index >= 0; index--) {
            Node child = children.item(index);
            if (child instanceof Element element && "bendpoint".equals(element.getLocalName())) {
                connection.removeChild(child);
            }
        }
    }

    private static void setInt(Element element, String attribute, int value, Options options) {
        element.setAttribute(attribute, Integer.toString(snap(value, options.snapGrid())));
    }

    private static int snap(int value, int grid) {
        if (grid <= 0) {
            return value;
        }
        return Math.round((float) value / grid) * grid;
    }

    public record Options(int snapGrid, boolean preserveLockedNodes) {
    }
}
