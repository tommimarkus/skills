package com.souroldgeezer.architecture.layout;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class ValidationResult {
    private final List<String> diagnostics = new ArrayList<>();

    public void add(String diagnostic) {
        diagnostics.add(diagnostic);
    }

    public boolean ok() {
        return diagnostics.isEmpty();
    }

    public List<String> diagnostics() {
        return Collections.unmodifiableList(diagnostics);
    }
}
