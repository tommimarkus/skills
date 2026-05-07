package com.souroldgeezer.architecture.layout.ir;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.souroldgeezer.architecture.layout.ArchLayoutCli;
import com.souroldgeezer.architecture.layout.JsonFiles;
import com.souroldgeezer.architecture.layout.LayoutPaths;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ArchitectureIrCliTest {
    @TempDir
    Path tempDir;

    @Test
    void validateIrAcceptsServiceRealizationFixture() {
        Path archDir = fixture("architecture-ir/service-realization");
        assertEquals(0, cli().execute("validate-ir", "--arch-dir", archDir.toString()));
    }

    @Test
    void validateIrRejectsMissingElementReference() throws Exception {
        Path archDir = tempDir.resolve("bad-arch");
        copyFixtureDirectory(fixture("architecture-ir/service-realization"), archDir);
        Files.writeString(
                archDir.resolve("views.yaml"),
                Files.readString(archDir.resolve("views.yaml")).replace("id-orders-api", "id-missing-api"));

        assertEquals(1, cli().execute("validate-ir", "--arch-dir", archDir.toString()));
    }

    @Test
    void importOefWritesIrAndPreservesArchitectGeometryAsLocks() throws Exception {
        Path archDir = tempDir.resolve("imported.arch");
        Path oef = fixture("service-realization.oef.xml");

        assertEquals(0, cli().execute("import-oef", "--oef", oef.toString(), "--arch-dir", archDir.toString()));
        assertEquals(0, cli().execute("validate-ir", "--arch-dir", archDir.toString()));

        JsonNode layout = YamlFiles.read(archDir.resolve("layout.yaml"));
        assertTrue(layout.toString().contains("architect-edited-oef"));
        assertTrue(layout.toString().contains("id-node-process"));
        assertTrue(layout.toString().contains("id-conn-page-route"));
    }

    @Test
    void compileIrEmitsSchemaValidLayoutRequest() throws Exception {
        Path archDir = fixture("architecture-ir/service-realization");

        assertEquals(0, cli().execute("compile-ir", "--arch-dir", archDir.toString()));
        Path request = archDir.resolve("layout-requests/id-view-service-realization.request.json");

        assertTrue(Files.exists(request));
        assertEquals(0, cli().execute("validate-request", "--request", request.toString()));
        JsonNode requestJson = JsonFiles.read(request);
        assertEquals("Service Realization", requestJson.path("view").path("viewpoint").asText());
        assertEquals("layout-elk", requestJson.path("selectedGeometryPath").asText(""));
    }

    @Test
    void buildIrArtifactsRunsLayoutAndWritesResult() throws Exception {
        Path archDir = tempDir.resolve("service-realization.arch");
        copyFixtureDirectory(fixture("architecture-ir/service-realization"), archDir);

        assertEquals(0, cli().execute("build-ir-artifacts", "--arch-dir", archDir.toString()));

        Path request = archDir.resolve("layout-requests/id-view-service-realization.request.json");
        Path result = archDir.resolve("layout-results/id-view-service-realization.result.json");
        assertEquals(0, cli().execute("validate-request", "--request", request.toString()));
        assertEquals(0, cli().execute("validate-result", "--result", result.toString(), "--strict"));
    }

    @Test
    void exportOefUsesCurrentIrAndLayoutResult() throws Exception {
        Path archDir = tempDir.resolve("service-realization.arch");
        Path out = tempDir.resolve("service-realization.oef.xml");
        copyFixtureDirectory(fixture("architecture-ir/service-realization"), archDir);

        assertEquals(0, cli().execute("build-ir-artifacts", "--arch-dir", archDir.toString()));
        assertEquals(0, cli().execute("export-oef", "--arch-dir", archDir.toString(), "--out", out.toString()));

        String xml = Files.readString(out);
        assertTrue(xml.contains("identifier=\"id-place-order-process\""));
        assertTrue(xml.contains("relationshipRef=\"id-rel-service-realises-process\""));
        assertTrue(xml.contains("viewpoint=\"Service Realization\""));
    }

    @Test
    void freshnessReportsReviewOnlyDriftWithoutMutation() throws Exception {
        Path archDir = tempDir.resolve("service-realization.arch");
        Path oef = tempDir.resolve("service-realization.oef.xml");
        copyFixtureDirectory(fixture("architecture-ir/service-realization"), archDir);
        Files.writeString(oef, "<model/>");

        int exit = cli().execute("freshness", "--arch-dir", archDir.toString(), "--oef", oef.toString(), "--mode", "review");

        assertEquals(1, exit);
    }

    @Test
    void freshnessAcceptsCurrentBuildArtifacts() throws Exception {
        Path archDir = tempDir.resolve("service-realization.arch");
        Path oef = tempDir.resolve("service-realization.oef.xml");
        copyFixtureDirectory(fixture("architecture-ir/service-realization"), archDir);
        assertEquals(0, cli().execute("build-ir-artifacts", "--arch-dir", archDir.toString()));
        assertEquals(0, cli().execute("export-oef", "--arch-dir", archDir.toString(), "--out", oef.toString()));

        assertEquals(0, cli().execute("freshness", "--arch-dir", archDir.toString(), "--oef", oef.toString(), "--mode", "build"));
    }

    @Test
    void validateIrRejectsMissingLockTarget() {
        assertEquals(1, cli().execute("validate-ir", "--arch-dir", fixture("architecture-ir/invalid/missing-lock-target").toString()));
    }

    @Test
    void oefImportBuildExportRoundTripPreservesIdentifiers() throws Exception {
        Path imported = tempDir.resolve("imported.arch");
        Path exported = tempDir.resolve("exported.oef.xml");

        assertEquals(0, cli().execute("import-oef", "--oef", fixture("service-realization.oef.xml").toString(), "--arch-dir", imported.toString()));
        assertEquals(0, cli().execute("build-ir-artifacts", "--arch-dir", imported.toString(), "--allow-warning"));
        assertEquals(0, cli().execute("export-oef", "--arch-dir", imported.toString(), "--out", exported.toString()));

        String xml = Files.readString(exported);
        assertTrue(xml.contains("identifier=\"id-place-order-process\""));
        assertTrue(xml.contains("identifier=\"id-rel-service-realises-process\""));
        assertTrue(xml.contains("identifier=\"id-view-service-realization\""));
    }

    private ArchLayoutCli cli() {
        return new ArchLayoutCli(new PrintStream(new ByteArrayOutputStream()), new PrintStream(new ByteArrayOutputStream()));
    }

    private static Path fixture(String name) {
        return LayoutPaths.referencesDir().resolve("fixtures").resolve(name);
    }

    private static void copyFixtureDirectory(Path source, Path target) throws IOException {
        try (var paths = Files.walk(source)) {
            for (Path path : paths.toList()) {
                Path destination = target.resolve(source.relativize(path));
                if (Files.isDirectory(path)) {
                    Files.createDirectories(destination);
                } else {
                    Files.createDirectories(destination.getParent());
                    Files.copy(path, destination);
                }
            }
        }
    }
}
