package com.souroldgeezer.architecture.layout.geometry;

import java.util.Comparator;
import java.util.List;

public final class PortAssigner {
    private PortAssigner() {
    }

    public static Port portToward(Rectangle from, Rectangle to) {
        int dx = to.center().x() - from.center().x();
        int dy = to.center().y() - from.center().y();
        if (Math.abs(dx) > Math.abs(dy)) {
            return dx >= 0
                    ? new Port(PortSide.EAST, new Point(from.right(), from.center().y()))
                    : new Port(PortSide.WEST, new Point(from.left(), from.center().y()));
        }
        return dy >= 0
                ? new Port(PortSide.SOUTH, new Point(from.center().x(), from.bottom()))
                : new Port(PortSide.NORTH, new Point(from.center().x(), from.top()));
    }

    public static List<PortSide> deterministicSides() {
        return List.of(PortSide.NORTH, PortSide.EAST, PortSide.SOUTH, PortSide.WEST).stream()
                .sorted(Comparator.comparing(PortSide::wireName))
                .toList();
    }
}
