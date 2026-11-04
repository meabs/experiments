package com.example.accounts.web;

/** 409: the resource is not in a state that allows this. */
public class ConflictException extends RuntimeException {
    public ConflictException(String message) {
        super(message);
    }
}
