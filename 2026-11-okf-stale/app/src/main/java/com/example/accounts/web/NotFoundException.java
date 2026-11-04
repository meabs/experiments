package com.example.accounts.web;

/** 404. Also used when the caller may not know the resource exists (see the API conventions in README.md). */
public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) {
        super(message);
    }
}
