package com.souroldgeezer.architecture.layout;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ArchLayoutCliTest {
    @TempDir
    Path tempDir;

    @Test
    void versionCommandPrintsDeterministicNameAndExitsZero() {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        int exitCode = new ArchLayoutCli(new PrintStream(out), new PrintStream(new ByteArrayOutputStream()))
                .execute("--version");

        assertEquals(0, exitCode);
        assertTrue(out.toString().contains("arch-layout 0.21.0"));
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
}
