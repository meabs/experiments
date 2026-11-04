package com.example.accounts.integration.scheme;

/** The scheme gateway did not answer within the configured timeout. */
public class SchemeTimeoutException extends RuntimeException {

    public SchemeTimeoutException(String message, Throwable cause) {
        super(message, cause);
    }
}
