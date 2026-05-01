package com.souroldgeezer.architecture.layout.geometry;

public record Rectangle(int x, int y, int width, int height) {
    public int left() {
        return x;
    }

    public int right() {
        return x + width;
    }

    public int top() {
        return y;
    }

    public int bottom() {
        return y + height;
    }

    public Point center() {
        return new Point(x + width / 2, y + height / 2);
    }

    public Rectangle expandedBy(int margin) {
        return new Rectangle(x - margin, y - margin, width + margin * 2, height + margin * 2);
    }

    public boolean contains(Point point) {
        return point.x() >= left() && point.x() <= right() && point.y() >= top() && point.y() <= bottom();
    }

    public boolean strictlyContains(Point point) {
        return point.x() > left() && point.x() < right() && point.y() > top() && point.y() < bottom();
    }

    public boolean intersects(Rectangle other) {
        return left() < other.right() && right() > other.left() && top() < other.bottom() && bottom() > other.top();
    }
}
