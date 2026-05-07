package com.souroldgeezer.architecture.layout.ir;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.souroldgeezer.architecture.layout.ArchLayoutCli;
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
