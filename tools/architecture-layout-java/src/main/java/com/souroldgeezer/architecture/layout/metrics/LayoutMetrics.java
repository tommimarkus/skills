package com.souroldgeezer.architecture.layout.metrics;

public record LayoutMetrics(
        int nodeOverlaps,
        int sameParentNodeOverlaps,
        int parentChildContainments,
        int childOutsideParentBounds,
        int connectorNodeIntersections,
        int connectorUnrelatedNodeIntersections,
        int connectorContainerBoundaryCrossings,
        int connectorCrossings,
        int maxBends,
        double averageBends,
        int canvasWidth,
        int canvasHeight,
        int lockedNodeDisplacement,
        int movableNodeDisplacement) {
}
