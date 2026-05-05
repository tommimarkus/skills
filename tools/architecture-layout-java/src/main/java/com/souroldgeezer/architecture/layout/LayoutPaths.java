package com.souroldgeezer.architecture.layout;

import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;

public final class LayoutPaths {
    private static final String REFERENCES = "souroldgeezer-architecture/skills/architecture-design/references";

    private LayoutPaths() {
    }

    public static Path referencesDir() {
        String fromEnv = System.getenv("ARCH_LAYOUT_REFERENCES");
        if (fromEnv != null && !fromEnv.isBlank()) {
            return Path.of(fromEnv).toAbsolutePath().normalize();
        }

        Optional<Path> fromCwd = findFrom(Path.of("").toAbsolutePath());
        if (fromCwd.isPresent()) {
            return fromCwd.get();
        }

        try {
            Path location = Path.of(LayoutPaths.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            if (Files.isRegularFile(location) && location.getParent() != null && location.getParent().getFileName().toString().equals("bin")) {
                return location.getParent().getParent().toAbsolutePath().normalize();
            }
            Optional<Path> fromClassPath = findFrom(location);
            if (fromClassPath.isPresent()) {
                return fromClassPath.get();
            }
        } catch (URISyntaxException ignored) {
            // Fall through to the deterministic relative path.
        }

        return Path.of(REFERENCES).toAbsolutePath().normalize();
    }

    private static Optional<Path> findFrom(Path start) {
        Path cursor = start.toAbsolutePath().normalize();
        while (cursor != null) {
            Path candidate = cursor.resolve(REFERENCES);
            if (Files.isDirectory(candidate)) {
                return Optional.of(candidate);
            }
            cursor = cursor.getParent();
        }
        return Optional.empty();
    }
}
