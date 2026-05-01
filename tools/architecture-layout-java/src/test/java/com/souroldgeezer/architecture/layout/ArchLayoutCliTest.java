package com.souroldgeezer.architecture.layout;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.xml.parsers.DocumentBuilderFactory;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

class ArchLayoutCliTest {
    @TempDir
    Path tempDir;

    @Test
    void versionCommandPrintsDeterministicNameAndExitsZero() {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        int exitCode = new ArchLayoutCli(new PrintStream(out), new PrintStream(new ByteArrayOutputStream()))
                .execute("--version");

        assertEquals(0, exitCode);
        assertTrue(out.toString().contains("arch-layout 0.25.1"));
    }

    @Test
    void validationCommandsAcceptValidFixturesAndRejectInvalidFixtures() {
        assertEquals(0, cli().execute("validate-request", "--request", fixture("layout-contract/valid-service-realization.request.json").toString()));
        assertEquals(1, cli().execute("validate-request", "--request", fixture("layout-contract/invalid-missing-view.request.json").toString()));
        assertEquals(1, cli().execute("validate-request", "--request", fixture("layout-contract/invalid-archimate-4.request.json").toString()));
        assertEquals(1, cli().execute("validate-request", "--request", fixture("layout-contract/invalid-edge-endpoint.request.json").toString()));

        assertEquals(0, cli().execute("validate-result", "--result", fixture("layout-contract/valid-service-realization.result.json").toString()));
        assertEquals(1, cli().execute("validate-result", "--result", fixture("layout-contract/invalid-missing-node-geometry.result.json").toString()));
        assertEquals(1, cli().execute("validate-result", "--result", fixture("layout-contract/invalid-missing-backend.result.json").toString()));
        assertEquals(1, cli().execute("validate-result", "--result", fixture("layout-contract/invalid-edge-without-route-status.result.json").toString()));
    }

    @Test
    void validationCommandsExposeRichRequestContractAndRejectContradictions() {
        assertEquals(0, cli().execute("validate-request", "--request", fixture("layout-contract/valid-rich-layout-contract.request.json").toString()));
        assertEquals(1, cli().execute("validate-request", "--request", fixture("layout-contract/invalid-missing-parent.request.json").toString()));
        assertEquals(1, cli().execute("validate-request", "--request", fixture("layout-contract/invalid-locked-node-without-coordinates.request.json").toString()));
        assertEquals(1, cli().execute("validate-request", "--request", fixture("layout-contract/invalid-route-locked-without-existing-route.request.json").toString()));
    }

    @Test
    void validateResultStrictFailsWarningStateWhileNonStrictKeepsSchemaMode() {
        Path warningResult = fixture("materialize-oef/warning.result.json");
        ByteArrayOutputStream err = new ByteArrayOutputStream();

        assertEquals(0, cli().execute("validate-result", "--result", warningResult.toString()));
        assertEquals(1, new ArchLayoutCli(new PrintStream(new ByteArrayOutputStream()), new PrintStream(err))
                .execute("validate-result", "--result", warningResult.toString(), "--strict"));
        assertTrue(err.toString().contains("layoutResult validation state is warning"));
    }

    @Test
    void validateResultStrictCanGateOnMetricThresholds() throws Exception {
        ObjectNode result = (ObjectNode) JsonFiles.read(fixture("layout-contract/valid-service-realization.result.json")).deepCopy();
        ((ObjectNode) result.path("metrics")).put("connectorNodeIntersections", 1);
        Path resultPath = tempDir.resolve("quality-warning.result.json");
        JsonFiles.write(resultPath, result);
        ByteArrayOutputStream err = new ByteArrayOutputStream();

        assertEquals(0, cli().execute("validate-result", "--result", resultPath.toString(), "--strict"));
        assertEquals(1, new ArchLayoutCli(new PrintStream(new ByteArrayOutputStream()), new PrintStream(err))
                .execute(
                        "validate-result",
                        "--result", resultPath.toString(),
                        "--strict",
                        "--max-connector-node-intersections", "0"));
        assertTrue(err.toString().contains("connectorNodeIntersections=1 exceeds 0"));
    }

