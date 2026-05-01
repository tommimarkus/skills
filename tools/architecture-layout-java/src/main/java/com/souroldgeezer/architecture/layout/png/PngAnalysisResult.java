package com.souroldgeezer.architecture.layout.png;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.JsonFiles;

public record PngAnalysisResult(
        boolean valid,
        int width,
        int height,
        int colorDiversity,
        boolean blank,
        boolean tiny,
        boolean croppedToEdge,
        boolean excessiveWhitespace,
        double changedPixelRatio,
        String message) {
    public ObjectNode toJson() {
        ObjectNode node = JsonFiles.MAPPER.createObjectNode();
        node.put("valid", valid);
        node.put("width", width);
        node.put("height", height);
        node.put("colorDiversity", colorDiversity);
        node.put("blank", blank);
        node.put("tiny", tiny);
        node.put("croppedToEdge", croppedToEdge);
        node.put("excessiveWhitespace", excessiveWhitespace);
        node.put("changedPixelRatio", changedPixelRatio);
        node.put("message", message);
        return node;
    }
}
