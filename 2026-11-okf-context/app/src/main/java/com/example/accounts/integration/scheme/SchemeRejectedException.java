package com.example.accounts.integration.scheme;

/** The scheme refused the instruction. {@code code} is the scheme's reason code. */
public class SchemeRejectedException extends RuntimeException {

    private final String code;

    public SchemeRejectedException(String code, String message) {
        super(message);
        this.code = code;
    }

    public String getCode() {
        return code;
    }
}
