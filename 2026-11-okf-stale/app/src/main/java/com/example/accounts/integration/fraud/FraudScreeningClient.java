package com.example.accounts.integration.fraud;

/** Client for the bank's fraud screening service. */
public interface FraudScreeningClient {

    /** @throws FraudScreeningUnavailableException if the service does not answer within the configured timeout */
    Decision screen(ScreeningRequest request);
}