    @Test
    void layoutElkProducesSchemaValidDeterministicResult() throws Exception {
        Path first = tempDir.resolve("first.json");
        Path second = tempDir.resolve("second.json");

        assertEquals(0, cli().execute("layout-elk", "--request", fixture("layout-elk-java/service-realization.request.json").toString(), "--result", first.toString()));
        assertEquals(0, cli().execute("layout-elk", "--request", fixture("layout-elk-java/service-realization.request.json").toString(), "--result", second.toString()));
        assertEquals(0, cli().execute("validate-result", "--result", first.toString()));
        assertEquals(Files.readString(first), Files.readString(second));

        JsonNode result = JsonFiles.read(first);
        assertEquals("elk-layered", result.path("backend").path("name").asText());
        assertTrue(result.path("metrics").has("connectorNodeIntersections"));
    }

    @Test
    void unsupportedCapabilityMapIsCappedNotPretendedSuccessful() throws Exception {
        Path resultPath = tempDir.resolve("capability.json");

        assertEquals(0, cli().execute("layout-elk", "--request", fixture("layout-elk-java/unsupported-capability-map.request.json").toString(), "--result", resultPath.toString()));

        JsonNode result = JsonFiles.read(resultPath);
        assertEquals("capped", result.path("readiness").asText());
        assertEquals("LAYOUT_UNSUPPORTED_VIEWPOINT", result.path("warnings").get(0).path("code").asText());
    }

    @Test
    void layoutElkRestoresLockedNodeCoordinatesAndCapsReadiness() throws Exception {
        Path resultPath = tempDir.resolve("locked.json");

        assertEquals(0, cli().execute("layout-elk", "--request", fixture("layout-elk-java/locked-node-warning.request.json").toString(), "--result", resultPath.toString()));

        JsonNode result = JsonFiles.read(resultPath);
        assertEquals(300, node(result, "locked").path("x").asInt());
        assertEquals(300, node(result, "locked").path("y").asInt());
        assertEquals("capped", result.path("readiness").asText());
        assertTrue(result.path("warnings").toString().contains("LAYOUT_LOCKED_NODE_RESTORED"));
    }

    @Test
    void routeRepairPreservesNodeCoordinatesAndFlagsInvalidLockedRoutes() throws Exception {
        Path repaired = tempDir.resolve("route.json");
        Path lockedInvalid = tempDir.resolve("locked-invalid.json");

        assertEquals(0, cli().execute("route-repair", "--request", fixture("route-repair/simple-obstacle.request.json").toString(), "--result", repaired.toString()));
        JsonNode result = JsonFiles.read(repaired);
        assertEquals(40, node(result, "source").path("x").asInt());
        assertEquals(0, result.path("metrics").path("connectorNodeIntersections").asInt());

        assertEquals(0, cli().execute("route-repair", "--request", fixture("route-repair/locked-route-invalid.request.json").toString(), "--result", lockedInvalid.toString()));
        JsonNode invalid = JsonFiles.read(lockedInvalid);
        assertEquals("locked-invalid", invalid.path("edges").get(0).path("route").path("status").asText());
        assertTrue(invalid.path("warnings").toString().contains("LAYOUT_LOCKED_ROUTE_INVALID"));
    }

    @Test
    void connectorNodeIntersectionWarningsCarryMachineReadableGeometryEvidence() throws Exception {
        Path lockedInvalid = tempDir.resolve("locked-invalid.json");

        assertEquals(0, cli().execute("route-repair", "--request", fixture("route-repair/locked-route-invalid.request.json").toString(), "--result", lockedInvalid.toString()));

        JsonNode warning = warning(JsonFiles.read(lockedInvalid), "LAYOUT_CONNECTOR_NODE_INTERSECTION");
        assertEquals("locked", warning.path("edgeId").asText());
        assertEquals("obstacle", warning.path("nodeId").asText());
        assertEquals("unrelated", warning.path("relationship").asText());
        assertEquals(140, warning.path("segment").path("x1").asInt());
        assertEquals(110, warning.path("segment").path("y1").asInt());
        assertEquals(420, warning.path("segment").path("x2").asInt());
        assertEquals(110, warning.path("segment").path("y2").asInt());
        assertEquals(220, warning.path("nodeBounds").path("x").asInt());
        assertEquals(60, warning.path("nodeBounds").path("y").asInt());
        assertEquals(100, warning.path("nodeBounds").path("w").asInt());
        assertEquals(100, warning.path("nodeBounds").path("h").asInt());
    }

