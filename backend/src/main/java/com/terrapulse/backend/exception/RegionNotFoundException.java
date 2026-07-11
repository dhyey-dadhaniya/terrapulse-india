package com.terrapulse.backend.exception;

/**
 * Thrown when a client asks for a region id that does not exist in the database.
 */
public class RegionNotFoundException extends RuntimeException {

    private final Long id;

    public RegionNotFoundException(Long id) {
        super("Region not found with id " + id);
        this.id = id;
    }

    public Long getId() {
        return id;
    }
}
