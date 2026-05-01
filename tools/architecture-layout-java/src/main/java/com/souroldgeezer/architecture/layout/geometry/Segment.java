package com.souroldgeezer.architecture.layout.geometry;

public record Segment(Point start, Point end) {
    public boolean horizontal() {
        return start.y() == end.y();
    }

    public boolean vertical() {
        return start.x() == end.x();
    }

    public int length() {
        return Math.abs(start.x() - end.x()) + Math.abs(start.y() - end.y());
    }

    public boolean intersects(Rectangle rectangle) {
        if (horizontal()) {
            int y = start.y();
            if (y <= rectangle.top() || y >= rectangle.bottom()) {
                return false;
            }
            int minX = Math.min(start.x(), end.x());
            int maxX = Math.max(start.x(), end.x());
            return minX < rectangle.right() && maxX > rectangle.left();
        }
        if (vertical()) {
            int x = start.x();
            if (x <= rectangle.left() || x >= rectangle.right()) {
                return false;
            }
            int minY = Math.min(start.y(), end.y());
            int maxY = Math.max(start.y(), end.y());
            return minY < rectangle.bottom() && maxY > rectangle.top();
        }
        return rectangle.contains(start) || rectangle.contains(end);
    }

    public boolean crosses(Segment other) {
        if (horizontal() && other.vertical()) {
            return between(other.start().x(), start.x(), end.x())
                    && between(start.y(), other.start().y(), other.end().y())
                    && !touchesEndpoint(new Point(other.start().x(), start.y()))
                    && !other.touchesEndpoint(new Point(other.start().x(), start.y()));
        }
        if (vertical() && other.horizontal()) {
            return other.crosses(this);
        }
        return false;
    }

    private boolean touchesEndpoint(Point point) {
        return point.equals(start) || point.equals(end);
    }

    private static boolean between(int value, int a, int b) {
        return value > Math.min(a, b) && value < Math.max(a, b);
    }
}