    @Test
    void overlapWarningsCarryBothNodeIdsAndRectangles() throws Exception {
        Path request = tempDir.resolve("overlap.request.json");
        Path result = tempDir.resolve("overlap.result.json");
        Files.writeString(request, """
                {
                  "schemaVersion": "1.0",
                  "requestId": "overlap-evidence",
                  "archimateTarget": "3.2",
                  "mode": "route-repair",
                  "view": {
                    "id": "view",
                    "name": "Overlap Evidence",
                    "viewpoint": "Application Cooperation",
                    "direction": "RIGHT",
                    "qualityTarget": "diagram-readable"
                  },
                  "nodes": [
                    { "id": "first", "width": 120, "height": 70, "x": 40, "y": 40 },
                    { "id": "second", "width": 100, "height": 60, "x": 100, "y": 70 }
                  ],
                  "edges": [],
                  "constraints": {}
                }
                """);

        assertEquals(0, cli().execute("route-repair", "--request", request.toString(), "--result", result.toString()));

        JsonNode warning = warning(JsonFiles.read(result), "LAYOUT_NODE_OVERLAP");
        assertEquals("first", warning.path("nodeIds").get(0).asText());
        assertEquals("second", warning.path("nodeIds").get(1).asText());
        assertEquals(40, warning.path("nodeBounds").get(0).path("x").asInt());
        assertEquals(40, warning.path("nodeBounds").get(0).path("y").asInt());
        assertEquals(120, warning.path("nodeBounds").get(0).path("w").asInt());
        assertEquals(70, warning.path("nodeBounds").get(0).path("h").asInt());
        assertEquals(100, warning.path("nodeBounds").get(1).path("x").asInt());
        assertEquals(70, warning.path("nodeBounds").get(1).path("y").asInt());
        assertEquals(100, warning.path("nodeBounds").get(1).path("w").asInt());
        assertEquals(60, warning.path("nodeBounds").get(1).path("h").asInt());
    }

    @Test
    void lockedNodeWarningsCarryRequestedAndProducedCoordinates() throws Exception {
        Path resultPath = tempDir.resolve("locked.json");

        assertEquals(0, cli().execute("layout-elk", "--request", fixture("layout-elk-java/locked-node-warning.request.json").toString(), "--result", resultPath.toString()));

        JsonNode warning = warning(JsonFiles.read(resultPath), "LAYOUT_LOCKED_NODE_RESTORED");
        assertEquals("locked", warning.path("nodeId").asText());
        assertEquals(300, warning.path("requested").path("x").asInt());
        assertEquals(300, warning.path("requested").path("y").asInt());
        assertTrue(warning.path("produced").has("x"));
        assertTrue(warning.path("produced").has("y"));
    }

    @Test
    void globalPolishImprovesWhenSafeAndReturnsOriginalWhenNoImprovementExists() throws Exception {
        Path improved = tempDir.resolve("polished.json");
        Path unchanged = tempDir.resolve("unchanged.json");

        assertEquals(0, cli().execute("global-polish", "--request", fixture("global-polish/overlap-cluster.request.json").toString(), "--result", improved.toString()));
        JsonNode improvedResult = JsonFiles.read(improved);
        assertTrue(improvedResult.path("afterMetrics").path("nodeOverlaps").asInt() <= improvedResult.path("beforeMetrics").path("nodeOverlaps").asInt());
        assertFalse(improvedResult.path("displacements").isEmpty());

        assertEquals(0, cli().execute("global-polish", "--request", fixture("global-polish/no-improvement.request.json").toString(), "--result", unchanged.toString()));
        JsonNode unchangedResult = JsonFiles.read(unchanged);
        assertTrue(unchangedResult.path("warnings").toString().contains("LAYOUT_GLOBAL_POLISH_NO_IMPROVEMENT"));
    }

