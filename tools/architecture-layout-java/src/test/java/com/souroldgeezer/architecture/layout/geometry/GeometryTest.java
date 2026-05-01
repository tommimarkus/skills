package com.souroldgeezer.architecture.layout.geometry;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class GeometryTest {
    @Test
    void rectangleEdgeTouchingIsNotStrictOverlap() {
        Rectangle first = new Rectangle(0, 0, 100, 60);
        Rectangle touching = new Rectangle(100, 0, 100, 60);
        Rectangle overlapping = new Rectangle(99, 0, 100, 60);

        assertFalse(first.intersects(touching));
        assertTrue(first.intersects(overlapping));
        assertTrue(first.contains(new Point(100, 60)));
        assertFalse(first.strictlyContains(new Point(100, 60)));
    }

    @Test
    void routeCountsBendsAndSegmentsIntersectBodies() {
        Route route = new Route(List.of(new Point(0, 0), new Point(100, 0), new Point(100, 100), new Point(160, 100)));

        assertEquals(2, route.bendCount());
        assertTrue(route.segments().get(1).intersects(new Rectangle(90, 20, 30, 40)));
    }
}
