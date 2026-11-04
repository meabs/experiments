package com.example.accounts.integration.fraud;

/** The fraud screening service did not answer in time, or answered with an error. */
public class FraudScreeningUnavailableException extends RuntimeException {

    public FraudScreeningUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}
