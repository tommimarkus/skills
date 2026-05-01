package com.souroldgeezer.architecture.layout.geometry;

public enum PortSide {
    NORTH("north"),
    EAST("east"),
    SOUTH("south"),
    WEST("west");

    private final String wireName;

    PortSide(String wireName) {
        this.wireName = wireName;
    }

    public String wireName() {
        return wireName;
    }
}
