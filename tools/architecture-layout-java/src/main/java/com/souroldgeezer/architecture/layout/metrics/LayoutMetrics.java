package com.souroldgeezer.architecture.layout.metrics;

public record LayoutMetrics(
        int nodeOverlaps,
        int connectorNodeIntersections,
        int connectorCrossings,
        int maxBends,
        double averageBends,
        int canvasWidth,
        int canvasHeight,
        int lockedNodeDisplacement,
        int movableNodeDisplacement) {
}
