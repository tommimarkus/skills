package com.souroldgeezer.architecture.layout.geometry;

import java.util.ArrayList;
import java.util.List;

public record Route(List<Point> points) {
    public List<Segment> segments() {
        List<Segment> segments = new ArrayList<>();
        for (int i = 1; i < points.size(); i++) {
            Point previous = points.get(i - 1);
            Point current = points.get(i);
            if (!previous.equals(current)) {
                segments.add(new Segment(previous, current));
            }
        }
        return segments;
    }

    public int bendCount() {
        int bends = 0;
        List<Segment> segments = segments();
        for (int i = 1; i < segments.size(); i++) {
            if (segments.get(i - 1).horizontal() != segments.get(i).horizontal()) {
                bends++;
            }
        }
        return bends;
    }

    public Route withoutRedundantPoints() {
        if (points.size() <= 2) {
            return this;
        }
        List<Point> simplified = new ArrayList<>();
        simplified.add(points.get(0));
        for (int i = 1; i < points.size() - 1; i++) {
            Point before = simplified.get(simplified.size() - 1);
            Point current = points.get(i);
            Point after = points.get(i + 1);
            boolean collinear = (before.x() == current.x() && current.x() == after.x())
                    || (before.y() == current.y() && current.y() == after.y());
            boolean tinyDogleg = Math.abs(before.x() - current.x()) + Math.abs(before.y() - current.y()) <= 2
                    || Math.abs(after.x() - current.x()) + Math.abs(after.y() - current.y()) <= 2;
            if (!collinear && !tinyDogleg) {
                simplified.add(current);
            }
        }
        simplified.add(points.get(points.size() - 1));
        return new Route(simplified);
    }
}
