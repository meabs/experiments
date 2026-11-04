package com.example.accounts.web;

/** 403: the caller can see the resource but may not do this to it. */
public class ForbiddenException extends RuntimeException {
    public ForbiddenException(String message) {
        super(message);
    }
}