    @Test
    void materializeOefAppliesLayoutResultToNestedViewWithSnapping() throws Exception {
        Path source = fixture("application-cooperation.oef.xml");
        Path materialized = tempDir.resolve("application-cooperation.materialized.oef.xml");

        assertEquals(0, cli().execute(
                "materialize-oef",
                "--oef", source.toString(),
                "--view", "id-view-application-cooperation",
                "--result", fixture("materialize-oef/layout-elk.result.json").toString(),
                "--out", materialized.toString(),
                "--snap-grid", "10"));

        Document document = parseXml(materialized);
        Element container = elementById(document, "id-node-collab-commerce");
        Element service = elementById(document, "id-node-svc-checkout");
        Element connection = elementById(document, "id-conn-http-serves-web");

        assertEquals("40", container.getAttribute("x"));
        assertEquals("430", service.getAttribute("x"));
        assertEquals("80", service.getAttribute("y"));
        assertEquals("id-node-collab-commerce", ((Element) service.getParentNode()).getAttribute("identifier"));
        assertEquals("id-rel-http-serves-web", connection.getAttribute("relationshipRef"));
        assertEquals("id-node-iface-checkout-http", connection.getAttribute("source"));
        assertEquals("id-node-app-web", connection.getAttribute("target"));

        NodeList bendpoints = connection.getElementsByTagNameNS("*", "bendpoint");
        assertEquals(2, bendpoints.getLength());
        assertEquals("580", ((Element) bendpoints.item(0)).getAttribute("x"));
        assertEquals("570", ((Element) bendpoints.item(0)).getAttribute("y"));
        assertEquals("220", ((Element) bendpoints.item(1)).getAttribute("x"));
        assertEquals("570", ((Element) bendpoints.item(1)).getAttribute("y"));
    }

    @Test
    void materializeOefCoversRouteRepairAndGlobalPolishResults() throws Exception {
        assertCanMaterialize("route-repair.result.json");
        assertCanMaterialize("global-polish.result.json");
    }

    @Test
    void materializeOefCanRejectWarningResultsBeforeWritingOutput() {
        Path materialized = tempDir.resolve("warning.oef.xml");

        assertEquals(1, cli().execute(
                "materialize-oef",
                "--oef", fixture("application-cooperation.oef.xml").toString(),
                "--view", "id-view-application-cooperation",
                "--result", fixture("materialize-oef/warning.result.json").toString(),
                "--out", materialized.toString(),
                "--fail-on-warning"));
        assertFalse(Files.exists(materialized));
    }

    @Test
    void materializeOefCanRunSourceGeometryGate() {
        Path materialized = tempDir.resolve("off-grid.oef.xml");

        assertEquals(1, cli().execute(
                "materialize-oef",
                "--oef", fixture("application-cooperation.oef.xml").toString(),
                "--view", "id-view-application-cooperation",
                "--result", fixture("materialize-oef/off-grid.result.json").toString(),
                "--out", materialized.toString(),
                "--run-source-gate"));
        assertTrue(Files.exists(materialized));
    }

    @Test
    void realisticNestedElkFixturesCompleteSourceGateLoop() throws Exception {
        assertRealisticNestedFixturePassesSourceGate(
                "application-cooperation-compound-trust-boundaries",
                "id-view-realistic-application-cooperation",
                "id-node-external-identity-interface",
                "id-node-external-identity-provider");
        assertRealisticNestedFixturePassesSourceGate(
                "technology-usage-hosting-stack",
                "id-view-realistic-technology-usage",
                "id-node-function-runtime",
                "id-node-function-app");
        assertRealisticNestedFixturePassesSourceGate(
                "service-realization-ui-container",
                "id-view-realistic-service-realization",
                "id-node-ui-route-signup",
                "id-node-ui-component");
    }

