package com.souroldgeezer.architecture.layout.ir;

import com.fasterxml.jackson.databind.JsonNode;
import com.souroldgeezer.architecture.layout.ValidationResult;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.util.ArrayList;
import java.util.List;

public final class ArchitectureIrFreshness {
    public Report check(Path archDir, Path oef, String mode) throws IOException {
        ValidationResult validation = new ArchitectureIrValidator().validate(archDir);
        if (!validation.ok()) {
            return report("inconsistent", decision("inconsistent", mode), validation.diagnostics(), 1);
        }
        ArchitectureIrPaths paths = new ArchitectureIrPaths(archDir);
        JsonNode model = YamlFiles.read(paths.model());
        JsonNode views = YamlFiles.read(paths.views());
        if (!Files.isRegularFile(oef)) {
            return report("missing-oef", decision("missing-oef", mode), List.of("OEF file is missing: " + oef), 1);
        }
        List<Path> generated = generatedArtifacts(paths, views);
        List<Path> missing = generated.stream().filter(path -> !Files.isRegularFile(path)).toList();
        if (!missing.isEmpty()) {
            return report("missing-generated", decision("missing-generated", mode), missing.stream().map(path -> "missing generated artifact: " + path).toList(), 1);
        }
        if (!oefContainsCurrentIds(oef, model, views)) {
            return report("inconsistent", decision("inconsistent", mode), List.of("OEF content does not contain current IR identifiers"), 1);
        }

        FileTime sourceTime = latest(List.of(paths.model(), paths.views(), paths.layout()));
        FileTime generatedTime = latest(generated);
        FileTime oefTime = Files.getLastModifiedTime(oef);
        if (sourceTime.compareTo(generatedTime) > 0) {
            return report("ir-newer-than-generated", decision("ir-newer-than-generated", mode), List.of("IR YAML is newer than generated layout artifacts"), 1);
        }
        if (generatedTime.compareTo(oefTime) > 0) {
            return report("generated-newer-than-oef", decision("generated-newer-than-oef", mode), List.of("generated layout artifacts are newer than OEF export"), 1);
        }
        return report("current", "current", List.of(), 0);
    }

    private static List<Path> generatedArtifacts(ArchitectureIrPaths paths, JsonNode views) {
        List<Path> generated = new ArrayList<>();
        for (JsonNode view : views.path("views")) {
            String viewId = view.path("id").asText();
            generated.add(paths.request(viewId));
            generated.add(paths.result(viewId));
            generated.add(paths.provenance(viewId));
        }
        return generated;
    }

    private static boolean oefContainsCurrentIds(Path oef, JsonNode model, JsonNode views) throws IOException {
        String content = Files.readString(oef);
        if (!content.contains(model.path("feature").path("id").asText())) {
            return false;
        }
        for (JsonNode element : model.path("elements")) {
            if (!content.contains(element.path("id").asText())) {
                return false;
            }
        }
        for (JsonNode relationship : model.path("relationships")) {
            if (!content.contains(relationship.path("id").asText())) {
                return false;
            }
        }
        for (JsonNode view : views.path("views")) {
            if (!content.contains(view.path("id").asText())) {
                return false;
            }
        }
        return true;
    }

    private static FileTime latest(List<Path> paths) throws IOException {
        FileTime latest = FileTime.fromMillis(0);
        for (Path path : paths) {
            FileTime modified = Files.getLastModifiedTime(path);
            if (modified.compareTo(latest) > 0) {
                latest = modified;
            }
        }
        return latest;
    }

    private static String decision(String state, String mode) {
        return switch (mode) {
            case "review" -> "report-only";
            case "lookup" -> "read-freshest-no-mutation";
            case "build" -> "oef-newer-than-ir".equals(state) ? "import-oef-before-build" : "regenerate-generated-artifacts";
            case "extract", "repair", "polish", "render" -> "regenerate-generated-artifacts";
            default -> "unsupported-mode";
        };
    }

    private static Report report(String state, String decision, List<String> diagnostics, int exitCode) {
        return new Report(state, decision, diagnostics, exitCode);
    }

    public record Report(String state, String decision, List<String> diagnostics, int exitCode) {
    }
}
