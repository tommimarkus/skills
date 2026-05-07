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