    private ArchLayoutCli cli() {
        return new ArchLayoutCli(new PrintStream(new ByteArrayOutputStream()), new PrintStream(new ByteArrayOutputStream()));
    }

    private static Path fixture(String name) {
        return LayoutPaths.referencesDir().resolve("fixtures").resolve(name);
    }

    private static JsonNode node(JsonNode result, String id) {
        for (JsonNode node : result.path("nodeGeometry")) {
            if (id.equals(node.path("id").asText())) {
                return node;
            }
        }
        throw new AssertionError("Missing node " + id);
    }

    private static JsonNode warning(JsonNode result, String code) {
        for (JsonNode warning : result.path("warnings")) {
            if (code.equals(warning.path("code").asText())) {
                return warning;
            }
        }
        throw new AssertionError("Missing warning " + code + " in " + result.path("warnings"));
    }

    private void assertCanMaterialize(String resultFixture) throws Exception {
        Path materialized = tempDir.resolve(resultFixture + ".oef.xml");

        assertEquals(0, cli().execute(
                "materialize-oef",
                "--oef", fixture("application-cooperation.oef.xml").toString(),
                "--view", "id-view-application-cooperation",
                "--result", fixture("materialize-oef/" + resultFixture).toString(),
                "--out", materialized.toString(),
                "--snap-grid", "10"));
        assertTrue(Files.exists(materialized));
        assertEquals("100", elementById(parseXml(materialized), "id-node-app-payments").getAttribute("x"));
    }

    private void assertRealisticNestedFixturePassesSourceGate(
            String fixtureName,
            String viewId,
            String nestedNodeId,
            String parentNodeId) throws Exception {
        Path result = tempDir.resolve(fixtureName + ".result.json");
        Path materialized = tempDir.resolve(fixtureName + ".oef.xml");

        assertEquals(0, cli().execute(
                "layout-elk",
                "--request", fixture("layout-elk-realistic/" + fixtureName + ".request.json").toString(),
                "--result", result.toString()));
        assertEquals(0, cli().execute("validate-result", "--result", result.toString()));

        assertEquals(0, cli().execute(
                "materialize-oef",
                "--oef", fixture("layout-elk-realistic/" + fixtureName + ".oef.xml").toString(),
                "--view", viewId,
                "--result", result.toString(),
                "--out", materialized.toString(),
                "--snap-grid", "10",
                "--run-source-gate"));

        Document document = parseXml(materialized);
        assertEquals(parentNodeId, ((Element) elementById(document, nestedNodeId).getParentNode()).getAttribute("identifier"));
        assertTenPixelGrid(document);
    }

    private static void assertTenPixelGrid(Document document) {
        NodeList all = document.getElementsByTagNameNS("*", "*");
        for (int index = 0; index < all.getLength(); index++) {
            Node node = all.item(index);
            if (node instanceof Element element && ("node".equals(element.getLocalName()) || "bendpoint".equals(element.getLocalName()))) {
                assertMultipleOfTen(element, "x");
                assertMultipleOfTen(element, "y");
                assertMultipleOfTen(element, "w");
                assertMultipleOfTen(element, "h");
            }
        }
    }

    private static void assertMultipleOfTen(Element element, String attribute) {
        if (element.hasAttribute(attribute)) {
            assertEquals(0, Integer.parseInt(element.getAttribute(attribute)) % 10, element.getAttribute("identifier") + " " + attribute);
        }
    }

    private static Document parseXml(Path path) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        return factory.newDocumentBuilder().parse(path.toFile());
    }

    private static Element elementById(Document document, String id) {
        NodeList all = document.getElementsByTagNameNS("*", "*");
        for (int index = 0; index < all.getLength(); index++) {
            Node node = all.item(index);
            if (node instanceof Element element && id.equals(element.getAttribute("identifier"))) {
                return element;
            }
        }
        throw new AssertionError("Missing XML element " + id);
    }
}
