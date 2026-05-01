package com.souroldgeezer.architecture.layout;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Collection;

public final class WarningFactory {
    private WarningFactory() {
    }

    public static ObjectNode warning(String code, String severity, String message, Collection<String> subjectIds) {
        ObjectNode warning = JsonFiles.MAPPER.createObjectNode();
        warning.put("code", code);
        warning.put("severity", severity);
        warning.put("message", message);
        ArrayNode subjects = warning.putArray("subjectIds");
        subjectIds.stream().sorted().forEach(subjects::add);
        return warning;
    }
}
