package com.souroldgeezer.architecture.layout;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;

public final class LayoutProvenanceReporter {
    public ObjectNode report(Input input) {
        ObjectNode report = JsonFiles.MAPPER.createObjectNode();
        report.put("schemaVersion", "1.0");
        report.put("generatedBy", VersionCommand.VERSION);
        ArrayNode views = report.putArray("views");
        views.add(view(input));
        return report;
    }

    private static ObjectNode view(Input input) {
        ObjectNode view = JsonFiles.MAPPER.createObjectNode();
        JsonNode backend = input.result() == null ? JsonFiles.MAPPER.createObjectNode() : input.result().path("backend");
        String backendName = input.result() == null ? "not-run" : backend.path("name").asText("not-run");
        String backendVersion = input.result() == null ? "" : backend.path("version").asText("");
        String mode = input.result() == null ? input.selectedGeometryPath() : input.result().path("mode").asText(input.selectedGeometryPath());
        String viewpoint = input.request().path("view").path("viewpoint").asText("");

        view.put("viewId", input.viewId());
        view.put("viewpoint", viewpoint);
        view.put("layoutIntent", input.layoutIntent());
        view.put("selectedGeometryPath", input.selectedGeometryPath());
        view.put("backend", backendName);
        view.put("backendVersion", backendVersion);
        view.put("backendMode", backend.path("mode").asText(mode));
        view.put("mode", mode);
        view.put("request", input.requestPath().toString());
        if (input.resultPath() != null) {
            view.put("result", input.resultPath().toString());
        }
        if (input.materializedOefPath() != null) {
            view.put("materializedOef", input.materializedOefPath().toString());
        }
        view.put("sourceGeometryGate", input.sourceGeometryGate());
        view.put("renderGate", input.renderGate());

        ObjectNode commands = view.putObject("commands");
        commands.put("geometry", geometryCommand(input.selectedGeometryPath()));
        commands.put("requestValidation", "validate-request");
        commands.put("resultValidation", input.resultPath() == null ? "not-run" : "validate-result");
        commands.put("materialization", input.materializedOefPath() == null ? "not-run" : "materialize-oef");
        commands.put("renderValidation", input.pngResultPath() == null ? "not-run" : "validate-png");

        ArrayNode postProcessing = view.putArray("postProcessing");
        if (input.snapGrid() > 0) {
            postProcessing.add("snap-" + input.snapGrid() + "px");
        }
        if (input.preserveOefContainment()) {
            postProcessing.add("preserve-oef-containment");
        }
        input.postProcessing().stream().sorted().forEach(postProcessing::add);

        if (input.pngResultPath() != null) {
            ObjectNode pngValidation = view.putObject("pngValidation");
            pngValidation.put("path", input.pngResultPath().toString());
            if (input.pngResult() != null && input.pngResult().isObject()) {
                pngValidation.setAll((ObjectNode) input.pngResult());
            }
        }

        view.put("responseSummary", responseSummary(input, backendName, backendVersion, mode));
        view.put("readmeMarkdown", readmeMarkdown(input, backendName, backendVersion, mode));
        view.put("oefDocumentation", oefDocumentation(input, backendName, backendVersion));
        return view;
    }

    private static String geometryCommand(String selectedGeometryPath) {
        return switch (selectedGeometryPath) {
            case "layout-elk", "route-repair", "global-polish" -> selectedGeometryPath;
            case "deterministic-fallback", "viewpoint-policy", "preserved-authored" -> "not-run";
            default -> selectedGeometryPath;
        };
    }

    private static String responseSummary(Input input, String backendName, String backendVersion, String mode) {
        return input.viewId() + ": " + input.selectedGeometryPath()
                + " (" + backendName + (backendVersion.isBlank() ? "" : " " + backendVersion)
                + ", mode " + mode + "); source geometry gate: " + input.sourceGeometryGate()
                + "; render gate: " + input.renderGate();
    }

    private static String readmeMarkdown(Input input, String backendName, String backendVersion, String mode) {
        return "| " + input.viewId() + " | " + input.selectedGeometryPath() + " | "
                + backendName + (backendVersion.isBlank() ? "" : " " + backendVersion)
                + " | " + mode + " | " + input.sourceGeometryGate() + " | " + input.renderGate() + " |";
    }

    private static String oefDocumentation(Input input, String backendName, String backendVersion) {
        return "Layout provenance: view " + input.viewId()
                + "; geometry path: " + input.selectedGeometryPath()
                + "; backend: " + backendName + (backendVersion.isBlank() ? "" : " " + backendVersion)
                + "; source geometry gate: " + input.sourceGeometryGate()
                + "; render gate: " + input.renderGate() + ".";
    }

    public record Input(
            String viewId,
            String layoutIntent,
            String selectedGeometryPath,
            Path requestPath,
            JsonNode request,
            Path resultPath,
            JsonNode result,
            Path materializedOefPath,
            String sourceGeometryGate,
            Path pngResultPath,
            JsonNode pngResult,
            String renderGate,
            int snapGrid,
            boolean preserveOefContainment,
            List<String> postProcessing) {
    }
}
