package com.souroldgeezer.architecture.layout;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.geometry.Point;
import com.souroldgeezer.architecture.layout.geometry.Rectangle;
import com.souroldgeezer.architecture.layout.geometry.Segment;
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

    public static ObjectNode point(Point point) {
        ObjectNode node = JsonFiles.MAPPER.createObjectNode();
        node.put("x", point.x());
        node.put("y", point.y());
        return node;
    }

    public static ObjectNode rectangle(Rectangle rectangle) {
        ObjectNode node = JsonFiles.MAPPER.createObjectNode();
        node.put("x", rectangle.x());
        node.put("y", rectangle.y());
        node.put("w", rectangle.width());
        node.put("h", rectangle.height());
        return node;
    }

    public static ObjectNode segment(Segment segment) {
        ObjectNode node = JsonFiles.MAPPER.createObjectNode();
        node.put("x1", segment.start().x());
        node.put("y1", segment.start().y());
        node.put("x2", segment.end().x());
        node.put("y2", segment.end().y());
        return node;
    }
}
