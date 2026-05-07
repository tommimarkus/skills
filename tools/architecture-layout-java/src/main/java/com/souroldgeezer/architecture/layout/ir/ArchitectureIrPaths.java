package com.souroldgeezer.architecture.layout.ir;

import java.nio.file.Path;

public record ArchitectureIrPaths(Path root) {
    public Path model() {
        return root.resolve("model.yaml");
    }

    public Path views() {
        return root.resolve("views.yaml");
    }

    public Path layout() {
        return root.resolve("layout.yaml");
    }

    public Path requestsDir() {
        return root.resolve("layout-requests");
    }

    public Path resultsDir() {
        return root.resolve("layout-results");
    }

    public Path provenanceDir() {
        return root.resolve("layout-provenance");
    }

    public Path request(String viewId) {
        return requestsDir().resolve(viewId + ".request.json");
    }

    public Path result(String viewId) {
        return resultsDir().resolve(viewId + ".result.json");
    }

    public Path provenance(String viewId) {
        return provenanceDir().resolve(viewId + ".provenance.json");
    }
}
