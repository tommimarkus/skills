package com.souroldgeezer.architecture.layout;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.ObjectWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public final class JsonFiles {
    public static final ObjectMapper MAPPER = new ObjectMapper();
    private static final ObjectWriter PRETTY = MAPPER.writerWithDefaultPrettyPrinter();

    private JsonFiles() {
    }

    public static JsonNode read(Path path) throws IOException {
        return MAPPER.readTree(path.toFile());
    }

    public static void write(Path path, JsonNode node) throws IOException {
        Path parent = path.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        PRETTY.writeValue(path.toFile(), node);
    }
}
