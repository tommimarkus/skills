package com.souroldgeezer.architecture.layout.polish;

import com.souroldgeezer.architecture.layout.metrics.LayoutMetrics;

public final class LayoutScorer {
    public int score(LayoutMetrics metrics) {
        int hardViolations = metrics.lockedNodeDisplacement() > 0 ? 100_000 : 0;
        return hardViolations
                + metrics.nodeOverlaps() * 1_000
                + metrics.connectorNodeIntersections() * 800
                + metrics.connectorCrossings() * 300
                + metrics.maxBends() * 20
                + metrics.movableNodeDisplacement()
                + Math.max(0, metrics.canvasWidth() - 1200)
                + Math.max(0, metrics.canvasHeight() - 1000);
    }
}
